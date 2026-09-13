#!/usr/bin/env python3
"""Acquire configured ArcGIS constraint layers for the bounded S1 envelope."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ico_model.sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    summarize_arcgis_metadata,
    validate_expected_layers,
    validate_feature_geometries,
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


def _acquire_complete_layer(
    client: ArcGISClient,
    layer_url: str,
    layer: dict[str, Any],
    envelope: dict[str, float],
    input_crs: int,
    output_crs: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch a bounded layer by IDs so transfer limits cannot truncate it."""

    object_ids = client.query_object_ids(
        layer_url,
        where="1=1",
        geometry=envelope,
        in_crs_epsg=input_crs,
    )
    features: list[dict[str, Any]] = []
    for offset in range(0, len(object_ids), page_size):
        page_ids = object_ids[offset : offset + page_size]
        payload = client.query_feature_payload(
            layer_url,
            where="1=1",
            out_fields=layer.get("out_fields", ["*"]),
            object_ids=page_ids,
            geometry=envelope,
            geometry_type="esriGeometryEnvelope",
            in_crs_epsg=input_crs,
            out_crs_epsg=output_crs,
        )
        if payload.get("exceededTransferLimit") is True:
            raise SourceAccessError(
                f"ArcGIS paged query exceeded the transfer limit: {layer_url}"
            )
        validate_feature_payload_crs(payload, output_crs, layer_url)
        page_features = payload["features"]
        validate_feature_geometries(page_features, layer["geometry_type"], layer_url)
        features.extend(page_features)
    return features, {
        "where": "1=1",
        "out_fields": layer.get("out_fields", ["*"]),
        "geometry": envelope,
        "geometry_type": "esriGeometryEnvelope",
        "in_crs_epsg": input_crs,
        "out_crs_epsg": output_crs,
        "pagination": "objectIds",
        "page_size": page_size,
        "object_id_count": len(object_ids),
        "page_count": (len(object_ids) + page_size - 1) // page_size,
    }


def acquire(
    config: dict[str, Any],
    client: ArcGISClient,
    source_ids: set[str] | None = None,
    components: set[str] | None = None,
) -> dict[str, Any]:
    """Fetch all configured vector layers and return an in-memory acquisition bundle."""

    envelope = config["provisional_processing_envelope_gda2020"]
    arcgis_envelope = {
        "xmin": envelope["west"],
        "ymin": envelope["south"],
        "xmax": envelope["east"],
        "ymax": envelope["north"],
    }
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
            layer_summary = next(
                (item for item in summary["layers"] if item.get("id") == layer_id), None
            )
            if layer_summary is None:
                raise SourceValidationError(
                    f"configured acquisition layer is unavailable: {source['id']}:{layer_id}"
                )
            if layer_summary.get("type") != "Feature Layer":
                raise SourceValidationError(
                    f"configured acquisition layer is not queryable: {source['id']}:{layer_id}"
                )
            if layer_summary.get("geometryType") != layer["geometry_type"]:
                raise SourceValidationError(
                    f"configured acquisition geometry mismatch: {source['id']}:{layer_id}"
                )
            layer_url = _layer_url(source_url, layer_id)
            features, query = _acquire_complete_layer(
                client,
                layer_url,
                layer,
                arcgis_envelope,
                input_crs,
                output_crs,
                page_size,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-id", action="append", help="limit acquisition to one or more source IDs")
    parser.add_argument("--component", action="append", help="limit acquisition to one or more configured components")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    bundle = acquire(
        load_config(args.config),
        ArcGISClient(timeout_seconds=args.timeout),
        set(args.source_id) if args.source_id else None,
        set(args.component) if args.component else None,
    )
    manifest_path = write_acquisition(bundle, args.output_dir)
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
