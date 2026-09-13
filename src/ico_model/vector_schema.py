"""Source-preserving canonical schemas for validated ArcGIS vector features."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .sources import SourceValidationError


COMPONENT_FIELD_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "protected_land": {
        "name": ("name",),
        "land_type": ("type",),
        "iucn_category": ("iucn",),
        "gazetted_area": ("gaz_area",),
        "gis_area": ("gis_area",),
        "reserve_number": ("res_no",),
        "gazetted_date": ("gaz_date",),
    },
    "hydrography_line": {
        "name": ("hydroname",),
        "name_type": ("hydronametype",),
        "perenniality": ("perenniality",),
        "hierarchy": ("hierarchy",),
        "hydro_type": ("hydrotype",),
        "relevance": ("relevance",),
    },
    "named_watercourse_ss": {
        "name": ("hydroname",),
        "name_type": ("hydronametype",),
        "perenniality": ("perenniality",),
        "hierarchy": ("hierarchy",),
        "hydro_type": ("hydrotype",),
        "relevance": ("relevance",),
    },
    "named_watercourse_ls": {
        "name": ("hydroname",),
        "name_type": ("hydronametype",),
        "perenniality": ("perenniality",),
        "hierarchy": ("hierarchy",),
        "hydro_type": ("hydrotype",),
        "relevance": ("relevance",),
    },
    "hydrography_area": {
        "name": ("hydroname",),
        "name_type": ("hydronametype",),
        "perenniality": ("perenniality",),
        "hydro_type": ("hydrotype",),
        "relevance": ("relevance",),
    },
    "roads": {
        "name": ("roadnamebase",),
        "name_type": ("roadnametype",),
        "hierarchy": ("functionhierarchy",),
        "operational_type": ("roadontype",),
        "surface": ("surface",),
        "lane_count": ("lanecount",),
        "operational_status": ("operationalstatus",),
        "relevance": ("relevance",),
    },
    "railways": {
        "name": ("railwayname",),
        "gauge": ("gauge",),
        "operational_type": ("railontype",),
        "operational_status": ("operationalstatus",),
        "relevance": ("relevance",),
    },
}

_OBJECT_ID_ALIASES = ("objectid", "object_id", "fid", "id")


def _casefolded_attributes(feature: Mapping[str, Any]) -> dict[str, Any]:
    attributes = feature.get("attributes")
    if not isinstance(attributes, Mapping):
        raise SourceValidationError("ArcGIS feature has no attribute object")
    return {str(key).casefold(): value for key, value in attributes.items()}


def _object_id(attributes: Mapping[str, Any], component: str) -> int:
    for alias in _OBJECT_ID_ALIASES:
        if alias in attributes:
            value = attributes[alias]
            if isinstance(value, bool):
                break
            try:
                return int(value)
            except (TypeError, ValueError):
                break
    raise SourceValidationError(f"{component} feature has no integer object ID")


def normalize_feature(feature: Mapping[str, Any], component: str) -> dict[str, Any]:
    """Return one canonical feature while retaining raw source values and geometry."""

    aliases = COMPONENT_FIELD_ALIASES.get(component)
    if aliases is None:
        raise SourceValidationError(f"no canonical vector schema is configured: {component}")
    if "geometry" not in feature:
        raise SourceValidationError(f"{component} feature has no geometry member")
    attributes = _casefolded_attributes(feature)
    source_object_id = _object_id(attributes, component)
    properties: dict[str, Any] = {"source_object_id": source_object_id}
    for canonical_name, source_names in aliases.items():
        for source_name in source_names:
            folded_name = source_name.casefold()
            if folded_name in attributes:
                properties[canonical_name] = attributes[folded_name]
                break
    return {
        "type": "Feature",
        "id": source_object_id,
        "properties": properties,
        "source_attributes": dict(feature["attributes"]),
        "geometry": feature["geometry"],
    }


def normalize_feature_collection(
    artifact: Mapping[str, Any], component: str
) -> dict[str, Any]:
    """Normalize an acquired collection without changing geometry or analytical values."""

    if artifact.get("format") != "arcgis-json-feature-collection":
        raise SourceValidationError("cannot normalize an unknown vector artifact format")
    source_id = artifact.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        raise SourceValidationError("vector artifact has no source ID")
    features = artifact.get("features")
    if (
        not isinstance(features, Sequence)
        or isinstance(features, (str, bytes))
        or not all(isinstance(feature, Mapping) for feature in features)
    ):
        raise SourceValidationError("vector artifact has no feature sequence")
    normalized = [normalize_feature(feature, component) for feature in features]
    return {
        "schema_version": 1,
        "format": "ico-canonical-vector-feature-collection",
        "source_id": source_id,
        "component": component,
        "layer_id": artifact.get("layer_id"),
        "layer_name": artifact.get("layer_name"),
        "geometry_type": artifact.get("geometry_type"),
        "source_crs_epsg": artifact.get("source_crs_epsg"),
        "output_crs_epsg": artifact.get("output_crs_epsg"),
        "processing_envelope": artifact.get("processing_envelope"),
        "query": artifact.get("query"),
        "features": normalized,
    }
