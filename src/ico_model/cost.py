"""Validation and combination of normalized routing-cost grids.

The module intentionally contains no raster or GIS dependency. Geospatial
preprocessing will produce the grids consumed here in the later pipeline.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

Grid = list[list[float]]


def normalize_clamped(value: float, lower: float, upper: float) -> float:
    """Normalize a value to [0, 1], clipping values outside the source range."""

    if not math.isfinite(value):
        raise ValueError("normalization value must be finite")
    if not math.isfinite(lower) or not math.isfinite(upper) or upper <= lower:
        raise ValueError("normalization requires finite upper > lower bounds")
    return min(1.0, max(0.0, (value - lower) / (upper - lower)))


def validate_weights(
    weights: Mapping[str, float], expected_components: Sequence[str]
) -> None:
    """Validate a complete, non-negative weight vector."""

    expected = set(expected_components)
    actual = set(weights)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(
            f"weight components do not match model; missing={missing}, "
            f"unexpected={unexpected}"
        )
    if any(not math.isfinite(value) or value < 0 for value in weights.values()):
        raise ValueError("weights must be finite and non-negative")
    if sum(weights.values()) <= 0:
        raise ValueError("at least one weight must be positive")


def _shape(grid: Sequence[Sequence[float]]) -> tuple[int, int]:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0 or any(len(row) != cols for row in grid):
        raise ValueError("cost grids must be non-empty and rectangular")
    return rows, cols


def combine_cost_layers(
    layers: Mapping[str, Sequence[Sequence[float]]],
    weights: Mapping[str, float],
    hard_excluded: Sequence[Sequence[bool]] | None = None,
) -> Grid:
    """Return a weighted cost grid, using infinity for invalid/blocked cells.

    Component values are expected to be normalized or otherwise explicitly scaled
    by the preprocessing stage. A non-finite input is treated as unusable so a
    partial raster cannot silently become a plausible route.
    """

    if not layers:
        raise ValueError("at least one cost layer is required")
    component_ids = list(layers)
    validate_weights(weights, component_ids)
    dimensions = [_shape(layer) for layer in layers.values()]
    if len(set(dimensions)) != 1:
        raise ValueError("all cost layers must have the same shape")
    rows, cols = dimensions[0]
    if hard_excluded is not None and _shape(hard_excluded) != (rows, cols):
        raise ValueError("hard exclusion grid must match cost-layer shape")

    combined: Grid = []
    for row_index in range(rows):
        output_row: list[float] = []
        for col_index in range(cols):
            if hard_excluded is not None and hard_excluded[row_index][col_index]:
                output_row.append(math.inf)
                continue
            values = [layers[name][row_index][col_index] for name in component_ids]
            if any(not math.isfinite(value) for value in values):
                output_row.append(math.inf)
                continue
            output_row.append(
                sum(weights[name] * layers[name][row_index][col_index] for name in component_ids)
            )
        combined.append(output_row)
    return combined
