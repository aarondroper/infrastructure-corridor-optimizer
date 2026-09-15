"""Validate local DEM sidecars and select the configured terrain source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ico_model.config import load_config
from ico_model.terrain import (
    TerrainArtifactError,
    load_terrain_artifact_metadata,
    select_terrain_artifact,
    write_terrain_selection,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--primary-metadata", type=Path, required=True)
    parser.add_argument("--fallback-metadata", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/terrain_selection.json"))
    args = parser.parse_args()
    config = load_config(args.config)
    candidates = {
        config["terrain_source_policy"]["primary_source_id"]: load_terrain_artifact_metadata(
            args.primary_metadata
        )
    }
    fallback_id = config["terrain_source_policy"].get("fallback_source_id")
    if args.fallback_metadata and fallback_id:
        candidates[fallback_id] = load_terrain_artifact_metadata(args.fallback_metadata)
    selection = select_terrain_artifact(config, candidates)
    write_terrain_selection(selection, args.output)
    print(f"Selected terrain source {selection['selected_source_id']}: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, TerrainArtifactError) as exc:
        raise SystemExit(f"Terrain source selection failed: {exc}") from exc
