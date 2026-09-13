"""Deterministic 8-connected least-cost routing on a rectangular grid."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from collections.abc import Sequence

Grid = Sequence[Sequence[float]]
Cell = tuple[int, int]


class NoPathError(RuntimeError):
    """Raised when the goal cannot be reached through finite-cost cells."""


@dataclass(frozen=True)
class RouteResult:
    path: tuple[Cell, ...]
    cost: float
    explored_cells: int


def _validate_grid(costs: Grid) -> tuple[int, int]:
    rows = len(costs)
    cols = len(costs[0]) if rows else 0
    if rows == 0 or cols == 0 or any(len(row) != cols for row in costs):
        raise ValueError("routing grid must be non-empty and rectangular")
    for row in costs:
        for value in row:
            if math.isnan(value) or value < 0:
                raise ValueError("routing costs must be non-negative and not NaN")
    return rows, cols


def _neighbors(cell: Cell, rows: int, cols: int) -> list[tuple[Cell, float]]:
    row, col = cell
    result: list[tuple[Cell, float]] = []
    for delta_row, delta_col, distance in (
        (-1, -1, math.sqrt(2)),
        (-1, 0, 1.0),
        (-1, 1, math.sqrt(2)),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (1, -1, math.sqrt(2)),
        (1, 0, 1.0),
        (1, 1, math.sqrt(2)),
    ):
        neighbor = (row + delta_row, col + delta_col)
        if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
            result.append((neighbor, distance))
    return result


def route_least_cost(
    costs: Grid,
    start: Cell,
    goal: Cell,
    algorithm: str = "astar",
) -> RouteResult:
    """Route from start to goal with A* or Dijkstra.

    Edge cost is the average of adjacent cell costs multiplied by physical grid
    distance (orthogonal=1, diagonal=sqrt(2)). Infinite cells are unavailable;
    diagonal moves cannot cut between two blocked orthogonal corners.
    Ties are resolved by heap insertion order and neighbor order for reproducibility.
    """

    rows, cols = _validate_grid(costs)
    if algorithm not in {"astar", "dijkstra"}:
        raise ValueError("algorithm must be 'astar' or 'dijkstra'")
    for cell in (start, goal):
        if not (0 <= cell[0] < rows and 0 <= cell[1] < cols):
            raise ValueError(f"cell {cell} is outside the routing grid")
    if not math.isfinite(costs[start[0]][start[1]]) or not math.isfinite(
        costs[goal[0]][goal[1]]
    ):
        raise NoPathError("start and goal must be traversable cells")
    if start == goal:
        return RouteResult((start,), 0.0, 1)

    finite_costs = [value for row in costs for value in row if math.isfinite(value)]
    minimum_cost = min(finite_costs, default=0.0)

    def heuristic(cell: Cell) -> float:
        if algorithm == "dijkstra":
            return 0.0
        return math.hypot(cell[0] - goal[0], cell[1] - goal[1]) * minimum_cost

    queue: list[tuple[float, float, int, Cell]] = []
    sequence = 0
    distances: dict[Cell, float] = {start: 0.0}
    previous: dict[Cell, Cell] = {}
    heapq.heappush(queue, (heuristic(start), 0.0, sequence, start))
    explored = 0

    while queue:
        _, distance, _, current = heapq.heappop(queue)
        if distance != distances.get(current):
            continue
        explored += 1
        if current == goal:
            path = [current]
            while path[-1] != start:
                path.append(previous[path[-1]])
            path.reverse()
            return RouteResult(tuple(path), distance, explored)
        current_cost = costs[current[0]][current[1]]
        for neighbor, step_distance in _neighbors(current, rows, cols):
            if step_distance > 1.0:
                crosses_blocked_corner = not math.isfinite(
                    costs[current[0]][neighbor[1]]
                ) or not math.isfinite(costs[neighbor[0]][current[1]])
                if crosses_blocked_corner:
                    continue
            neighbor_cost = costs[neighbor[0]][neighbor[1]]
            if not math.isfinite(neighbor_cost):
                continue
            candidate = distance + ((current_cost + neighbor_cost) / 2.0) * step_distance
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = current
                sequence += 1
                heapq.heappush(
                    queue,
                    (candidate + heuristic(neighbor), candidate, sequence, neighbor),
                )

    raise NoPathError(f"no traversable path from {start} to {goal}")
