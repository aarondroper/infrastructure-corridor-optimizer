"""Generate provenance-rich offline route assets from normalized cost grids."""

from __future__ import annotations

import json
import math
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .cost import combine_cost_layers
from .routing import NoPathError, route_least_cost
from .sources import write_manifest


class RouteAssetError(ValueError):
    """Raised when a normalized grid bundle cannot produce route assets."""


def _cell(value: Any, name: str, rows: int, cols: int) -> tuple[int, int]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        raise RouteAssetError(f"{name} must be a two-integer cell")
    cell = (value[0], value[1])
    if not (0 <= cell[0] < rows and 0 <= cell[1] < cols):
        raise RouteAssetError(f"{name} is outside the normalized grid")
    return cell


def _hard_exclusions(bundle: Mapping[str, Any], rows: int, cols: int) -> list[list[bool]]:
    exclusions = [[False for _ in range(cols)] for _ in range(rows)]
    values = bundle.get("unavailable_cells", [])
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise RouteAssetError("unavailable_cells must be a sequence")
    for value in values:
        row, col = _cell(value, "unavailable cell", rows, cols)
        exclusions[row][col] = True
    return exclusions


def _grid_shape(grids: Mapping[str, Any]) -> tuple[int, int]:
    try:
        first = next(iter(grids.values()))
        rows = len(first)
        cols = len(first[0]) if rows else 0
        if rows == 0 or cols == 0 or any(len(row) != cols for row in first):
            raise ValueError
        return rows, cols
    except (StopIteration, TypeError, ValueError, IndexError) as exc:
        raise RouteAssetError("component grids must be non-empty rectangular sequences") from exc


def generate_precomputed_routes(
    config: Mapping[str, Any], grid_bundle: Mapping[str, Any]
) -> dict[str, Any]:
    """Generate all configured preset routes from one normalized grid bundle."""

    if grid_bundle.get("schema_version") != 1 or grid_bundle.get("format") != "ico-normalized-cost-grids":
        raise RouteAssetError("unsupported normalized grid bundle schema")
    scenario = grid_bundle.get("scenario")
    if scenario != config.get("scenario"):
        raise RouteAssetError(
            f"grid bundle scenario mismatch: expected {config.get('scenario')!r}, observed {scenario!r}"
        )
    analysis_crs = grid_bundle.get("analysis_crs_epsg")
    if analysis_crs != config.get("analysis_crs_epsg"):
        raise RouteAssetError(
            f"grid bundle CRS mismatch: expected EPSG:{config.get('analysis_crs_epsg')}, observed {analysis_crs!r}"
        )
    cell_size = grid_bundle.get("cell_size_m")
    if isinstance(cell_size, bool) or not isinstance(cell_size, (int, float)) or not math.isfinite(cell_size) or cell_size <= 0:
        raise RouteAssetError("grid bundle cell_size_m must be finite and positive")
    grids = grid_bundle.get("component_grids")
    if not isinstance(grids, Mapping):
        raise RouteAssetError("grid bundle has no component_grids object")
    expected_components = [component["id"] for component in config.get("components", [])]
    if set(grids) != set(expected_components):
        raise RouteAssetError("grid bundle components do not match the configured model")
    rows, cols = _grid_shape(grids)
    hard_excluded = _hard_exclusions(grid_bundle, rows, cols)
    origin = _cell(grid_bundle.get("origin_cell"), "origin_cell", rows, cols)
    destination = _cell(grid_bundle.get("destination_cell"), "destination_cell", rows, cols)
    presets = config.get("sensitivity_presets")
    if not isinstance(presets, Mapping) or not presets:
        raise RouteAssetError("configuration has no sensitivity presets")

    routes: list[dict[str, Any]] = []
    for preset_name, preset in presets.items():
        if not isinstance(preset, Mapping) or not isinstance(preset.get("weights"), Mapping):
            raise RouteAssetError(f"preset has no weights: {preset_name}")
        try:
            costs = combine_cost_layers(grids, preset["weights"], hard_excluded=hard_excluded)
            result = route_least_cost(costs, origin, destination, algorithm="astar")
        except (TypeError, ValueError, NoPathError) as exc:
            raise RouteAssetError(f"could not generate preset {preset_name!r}: {exc}") from exc
        routes.append(
            {
                "schema_version": 1,
                "format": "ico-precomputed-route",
                "scenario": scenario,
                "preset": preset_name,
                "preset_description": preset.get("description", ""),
                "weights": dict(preset["weights"]),
                "algorithm": "astar",
                "analysis_crs_epsg": analysis_crs,
                "cell_size_m": cell_size,
                "grid_shape": {"rows": rows, "cols": cols},
                "origin_cell": list(origin),
                "destination_cell": list(destination),
                "path_cells": [list(cell) for cell in result.path],
                "path_cell_count": len(result.path),
                "cost": result.cost,
                "explored_cells": result.explored_cells,
                "grid_provenance": grid_bundle.get("provenance"),
            }
        )
    return {
        "schema_version": 1,
        "format": "ico-precomputed-route-assets",
        "scenario": scenario,
        "analysis_crs_epsg": analysis_crs,
        "cell_size_m": cell_size,
        "grid_shape": {"rows": rows, "cols": cols},
        "origin_cell": list(origin),
        "destination_cell": list(destination),
        "algorithm": "astar",
        "routes": routes,
    }


def write_precomputed_routes(bundle: Mapping[str, Any], output_dir: str | Path) -> Path:
    """Publish preset route assets and manifest atomically into an empty directory."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise RouteAssetError(f"route output directory must be empty: {destination}")
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=destination))
    try:
        manifest = {key: value for key, value in bundle.items() if key != "routes"}
        manifest["routes"] = []
        for route in bundle["routes"]:
            preset = route["preset"]
            filename = f"{preset}.json"
            write_manifest(route, staging / filename)
            manifest["routes"].append(
                {
                    "preset": preset,
                    "artifact_path": filename,
                    "path_cell_count": route["path_cell_count"],
                    "cost": route["cost"],
                    "explored_cells": route["explored_cells"],
                }
            )
        write_manifest(manifest, staging / "routes_manifest.json")
        for staged_file in staging.iterdir():
            staged_file.replace(destination / staged_file.name)
        return destination / "routes_manifest.json"
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def load_grid_bundle(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RouteAssetError(f"could not read normalized grid bundle: {path}") from exc
    if not isinstance(payload, dict):
        raise RouteAssetError("normalized grid bundle must be a JSON object")
    return payload
