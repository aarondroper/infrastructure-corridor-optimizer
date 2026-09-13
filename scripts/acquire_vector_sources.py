#!/usr/bin/env python3
"""Acquire configured ArcGIS constraint layers for the bounded S1 envelope."""

from __future__ import annotations

import argparse
import json
import math
import numbers
import shutil
import tempfile
from datetime import datetime, timezone
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ico_model.sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    summarize_arcgis_metadata,
    validate_expected_layers,
    validate_feature_geometries,
    validate_feature_object_ids,
    validate_feature_payload_crs,
    validate_service_crs,
    write_manifest,
)


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SourceValidationError("model configuration must be a JSON object")
    return payload


def _layer_url(source_url: str, layer_id: int) -> str:
    last_segment = source_url.rstrip("/").rsplit("/", 1)[-1]
    return source_url.rstrip("/") if last_segment.isdigit() else f"{source_url.rstrip('/')}/{layer_id}"


def _tile_envelopes(
    envelope: dict[str, float], tile_size_degrees: float | None
) -> list[dict[str, float]]:
    """Split the configured longitude/latitude envelope into deterministic tiles."""

    west, south, east, north = (
        envelope["west"],
        envelope["south"],
        envelope["east"],
        envelope["north"],
    )
    if not (west < east and south < north):
        raise SourceValidationError("processing envelope must have positive dimensions")
    if tile_size_degrees is None:
        tile_size_degrees = max(east - west, north - south)
    if not math.isfinite(tile_size_degrees) or tile_size_degrees <= 0:
        raise SourceValidationError("tile_size_degrees must be finite and positive")
    columns = math.ceil((east - west) / tile_size_degrees)
    rows = math.ceil((north - south) / tile_size_degrees)
    return [
        {
            "west": west + column * tile_size_degrees,
            "south": south + row * tile_size_degrees,
            "east": min(east, west + (column + 1) * tile_size_degrees),
            "north": min(north, south + (row + 1) * tile_size_degrees),
        }
        for row in range(rows)
        for column in range(columns)
    ]


def _tile_size_degrees(config: dict[str, Any], source: dict[str, Any]) -> float | None:
    global_settings = config.get("arcgis_acquisition", {})
    source_settings = source.get("spatial_chunking", {})
    if not isinstance(global_settings, dict) or not isinstance(source_settings, dict):
        raise SourceValidationError("ArcGIS spatial_chunking settings must be objects")
    value = source_settings.get("tile_size_degrees", global_settings.get("tile_size_degrees"))
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SourceValidationError("tile_size_degrees must be numeric")
    return float(value)


def _cache_page_path(
    cache_dir: Path, cache_namespace: str, tile_index: int, page_index: int
) -> Path:
    return (
        cache_dir
        / cache_namespace
        / f"tile-{tile_index:04d}-page-{page_index:05d}.json"
    )


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _acquisition_safety(config: dict[str, Any]) -> dict[str, int]:
    defaults = {
        "max_response_bytes": 32_000_000,
        "max_expected_features": 300_000,
        "max_inventory_ids": 1_000_000,
        "max_expected_pages": 1_000,
        "max_page_bytes": 32_000_000,
        "max_cache_bytes": 8_000_000_000,
        "max_staging_bytes": 4_000_000_000,
        "max_working_set_bytes": 12_000_000_000,
    }
    configured = config.get("acquisition_safety", {})
    if not isinstance(configured, dict):
        raise SourceValidationError("acquisition_safety settings must be an object")
    for key in defaults:
        if key in configured:
            value = configured[key]
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise SourceValidationError(f"acquisition safety limit {key} must be positive")
            defaults[key] = value
    return defaults


def _feature_object_id(feature: dict[str, Any], layer_url: str) -> int:
    attributes = feature.get("attributes")
    if not isinstance(attributes, dict):
        raise SourceValidationError(f"ArcGIS feature has no attributes: {layer_url}")
    value = next(
        (item for key, item in attributes.items() if str(key).lower() == "objectid"),
        None,
    )
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SourceValidationError(f"ArcGIS feature has no valid OBJECTID: {layer_url}") from exc


