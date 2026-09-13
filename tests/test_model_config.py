import json
import unittest
from pathlib import Path

from ico_model.cost import validate_weights


class ModelConfigTests(unittest.TestCase):
    def test_approved_configuration_has_unique_endpoint_records(self):
        config_path = Path(__file__).parents[1] / "config" / "model.json"
        config = json.loads(config_path.read_text())
        origin = config["endpoints"]["origin"]
        destination = config["endpoints"]["destination"]
        self.assertNotEqual(origin["source_global_id"], destination["source_global_id"])
        self.assertEqual(origin["state"], "NSW")
        self.assertEqual(destination["state"], "NSW")
        self.assertEqual(config["source_crs_epsg"], 7844)
        self.assertEqual(config["analysis_crs_epsg"], 7856)

    def test_sensitivity_presets_cover_all_components_and_sum_to_one(self):
        config_path = Path(__file__).parents[1] / "config" / "model.json"
        config = json.loads(config_path.read_text())
        component_ids = [component["id"] for component in config["components"]]
        for preset in config["sensitivity_presets"].values():
            validate_weights(preset["weights"], component_ids)
            self.assertAlmostEqual(sum(preset["weights"].values()), 1.0)

    def test_component_sources_are_declared(self):
        config_path = Path(__file__).parents[1] / "config" / "model.json"
        config = json.loads(config_path.read_text())
        source_ids = {source["id"] for source in config["sources"]}
        for component in config["components"]:
            if "source_id" in component:
                self.assertIn(component["source_id"], source_ids)


if __name__ == "__main__":
    unittest.main()
