import json
import tempfile
import unittest
from pathlib import Path

from scripts.acquire_vector_sources import acquire, stream_acquisition, write_acquisition
from ico_model.sources import SourceValidationError, write_manifest
from ico_model.vector_artifacts import validate_vector_manifest


def load_config():
    return json.loads(
        (Path(__file__).parents[1] / "config" / "model.json").read_text(encoding="utf-8")
    )


class FakeVectorClient:
    def __init__(self):
        self.queries = []
        self.id_queries = []

    def service_metadata(self, url):
        if url.endswith("/0"):
            return {
                "id": 0,
                "name": "NPWS Estate",
                "type": "Feature Layer",
                "geometryType": "esriGeometryPolygon",
                "spatialReference": {"wkid": 4283},
            }
        if "Hydrography" in url:
            layer_id_text = url.rstrip("/").rsplit("/", 1)[-1]
            if layer_id_text.isdigit():
                layer_id = int(layer_id_text)
                layer_details = {
                    3: ("Hydroline", "esriGeometryPolyline"),
                    4: ("Named Watercourse", "esriGeometryPolyline"),
                    5: ("Named Watercourse SS", "esriGeometryPolyline"),
                    6: ("Named Watercourse LS", "esriGeometryPolyline"),
                    10: ("HydroArea", "esriGeometryPolygon"),
                }
                name, geometry_type = layer_details[layer_id]
                return {
                    "id": layer_id,
                    "name": name,
                    "type": "Feature Layer",
                    "geometryType": geometry_type,
                    "spatialReference": {"wkid": 3857},
                }
            return {
                "spatialReference": {"wkid": 3857},
                "layers": [
                    {"id": 3, "name": "Hydroline", "parentLayerId": 0},
                    {"id": 4, "name": "Named Watercourse", "parentLayerId": 0},
                    {"id": 5, "name": "Named Watercourse SS", "parentLayerId": 4},
                    {"id": 6, "name": "Named Watercourse LS", "parentLayerId": 4},
                    {"id": 10, "name": "HydroArea", "parentLayerId": 0},
                ],
            }
        return {
            "spatialReference": {"wkid": 7844},
            "layers": [
                {"id": 5, "name": "RoadSegment", "type": "Feature Layer", "geometryType": "esriGeometryPolyline"},
                {"id": 7, "name": "Railway", "type": "Feature Layer", "geometryType": "esriGeometryPolyline"},
            ],
        }

    def query_feature_payload(self, url, **query):
        self.queries.append((url, query))
        is_polygon = url.endswith("/0") or url.endswith("/10")
        geometry = {"rings": [[[1, 2], [3, 4], [5, 6], [1, 2]]]} if is_polygon else {
            "paths": [[[1, 2], [3, 4]]]
        }
        return {"spatialReference": {"wkid": 7856}, "features": [{"attributes": {}, "geometry": geometry}]}

    def query_object_ids(self, url, **query):
        self.id_queries.append((url, query))
        return [1]


class VectorAcquisitionTests(unittest.TestCase):
    def test_acquisition_is_bounded_reprojected_and_written_with_manifest(self):
        config = load_config()
        client = FakeVectorClient()
        bundle = acquire(config, client)
        self.assertEqual(len(bundle["sources"]), 3)
        self.assertEqual(len(client.id_queries), 7)
        self.assertEqual(len(client.queries), 7)
        for _, query in client.id_queries:
            self.assertEqual(query["in_crs_epsg"], 7844)
            self.assertEqual(query["geometry"], {"xmin": 150.82, "ymin": -33.15, "xmax": 151.62, "ymax": -32.27})
        for _, query in client.queries:
            self.assertEqual(query["in_crs_epsg"], 7844)
            self.assertEqual(query["out_crs_epsg"], 7856)
            self.assertEqual(
                query["geometry"],
                {"xmin": 150.82, "ymin": -33.15, "xmax": 151.62, "ymax": -32.27},
            )
            self.assertNotEqual(query["out_fields"], ["*"])

        with tempfile.TemporaryDirectory() as directory:
            manifest_path = write_acquisition(bundle, Path(directory))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            layer_records = [
                layer
                for source in manifest["sources"]
                for layer in source["layers"]
            ]
            self.assertEqual(len(layer_records), 7)
            self.assertTrue(all(record["feature_count"] == 1 for record in layer_records))
            self.assertTrue(all(Path(record["artifact_path"]).is_file() for record in layer_records))

    def test_source_filter_limits_acquisition_without_changing_query_contract(self):
        config = load_config()
        client = FakeVectorClient()
        bundle = acquire(config, client, {"nsw-npws-estate"})
        self.assertEqual([source["source_id"] for source in bundle["sources"]], ["nsw-npws-estate"])
        self.assertEqual(len(client.queries), 1)

    def test_component_filter_limits_layers_and_omits_empty_sources(self):
        config = load_config()
        client = FakeVectorClient()
        bundle = acquire(config, client, components={"railways"})
        self.assertEqual([source["source_id"] for source in bundle["sources"]], ["nsw-transport"])
        self.assertEqual([layer["component"] for layer in bundle["sources"][0]["layers"]], ["railways"])

    def test_layer_page_size_override_is_carried_to_feature_queries(self):
        config = load_config()
        client = FakeVectorClient()
        bundle = acquire(config, client, components={"roads"})
        layer = bundle["sources"][0]["layers"][0]
        self.assertEqual(layer["query"]["page_size"], 150)

    def test_streaming_writer_publishes_only_after_layer_validation(self):
        config = load_config()
        client = FakeVectorClient()
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "acquired"
            manifest_path = stream_acquisition(
                config, client, output_dir, {"nsw-npws-estate"}
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            artifact = output_dir / "nsw-npws-estate--protected_land.json"
            self.assertTrue(artifact.is_file())
            self.assertFalse(any(path.name.startswith(".staging-") for path in output_dir.iterdir()))
            self.assertEqual(manifest["sources"][0]["layers"][0]["feature_count"], 1)

    def test_streaming_writer_cleans_staging_after_validation_failure(self):
        config = load_config()
        client = FakeVectorClient()

        def bad_payload(url, **query):
            return {"spatialReference": {"wkid": 7856}, "features": [{"geometry": None}]}

        client.query_feature_payload = bad_payload
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "acquired"
            with self.assertRaises(SourceValidationError):
                stream_acquisition(config, client, output_dir, {"nsw-npws-estate"})
            self.assertEqual(list(output_dir.iterdir()), [])

    def test_artifact_validator_reports_complete_written_bundle(self):
        config = load_config()
        bundle = acquire(config, FakeVectorClient())
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = write_acquisition(bundle, Path(directory))
            report = validate_vector_manifest(
                manifest_path,
                expected_scenario=config["scenario"],
                expected_output_crs_epsg=config["analysis_crs_epsg"],
            )
            self.assertEqual(report["source_count"], 3)
            self.assertEqual(report["layer_count"], 7)
            self.assertEqual(report["feature_count"], 7)

    def test_artifact_validator_rejects_manifest_count_mismatch(self):
        config = load_config()
        bundle = acquire(config, FakeVectorClient())
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = write_acquisition(bundle, Path(directory))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["sources"][0]["layers"][0]["feature_count"] += 1
            write_manifest(manifest, manifest_path)
            with self.assertRaisesRegex(SourceValidationError, "feature count"):
                validate_vector_manifest(manifest_path)


if __name__ == "__main__":
    unittest.main()
