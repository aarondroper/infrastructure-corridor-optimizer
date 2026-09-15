import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

from ico_model.config import load_config as load_model_config
from ico_model.sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    build_endpoint_manifest,
    validate_endpoint_features,
    summarize_arcgis_metadata,
    validate_service_crs,
    validate_expected_layers,
    validate_expected_layer_names,
    validate_required_layer_type,
    validate_feature_geometries,
    validate_feature_object_ids,
    validate_feature_payload_crs,
    write_manifest,
)


def load_config():
    return load_model_config(Path(__file__).parents[1] / "config" / "model.json")


def endpoint_features(config):
    return [
        {
            "attributes": {
                "OBJECTID": config["endpoints"]["origin"]["source_object_id"],
                "feature_name": "Bayswater",
                "state": "NSW",
                "latitude": -32.39525728,
                "longitude": 150.94913566,
            },
            "geometry": {"x": 150.94913566, "y": -32.39525728},
        },
        {
            "attributes": {
                "OBJECTID": config["endpoints"]["destination"]["source_object_id"],
                "feature_name": "Eraring",
                "state": "NSW",
                "latitude": -33.06206226,
                "longitude": 151.52065341,
            },
            "geometry": {"x": 151.52065341, "y": -33.06206226},
        },
    ]


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, size=-1):
        return self.payload if size < 0 else self.payload[:size]


