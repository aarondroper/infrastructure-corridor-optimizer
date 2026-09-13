"""Integrity checks for externally acquired ArcGIS vector artifacts."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .sources import (
    SourceValidationError,
    validate_feature_geometries,
    validate_feature_object_ids,
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceValidationError(f"could not read JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise SourceValidationError(f"JSON artifact must be an object: {path}")
    return payload


def _required_text(payload: dict[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise SourceValidationError(f"{context} has no non-empty {key}")
    return value


def _required_int(payload: dict[str, Any], key: str, context: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise SourceValidationError(f"{context} has no integer {key}")
    return value


def _required_mapping(payload: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise SourceValidationError(f"{context} has no object {key}")
    return value


def validate_vector_manifest(
    manifest_path: str | Path,
    *,
    expected_scenario: str | None = None,
    expected_output_crs_epsg: int | None = None,
) -> dict[str, Any]:
    """Validate a streamed vector manifest and every artifact it references."""

    manifest_file = Path(manifest_path)
    manifest = _read_json(manifest_file)
    if manifest.get("schema_version") != 1:
        raise SourceValidationError(f"unsupported vector manifest schema: {manifest_file}")
    if manifest.get("format") != "arcgis-json-feature-collections":
        raise SourceValidationError(f"unsupported vector manifest format: {manifest_file}")
    scenario = _required_text(manifest, "scenario", str(manifest_file))
    if expected_scenario is not None and scenario != expected_scenario:
        raise SourceValidationError(
            f"vector manifest scenario mismatch: expected {expected_scenario!r}, observed {scenario!r}"
        )
    manifest_crs = _required_int(manifest, "output_crs_epsg", str(manifest_file))
    if expected_output_crs_epsg is not None and manifest_crs != expected_output_crs_epsg:
        raise SourceValidationError(
            f"vector manifest CRS mismatch: expected EPSG:{expected_output_crs_epsg}, observed {manifest_crs}"
        )
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SourceValidationError(f"vector manifest has no source records: {manifest_file}")

    seen_artifacts: set[Path] = set()
    report_layers: list[dict[str, Any]] = []
    total_features = 0
    for source in sources:
        if not isinstance(source, dict):
            raise SourceValidationError(f"vector manifest has an invalid source record: {manifest_file}")
        source_id = _required_text(source, "source_id", str(manifest_file))
        source_url = _required_text(source, "url", source_id)
        layers = source.get("layers")
        if not isinstance(layers, list) or not layers:
            raise SourceValidationError(f"vector source has no layers: {source_id}")
        for layer in layers:
            if not isinstance(layer, dict):
                raise SourceValidationError(f"vector source has an invalid layer record: {source_id}")
            component = _required_text(layer, "component", source_id)
            context = f"{source_id}:{component}"
            layer_id = _required_int(layer, "layer_id", context)
            geometry_type = _required_text(layer, "geometry_type", context)
            source_crs = _required_int(layer, "source_crs_epsg", context)
            layer_output_crs = _required_int(layer, "output_crs_epsg", context)
            processing_envelope = _required_mapping(layer, "processing_envelope", context)
            query = _required_mapping(layer, "query", context)
            artifact_value = _required_text(layer, "artifact_path", context)
            artifact_path = Path(artifact_value)
            if not artifact_path.is_absolute():
                artifact_path = manifest_file.parent / artifact_path
            artifact_path = artifact_path.resolve()
            if artifact_path in seen_artifacts:
                raise SourceValidationError(f"vector artifact is referenced more than once: {artifact_path}")
            seen_artifacts.add(artifact_path)
            if not artifact_path.is_file():
                raise SourceValidationError(f"vector artifact is missing: {artifact_path}")
            artifact = _read_json(artifact_path)
            if artifact.get("schema_version") != 1 or artifact.get("format") != "arcgis-json-feature-collection":
                raise SourceValidationError(f"unsupported vector artifact schema: {artifact_path}")
            for key, expected in (
                ("source_id", source_id),
                ("source_url", source_url),
                ("component", component),
                ("layer_id", layer_id),
                ("geometry_type", geometry_type),
                ("source_crs_epsg", source_crs),
                ("output_crs_epsg", layer_output_crs),
                ("processing_envelope", processing_envelope),
                ("query", query),
            ):
                if artifact.get(key) != expected:
                    raise SourceValidationError(f"{context} artifact {key} does not match its manifest")
            artifact_crs = _required_int(artifact, "output_crs_epsg", context)
            if artifact_crs != manifest_crs:
                raise SourceValidationError(
                    f"{context} artifact CRS does not match the manifest: {artifact_crs} vs {manifest_crs}"
                )
            features = artifact.get("features")
            if not isinstance(features, list) or not all(isinstance(feature, dict) for feature in features):
                raise SourceValidationError(f"{context} artifact has no complete feature list")
            validate_feature_geometries(features, geometry_type, str(artifact_path))
            feature_count = _required_int(layer, "feature_count", context)
            object_id_count = _required_int(query, "object_id_count", f"{context} query")
            page_size = _required_int(query, "page_size", f"{context} query")
            page_count = _required_int(query, "page_count", f"{context} query")
            if feature_count < 0 or object_id_count < 0 or page_size <= 0 or page_count < 0:
                raise SourceValidationError(f"{context} has invalid count or page metadata")
            tiles = query.get("tiles")
            if tiles is not None:
                if not isinstance(tiles, list) or not tiles:
                    raise SourceValidationError(f"{context} query has invalid tile metadata")
                expected_page_count = 0
                tile_id_count = 0
                for tile in tiles:
                    if not isinstance(tile, dict):
                        raise SourceValidationError(f"{context} query has an invalid tile record")
                    tile_object_count = _required_int(tile, "object_id_count", f"{context} tile")
                    tile_pages = _required_int(tile, "page_count", f"{context} tile")
                    if tile_object_count < 0 or tile_pages < 0:
                        raise SourceValidationError(f"{context} tile has invalid count metadata")
                    if tile_pages != math.ceil(tile_object_count / page_size):
                        raise SourceValidationError(f"{context} tile page count is inconsistent")
                    expected_page_count += tile_pages
                    tile_id_count += tile_object_count
                if query.get("complete") is not True:
                    raise SourceValidationError(f"{context} tiled query is not complete")
                returned_feature_count = _required_int(
                    query, "returned_feature_count", f"{context} query"
                )
                if returned_feature_count != feature_count:
                    raise SourceValidationError(f"{context} returned feature count is inconsistent")
                if tile_id_count < object_id_count:
                    raise SourceValidationError(f"{context} tile IDs undercount the unique object IDs")
            else:
                expected_page_count = math.ceil(object_id_count / page_size)
            if page_count != expected_page_count:
                raise SourceValidationError(f"{context} page count does not match object-ID count")
            if feature_count != object_id_count or len(features) != feature_count:
                raise SourceValidationError(f"{context} feature count does not match its object-ID manifest")
            feature_ids: list[int] = []
            for index, feature in enumerate(features):
                attributes = feature.get("attributes")
                if not isinstance(attributes, Mapping):
                    raise SourceValidationError(
                        f"{context} feature {index} has no attributes for object-ID validation"
                    )
                value = next(
                    (item for key, item in attributes.items() if str(key).lower() == "objectid"),
                    None,
                )
                try:
                    feature_ids.append(int(value))
                except (TypeError, ValueError) as exc:
                    raise SourceValidationError(
                        f"{context} feature {index} has no valid OBJECTID"
                    ) from exc
            validate_feature_object_ids(features, feature_ids, str(artifact_path))
            total_features += feature_count
            report_layers.append(
                {
                    "source_id": source_id,
                    "component": component,
                    "layer_id": layer_id,
                    "feature_count": feature_count,
                    "page_count": page_count,
                    "output_crs_epsg": artifact_crs,
                    "artifact_path": str(artifact_path),
                }
            )

    return {
        "schema_version": 1,
        "format": "validated-arcgis-json-feature-collections",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(manifest_file.resolve()),
        "scenario": scenario,
        "output_crs_epsg": manifest_crs,
        "source_count": len(sources),
        "layer_count": len(report_layers),
        "feature_count": total_features,
        "layers": report_layers,
    }
