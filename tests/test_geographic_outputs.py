import importlib.util
import unittest


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


if __name__ == "__main__":
    unittest.main()
