"""Derive the approved S1 geographic cost grid from validated source artifacts."""

from __future__ import annotations

import hashlib
import json
import math
from contextlib import ExitStack
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class GeographicGridError(ValueError):
    """Raised when geographic source inputs cannot produce a defensible grid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GeographicGridError(f"could not read JSON source: {path}") from exc
    if not isinstance(payload, dict):
        raise GeographicGridError(f"JSON source must be an object: {path}")
    return payload


def _arcgis_geometry_to_shape(geometry: Mapping[str, Any], geometry_type: str) -> tuple[Any, bool]:
    from shapely.geometry import LineString, MultiLineString, Polygon, shape
    from shapely.validation import make_valid

    try:
        if geometry_type == "esriGeometryPolyline":
            paths = geometry.get("paths")
            if not isinstance(paths, list):
                raise GeographicGridError("polyline geometry has no paths")
            parts = [path for path in paths if isinstance(path, list) and len(path) >= 2]
            if not parts:
                raise GeographicGridError("polyline geometry has no usable path")
            result = LineString(parts[0]) if len(parts) == 1 else MultiLineString(parts)
        elif geometry_type == "esriGeometryPolygon":
            rings = geometry.get("rings")
            if not isinstance(rings, list) or not rings:
                raise GeographicGridError("polygon geometry has no rings")
            result = shape({"type": "Polygon", "coordinates": rings})
        else:
            raise GeographicGridError(f"unsupported rasterization geometry: {geometry_type}")
    except (TypeError, ValueError) as exc:
        raise GeographicGridError("ArcGIS geometry cannot be converted to a valid shape") from exc
    if result.is_empty:
        raise GeographicGridError("ArcGIS geometry is empty")
    repaired = not result.is_valid
    if repaired:
        result = make_valid(result)
    if result.is_empty or not result.is_valid:
        raise GeographicGridError("ArcGIS geometry remains invalid after repair")
    return result, repaired


def _vector_mask(
    artifact_path: Path,
    *,
    geometry_type: str,
    shape: tuple[int, int],
    transform: Any,
) -> tuple[Any, dict[str, int]]:
    import numpy as np
    from rasterio.features import rasterize

    artifact = _load_json(artifact_path)
    if artifact.get("format") != "arcgis-json-feature-collection":
        raise GeographicGridError(f"unsupported vector artifact: {artifact_path}")
    if artifact.get("output_crs_epsg") != 7856:
        raise GeographicGridError(f"vector artifact is not EPSG:7856: {artifact_path}")
    features = artifact.get("features")
    if not isinstance(features, list) or not features:
        raise GeographicGridError(f"vector artifact has no features: {artifact_path}")
    geometries = []
    repaired = 0
    for feature in features:
        if not isinstance(feature, Mapping):
            raise GeographicGridError(f"vector artifact has an invalid feature: {artifact_path}")
        geometry = feature.get("geometry")
        if not isinstance(geometry, Mapping):
            raise GeographicGridError(f"vector feature has no geometry: {artifact_path}")
        converted, was_repaired = _arcgis_geometry_to_shape(geometry, geometry_type)
        geometries.append(converted)
        repaired += int(was_repaired)
    mask = rasterize(
        ((geometry, 1) for geometry in geometries),
        out_shape=shape,
        transform=transform,
        fill=0,
        all_touched=True,
        dtype="uint8",
    )
    return mask.astype(np.float32), {"feature_count": len(features), "repaired_geometry_count": repaired}


def _manifest_layer(manifest_path: Path, component: str) -> tuple[dict[str, Any], Path]:
    manifest = _load_json(manifest_path)
    if manifest.get("format") != "arcgis-json-feature-collections":
        raise GeographicGridError(f"unsupported vector manifest: {manifest_path}")
    for source in manifest.get("sources", []):
        for layer in source.get("layers", []):
            if layer.get("component") == component:
                artifact = Path(layer["artifact_path"])
                if not artifact.is_absolute():
                    artifact = manifest_path.parent / artifact
                return layer, artifact.resolve()
    raise GeographicGridError(f"component {component!r} is absent from {manifest_path}")


def _grid_context(config: Mapping[str, Any], cell_size_m: float) -> tuple[Any, int, int, dict[str, float]]:
    from rasterio.transform import from_origin
    from rasterio.warp import transform_bounds

    envelope = config.get("provisional_processing_envelope_gda2020")
    if not isinstance(envelope, Mapping):
        raise GeographicGridError("configuration has no S1 envelope")
    try:
        source_bounds = tuple(float(envelope[key]) for key in ("west", "south", "east", "north"))
    except (KeyError, TypeError, ValueError) as exc:
        raise GeographicGridError("S1 envelope is incomplete") from exc
    target_bounds = transform_bounds("EPSG:7844", "EPSG:7856", *source_bounds)
    west = math.floor(target_bounds[0] / cell_size_m) * cell_size_m
    south = math.floor(target_bounds[1] / cell_size_m) * cell_size_m
    east = math.ceil(target_bounds[2] / cell_size_m) * cell_size_m
    north = math.ceil(target_bounds[3] / cell_size_m) * cell_size_m
    cols = int(round((east - west) / cell_size_m))
    rows = int(round((north - south) / cell_size_m))
    if rows <= 0 or cols <= 0 or rows * cols > 2_000_000:
        raise GeographicGridError(f"unsafe S1 grid dimensions: {rows}x{cols}")
    return from_origin(west, north, cell_size_m, cell_size_m), rows, cols, {
        "west": west,
        "south": south,
        "east": east,
        "north": north,
    }


def _endpoint_cell(config: Mapping[str, Any], endpoint_name: str, transform: Any, rows: int, cols: int) -> list[int]:
    from rasterio.transform import rowcol
    from rasterio.warp import transform as project

    endpoint = config["endpoints"][endpoint_name]
    x, y = project("EPSG:7844", "EPSG:7856", [float(endpoint["longitude"])], [float(endpoint["latitude"])])
    row, col = rowcol(transform, x[0], y[0])
    if not (0 <= row < rows and 0 <= col < cols):
        raise GeographicGridError(f"{endpoint_name} endpoint is outside the S1 grid")
    return [int(row), int(col)]


def _source_record(manifest_path: Path, component: str, artifact: Path) -> dict[str, Any]:
    layer, _ = _manifest_layer(manifest_path, component)
    return {
        "manifest_path": str(manifest_path.resolve()),
        "artifact_path": str(artifact.resolve()),
        "artifact_bytes": artifact.stat().st_size,
        "artifact_sha256": _sha256(artifact),
        "component": component,
        "feature_count": layer["feature_count"],
        "output_crs_epsg": layer["output_crs_epsg"],
    }


def derive_s1_grid(
    config: Mapping[str, Any],
    *,
    cell_size_m: float,
    dem_dir: str | Path,
    svtm_raster: str | Path,
    vector_manifests: Mapping[str, str | Path],
) -> dict[str, Any]:
    """Build a 100 m normalized grid from the approved local S1 sources."""

    try:
        import numpy as np
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.merge import merge
        from rasterio.warp import reproject
    except ImportError as exc:
        raise GeographicGridError("geographic derivation requires the project geospatial extra") from exc
    if not math.isfinite(cell_size_m) or cell_size_m <= 0:
        raise GeographicGridError("cell_size_m must be finite and positive")
    transform, rows, cols, bounds = _grid_context(config, cell_size_m)
    dem_root = Path(dem_dir).resolve()
    dem_manifest_path = dem_root / "dem_manifest.json"
    dem_manifest = _load_json(dem_manifest_path)
    if dem_manifest.get("coverage_status") != "complete" or dem_manifest.get("crs_epsg") != 4326:
        raise GeographicGridError("DEM manifest is not a complete EPSG:4326 artifact")
    dem_paths = sorted(dem_root.rglob("*.tif"))
    if not dem_paths:
        raise GeographicGridError("DEM directory contains no GeoTIFF tiles")
    svtm_path = Path(svtm_raster).resolve()
    if not svtm_path.is_file():
        raise GeographicGridError(f"SVTM raster is missing: {svtm_path}")

    with ExitStack() as stack:
        dem_sources = [stack.enter_context(rasterio.open(path)) for path in dem_paths]
        mosaic, mosaic_transform = merge(dem_sources, nodata=-32767)
        elevation = np.full((rows, cols), np.nan, dtype="float32")
        reproject(
            mosaic[0], elevation,
            src_transform=mosaic_transform,
            src_crs=dem_sources[0].crs,
            src_nodata=-32767,
            dst_transform=transform,
            dst_crs="EPSG:7856",
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        valid_elevation = np.isfinite(elevation)
        if not valid_elevation.any():
            raise GeographicGridError("DEM reprojection produced no valid S1 cells")
        slope_x, slope_y = np.gradient(np.nan_to_num(elevation, nan=0.0), cell_size_m, cell_size_m)
        slope = np.degrees(np.arctan(np.hypot(slope_x, slope_y))).astype("float32")

        with rasterio.open(svtm_path) as source:
            svtm = np.full((rows, cols), 65535, dtype="uint16")
            reproject(
                rasterio.band(source, 1), svtm,
                src_transform=source.transform,
                src_crs=source.crs,
                src_nodata=65535,
                dst_transform=transform,
                dst_crs="EPSG:7856",
                dst_nodata=65535,
                resampling=Resampling.nearest,
            )
        valid_svtm = svtm != 65535

    vector_inputs: dict[str, dict[str, Any]] = {}
    for component, manifest_value in vector_manifests.items():
        manifest_path = Path(manifest_value).resolve()
        from .vector_artifacts import validate_vector_manifest

        validate_vector_manifest(
            manifest_path,
            expected_scenario=str(config["scenario"]),
            expected_output_crs_epsg=7856,
        )
        layer, artifact_path = _manifest_layer(manifest_path, component)
        vector_inputs[component] = _source_record(manifest_path, component, artifact_path)
        vector_inputs[component]["geometry_type"] = layer["geometry_type"]
        vector_inputs[component]["mask"], vector_inputs[component]["rasterization"] = _vector_mask(
            artifact_path,
            geometry_type=layer["geometry_type"],
            shape=(rows, cols),
            transform=transform,
        )

    components = {
        "length": np.ones((rows, cols), dtype="float32"),
        "terrain": np.clip(slope / 20.0, 0.0, 1.0),
        "protected_land": vector_inputs["protected_land"]["mask"],
        "native_vegetation": (svtm > 0).astype("float32"),
        "hydrography": np.maximum(vector_inputs["hydrography_line"]["mask"], vector_inputs["hydrography_area"]["mask"]),
        "roads": vector_inputs["roads"]["mask"],
        "railways": vector_inputs["railways"]["mask"],
    }
    unavailable = np.argwhere(~valid_elevation | ~valid_svtm)
    origin_cell = _endpoint_cell(config, "origin", transform, rows, cols)
    destination_cell = _endpoint_cell(config, "destination", transform, rows, cols)
    unavailable_set = {tuple(int(value) for value in cell) for cell in unavailable}
    if tuple(origin_cell) in unavailable_set or tuple(destination_cell) in unavailable_set:
        raise GeographicGridError("an endpoint falls on a DEM or SVTM nodata cell")
    return {
        "schema_version": 1,
        "format": "ico-normalized-cost-grids",
        "scenario": config["scenario"],
        "analysis_crs_epsg": 7856,
        "cell_size_m": cell_size_m,
        "grid_shape": {"rows": rows, "cols": cols},
        "grid_bounds": bounds,
        "origin_cell": origin_cell,
        "destination_cell": destination_cell,
        "unavailable_cells": [list(cell) for cell in sorted(unavailable_set)],
        "component_grids": {
            name: values.tolist() for name, values in components.items()
        },
        "diagnostic_grids": {
            "slope_degrees": slope.tolist(),
        },
        "diagnostics": {
            "dem_valid_cell_count": int(valid_elevation.sum()),
            "svtm_valid_cell_count": int(valid_svtm.sum()),
            "unavailable_cell_count": len(unavailable_set),
            "native_vegetation_cell_count": int((svtm > 0).sum()),
            "slope_min_degrees": float(np.nanmin(slope[valid_elevation])),
            "slope_max_degrees": float(np.nanmax(slope[valid_elevation])),
        },
        "provenance": {
            "config_path": "config/model.json",
            "source_crs_epsg": 7844,
            "processing_envelope": config["provisional_processing_envelope_gda2020"],
            "dem_manifest_path": str(dem_manifest_path),
            "dem_manifest_sha256": _sha256(dem_manifest_path),
            "svtm_raster_path": str(svtm_path),
            "svtm_raster_sha256": _sha256(svtm_path),
            "vector_inputs": {
                key: {k: value for k, value in record.items() if k not in {"mask"}}
                for key, record in vector_inputs.items()
            },
            "transform": [float(value) for value in transform],
        },
    }


def write_grid_bundle(bundle: Mapping[str, Any], path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(json.dumps(bundle, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination
