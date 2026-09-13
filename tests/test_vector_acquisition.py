import json
import tempfile
import unittest
from pathlib import Path

from scripts.acquire_vector_sources import acquire, write_acquisition


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
            return {
                "spatialReference": {"wkid": 3857},
                "layers": [
                    {"id": 3, "name": "Hydroline", "type": "Feature Layer", "geometryType": "esriGeometryPolyline"},
                    {"id": 4, "name": "Named Watercourse", "type": "Feature Layer", "geometryType": "esriGeometryPolyline"},
                    {"id": 5, "name": "Named Watercourse SS", "type": "Feature Layer", "geometryType": "esriGeometryPolyline"},
                    {"id": 6, "name": "Named Watercourse LS", "type": "Feature Layer", "geometryType": "esriGeometryPolyline"},
                    {"id": 10, "name": "HydroArea", "type": "Feature Layer", "geometryType": "esriGeometryPolygon"},
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


if __name__ == "__main__":
    unittest.main()
