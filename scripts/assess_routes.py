#!/usr/bin/env python3
"""Georeference and independently assess generated S1 route assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ico_model.route_assessment import RouteAssessmentError, assess_route_directory, write_route_assessments


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid-bundle", type=Path, required=True)
    parser.add_argument("--routes-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--protected-land", type=Path)
    parser.add_argument("--hydrography-line", type=Path)
    parser.add_argument("--hydrography-area", type=Path)
    parser.add_argument("--roads", type=Path)
    parser.add_argument("--railways", type=Path)
    parser.add_argument("--svtm-raster", type=Path)
    parser.add_argument("--svtm-archive", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else None
    vector_layers = {
        key: value for key, value in {
            "protected_land": args.protected_land,
            "hydrography_line": args.hydrography_line,
            "hydrography_area": args.hydrography_area,
            "roads": args.roads,
            "railways": args.railways,
        }.items() if value is not None
    }
    result = assess_route_directory(
        args.grid_bundle,
        args.routes_dir,
        config=config,
        vector_layers=vector_layers or None,
        svtm_raster=args.svtm_raster,
        svtm_archive=args.svtm_archive,
    )
    output = write_route_assessments(result, args.output)
    print(f"Wrote route assessments: {output.resolve()}")
    for assessment in result["assessments"]:
        print(
            f"{assessment['preset']}: {assessment['route_length_km']:.2f} km, "
            f"{assessment['path_cell_count']} cells, "
            f"available={assessment['diagnostics']['route_is_available']}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, RouteAssessmentError) as exc:
        raise SystemExit(f"Route assessment failed: {exc}") from exc
