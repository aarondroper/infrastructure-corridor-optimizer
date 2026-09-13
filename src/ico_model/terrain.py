"""Terrain artifact provenance and source-selection checks.

This module deliberately validates metadata rather than reading raster pixels. A
later GIS-backed stage can consume the selected artifact after these checks pass.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from .dem_acquisition import (
    DemAcquisitionError,
    inspect_geotiff,
    validate_copernicus_geotiff,
)
from .sources import write_manifest


class TerrainArtifactError(ValueError):
    """Raised when a terrain artifact cannot support the configured analysis."""


def _finite_number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TerrainArtifactError(f"terrain metadata field {field!r} is not numeric") from exc
    if not math.isfinite(number):
        raise TerrainArtifactError(f"terrain metadata field {field!r} is not finite")
    return number


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise TerrainArtifactError(f"terrain metadata field {field!r} is not an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise TerrainArtifactError(f"terrain metadata field {field!r} is not an integer") from exc
    if isinstance(value, float) and value != number:
        raise TerrainArtifactError(f"terrain metadata field {field!r} is not an integer")
    return number


def _bounds(metadata: Mapping[str, Any]) -> dict[str, float]:
    raw = metadata.get("bounds")
    if not isinstance(raw, Mapping):
        raise TerrainArtifactError("terrain metadata must declare bounds")
    values = {
        key: _finite_number(raw.get(key), f"bounds.{key}")
        for key in ("west", "south", "east", "north")
    }
    if values["west"] >= values["east"] or values["south"] >= values["north"]:
        raise TerrainArtifactError("terrain bounds must have positive width and height")
    return values


def _contains(container: Mapping[str, float], required: Mapping[str, Any]) -> bool:
    return (
        container["west"] <= _finite_number(required.get("west"), "required bounds.west")
        and container["south"] <= _finite_number(required.get("south"), "required bounds.south")
        and container["east"] >= _finite_number(required.get("east"), "required bounds.east")
        and container["north"] >= _finite_number(required.get("north"), "required bounds.north")
    )


def load_terrain_artifact_metadata(metadata_path: str | Path) -> dict[str, Any]:
    """Load one JSON sidecar describing a local DEM artifact."""

    path = Path(metadata_path)
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TerrainArtifactError(f"could not read terrain metadata: {path}: {exc}") from exc
    if not isinstance(metadata, dict):
        raise TerrainArtifactError("terrain metadata must be a JSON object")
    metadata["metadata_path"] = str(path)
    artifact_path = metadata.get("artifact_path")
    if isinstance(artifact_path, str) and not Path(artifact_path).is_absolute():
        metadata["artifact_path"] = str((path.parent / artifact_path).resolve())
    return metadata


def validate_terrain_artifact(
    metadata: Mapping[str, Any], config: Mapping[str, Any], expected_source_id: str
) -> dict[str, Any]:
    """Validate a DEM sidecar against the configured source and envelope."""

    policy = config.get("terrain_source_policy")
    if not isinstance(policy, Mapping):
        raise TerrainArtifactError("configuration has no terrain_source_policy")
    configured_source_ids = {
        source.get("id")
        for source in config.get("sources", [])
        if isinstance(source, Mapping)
    }
    if expected_source_id not in configured_source_ids:
        raise TerrainArtifactError(
            f"terrain source is not declared in configuration: {expected_source_id!r}"
        )
    if metadata.get("source_id") != expected_source_id:
        raise TerrainArtifactError(
            f"terrain artifact source mismatch: expected {expected_source_id!r}, "
            f"observed {metadata.get('source_id')!r}"
        )
    artifact_type = metadata.get("artifact_type")
    required_artifact_type = policy.get("required_artifact_type")
    accepted_tile_set = required_artifact_type == "raster-dem" and artifact_type == "raster-dem-tile-set"
    if artifact_type != required_artifact_type and not accepted_tile_set:
        raise TerrainArtifactError(
            f"terrain artifact type must be {required_artifact_type!r}"
        )
    artifact_path = metadata.get("artifact_path")
    if not isinstance(artifact_path, str) or not artifact_path:
        raise TerrainArtifactError("terrain metadata must declare artifact_path")
    artifact_file = Path(artifact_path)
    if not artifact_file.is_file():
        raise TerrainArtifactError(f"terrain artifact file is unavailable: {artifact_path}")
    if accepted_tile_set:
        try:
            tile_manifest = json.loads(artifact_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TerrainArtifactError(f"DEM tile manifest is unreadable: {artifact_path}") from exc
        if not isinstance(tile_manifest, dict) or tile_manifest.get("format") != "copernicus-dem-tile-set":
            raise TerrainArtifactError("DEM tile manifest has an unsupported schema")
        tiles = tile_manifest.get("tiles")
        if not isinstance(tiles, list) or not tiles:
            raise TerrainArtifactError("DEM tile manifest has no tiles")
        for tile in tiles:
            if not isinstance(tile, Mapping) or not isinstance(tile.get("artifact_path"), str):
                raise TerrainArtifactError("DEM tile manifest has an invalid tile record")
            tile_path = artifact_file.parent / tile["artifact_path"]
            if not tile_path.is_file():
                raise TerrainArtifactError(f"DEM tile is unavailable: {tile_path}")
            try:
                tile_metadata = inspect_geotiff(tile_path)
                validate_copernicus_geotiff(tile_metadata, tile_path)
            except (DemAcquisitionError, OSError) as exc:
                raise TerrainArtifactError(f"DEM tile is invalid: {tile_path}") from exc
            if tile_metadata["crs_epsg"] != 4326 or tile_metadata["nominal_resolution_m"] != 30.0:
                raise TerrainArtifactError(f"DEM tile metadata is unsuitable: {tile_path}")
    artifact_crs = _integer(metadata.get("crs_epsg"), "crs_epsg")
    bounds_crs = _integer(metadata.get("bounds_crs_epsg"), "bounds_crs_epsg")
    expected_bounds_crs = _integer(
        policy.get("processing_envelope_crs_epsg"), "processing_envelope_crs_epsg"
    )
    if bounds_crs != expected_bounds_crs and {bounds_crs, expected_bounds_crs} != {4326, 7844}:
        raise TerrainArtifactError(
            f"terrain bounds CRS must be EPSG:{expected_bounds_crs}, observed EPSG:{bounds_crs}"
        )
    resolution = _finite_number(metadata.get("resolution_m"), "resolution_m")
    if resolution <= 0:
        raise TerrainArtifactError("terrain resolution_m must be positive")
    if metadata.get("nodata_defined") is not True:
        raise TerrainArtifactError("terrain metadata must declare nodata_defined=true")
    if metadata.get("coverage_status") != "complete":
        raise TerrainArtifactError("terrain coverage_status must be 'complete'")
    acquired_at = metadata.get("acquired_at_utc")
    if not isinstance(acquired_at, str) or not acquired_at:
        raise TerrainArtifactError("terrain metadata must declare acquired_at_utc")
    try:
        parsed_acquired_at = datetime.fromisoformat(acquired_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TerrainArtifactError(
            "terrain acquired_at_utc must be an ISO-8601 timestamp"
        ) from exc
    if parsed_acquired_at.tzinfo is None:
        raise TerrainArtifactError("terrain acquired_at_utc must include a timezone")
    artifact_bounds = _bounds(metadata)
    required_bounds = policy.get("required_processing_envelope")
    if not isinstance(required_bounds, Mapping) or not _contains(artifact_bounds, required_bounds):
        raise TerrainArtifactError("terrain artifact bounds do not contain the processing envelope")
    return {
        "source_id": expected_source_id,
        "artifact_type": artifact_type,
        "artifact_path": artifact_path,
        "metadata_path": metadata.get("metadata_path"),
        "crs_epsg": artifact_crs,
        "bounds_crs_epsg": bounds_crs,
        "resolution_m": resolution,
        "bounds": artifact_bounds,
        "nodata_defined": True,
        "coverage_status": "complete",
        "acquired_at_utc": acquired_at,
    }


def select_terrain_artifact(
    config: Mapping[str, Any], candidates: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Select the valid primary DEM, or the explicitly configured fallback."""

    policy = config.get("terrain_source_policy")
    if not isinstance(policy, Mapping):
        raise TerrainArtifactError("configuration has no terrain_source_policy")
    primary_id = policy.get("primary_source_id")
    fallback_id = policy.get("fallback_source_id")
    if not isinstance(primary_id, str) or not isinstance(fallback_id, str):
        raise TerrainArtifactError("terrain source policy must declare primary and fallback IDs")
    if primary_id == fallback_id:
        raise TerrainArtifactError("terrain source policy primary and fallback IDs must differ")
    source_records = {
        source.get("id"): source
        for source in config.get("sources", [])
        if isinstance(source, Mapping) and isinstance(source.get("id"), str)
    }
    if primary_id not in source_records or fallback_id not in source_records:
        raise TerrainArtifactError("terrain source policy IDs must be declared in sources")
    failures: dict[str, str] = {}
    for source_id in (primary_id, fallback_id):
        if source_id == fallback_id and not policy.get("allow_fallback"):
            break
        metadata = candidates.get(source_id)
        if metadata is None:
            failures[source_id] = "no metadata sidecar supplied"
            continue
        try:
            artifact = validate_terrain_artifact(metadata, config, source_id)
        except TerrainArtifactError as exc:
            failures[source_id] = str(exc)
            continue
        fallback_used = source_id != primary_id
        result = {
            "schema_version": 1,
            "selected_source_id": source_id,
            "selected_source": {
                key: source_records[source_id][key]
                for key in ("id", "role", "url", "product")
                if key in source_records[source_id]
            },
            "fallback_used": fallback_used,
            "selection_reason": (
                "primary artifact passed validation"
                if not fallback_used
                else "primary artifact failed validation; configured fallback passed validation"
            ),
            "target_analysis_crs_epsg": _integer(
                policy.get("target_analysis_crs_epsg"), "target_analysis_crs_epsg"
            ),
            "artifact": artifact,
            "attempts": [
                {"source_id": attempted, "status": "selected" if attempted == source_id else "failed", **(
                    {"reason": failures[attempted]} if attempted in failures else {}
                )}
                for attempted in (primary_id, fallback_id)
                if attempted in failures or attempted == source_id
            ],
        }
        return result
    raise TerrainArtifactError(
        "no usable terrain artifact: "
        + "; ".join(f"{source_id}: {reason}" for source_id, reason in failures.items())
    )


def write_terrain_selection(selection: Mapping[str, Any], output_path: str | Path) -> None:
    """Write the selected-source provenance report atomically."""

    write_manifest(selection, output_path)
