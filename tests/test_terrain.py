import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ico_model.terrain import (
    TerrainArtifactError,
    load_terrain_artifact_metadata,
    select_terrain_artifact,
    validate_terrain_artifact,
)


def load_config():
    return json.loads(
        (Path(__file__).parents[1] / "config" / "model.json").read_text(encoding="utf-8")
    )


def metadata(config, source_id, artifact_path, **overrides):
    policy = config["terrain_source_policy"]
    result = {
        "source_id": source_id,
        "artifact_type": policy["required_artifact_type"],
        "artifact_path": str(artifact_path),
        "crs_epsg": policy["target_analysis_crs_epsg"],
        "bounds_crs_epsg": policy["processing_envelope_crs_epsg"],
        "resolution_m": 5,
        "bounds": {"west": 150.7, "south": -33.2, "east": 151.7, "north": -32.2},
        "nodata_defined": True,
        "coverage_status": "complete",
        "acquired_at_utc": "2026-09-13T00:00:00+00:00",
    }
    result.update(overrides)
    return result


class TerrainTests(unittest.TestCase):
    def test_primary_artifact_is_selected_and_provenance_is_retained(self):
        config = load_config()
        primary_id = config["terrain_source_policy"]["primary_source_id"]
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "primary.tif"
            artifact.write_bytes(b"fixture placeholder")
            selected = select_terrain_artifact(
                config, {primary_id: metadata(config, primary_id, artifact)}
            )
        self.assertEqual(selected["selected_source_id"], primary_id)
        self.assertFalse(selected["fallback_used"])
        self.assertEqual(selected["selected_source"]["id"], primary_id)
        self.assertIn("elevation.fsdf.org.au", selected["selected_source"]["url"])
        self.assertEqual(selected["artifact"]["resolution_m"], 5)

    def test_invalid_primary_uses_only_valid_configured_fallback(self):
        config = load_config()
        policy = config["terrain_source_policy"]
        with tempfile.TemporaryDirectory() as directory:
            primary = Path(directory) / "primary.tif"
            fallback = Path(directory) / "fallback.tif"
            primary.write_bytes(b"fixture placeholder")
            fallback.write_bytes(b"fixture placeholder")
            selected = select_terrain_artifact(
                config,
                {
                    policy["primary_source_id"]: metadata(
                        config, policy["primary_source_id"], primary, coverage_status="partial"
                    ),
                    policy["fallback_source_id"]: metadata(
                        config, policy["fallback_source_id"], fallback, resolution_m=30
                    ),
                },
            )
        self.assertEqual(selected["selected_source_id"], policy["fallback_source_id"])
        self.assertTrue(selected["fallback_used"])
        self.assertIn("primary artifact failed", selected["selection_reason"])
        self.assertEqual(selected["attempts"][0]["status"], "failed")

    def test_artifact_requires_envelope_nodata_and_local_file(self):
        config = load_config()
        source_id = config["terrain_source_policy"]["primary_source_id"]
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "terrain.tif"
            artifact.write_bytes(b"fixture placeholder")
            with self.assertRaisesRegex(TerrainArtifactError, "processing envelope"):
                validate_terrain_artifact(
                    metadata(config, source_id, artifact, bounds={"west": 151, "south": -33, "east": 151.1, "north": -32.9}),
                    config,
                    source_id,
                )
            with self.assertRaisesRegex(TerrainArtifactError, "nodata_defined"):
                validate_terrain_artifact(
                    metadata(config, source_id, artifact, nodata_defined=False), config, source_id
                )
            with self.assertRaisesRegex(TerrainArtifactError, "acquired_at_utc"):
                validate_terrain_artifact(
                    metadata(config, source_id, artifact, acquired_at_utc=""), config, source_id
                )
            with self.assertRaisesRegex(TerrainArtifactError, "ISO-8601"):
                validate_terrain_artifact(
                    metadata(config, source_id, artifact, acquired_at_utc="not-a-date"), config, source_id
                )
            with self.assertRaisesRegex(TerrainArtifactError, "unavailable"):
                validate_terrain_artifact(
                    metadata(config, source_id, Path(directory) / "missing.tif"), config, source_id
                )

    def test_sidecar_resolves_relative_artifact_path(self):
        config = load_config()
        source_id = config["terrain_source_policy"]["primary_source_id"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "terrain.tif").write_bytes(b"fixture placeholder")
            sidecar = root / "terrain.json"
            sidecar.write_text(
                json.dumps(metadata(config, source_id, "terrain.tif")), encoding="utf-8"
            )
            loaded = load_terrain_artifact_metadata(sidecar)
        self.assertEqual(loaded["artifact_path"], str(root / "terrain.tif"))

    def test_both_unusable_candidates_fail_explicitly(self):
        config = load_config()
        policy = config["terrain_source_policy"]
        with self.assertRaisesRegex(TerrainArtifactError, "no usable terrain artifact"):
            select_terrain_artifact(config, {})
        with self.assertRaisesRegex(TerrainArtifactError, policy["fallback_source_id"]):
            select_terrain_artifact(
                config,
                {
                    policy["primary_source_id"]: {"source_id": policy["primary_source_id"]},
                    policy["fallback_source_id"]: {"source_id": policy["fallback_source_id"]},
                },
            )

    def test_cli_writes_selection_report_from_sidecar(self):
        config = load_config()
        source_id = config["terrain_source_policy"]["primary_source_id"]
        project_root = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "terrain.tif").write_bytes(b"fixture placeholder")
            sidecar = root / "terrain.json"
            sidecar.write_text(
                json.dumps(metadata(config, source_id, "terrain.tif")), encoding="utf-8"
            )
            output = root / "selection.json"
            environment = {**os.environ, "PYTHONPATH": str(project_root / "src")}
            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "select_terrain_source.py"),
                    "--primary-metadata",
                    str(sidecar),
                    "--output",
                    str(output),
                ],
                cwd=project_root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["selected_source_id"], source_id)


if __name__ == "__main__":
    unittest.main()
