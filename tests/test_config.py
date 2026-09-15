import json
import tempfile
import unittest
from pathlib import Path

from ico_model.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_returns_the_project_model_object(self):
        config = load_config(Path(__file__).parents[1] / "config" / "model.json")
        self.assertEqual(config["scenario"], "S1")

    def test_load_config_rejects_non_object_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(["not", "a", "model"]), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "JSON object"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
