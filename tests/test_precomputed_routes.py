import json
import tempfile
import unittest
from pathlib import Path

from ico_model.precomputed_routes import (
    RouteAssetError,
    generate_precomputed_routes,
    write_precomputed_routes,
)


def load_config():
    return json.loads(
        (Path(__file__).parents[1] / "config" / "model.json").read_text(encoding="utf-8")
    )


def grid_bundle(config):
    components = [component["id"] for component in config["components"]]
    grids = {}
    for component in components:
        grids[component] = [[0.0 for _ in range(7)] for _ in range(7)]
    for row in range(1, 6):
        grids["length"][row][3] = 5.0
    return {
        "schema_version": 1,
        "format": "ico-normalized-cost-grids",
        "scenario": config["scenario"],
        "analysis_crs_epsg": config["analysis_crs_epsg"],
        "cell_size_m": 100,
        "origin_cell": [0, 0],
        "destination_cell": [6, 6],
        "component_grids": grids,
        "provenance": {"fixture": True},
    }


class PrecomputedRouteTests(unittest.TestCase):
    def test_all_approved_presets_produce_provenance_rich_routes(self):
        config = load_config()
        bundle = generate_precomputed_routes(config, grid_bundle(config))
        self.assertEqual(bundle["format"], "ico-precomputed-route-assets")
        self.assertEqual({route["preset"] for route in bundle["routes"]}, set(config["sensitivity_presets"]))
        for route in bundle["routes"]:
            self.assertEqual(route["algorithm"], "astar")
            self.assertEqual(route["path_cells"][0], [0, 0])
            self.assertEqual(route["path_cells"][-1], [6, 6])
            self.assertEqual(route["grid_provenance"], {"fixture": True})

    def test_generation_rejects_missing_component(self):
        config = load_config()
        bundle = grid_bundle(config)
        del bundle["component_grids"]["railways"]
        with self.assertRaisesRegex(RouteAssetError, "components"):
            generate_precomputed_routes(config, bundle)

    def test_generation_rejects_mismatched_context_and_invalid_grid(self):
        config = load_config()
        bundle = grid_bundle(config)
        bundle["scenario"] = "not-s1"
        with self.assertRaisesRegex(RouteAssetError, "scenario mismatch"):
            generate_precomputed_routes(config, bundle)

        bundle = grid_bundle(config)
        bundle["component_grids"]["terrain"][0].append(0.0)
        with self.assertRaisesRegex(RouteAssetError, "preset"):
            generate_precomputed_routes(config, bundle)

    def test_generation_rejects_invalid_endpoint(self):
        config = load_config()
        bundle = grid_bundle(config)
        bundle["destination_cell"] = [7, 7]
        with self.assertRaisesRegex(RouteAssetError, "outside"):
            generate_precomputed_routes(config, bundle)

    def test_generation_respects_unavailable_cells(self):
        config = load_config()
        bundle = grid_bundle(config)
        bundle["unavailable_cells"] = [[0, 2], [2, 0]]
        generated = generate_precomputed_routes(config, bundle)
        for route in generated["routes"]:
            self.assertNotIn([0, 2], route["path_cells"])
            self.assertNotIn([2, 0], route["path_cells"])

    def test_writer_publishes_manifest_and_preset_files(self):
        config = load_config()
        bundle = generate_precomputed_routes(config, grid_bundle(config))
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = write_precomputed_routes(bundle, Path(directory) / "routes")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["routes"]), 3)
            self.assertTrue(
                all(
                    (manifest_path.parent / record["artifact_path"]).is_file()
                    for record in manifest["routes"]
                )
            )


if __name__ == "__main__":
    unittest.main()