def _nested_values_equal(left: Any, right: Any, tolerance: float = 1e-6) -> bool:
    """Compare ArcGIS JSON while tolerating tiny reprojection round-off."""

    if isinstance(left, numbers.Real) and isinstance(right, numbers.Real):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _nested_values_equal(left[key], right[key], tolerance) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _nested_values_equal(item_left, item_right, tolerance)
            for item_left, item_right in zip(left, right)
        )
    return left == right


def _features_equivalent(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return _nested_values_equal(left, right)


def _load_cached_page(
    path: Path,
    page_ids: list[int],
    expected_geometry_type: str,
    output_crs: int,
    layer_url: str,
    cache_key: str,
    out_fields: list[str],
) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceValidationError(f"cached ArcGIS page is unreadable: {path}") from exc
    if not isinstance(payload, dict) or payload.get("format") != "ico-arcgis-feature-page-cache":
        raise SourceValidationError(f"cached ArcGIS page has an unsupported schema: {path}")
    if payload.get("object_ids") != page_ids:
        raise SourceValidationError(f"cached ArcGIS page IDs are stale: {path}")
    if payload.get("cache_key") != cache_key or payload.get("out_fields") != out_fields:
        raise SourceValidationError(f"cached ArcGIS page configuration is stale: {path}")
    features = payload.get("features")
    if not isinstance(features, list) or not all(isinstance(feature, dict) for feature in features):
        raise SourceValidationError(f"cached ArcGIS page has no feature list: {path}")
    cached_crs = payload.get("output_crs_epsg")
    if cached_crs != output_crs:
        raise SourceValidationError(f"cached ArcGIS page CRS is stale: {path}")
    validate_feature_object_ids(features, page_ids, layer_url)
    validate_feature_geometries(features, expected_geometry_type, layer_url)
    return features


def _write_cached_page(
    path: Path,
    page_ids: list[int],
    features: list[dict[str, Any]],
    output_crs: int,
    cache_key: str,
    out_fields: list[str],
) -> None:
    write_manifest(
        {
            "schema_version": 1,
            "format": "ico-arcgis-feature-page-cache",
            "cache_key": cache_key,
            "out_fields": out_fields,
            "object_ids": page_ids,
            "output_crs_epsg": output_crs,
            "feature_count": len(features),
            "features": features,
        },
        path,
    )


def _configured_layer_summary(
    client: ArcGISClient,
    source_url: str,
    source_id: str,
    summary: dict[str, Any],
    layer: dict[str, Any],
) -> dict[str, Any]:
    """Resolve a configured layer, filling sparse service summaries from layer metadata."""

    layer_id = layer["layer_id"]
    layer_summary = next(
        (item for item in summary["layers"] if item.get("id") == layer_id), None
    )
    if layer_summary is None:
        raise SourceValidationError(
            f"configured acquisition layer is unavailable: {source_id}:{layer_id}"
        )
    if "type" not in layer_summary or "geometryType" not in layer_summary:
        detail_summary = summarize_arcgis_metadata(
            client.service_metadata(_layer_url(source_url, layer_id))
        )
        detail = next(
            (item for item in detail_summary["layers"] if item.get("id") == layer_id), None
        )
        if detail is None:
            raise SourceValidationError(
                f"configured acquisition layer detail is unavailable: {source_id}:{layer_id}"
            )
        layer_summary = detail
    if layer_summary.get("type") != "Feature Layer":
        raise SourceValidationError(
            f"configured acquisition layer is not queryable: {source_id}:{layer_id}"
        )
    if layer_summary.get("geometryType") != layer["geometry_type"]:
        raise SourceValidationError(
            f"configured acquisition geometry mismatch: {source_id}:{layer_id}"
        )
    return layer_summary


def _acquire_complete_layer(
    client: ArcGISClient,
    layer_url: str,
    layer: dict[str, Any],
    envelope: dict[str, float],
    input_crs: int,
    output_crs: int,
    page_size: int,
    on_begin: Callable[[dict[str, Any]], None] | None = None,
    on_page: Callable[[list[dict[str, Any]]], None] | None = None,
    on_end: Callable[[], None] | None = None,
    tile_size_degrees: float | None = None,
    cache_dir: Path | None = None,
    cache_namespace: str | None = None,
    resume: bool = False,
    safety_limits: dict[str, int] | None = None,
    on_page_complete: Callable[[], None] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch a bounded layer by tiled IDs with completeness and cache checks."""

    if page_size <= 0:
        raise SourceValidationError("page_size must be positive")
    if resume and cache_dir is None:
        raise SourceValidationError("resume requires a cache directory")
    safety_limits = safety_limits or {}
    tiles = _tile_envelopes(envelope, tile_size_degrees)
    tile_records: list[dict[str, Any]] = []
    tile_object_ids: list[list[int]] = []
    for tile_index, tile in enumerate(tiles):
        object_ids = client.query_object_ids(
            layer_url,
            where="1=1",
            geometry={
                "xmin": tile["west"],
                "ymin": tile["south"],
                "xmax": tile["east"],
                "ymax": tile["north"],
            },
            in_crs_epsg=input_crs,
        )
        if len(object_ids) != len(set(object_ids)):
            raise SourceValidationError(f"ArcGIS tile returned duplicate object IDs: {layer_url}")
        object_ids = sorted(object_ids)
        tile_object_ids.append(object_ids)
        tile_records.append(
            {
                "tile_index": tile_index,
                "envelope": tile,
                "object_id_count": len(object_ids),
                "page_count": (len(object_ids) + page_size - 1) // page_size,
            }
        )
    expected_ids = sorted({object_id for ids in tile_object_ids for object_id in ids})
    if len(expected_ids) > safety_limits.get("max_expected_features", len(expected_ids)):
        raise SourceAccessError(
            f"ArcGIS capture exceeds max_expected_features: {len(expected_ids)}"
        )
    inventory_ids = sum(len(ids) for ids in tile_object_ids)
    if inventory_ids > safety_limits.get("max_inventory_ids", inventory_ids):
        raise SourceAccessError(
            f"ArcGIS tiled inventory exceeds max_inventory_ids: {inventory_ids}"
        )
    expected_pages = sum(tile["page_count"] for tile in tile_records)
    if expected_pages > safety_limits.get("max_expected_pages", expected_pages):
        raise SourceAccessError(
            f"ArcGIS capture exceeds max_expected_pages: {expected_pages}"
        )
    query = {
        "where": "1=1",
        "out_fields": layer.get("out_fields", ["*"]),
        "geometry": {
            "xmin": envelope["west"],
            "ymin": envelope["south"],
            "xmax": envelope["east"],
            "ymax": envelope["north"],
        },
        "geometry_type": "esriGeometryEnvelope",
        "in_crs_epsg": input_crs,
        "out_crs_epsg": output_crs,
        "pagination": "objectIds",
        "page_size": page_size,
        "object_id_count": len(expected_ids),
        "page_count": sum(tile["page_count"] for tile in tile_records),
        "spatial_chunking": {
            "tile_size_degrees": tile_size_degrees,
            "tile_count": len(tiles),
        },
        "tiles": tile_records,
        "complete": False,
        "bytes_written": {
            "feature_payload_bytes": 0,
            "cache_page_bytes": 0,
            "cache_page_count": 0,
        },
    }
    if on_begin:
        on_begin(query)
    features: list[dict[str, Any]] = []
    seen_features: dict[int, dict[str, Any]] = {}
    out_fields = list(layer.get("out_fields", ["*"]))
    for tile_index, object_ids in enumerate(tile_object_ids):
        cache_key = "|".join(
            [
                layer_url,
                str(output_crs),
                layer["geometry_type"],
                ",".join(out_fields),
                json.dumps(tiles[tile_index], sort_keys=True, separators=(",", ":")),
            ]
        )
        for page_index, offset in enumerate(range(0, len(object_ids), page_size)):
            page_ids = object_ids[offset : offset + page_size]
            cache_path = (
                _cache_page_path(cache_dir, cache_namespace or layer_url, tile_index, page_index)
                if cache_dir is not None
                else None
            )
            if cache_path is not None and cache_path.exists():
                if not resume:
                    raise SourceValidationError(
                        f"cached ArcGIS page exists; rerun with resume enabled: {cache_path}"
                    )
                page_features = _load_cached_page(
                    cache_path,
                    page_ids,
                    layer["geometry_type"],
                    output_crs,
                    layer_url,
                    cache_key,
                    out_fields,
                )
                page_bytes = len(
                    json.dumps(
                        {"features": page_features},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
                if page_bytes > safety_limits.get("max_page_bytes", page_bytes):
                    raise SourceAccessError(
                        f"cached ArcGIS page exceeds max_page_bytes: {page_bytes} ({layer_url})"
                    )
                query["bytes_written"]["feature_payload_bytes"] += page_bytes
            else:
                payload = client.query_feature_payload(
                    layer_url,
                    where="1=1",
                    out_fields=out_fields,
                    object_ids=page_ids,
                    in_crs_epsg=input_crs,
                    out_crs_epsg=output_crs,
                )
                if payload.get("exceededTransferLimit") is True:
                    raise SourceAccessError(
                        f"ArcGIS paged query exceeded the transfer limit: {layer_url}"
                    )
                validate_feature_payload_crs(payload, output_crs, layer_url)
                page_features = payload["features"]
                validate_feature_object_ids(page_features, page_ids, layer_url)
                validate_feature_geometries(page_features, layer["geometry_type"], layer_url)
                page_bytes = len(
                    json.dumps(
                        {"features": page_features},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
                if page_bytes > safety_limits.get("max_page_bytes", page_bytes):
                    raise SourceAccessError(
                        f"ArcGIS page exceeds max_page_bytes: {page_bytes} ({layer_url})"
                    )
                query["bytes_written"]["feature_payload_bytes"] += page_bytes
                if cache_path is not None:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    _write_cached_page(
                        cache_path, page_ids, page_features, output_crs, cache_key, out_fields
                    )
                    cache_bytes = cache_path.stat().st_size
                    query["bytes_written"]["cache_page_bytes"] += cache_bytes
                    query["bytes_written"]["cache_page_count"] += 1
                    if _directory_size(cache_dir) > safety_limits.get(
                        "max_cache_bytes", _directory_size(cache_dir)
                    ):
                        raise SourceAccessError(
                            f"ArcGIS cache exceeds max_cache_bytes: {cache_dir}"
                        )
            unique_features: list[dict[str, Any]] = []
            for feature in page_features:
                object_id = _feature_object_id(feature, layer_url)
                previous = seen_features.get(object_id)
                if previous is not None:
                    if not _features_equivalent(previous, feature):
                        raise SourceValidationError(
                            f"ArcGIS object ID has conflicting tile features: {object_id}"
                        )
                    continue
                seen_features[object_id] = feature
                unique_features.append(feature)
            if on_page:
                on_page(unique_features)
            else:
                features.extend(unique_features)
            if on_page_complete:
                on_page_complete()
    if set(seen_features) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(seen_features))
        unexpected = sorted(set(seen_features) - set(expected_ids))
        raise SourceValidationError(
            f"ArcGIS capture is incomplete: missing={missing[:5]}, unexpected={unexpected[:5]}"
        )
    query["returned_feature_count"] = len(seen_features)
    query["complete"] = True
    if on_end:
        on_end()
    return features, query


def acquire(
    config: dict[str, Any],
    client: ArcGISClient,
    source_ids: set[str] | None = None,
    components: set[str] | None = None,
) -> dict[str, Any]:
    """Fetch all configured vector layers and return an in-memory acquisition bundle."""

    envelope = config["provisional_processing_envelope_gda2020"]
    input_crs = config["source_crs_epsg"]
    output_crs = config["analysis_crs_epsg"]
    page_size = int(config.get("arcgis_query_page_size", 200))
    if page_size <= 0:
        raise SourceValidationError("arcgis_query_page_size must be positive")
    acquired_sources = []
    for source in config["sources"]:
        if source_ids is not None and source["id"] not in source_ids:
            continue
        layers = source.get("acquisition_layers")
        if not layers:
            continue
        source_url = source["url"]
        service_metadata = client.service_metadata(source_url)
        service_crs = source.get("service_crs_epsg")
        if service_crs is None:
            raise SourceValidationError(f"source has no configured service CRS: {source['id']}")
        validate_service_crs(service_metadata, service_crs)
        summary = summarize_arcgis_metadata(service_metadata)
        expected_layers = source.get("expected_layers")
        if expected_layers:
            validate_expected_layers(summary, expected_layers)
        expected_layer = source.get("expected_layer")
        if expected_layer:
            validate_expected_layers(summary, [expected_layer])

        acquired_layers = []
        for layer in layers:
            if components is not None and layer["component"] not in components:
                continue
            layer_id = layer["layer_id"]
            layer_summary = _configured_layer_summary(
                client, source_url, source["id"], summary, layer
            )
            layer_url = _layer_url(source_url, layer_id)
            layer_page_size = int(layer.get("page_size", source.get("page_size", page_size)))
            if layer_page_size <= 0:
                raise SourceValidationError(
                    f"configured page size must be positive: {source['id']}:{layer_id}"
                )
            features, query = _acquire_complete_layer(
                client,
                layer_url,
                layer,
                envelope,
                input_crs,
                output_crs,
                layer_page_size,
                tile_size_degrees=_tile_size_degrees(config, source),
                cache_namespace=f"{source['id']}--{layer['component']}",
                safety_limits=_acquisition_safety(config),
            )
            acquired_layers.append(
                {
                    "component": layer["component"],
                    "layer_id": layer_id,
                    "layer_name": layer_summary.get("name"),
                    "geometry_type": layer["geometry_type"],
                    "source_crs_epsg": service_crs,
                    "output_crs_epsg": output_crs,
                    "processing_envelope": envelope,
                    "query": query,
                    "feature_count": len(features),
                    "features": features,
                }
            )
        if acquired_layers:
            acquired_sources.append(
                {
                    "source_id": source["id"],
                    "url": source_url,
                    "service_crs_epsg": service_crs,
                    "layers": acquired_layers,
                }
            )
    return {
        "schema_version": 1,
        "format": "arcgis-json-feature-collections",
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario": config["scenario"],
        "processing_envelope": envelope,
        "processing_envelope_crs_epsg": input_crs,
        "output_crs_epsg": output_crs,
        "sources": acquired_sources,
    }


def _artifact_name(source_id: str, component: str) -> str:
    return f"{source_id}--{component}.json"


def write_acquisition(bundle: dict[str, Any], output_dir: Path) -> Path:
    """Write per-layer feature collections and a compact acquisition manifest."""

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {key: value for key, value in bundle.items() if key != "sources"}
    manifest["sources"] = []
    for source in bundle["sources"]:
        source_manifest = {
            key: value for key, value in source.items() if key != "layers"
        }
        source_manifest["layers"] = []
        for layer in source["layers"]:
            filename = _artifact_name(source["source_id"], layer["component"])
            layer_output = {
                "schema_version": 1,
                "format": "arcgis-json-feature-collection",
                "source_id": source["source_id"],
                "source_url": source["url"],
                **layer,
            }
            write_manifest(layer_output, output_dir / filename)
            source_manifest["layers"].append(
                {
                    key: value
                    for key, value in layer.items()
                    if key != "features"
                }
                | {"artifact_path": str(output_dir / filename)}
            )
        manifest["sources"].append(source_manifest)
    manifest_path = output_dir / "acquisition_manifest.json"
    write_manifest(manifest, manifest_path)
    return manifest_path


def stream_acquisition(
    config: dict[str, Any],
    client: ArcGISClient,
    output_dir: Path,
    source_ids: set[str] | None = None,
    components: set[str] | None = None,
    cache_dir: Path | None = None,
    resume: bool = False,
) -> Path:
    """Acquire and publish layers incrementally through a staged output directory."""

    safety_limits = _acquisition_safety(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise SourceValidationError(f"output directory must be empty: {output_dir}")
    if resume and cache_dir is None:
        raise SourceValidationError("resume requires a cache directory")
    if cache_dir is not None:
        output_resolved = output_dir.resolve()
        cache_resolved = cache_dir.resolve()
        if (
            output_resolved == cache_resolved
            or output_resolved in cache_resolved.parents
            or cache_resolved in output_resolved.parents
        ):
            raise SourceValidationError("output and cache directories must be separate")
        cache_dir.mkdir(parents=True, exist_ok=True)
        if _directory_size(cache_dir) > safety_limits["max_cache_bytes"]:
            raise SourceAccessError(f"cache already exceeds max_cache_bytes: {cache_dir}")
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=output_dir))
    print(f"Acquisition output: {output_dir.resolve()}")
    print(f"Acquisition cache: {cache_dir.resolve() if cache_dir else 'disabled'}")
    print(f"Acquisition staging: {staging.resolve()}")
    print(f"Acquisition safety limits: {json.dumps(safety_limits, sort_keys=True)}")
    envelope = config["provisional_processing_envelope_gda2020"]
    input_crs = config["source_crs_epsg"]
    output_crs = config["analysis_crs_epsg"]
    page_size = int(config.get("arcgis_query_page_size", 200))
    if page_size <= 0:
        raise SourceValidationError("arcgis_query_page_size must be positive")
    acquired_sources = []
    try:
        for source in config["sources"]:
            if source_ids is not None and source["id"] not in source_ids:
                continue
            layers = source.get("acquisition_layers")
            if not layers:
                continue
            service_metadata = client.service_metadata(source["url"])
            service_crs = source.get("service_crs_epsg")
            if service_crs is None:
                raise SourceValidationError(f"source has no configured service CRS: {source['id']}")
            validate_service_crs(service_metadata, service_crs)
            summary = summarize_arcgis_metadata(service_metadata)
            if source.get("expected_layers"):
                validate_expected_layers(summary, source["expected_layers"])
            if source.get("expected_layer"):
                validate_expected_layers(summary, [source["expected_layer"]])
            source_manifest = {
                "source_id": source["id"],
                "url": source["url"],
                "service_crs_epsg": service_crs,
                "layers": [],
            }
            for layer in layers:
                if components is not None and layer["component"] not in components:
                    continue
                layer_id = layer["layer_id"]
                layer_summary = _configured_layer_summary(
                    client, source["url"], source["id"], summary, layer
                )
                layer_url = _layer_url(source["url"], layer_id)
                layer_page_size = int(layer.get("page_size", source.get("page_size", page_size)))
                if layer_page_size <= 0:
                    raise SourceValidationError(
                        f"configured page size must be positive: {source['id']}:{layer_id}"
                    )
                filename = _artifact_name(source["id"], layer["component"])
                staged_path = staging / filename
                handle = None
                first_feature = True
                feature_count = 0

                def begin(query, *, layer=layer, layer_summary=layer_summary, source=source):
                    nonlocal handle
                    header = {
                        "schema_version": 1,
                        "format": "arcgis-json-feature-collection",
                        "source_id": source["id"],
                        "source_url": source["url"],
                        "component": layer["component"],
                        "layer_id": layer["layer_id"],
                        "layer_name": layer_summary.get("name"),
                        "geometry_type": layer["geometry_type"],
                        "source_crs_epsg": service_crs,
                        "output_crs_epsg": output_crs,
                        "processing_envelope": envelope,
                        "query": query,
                    }
                    handle = staged_path.open("w", encoding="utf-8")
                    handle.write(json.dumps(header, ensure_ascii=False)[:-1])
                    handle.write(',"features":[\n')

                def page(features):
                    nonlocal first_feature, feature_count
                    for feature in features:
                        if not first_feature:
                            handle.write(",\n")
                        handle.write(json.dumps(feature, ensure_ascii=False))
                        first_feature = False
                        feature_count += 1

                def end():
                    handle.write("\n]}\n")
                    handle.close()

                def page_complete():
                    if staged_path.stat().st_size > safety_limits["max_staging_bytes"]:
                        raise SourceAccessError(
                            f"staging output exceeds max_staging_bytes: {staged_path}"
                        )
                    working_set = _directory_size(staging) + _directory_size(cache_dir) if cache_dir else _directory_size(staging)
                    if working_set > safety_limits["max_working_set_bytes"]:
                        raise SourceAccessError(
                            f"acquisition working set exceeds max_working_set_bytes: {working_set}"
                        )

                try:
                    _, query = _acquire_complete_layer(
                        client,
                        layer_url,
                        layer,
                        envelope,
                        input_crs,
                        output_crs,
                        layer_page_size,
                        on_begin=begin,
                        on_page=page,
                        on_end=end,
                        tile_size_degrees=_tile_size_degrees(config, source),
                        cache_dir=cache_dir,
                        cache_namespace=f"{source['id']}--{layer['component']}",
                        resume=resume,
                        safety_limits=safety_limits,
                        on_page_complete=page_complete,
                    )
                except Exception:
                    if handle is not None and not handle.closed:
                        handle.close()
                    staged_path.unlink(missing_ok=True)
                    raise
                final_path = output_dir / filename
                source_manifest["layers"].append(
                    {
                        "component": layer["component"],
                        "layer_id": layer_id,
                        "layer_name": layer_summary.get("name"),
                        "geometry_type": layer["geometry_type"],
                        "source_crs_epsg": service_crs,
                        "output_crs_epsg": output_crs,
                        "processing_envelope": envelope,
                        "query": query,
                        "feature_count": feature_count,
                        "artifact_path": str(final_path),
                        "artifact_bytes": staged_path.stat().st_size,
                    }
                )
            if source_manifest["layers"]:
                acquired_sources.append(source_manifest)
        manifest = {
            "schema_version": 1,
            "format": "arcgis-json-feature-collections",
            "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
            "scenario": config["scenario"],
            "processing_envelope": envelope,
            "processing_envelope_crs_epsg": input_crs,
            "output_crs_epsg": output_crs,
            "sources": acquired_sources,
        }
        write_manifest(manifest, staging / "acquisition_manifest.json")
        for staged_file in staging.iterdir():
            staged_file.replace(output_dir / staged_file.name)
        return output_dir / "acquisition_manifest.json"
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/external/vectors"))
    parser.add_argument("--source-id", action="append", help="limit acquisition to one or more source IDs")
    parser.add_argument("--component", action="append", help="limit acquisition to one or more configured components")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/cache/arcgis"),
        help="persistent page-cache directory; retain it to resume an interrupted capture",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="reuse validated pages already present in --cache-dir",
    )
    parser.add_argument(
        "--allow-temporary-path",
        action="store_true",
        help="allow --output-dir/--cache-dir under the system temporary directory for bounded probes",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    acquisition_settings = config.get("arcgis_acquisition", {})
    if not isinstance(acquisition_settings, dict):
        raise SourceValidationError("arcgis_acquisition settings must be an object")
    safety_limits = _acquisition_safety(config)
    temp_root = Path(tempfile.gettempdir()).resolve()
    paths = [args.output_dir.resolve(), args.cache_dir.resolve()]
    transient_roots = (temp_root, Path("/var/tmp"), Path("/dev/shm"))
    if not args.allow_temporary_path and any(
        any(path == root or root in path.parents for root in transient_roots)
        for path in paths
    ):
        raise SourceValidationError(
            "refusing system temporary output/cache path; use persistent data/cache paths "
            "or --allow-temporary-path for a bounded probe"
        )
    print(f"Planned vector output: {args.output_dir.resolve()}")
    print(f"Planned vector cache: {args.cache_dir.resolve()}")
    print(f"Planned vector limits: {json.dumps(safety_limits, sort_keys=True)}")
    manifest_path = stream_acquisition(
        config,
        ArcGISClient(
            timeout_seconds=args.timeout,
            max_retries=int(acquisition_settings.get("max_retries", 2)),
            retry_backoff_seconds=float(acquisition_settings.get("retry_backoff_seconds", 1.0)),
            max_response_bytes=safety_limits["max_response_bytes"],
        ),
        args.output_dir,
        set(args.source_id) if args.source_id else None,
        set(args.component) if args.component else None,
        args.cache_dir,
        args.resume,
    )
    print(f"Wrote bounded vector acquisition manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        SourceAccessError,
        SourceValidationError,
        json.JSONDecodeError,
    ) as exc:
        raise SystemExit(f"Vector source acquisition failed: {exc}") from exc
