import json
import tempfile
import unittest
from pathlib import Path


class WebAssetTests(unittest.TestCase):
    def test_builder_keeps_routes_compact_and_removes_source_paths(self):
        from scripts.build_web_assets import build_web_assets

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assessments = {
                "scenario": "S1",
                "assessments": [{
                    "preset": "shortest",
                    "geometry": {"type": "LineString", "coordinates": [[151, -32], [151.1, -32.1]]},
                    "route_length_km": 1.0,
                    "path_cell_count": 2,
                    "slope_mean_degrees": 2.0,
                    "slope_max_degrees": 4.0,
                    "diagnostics": {"route_is_available": True},
                    "impact_inventory": {"roads": {"source": {"artifact_path": "/private/raw.json"}, "features": []}},
                }],
            }
            config = {"endpoints": {"origin": {"name": "A", "longitude": 151, "latitude": -32}, "destination": {"name": "B", "longitude": 151.1, "latitude": -32.1}}}
            (root / "assessments.json").write_text(json.dumps(assessments), encoding="utf-8")
            (root / "shortest.json").write_text(json.dumps({"preset_description": "short"}), encoding="utf-8")
            (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
            payload = build_web_assets(root / "assessments.json", root, root / "config.json")
        self.assertEqual(payload["routes"][0]["description"], "short")
        self.assertNotIn("source", payload["routes"][0]["impact_inventory"]["roads"])
        self.assertEqual(len(payload["endpoints"]["features"]), 2)


if __name__ == "__main__":
    unittest.main()
