"""Dependency-light analytical primitives for corridor screening."""

from .cost import combine_cost_layers, normalize_clamped
from .routing import NoPathError, RouteResult, route_least_cost
from .sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    summarize_arcgis_metadata,
    validate_expected_layers,
    validate_expected_layer_names,
    validate_required_layer_type,
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
    "validate_expected_layers",
    "validate_expected_layer_names",
    "validate_required_layer_type",
]