class SourceTests(unittest.TestCase):
    def test_client_fetches_json_and_sends_query(self):
        observed = {}

        def opener(request, timeout):
            observed["url"] = request.full_url
            observed["timeout"] = timeout
            return FakeResponse({"ok": True})

        payload = ArcGISClient(opener, timeout_seconds=4).fetch_json(
            "https://example.test/service", {"where": "1=1", "returnGeometry": True}
        )
        self.assertEqual(payload, {"ok": True})
        self.assertIn("where=1%3D1", observed["url"])
        self.assertIn("returnGeometry=true", observed["url"])
        self.assertEqual(observed["timeout"], 4)

    def test_client_converts_http_failures_to_source_error(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 503, "unavailable", {}, io.BytesIO())

        with self.assertRaises(SourceAccessError):
            ArcGISClient(opener).fetch_json("https://example.test/service")

    def test_client_rejects_oversized_response(self):
        def opener(request, timeout):
            return FakeResponse({"payload": "too large"})

        with self.assertRaisesRegex(SourceAccessError, "exceeds configured limit"):
            ArcGISClient(opener, max_response_bytes=4).fetch_json("https://example.test/service")

    def test_client_retries_transient_failures_with_exponential_backoff(self):
        attempts = []
        delays = []

        def opener(request, timeout):
            attempts.append(request.full_url)
            if len(attempts) < 3:
                raise URLError("temporary failure")
            return FakeResponse({"ok": True})

        payload = ArcGISClient(
            opener,
            max_retries=2,
            retry_backoff_seconds=0.25,
            sleeper=delays.append,
        ).fetch_json("https://example.test/service")
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(len(attempts), 3)
        self.assertEqual(delays, [0.25, 0.5])

    def test_feature_object_ids_must_match_the_requested_page(self):
        features = [{"attributes": {"OBJECTID": 7}, "geometry": {"x": 1, "y": 2}}]
        validate_feature_object_ids(features, [7], "https://example.test/0")
        with self.assertRaisesRegex(SourceValidationError, "object IDs"):
            validate_feature_object_ids(features, [8], "https://example.test/0")

    def test_feature_query_carries_bounded_geometry_and_crs(self):
        observed = {}

        def opener(request, timeout):
            observed.update(parse_qs(urlparse(request.full_url).query))
            return FakeResponse({"spatialReference": {"wkid": 7856}, "features": []})

        payload = ArcGISClient(opener).query_feature_payload(
            "https://example.test/0",
            where="1=1",
            geometry={"xmin": 150.8, "ymin": -33.2, "xmax": 151.6, "ymax": -32.2},
            in_crs_epsg=7844,
            out_crs_epsg=7856,
        )
        self.assertEqual(payload["features"], [])
        self.assertEqual(observed["geometryType"], ["esriGeometryEnvelope"])
        self.assertEqual(observed["inSR"], ["7844"])
        self.assertEqual(observed["outSR"], ["7856"])
        self.assertIn("xmin", observed["geometry"][0])

    def test_transfer_limit_is_never_returned_as_complete_features(self):
        def opener(request, timeout):
            return FakeResponse({"exceededTransferLimit": True, "features": []})

        with self.assertRaisesRegex(SourceAccessError, "transfer limit"):
            ArcGISClient(opener).query_features("https://example.test/0", where="1=1")

    def test_object_id_query_returns_integer_ids(self):
        def opener(request, timeout):
            return FakeResponse({"objectIds": [7, "8"]})

        self.assertEqual(
            ArcGISClient(opener).query_object_ids("https://example.test/0", where="1=1"),
            [7, 8],
        )

    def test_object_id_query_accepts_arcgis_empty_tile_null(self):
        def opener(request, timeout):
            return FakeResponse({"objectIdFieldName": "OBJECTID", "objectIds": None})

        self.assertEqual(
            ArcGISClient(opener).query_object_ids("https://example.test/0", where="1=1"),
            [],
        )

    def test_endpoint_validation_accepts_configured_records(self):
        config = load_config()
        validated = validate_endpoint_features(config["endpoints"], endpoint_features(config))
        self.assertEqual([endpoint.name for endpoint in validated], ["Bayswater", "Eraring"])
        self.assertEqual(validated[1].geometry["x"], 151.52065341)

    def test_endpoint_validation_rejects_identity_mismatch(self):
        config = load_config()
        features = endpoint_features(config)
        features[0]["attributes"]["feature_name"] = "Other Station"
        with self.assertRaises(SourceValidationError):
            validate_endpoint_features(config["endpoints"], features)

    def test_endpoint_validation_rejects_missing_record(self):
        config = load_config()
        with self.assertRaises(SourceValidationError):
            validate_endpoint_features(config["endpoints"], endpoint_features(config)[:1])

    def test_service_crs_must_match_configuration(self):
        validate_service_crs({"spatialReference": {"latestWkid": 7844}}, 7844)
        with self.assertRaises(SourceValidationError):
            validate_service_crs({"spatialReference": {"latestWkid": 4283}}, 7844)

    def test_manifest_round_trip_preserves_provenance_and_endpoints(self):
        config = load_config()
        endpoints = validate_endpoint_features(config["endpoints"], endpoint_features(config))
        manifest = build_endpoint_manifest(
            config,
            {
                "currentVersion": 11.1,
                "spatialReference": {"latestWkid": 7844},
            },
            {"source_id": "ga-electricity-infrastructure", "where": "objectid IN (251,286)"},
            endpoints,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            write_manifest(manifest, path)
            written = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(written["source"]["crs_epsg"], 7844)
        self.assertEqual([item["name"] for item in written["endpoints"]], ["Bayswater", "Eraring"])

    def test_arcgis_metadata_summary_and_layer_guards(self):
        summary = summarize_arcgis_metadata(
            {
                "currentVersion": 10.9,
                "spatialReference": {"latestWkid": 7844},
                "fullExtent": {"xmin": 1, "ymin": 2, "xmax": 3, "ymax": 4},
                "layers": [
                    {"id": 5, "name": "RoadSegment", "type": "Feature Layer", "geometryType": "esriGeometryPolyline"}
                ],
            }
        )
        self.assertEqual(summary["crs_epsg"], 7844)
        self.assertEqual(summary["full_extent"]["xmax"], 3)
        validate_expected_layers(summary, [{"id": 5, "name": "RoadSegment", "geometry_type": "esriGeometryPolyline"}])
        validate_expected_layer_names(summary, ["RoadSegment"])
        with self.assertRaises(SourceValidationError):
            validate_required_layer_type(summary, "Raster Layer")

    def test_feature_response_crs_and_geometry_guards(self):
        payload = {"spatialReference": {"latestWkid": 7856}}
        validate_feature_payload_crs(payload, 7856, "https://example.test/0")
        validate_feature_geometries(
            [{"geometry": {"paths": [[[1, 2], [3, 4]]]}}],
            "esriGeometryPolyline",
            "https://example.test/0",
        )
        with self.assertRaises(SourceValidationError):
            validate_feature_payload_crs(payload, 7844, "https://example.test/0")
        with self.assertRaises(SourceValidationError):
            validate_feature_geometries(
                [{"geometry": {"rings": []}}],
                "esriGeometryPolyline",
                "https://example.test/0",
            )


if __name__ == "__main__":
    unittest.main()
