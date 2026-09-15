import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


GEOSPATIAL_AVAILABLE = importlib.util.find_spec("rasterio") is not None


@unittest.skipUnless(GEOSPATIAL_AVAILABLE, "optional geospatial dependencies are not installed")
class GeographicOutputTests(unittest.TestCase):
    def test_route_assessment_georeferences_and_measures_path(self):
        from ico_model.route_assessment import assess_route

        components = {
            name: [[0.0 for _ in range(3)] for _ in range(3)]
            for name in ("length", "terrain", "protected_land", "native_vegetation", "hydrography", "roads", "railways")
        }
        components["terrain"][1][1] = 0.5
        components["roads"][1][1] = 1.0
        bundle = {
            "scenario": "S1",
            "analysis_crs_epsg": 7856,
            "cell_size_m": 100.0,
            "grid_shape": {"rows": 3, "cols": 3},
            "provenance": {"transform": [100.0, 0.0, 0.0, 0.0, -100.0, 300.0, 0.0, 0.0, 1.0]},
            "component_grids": components,
        }
        route = {"preset": "balanced", "path_cells": [[0, 0], [1, 1], [2, 2]]}
        assessment = assess_route(bundle, route)
        self.assertAlmostEqual(assessment["route_length_m"], 200.0 * (2**0.5), places=6)
        self.assertEqual(assessment["component_intersected_cell_counts"]["roads"], 1)
        self.assertEqual(len(assessment["geometry"]["coordinates"]), 3)

    def test_route_diagnostics_flag_unavailable_cells_and_grid_quality(self):
        from ico_model.route_assessment import assess_route

        components = {
            name: [[0.0 for _ in range(3)] for _ in range(3)]
            for name in ("length", "terrain", "protected_land", "native_vegetation", "hydrography", "roads", "railways")
        }
        bundle = {
            "scenario": "S1",
            "analysis_crs_epsg": 7856,
            "cell_size_m": 100.0,
            "grid_shape": {"rows": 3, "cols": 3},
            "origin_cell": [0, 0],
            "destination_cell": [2, 2],
            "unavailable_cells": [[1, 1]],
            "provenance": {"transform": [100.0, 0.0, 0.0, 0.0, -100.0, 300.0, 0.0, 0.0, 1.0]},
            "component_grids": components,
        }
        route = {"preset": "balanced", "path_cells": [[0, 0], [1, 1], [2, 2]]}
        assessment = assess_route(bundle, route)
        self.assertFalse(assessment["diagnostics"]["route_is_available"])
        self.assertEqual(assessment["diagnostics"]["unavailable_cell_count"], 1)
        self.assertEqual(assessment["diagnostics"]["endpoints"]["origin_cell_match"], True)

    def test_feature_inventory_reports_unique_intersected_features(self):
        from shapely.geometry import LineString
        from ico_model.route_impacts import inventory_vector_intersections

        artifact = {
            "format": "arcgis-json-feature-collection",
            "output_crs_epsg": 7856,
            "geometry_type": "esriGeometryPolyline",
            "features": [
                {"attributes": {"OBJECTID": 7, "functionhierarchy": 2, "roadnamebase": "Main"}, "geometry": {"paths": [[[50, -10], [50, 10]]] }},
                {"attributes": {"OBJECTID": 8, "functionhierarchy": 8, "roadnamebase": "Local"}, "geometry": {"paths": [[[100, -10], [100, 10]]] }},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "roads.json"
            path.write_text(json.dumps(artifact), encoding="utf-8")
            result = inventory_vector_intersections(LineString([(0, 0), (100, 0)]), path, "roads")
        self.assertEqual(result["intersected_feature_count"], 2)
        self.assertEqual(result["major_road_intersection_count"], 1)
        self.assertEqual([item["source_object_id"] for item in result["features"]], [7, 8])


if __name__ == "__main__":
    unittest.main()
