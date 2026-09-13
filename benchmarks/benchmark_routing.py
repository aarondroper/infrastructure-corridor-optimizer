#!/usr/bin/env python3
"""Benchmark the dependency-light grid router on deterministic proxy workloads."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ico_model.routing import route_least_cost


def synthetic_cost_grid(size: int) -> list[list[float]]:
    """Build a deterministic penalty landscape with several broad avoidance zones."""

    grid: list[list[float]] = []
    for row in range(size):
        values = []
        for col in range(size):
            cost = 1.0
            if abs(col - int(size * 0.34)) < max(2, size // 35):
                cost += 7.0 if row < int(size * 0.72) else 1.0
            if abs(row - int(size * 0.62)) < max(2, size // 40):
                cost += 5.0 if col > int(size * 0.18) else 1.0
            distance = math.hypot(row - size * 0.60, col - size * 0.70)
            if distance < size * 0.13:
                cost += 4.0
            values.append(cost)
        grid.append(values)
    return grid


def run(size: int, algorithm: str) -> dict[str, float | int | str]:
    grid = synthetic_cost_grid(size)
    start = (1, 1)
    goal = (size - 2, size - 2)
    started = time.perf_counter()
    result = route_least_cost(grid, start, goal, algorithm)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "size": size,
        "algorithm": algorithm,
        "runtime_ms": round(elapsed_ms, 3),
        "explored_cells": result.explored_cells,
        "path_cells": len(result.path),
        "path_cost": round(result.cost, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[128, 256, 512])
    args = parser.parse_args()
    records = [run(size, algorithm) for size in args.sizes for algorithm in ("astar", "dijkstra")]
    print(json.dumps({"benchmark": "deterministic-penalty-grid", "records": records}, indent=2))


if __name__ == "__main__":
    main()
