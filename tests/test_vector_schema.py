import unittest

from ico_model.sources import SourceValidationError
from ico_model.vector_schema import (
    COMPONENT_FIELD_ALIASES,
    normalize_feature,
    normalize_feature_collection,
)


class VectorSchemaTests(unittest.TestCase):
    def test_all_configured_vector_components_have_explicit_aliases(self):
        self.assertEqual(
            set(COMPONENT_FIELD_ALIASES),
            {
                "protected_land",
                "hydrography_line",
                "named_watercourse_ss",
                "named_watercourse_ls",
                "hydrography_area",
                "roads",
                "railways",
            },
        )

    def test_normalize_feature_standardizes_case_and_preserves_source_values(self):
        feature = {
            "attributes": {
                "OBJECTID": "42",
                "RoadNameBase": "Example Road",
                "FunctionHierarchy": "Primary",
                "LaneCount": 2,
            },
            "geometry": {"paths": [[[1, 2], [3, 4]]]},
        }
        normalized = normalize_feature(feature, "roads")
        self.assertEqual(normalized["id"], 42)
        self.assertEqual(normalized["properties"]["source_object_id"], 42)
        self.assertEqual(normalized["properties"]["name"], "Example Road")
        self.assertEqual(normalized["properties"]["hierarchy"], "Primary")
        self.assertEqual(normalized["source_attributes"], feature["attributes"])
        self.assertEqual(normalized["geometry"], feature["geometry"])

    def test_normalize_feature_rejects_missing_object_id(self):
        with self.assertRaises(SourceValidationError):
            normalize_feature({"attributes": {"name": "No ID"}, "geometry": {}}, "roads")

    def test_normalize_collection_carries_provenance(self):
        artifact = {
            "format": "arcgis-json-feature-collection",
            "source_id": "nsw-transport",
            "layer_id": 5,
            "layer_name": "RoadSegment",
            "geometry_type": "esriGeometryPolyline",
            "source_crs_epsg": 7844,
            "output_crs_epsg": 7856,
            "processing_envelope": {"west": 1},
            "query": {"object_id_count": 1},
            "features": [{"attributes": {"OBJECTID": 1}, "geometry": {"paths": []}}],
        }
        normalized = normalize_feature_collection(artifact, "roads")
        self.assertEqual(normalized["output_crs_epsg"], 7856)
        self.assertEqual(normalized["features"][0]["properties"]["source_object_id"], 1)


if __name__ == "__main__":
    unittest.main()
