"""Georeference and independently summarize geographic route-cell assets."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


class RouteAssessmentError(ValueError):
    """Raised when a route cannot be assessed against its geographic grid."""


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RouteAssessmentError(f"could not read route input: {path}") from exc
    if not isinstance(payload, dict):
        raise RouteAssessmentError(f"route input must be an object: {path}")
    return payload


def _cell_coordinates(bundle: dict[str, Any], path_cells: list[list[int]]) -> list[tuple[float, float]]:
    from rasterio.transform import Affine
    from rasterio.warp import transform

    shape = bundle.get("grid_shape")
    transform_values = bundle.get("provenance", {}).get("transform")
    if not isinstance(shape, dict) or not isinstance(transform_values, list) or len(transform_values) != 9:
        raise RouteAssessmentError("grid bundle has no georeferencing transform")
    rows, cols = int(shape["rows"]), int(shape["cols"])
    affine = Affine(*[float(value) for value in transform_values[:6]])
    projected: list[tuple[float, float]] = []
    for cell in path_cells:
        if not isinstance(cell, list) or len(cell) != 2:
            raise RouteAssessmentError("route contains an invalid cell")
        row, col = int(cell[0]), int(cell[1])
        if not (0 <= row < rows and 0 <= col < cols):
            raise RouteAssessmentError("route cell is outside the grid")
        x, y = affine @ (col + 0.5, row + 0.5)
        projected.append((x, y))
    if not projected:
        raise RouteAssessmentError("route has no cells")
    longitudes, latitudes = transform("EPSG:7856", "EPSG:7844", [p[0] for p in projected], [p[1] for p in projected])
    return list(zip(longitudes, latitudes))


def assess_route(bundle: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    path_cells = route.get("path_cells")
    if not isinstance(path_cells, list) or not path_cells:
        raise RouteAssessmentError("route has no path_cells")
    coordinates = _cell_coordinates(bundle, path_cells)
    cell_size = float(bundle["cell_size_m"])
    component_grids = bundle.get("component_grids")
    if not isinstance(component_grids, dict):
        raise RouteAssessmentError("grid bundle has no component grids")
    component_cell_counts: dict[str, int] = {}
    terrain_values: list[float] = []
    total_length_m = 0.0
    for index, cell in enumerate(path_cells):
        row, col = int(cell[0]), int(cell[1])
        for component, values in component_grids.items():
            if not isinstance(values, list) or row >= len(values) or col >= len(values[row]):
                raise RouteAssessmentError(f"component grid is incompatible with route: {component}")
            value = float(values[row][col])
            if component == "terrain":
                terrain_values.append(value)
            if component != "length" and value > 0:
                component_cell_counts[component] = component_cell_counts.get(component, 0) + 1
        if index:
            previous = path_cells[index - 1]
            delta_row = abs(int(cell[0]) - int(previous[0]))
            delta_col = abs(int(cell[1]) - int(previous[1]))
            if max(delta_row, delta_col) != 1:
                raise RouteAssessmentError("route contains a non-adjacent cell transition")
            total_length_m += cell_size * (math.sqrt(2.0) if delta_row and delta_col else 1.0)
    return {
        "schema_version": 1,
        "format": "ico-route-assessment",
        "scenario": bundle["scenario"],
        "preset": route["preset"],
        "analysis_crs_epsg": bundle["analysis_crs_epsg"],
        "display_crs_epsg": 7844,
        "cell_size_m": cell_size,
        "path_cell_count": len(path_cells),
        "route_length_m": total_length_m,
        "route_length_km": total_length_m / 1000.0,
        "component_intersected_cell_counts": component_cell_counts,
        "terrain_normalized_mean": sum(terrain_values) / len(terrain_values),
        "terrain_normalized_max": max(terrain_values),
        "endpoint_cells": {
            "origin": path_cells[0],
            "destination": path_cells[-1],
        },
        "geometry": {
            "type": "LineString",
            "coordinates": [[float(x), float(y)] for x, y in coordinates],
        },
        "assessment_note": "Cell-intersection indicators are preliminary grid metrics; feature-level crossing counts remain a later refinement.",
    }


def assess_route_directory(bundle_path: str | Path, routes_dir: str | Path) -> dict[str, Any]:
    bundle = _load(Path(bundle_path))
    directory = Path(routes_dir)
    manifest = _load(directory / "routes_manifest.json")
    assessments = []
    for record in manifest.get("routes", []):
        route = _load(directory / record["artifact_path"])
        assessments.append(assess_route(bundle, route))
    return {
        "schema_version": 1,
        "format": "ico-route-assessments",
        "scenario": bundle["scenario"],
        "grid_bundle_path": str(Path(bundle_path).resolve()),
        "routes_manifest_path": str((directory / "routes_manifest.json").resolve()),
        "assessments": assessments,
    }


def write_route_assessments(payload: dict[str, Any], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    for assessment in payload["assessments"]:
        feature = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {key: value for key, value in assessment.items() if key != "geometry"},
                "geometry": assessment["geometry"],
            }],
        }
        geojson = destination.parent / f"{assessment['preset']}.geojson"
        temporary_geojson = geojson.with_name(f".{geojson.name}.tmp")
        temporary_geojson.write_text(json.dumps(feature, separators=(",", ":")) + "\n", encoding="utf-8")
        temporary_geojson.replace(geojson)
    return destination
