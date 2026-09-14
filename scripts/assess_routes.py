#!/usr/bin/env python3
"""Georeference and independently assess generated S1 route assets."""

from __future__ import annotations

import argparse
from pathlib import Path

from ico_model.route_assessment import RouteAssessmentError, assess_route_directory, write_route_assessments


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid-bundle", type=Path, required=True)
    parser.add_argument("--routes-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = assess_route_directory(args.grid_bundle, args.routes_dir)
    output = write_route_assessments(result, args.output)
    print(f"Wrote route assessments: {output.resolve()}")
    for assessment in result["assessments"]:
        print(f"{assessment['preset']}: {assessment['route_length_km']:.2f} km, {assessment['path_cell_count']} cells")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, RouteAssessmentError) as exc:
        raise SystemExit(f"Route assessment failed: {exc}") from exc
