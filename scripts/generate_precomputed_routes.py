"""Generate static route assets from a validated normalized-grid bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from ico_model.config import load_config
from ico_model.precomputed_routes import (
    RouteAssetError,
    generate_precomputed_routes,
    load_grid_bundle,
    write_precomputed_routes,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid-bundle", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    bundle = generate_precomputed_routes(config, load_grid_bundle(args.grid_bundle))
    manifest_path = write_precomputed_routes(bundle, args.output_dir)
    print(f"Wrote precomputed route manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, RouteAssetError) as exc:
        raise SystemExit(f"Precomputed route generation failed: {exc}") from exc
