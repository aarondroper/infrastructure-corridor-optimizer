"""Dependency-light analytical primitives for corridor screening."""

from .cost import combine_cost_layers, normalize_clamped
from .routing import NoPathError, RouteResult, route_least_cost
from .sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    summarize_arcgis_metadata,
    validate_feature_geometries,
    validate_feature_object_ids,
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
from .dem_acquisition import (
    DemAcquisitionError,
    acquire_copernicus_tiles,
    copernicus_tiles,
    inspect_geotiff,
    validate_copernicus_geotiff,
)
from .vector_artifacts import validate_vector_manifest
from .vector_schema import (
    COMPONENT_FIELD_ALIASES,
    normalize_feature,
    normalize_feature_collection,
)
from .precomputed_routes import (
    RouteAssetError,
    generate_precomputed_routes,
    load_grid_bundle,
    write_precomputed_routes,
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
    "validate_feature_object_ids",
    "validate_feature_payload_crs",
    "validate_expected_layers",
    "validate_expected_layer_names",
    "validate_required_layer_type",
    "TerrainArtifactError",
    "load_terrain_artifact_metadata",
    "select_terrain_artifact",
    "validate_terrain_artifact",
    "DemAcquisitionError",
    "acquire_copernicus_tiles",
    "copernicus_tiles",
    "inspect_geotiff",
    "validate_copernicus_geotiff",
    "validate_vector_manifest",
    "COMPONENT_FIELD_ALIASES",
    "normalize_feature",
    "normalize_feature_collection",
    "RouteAssetError",
    "generate_precomputed_routes",
    "load_grid_bundle",
    "write_precomputed_routes",
]
