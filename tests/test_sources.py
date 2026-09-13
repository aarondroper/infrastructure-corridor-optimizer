import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from ico_model.sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    build_endpoint_manifest,
    validate_endpoint_features,
    validate_service_crs,
    write_manifest,
)


def load_config():
    return json.loads(
        (Path(__file__).parents[1] / "config" / "model.json").read_text(encoding="utf-8")
    )


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

    def read(self):
        return self.payload


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


if __name__ == "__main__":
    unittest.main()
