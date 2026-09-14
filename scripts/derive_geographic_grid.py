#!/usr/bin/env python3
"""Derive the guarded S1 geographic normalized-grid bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from ico_model.geographic_grid import GeographicGridError, derive_s1_grid, write_grid_bundle
from scripts.acquire_vector_sources import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--cell-size-m", type=float, default=100.0)
    parser.add_argument("--dem-dir", type=Path, required=True)
    parser.add_argument("--svtm-raster", type=Path, required=True)
    parser.add_argument("--protected-land-manifest", type=Path, required=True)
    parser.add_argument("--hydrography-line-manifest", type=Path, required=True)
    parser.add_argument("--hydrography-area-manifest", type=Path, required=True)
    parser.add_argument("--roads-manifest", type=Path, required=True)
    parser.add_argument("--railways-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    manifests = {
        "protected_land": args.protected_land_manifest,
        "hydrography_line": args.hydrography_line_manifest,
        "hydrography_area": args.hydrography_area_manifest,
        "roads": args.roads_manifest,
        "railways": args.railways_manifest,
    }
    print(f"S1 geographic grid output: {args.output.resolve()}")
    print(f"S1 geographic grid cell size: {args.cell_size_m:g} m")
    bundle = derive_s1_grid(
        config,
        cell_size_m=args.cell_size_m,
        dem_dir=args.dem_dir,
        svtm_raster=args.svtm_raster,
        vector_manifests=manifests,
    )
    output = write_grid_bundle(bundle, args.output)
    print(f"Wrote geographic grid bundle: {output.resolve()}")
    print(f"Grid shape: {bundle['grid_shape']}")
    print(f"Unavailable cells: {bundle['diagnostics']['unavailable_cell_count']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, GeographicGridError) as exc:
        raise SystemExit(f"Geographic grid derivation failed: {exc}") from exc
