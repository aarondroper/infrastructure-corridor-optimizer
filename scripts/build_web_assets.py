#!/usr/bin/env python3
"""Build compact static application assets from validated route assessments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def build_web_assets(assessments_path: str | Path, routes_dir: str | Path, config_path: str | Path) -> dict[str, Any]:
    assessments_file = Path(assessments_path).resolve()
    routes_root = Path(routes_dir).resolve()
    config = _load(Path(config_path).resolve())
    assessments = _load(assessments_file)
    routes: list[dict[str, Any]] = []
    for assessment in assessments.get("assessments", []):
        preset = assessment["preset"]
        route = _load(routes_root / f"{preset}.json")
        inventory = assessment.get("impact_inventory", {})
        compact_inventory = {}
        for component, layer in inventory.items():
            compact = {key: value for key, value in layer.items() if key != "source"}
            compact_inventory[component] = compact
        routes.append(
            {
                "preset": preset,
                "description": route.get("preset_description", ""),
                "geometry": {"type": "Feature", "properties": {"preset": preset}, "geometry": assessment["geometry"]},
                "metrics": {
                    key: value
                    for key, value in assessment.items()
                    if key in {
                        "route_length_km", "path_cell_count", "slope_mean_degrees", "slope_max_degrees",
                        "terrain_normalized_mean", "terrain_normalized_max", "component_intersected_cell_counts",
                        "component_route_cell_sums", "weighted_cell_exposure", "endpoint_cells", "diagnostics",
                    }
                },
                "impact_inventory": compact_inventory,
            }
        )
    endpoint_features = []
    for role, endpoint in config["endpoints"].items():
        endpoint_features.append({
            "type": "Feature",
            "properties": {"role": role, "name": endpoint["name"]},
            "geometry": {"type": "Point", "coordinates": [endpoint["longitude"], endpoint["latitude"]]},
        })
    return {
        "schema_version": 1,
        "format": "ico-static-route-assets",
        "scenario": assessments["scenario"],
        "display_crs_epsg": 7844,
        "endpoints": {"type": "FeatureCollection", "features": endpoint_features},
        "routes": routes,
        "comparison": assessments.get("comparison", {}),
        "disclaimer": "Preliminary corridor screening only. Routes are 100 m grid centerlines and require engineering, environmental, land-access, and regulatory review.",
        "provenance": {
            "assessment_source": assessments_file.name,
            "generated_from_validated_precomputed_routes": True,
            "source_inventory_geometry_retained": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assessments", type=Path, required=True)
    parser.add_argument("--routes-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_web_assets(args.assessments, args.routes_dir, args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Wrote static application assets: {args.output.resolve()} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
