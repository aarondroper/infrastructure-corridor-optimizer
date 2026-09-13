"""Dependency-light analytical primitives for corridor screening."""

from .cost import combine_cost_layers, normalize_clamped
from .routing import NoPathError, RouteResult, route_least_cost
from .sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    summarize_arcgis_metadata,
    validate_feature_geometries,
    validate_feature_payload_crs,
    validate_expected_layers,
    validate_expected_layer_names,
    validate_required_layer_type,
)
from .terrain import (
    TerrainArtifactError,
    load_terrain_artifact_metadata,
    select_terrain_artifact,
    validate_terrain_artifact,
)

__all__ = [
    "NoPathError",
    "RouteResult",
    "combine_cost_layers",
    "normalize_clamped",
    "route_least_cost",
    "ArcGISClient",
    "SourceAccessError",
    "SourceValidationError",
    "summarize_arcgis_metadata",
    "validate_feature_geometries",
    "validate_feature_payload_crs",
    "validate_expected_layers",
    "validate_expected_layer_names",
    "validate_required_layer_type",
    "TerrainArtifactError",
    "load_terrain_artifact_metadata",
    "select_terrain_artifact",
    "validate_terrain_artifact",
]
