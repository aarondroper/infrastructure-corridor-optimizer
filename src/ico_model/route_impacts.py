"""Feature-level route impact inventories for validated S1 source artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class RouteImpactError(ValueError):
    """Raised when a route impact inventory cannot be produced safely."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RouteImpactError(f"could not read vector artifact: {path}") from exc
    if not isinstance(value, dict):
        raise RouteImpactError(f"vector artifact is not an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _arcgis_shape(geometry: Mapping[str, Any], geometry_type: str) -> Any:
    from shapely.geometry import LineString, MultiLineString, Polygon, shape
    from shapely.validation import make_valid

    try:
        if geometry_type == "esriGeometryPolyline":
            paths = geometry.get("paths")
            parts = [path for path in paths or [] if isinstance(path, list) and len(path) >= 2]
            if not parts:
                raise RouteImpactError("polyline feature has no usable path")
            result = LineString(parts[0]) if len(parts) == 1 else MultiLineString(parts)
        elif geometry_type == "esriGeometryPolygon":
            rings = geometry.get("rings")
            if not isinstance(rings, list) or not rings:
                raise RouteImpactError("polygon feature has no rings")
            result = shape({"type": "Polygon", "coordinates": rings})
        else:
            raise RouteImpactError(f"unsupported source geometry type: {geometry_type}")
    except (TypeError, ValueError) as exc:
        raise RouteImpactError("source geometry cannot be converted to a shape") from exc
    if result.is_empty:
        raise RouteImpactError("source geometry is empty")
    if not result.is_valid:
        result = make_valid(result)
    if result.is_empty or not result.is_valid:
        raise RouteImpactError("source geometry remains invalid after repair")
    return result


def _source_feature_id(attributes: Mapping[str, Any]) -> int | str:
    for key, value in attributes.items():
        if str(key).casefold() in {"objectid", "object_id", "fid", "id"}:
            try:
                return int(value)
            except (TypeError, ValueError):
                return str(value)
    raise RouteImpactError("source feature has no stable object ID")


def _compact_attributes(component: str, attributes: Mapping[str, Any]) -> dict[str, Any]:
    wanted = {
        "protected_land": ("NAME", "NAME_SHORT", "TYPE", "IUCN", "RES_NO"),
        "hydrography_line": ("hydroname", "hydronametype", "perenniality", "hierarchy", "hydrotype", "relevance"),
        "hydrography_area": ("hydroname", "hydronametype", "perenniality", "hydrotype", "relevance"),
        "roads": ("roadnamebase", "roadnametype", "functionhierarchy", "roadontype", "surface", "lanecount", "operationalstatus", "relevance"),
        "railways": ("railwayname", "gauge", "railontype", "operationalstatus", "relevance"),
    }.get(component, ())
    folded = {str(key).casefold(): value for key, value in attributes.items()}
    return {key: folded[key.casefold()] for key in wanted if key.casefold() in folded}


def _artifact_record(path: Path, feature_count: int) -> dict[str, Any]:
    return {
        "artifact_path": str(path.resolve()),
        "artifact_bytes": path.stat().st_size,
        "artifact_sha256": _sha256(path),
        "source_feature_count": feature_count,
    }


def inventory_vector_intersections(
    route_line: Any,
    artifact_path: str | Path,
    component: str,
    *,
    major_road_hierarchy_max: int = 4,
) -> dict[str, Any]:
    """Inventory each unique source feature intersected by a route centerline."""

    path = Path(artifact_path).resolve()
    artifact = _load_json(path)
    if artifact.get("format") != "arcgis-json-feature-collection":
        raise RouteImpactError(f"unsupported vector artifact format: {path}")
    if artifact.get("output_crs_epsg") != 7856:
        raise RouteImpactError(f"vector artifact is not EPSG:7856: {path}")
    geometry_type = artifact.get("geometry_type")
    features = artifact.get("features")
    if not isinstance(features, list) or not features:
        raise RouteImpactError(f"vector artifact has no features: {path}")

    geometries: list[Any] = []
    records: list[tuple[int | str, dict[str, Any], Any]] = []
    source_ids: set[int | str] = set()
    for feature in features:
        if not isinstance(feature, Mapping) or not isinstance(feature.get("attributes"), Mapping):
            raise RouteImpactError(f"invalid feature in vector artifact: {path}")
        geometry = feature.get("geometry")
        if not isinstance(geometry, Mapping):
            raise RouteImpactError(f"feature has no geometry in vector artifact: {path}")
        shape = _arcgis_shape(geometry, str(geometry_type))
        source_id = _source_feature_id(feature["attributes"])
        if source_id in source_ids:
            raise RouteImpactError(f"duplicate source object ID in vector artifact: {source_id}")
        source_ids.add(source_id)
        geometries.append(shape)
        records.append((source_id, dict(feature["attributes"]), shape))

    from shapely.strtree import STRtree

    tree = STRtree(geometries)
    candidate_indices = tree.query(route_line, predicate="intersects")
    features_out: list[dict[str, Any]] = []
    for raw_index in candidate_indices:
        index = int(raw_index)
        source_id, attributes, geometry = records[index]
        intersection = route_line.intersection(geometry)
        if intersection.is_empty:
            continue
        properties = _compact_attributes(component, attributes)
        dimension = 0 if intersection.geom_type in {"Point", "MultiPoint"} else 1 if intersection.geom_type in {"LineString", "MultiLineString"} else 2
        entry: dict[str, Any] = {
            "source_object_id": source_id,
            "intersection_length_m": round(float(intersection.length), 3),
            "intersection_dimension": dimension,
            "properties": properties,
        }
        if component == "roads":
            hierarchy = properties.get("functionhierarchy")
            try:
                hierarchy_value = int(hierarchy)
            except (TypeError, ValueError):
                hierarchy_value = None
            entry["major_road"] = hierarchy_value is not None and hierarchy_value <= major_road_hierarchy_max
        features_out.append(entry)

    features_out.sort(key=lambda item: str(item["source_object_id"]))
    result: dict[str, Any] = {
        "component": component,
        "source_crs_epsg": artifact.get("output_crs_epsg"),
        "geometry_type": geometry_type,
        "source": _artifact_record(path, len(features)),
        "intersected_feature_count": len(features_out),
        "total_intersection_length_m": round(sum(item["intersection_length_m"] for item in features_out), 3),
        "features": features_out,
    }
    if component == "roads":
        result["major_road_definition"] = {
            "field": "functionhierarchy",
            "operator": "<=",
            "threshold": major_road_hierarchy_max,
            "note": "reporting classification only; it does not alter the approved routing cost surface",
        }
        result["major_road_intersection_count"] = sum(1 for item in features_out if item["major_road"])
    if component in {"hydrography_line", "railways"}:
        result["crossing_feature_count"] = len(features_out)
    if component in {"hydrography_area", "protected_land"}:
        result["interaction_feature_count"] = len(features_out)
    return result


def _read_svtm_classes(archive_path: Path) -> dict[int, dict[str, Any]]:
    if not archive_path.is_file():
        return {}
    from .svtm_raster import read_dbf_from_zip
    with __import__("zipfile").ZipFile(archive_path) as archive:
        members = [info.filename for info in archive.infolist() if info.filename.lower().endswith(".tif.vat.dbf")]
    if len(members) != 1:
        return {}
    _fields, rows = read_dbf_from_zip(archive_path, members[0])
    classes: dict[int, dict[str, Any]] = {}
    for row in rows:
        try:
            value = int(row["Value"])
        except (KeyError, TypeError, ValueError):
            continue
        classes[value] = {key: row.get(key) for key in ("PCTID", "PCTName", "vegClass", "vegForm", "labels", "form_PCT", "PCT_form")}
    return classes


def inventory_svtm_route_cells(
    path_cells: list[list[int]],
    bundle: Mapping[str, Any],
    raster_path: str | Path,
    *,
    archive_path: str | Path | None = None,
) -> dict[str, Any]:
    """Report classified SVTM values sampled at the route's geographic cells."""

    try:
        import rasterio
        from rasterio.transform import Affine
        from rasterio.warp import transform
    except ImportError as exc:
        raise RouteImpactError("SVTM route inventory requires rasterio and numpy") from exc
    transform_values = bundle.get("provenance", {}).get("transform")
    if not isinstance(transform_values, list) or len(transform_values) < 6:
        raise RouteImpactError("grid bundle has no route transform")
    affine = Affine(*[float(value) for value in transform_values[:6]])
    projected = [affine @ (int(cell[1]) + 0.5, int(cell[0]) + 0.5) for cell in path_cells]
    x_values, y_values = transform("EPSG:7856", "EPSG:3308", [x for x, _ in projected], [y for _, y in projected])
    with rasterio.open(Path(raster_path).resolve()) as source:
        if source.crs.to_epsg() != 3308 or source.count != 1:
            raise RouteImpactError("SVTM route raster must be a single EPSG:3308 band")
        rows, cols = rasterio.transform.rowcol(source.transform, x_values, y_values)
        if any(row < 0 or row >= source.height or col < 0 or col >= source.width for row, col in zip(rows, cols)):
            raise RouteImpactError("SVTM route cells fall outside the validated raster coverage")
        samples = source.read(1, masked=False)[rows, cols]
        nodata = int(source.nodata) if source.nodata is not None else 65535
    classes = _read_svtm_classes(Path(archive_path).resolve()) if archive_path else {}
    counts: dict[int, int] = {}
    for value in samples.tolist():
        counts[int(value)] = counts.get(int(value), 0) + 1
    class_entries = []
    for value in sorted(counts):
        item: dict[str, Any] = {"value": value, "route_cell_count": counts[value]}
        if value in classes:
            item.update({key: val for key, val in classes[value].items() if val is not None})
        class_entries.append(item)
    native_count = sum(count for value, count in counts.items() if value > 0 and value != nodata)
    return {
        "component": "native_vegetation",
        "representation": "classified-raster-route-cell-inventory",
        "raster_path": str(Path(raster_path).resolve()),
        "raster_bytes": Path(raster_path).stat().st_size,
        "raster_sha256": _sha256(Path(raster_path).resolve()),
        "nodata_value": nodata,
        "route_cell_count": len(path_cells),
        "native_vegetation_cell_count": native_count,
        "native_vegetation_fraction": native_count / len(path_cells),
        "nodata_cell_count": counts.get(nodata, 0),
        "not_classified_cell_count": counts.get(0, 0),
        "unique_class_count": len([value for value in counts if value > 0 and value != nodata]),
        "classes": class_entries,
        "note": "Raster cell inventory is the analytical equivalent of feature inventory; no polygon feature count is inferred.",
    }
