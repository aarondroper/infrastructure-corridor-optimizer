"""Georeference and independently summarize geographic route-cell assets."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .route_impacts import (
    RouteImpactError,
    inventory_svtm_route_cells,
    inventory_vector_intersections,
)


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


def _cell_projected_coordinates(bundle: dict[str, Any], path_cells: list[list[int]]) -> list[tuple[float, float]]:
    from rasterio.transform import Affine

    transform_values = bundle.get("provenance", {}).get("transform")
    if not isinstance(transform_values, list) or len(transform_values) < 6:
        raise RouteAssessmentError("grid bundle has no projected transform")
    affine = Affine(*[float(value) for value in transform_values[:6]])
    return [affine @ (int(cell[1]) + 0.5, int(cell[0]) + 0.5) for cell in path_cells]


def _direction_quality(path_cells: list[list[int]], rows: int, cols: int) -> dict[str, Any]:
    directions = [
        (int(current[0]) - int(previous[0]), int(current[1]) - int(previous[1]))
        for previous, current in zip(path_cells, path_cells[1:])
    ]
    changes = sum(1 for previous, current in zip(directions, directions[1:]) if previous != current)
    diagonal = sum(1 for row, col in directions if row and col)
    boundary = sum(
        1 for row, col in path_cells if row in {0, rows - 1} or col in {0, cols - 1}
    )
    return {
        "step_count": len(directions),
        "diagonal_step_count": diagonal,
        "diagonal_step_fraction": diagonal / len(directions) if directions else 0.0,
        "direction_change_count": changes,
        "direction_change_fraction": changes / max(1, len(directions) - 1),
        "boundary_cell_count": boundary,
        "boundary_cell_fraction": boundary / len(path_cells),
        "note": "Direction changes and diagonal steps are grid diagnostics, not a survey-alignment quality measure.",
    }


def _endpoint_diagnostics(
    bundle: Mapping[str, Any], path_cells: list[list[int]], config: Mapping[str, Any] | None
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "route_start_cell": path_cells[0],
        "route_end_cell": path_cells[-1],
        "origin_cell_match": path_cells[0] == bundle.get("origin_cell"),
        "destination_cell_match": path_cells[-1] == bundle.get("destination_cell"),
    }
    if not config or not isinstance(config.get("endpoints"), Mapping):
        return result
    from rasterio.warp import transform

    projected = _cell_projected_coordinates(dict(bundle), [path_cells[0], path_cells[-1]])
    for role, endpoint in (("origin", config["endpoints"].get("origin")), ("destination", config["endpoints"].get("destination"))):
        if not isinstance(endpoint, Mapping):
            continue
        x_values, y_values = transform(
            "EPSG:7844",
            "EPSG:7856",
            [float(endpoint["longitude"])],
            [float(endpoint["latitude"])],
        )
        index = 0 if role == "origin" else 1
        result.setdefault("endpoint_snap_offsets_m", {})[role] = math.hypot(
            x_values[0] - projected[index][0], y_values[0] - projected[index][1]
        )
    return result


def assess_route(
    bundle: dict[str, Any],
    route: dict[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
    vector_layers: Mapping[str, str | Path] | None = None,
    svtm_raster: str | Path | None = None,
    svtm_archive: str | Path | None = None,
) -> dict[str, Any]:
    path_cells = route.get("path_cells")
    if not isinstance(path_cells, list) or not path_cells:
        raise RouteAssessmentError("route has no path_cells")
    coordinates = _cell_coordinates(bundle, path_cells)
    cell_size = float(bundle["cell_size_m"])
    component_grids = bundle.get("component_grids")
    if not isinstance(component_grids, dict):
        raise RouteAssessmentError("grid bundle has no component grids")
    component_cell_counts: dict[str, int] = {}
    component_route_sums: dict[str, float] = {}
    terrain_values: list[float] = []
    slope_degrees: list[float] = []
    total_length_m = 0.0
    for index, cell in enumerate(path_cells):
        row, col = int(cell[0]), int(cell[1])
        for component, values in component_grids.items():
            if not isinstance(values, list) or row >= len(values) or col >= len(values[row]):
                raise RouteAssessmentError(f"component grid is incompatible with route: {component}")
            value = float(values[row][col])
            component_route_sums[component] = component_route_sums.get(component, 0.0) + value
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
    rows, cols = int(bundle["grid_shape"]["rows"]), int(bundle["grid_shape"]["cols"])
    diagnostic_grids = bundle.get("diagnostic_grids", {})
    if isinstance(diagnostic_grids, Mapping) and isinstance(diagnostic_grids.get("slope_degrees"), list):
        slope_grid = diagnostic_grids["slope_degrees"]
        for row, col in path_cells:
            try:
                slope_degrees.append(float(slope_grid[int(row)][int(col)]))
            except (IndexError, TypeError, ValueError):
                raise RouteAssessmentError("slope diagnostic grid is incompatible with route")
    else:
        slope_degrees = [value * 20.0 for value in terrain_values]

    unavailable = {
        tuple(int(value) for value in cell)
        for cell in bundle.get("unavailable_cells", [])
        if isinstance(cell, list) and len(cell) == 2
    }
    unavailable_hits = [cell for cell in path_cells if tuple(cell) in unavailable]
    diagnostics: dict[str, Any] = {
        "unavailable_cell_count": len(unavailable_hits),
        "route_is_available": not unavailable_hits,
        "continuity_validated": True,
        "geometry_quality": _direction_quality(path_cells, rows, cols),
        "endpoints": _endpoint_diagnostics(bundle, path_cells, config),
    }
    try:
        from shapely.geometry import LineString

        centerline = LineString(_cell_projected_coordinates(bundle, path_cells))
        diagnostics["geometry_quality"]["route_centerline_is_simple"] = bool(centerline.is_simple)
    except ImportError:
        diagnostics["geometry_quality"]["route_centerline_is_simple"] = None
    assessment: dict[str, Any] = {
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
        "component_route_cell_sums": component_route_sums,
        "weighted_cell_exposure": {
            component: component_route_sums.get(component, 0.0) * float(weight)
            for component, weight in (route.get("weights") or {}).items()
        },
        "terrain_normalized_mean": sum(terrain_values) / len(terrain_values),
        "terrain_normalized_max": max(terrain_values),
        "slope_mean_degrees": sum(slope_degrees) / len(slope_degrees),
        "slope_max_degrees": max(slope_degrees),
        "diagnostics": diagnostics,
        "endpoint_cells": {
            "origin": path_cells[0],
            "destination": path_cells[-1],
        },
        "geometry": {
            "type": "LineString",
            "coordinates": [[float(x), float(y)] for x, y in coordinates],
        },
        "assessment_note": "Feature intersections use the route centerline through 100 m cell centres; rasterized source masks and source resolution limit physical precision.",
    }
    if vector_layers:
        try:
            from shapely.geometry import LineString

            projected = _cell_projected_coordinates(bundle, path_cells)
            route_line = LineString(projected)
            inventories = {}
            for component, artifact in vector_layers.items():
                inventories[component] = inventory_vector_intersections(route_line, artifact, component)
            assessment["impact_inventory"] = inventories
        except (RouteImpactError, OSError, TypeError, ValueError) as exc:
            raise RouteAssessmentError(f"could not inventory route impacts: {exc}") from exc
    if svtm_raster:
        try:
            assessment["impact_inventory"] = assessment.get("impact_inventory", {})
            assessment["impact_inventory"]["native_vegetation"] = inventory_svtm_route_cells(
                path_cells, bundle, svtm_raster, archive_path=svtm_archive
            )
        except (RouteImpactError, OSError, TypeError, ValueError) as exc:
            raise RouteAssessmentError(f"could not inventory SVTM route cells: {exc}") from exc
    return assessment


def assess_route_directory(
    bundle_path: str | Path,
    routes_dir: str | Path,
    *,
    config: Mapping[str, Any] | None = None,
    vector_layers: Mapping[str, str | Path] | None = None,
    svtm_raster: str | Path | None = None,
    svtm_archive: str | Path | None = None,
) -> dict[str, Any]:
    bundle = _load(Path(bundle_path))
    directory = Path(routes_dir)
    manifest = _load(directory / "routes_manifest.json")
    assessments = []
    for record in manifest.get("routes", []):
        route = _load(directory / record["artifact_path"])
        assessments.append(
            assess_route(
                bundle,
                route,
                config=config,
                vector_layers=vector_layers,
                svtm_raster=svtm_raster,
                svtm_archive=svtm_archive,
            )
        )
    by_preset = {assessment["preset"]: assessment for assessment in assessments}
    comparison = {
        "baseline": "shortest",
        "routes": [
            {
                "preset": assessment["preset"],
                "route_length_km": assessment["route_length_km"],
                "slope_mean_degrees": assessment["slope_mean_degrees"],
                "slope_max_degrees": assessment["slope_max_degrees"],
                "weighted_cell_exposure": assessment["weighted_cell_exposure"],
                "native_vegetation_cell_count": assessment.get("impact_inventory", {}).get("native_vegetation", {}).get("native_vegetation_cell_count"),
                "protected_area_count": assessment.get("impact_inventory", {}).get("protected_land", {}).get("intersected_feature_count"),
                "hydroline_crossing_count": assessment.get("impact_inventory", {}).get("hydrography_line", {}).get("crossing_feature_count"),
                "hydroarea_interaction_count": assessment.get("impact_inventory", {}).get("hydrography_area", {}).get("interaction_feature_count"),
                "major_road_crossing_count": assessment.get("impact_inventory", {}).get("roads", {}).get("major_road_intersection_count"),
                "railway_crossing_count": assessment.get("impact_inventory", {}).get("railways", {}).get("crossing_feature_count"),
            }
            for assessment in assessments
        ],
    }
    if "shortest" in by_preset:
        baseline = by_preset["shortest"]
        for record in comparison["routes"]:
            record["delta_to_shortest_km"] = record["route_length_km"] - baseline["route_length_km"]
            record["delta_weighted_cell_exposure"] = {
                component: record["weighted_cell_exposure"].get(component, 0.0)
                - baseline["weighted_cell_exposure"].get(component, 0.0)
                for component in set(record["weighted_cell_exposure"]) | set(baseline["weighted_cell_exposure"])
            }
            record["tradeoff_note"] = (
                "baseline shortest route"
                if record["preset"] == "shortest"
                else "compare added length against terrain, environmental, and crossing metrics; this is descriptive, not a preset recommendation"
            )
    return {
        "schema_version": 1,
        "format": "ico-route-assessments",
        "scenario": bundle["scenario"],
        "grid_bundle_path": str(Path(bundle_path).resolve()),
        "routes_manifest_path": str((directory / "routes_manifest.json").resolve()),
        "assessments": assessments,
        "comparison": comparison,
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
