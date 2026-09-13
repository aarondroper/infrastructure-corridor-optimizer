import math
import unittest

from ico_model.cost import combine_cost_layers, normalize_clamped


class CostModelTests(unittest.TestCase):
    def test_normalize_clamps_and_scales(self):
        self.assertEqual(normalize_clamped(5, 0, 10), 0.5)
        self.assertEqual(normalize_clamped(-1, 0, 10), 0.0)
        self.assertEqual(normalize_clamped(11, 0, 10), 1.0)

    def test_normalize_rejects_invalid_range_or_value(self):
        with self.assertRaises(ValueError):
            normalize_clamped(1, 1, 1)
        with self.assertRaises(ValueError):
            normalize_clamped(math.inf, 0, 1)

    def test_combines_layers_and_preserves_exclusion(self):
        result = combine_cost_layers(
            {"length": [[1, 1], [1, 1]], "terrain": [[0, 1], [1, 0]]},
            {"length": 0.75, "terrain": 0.25},
            [[False, True], [False, False]],
        )
        self.assertEqual(result[0][0], 0.75)
        self.assertTrue(math.isinf(result[0][1]))
        self.assertEqual(result[1][0], 1.0)

    def test_rejects_mismatched_shapes(self):
        with self.assertRaises(ValueError):
            combine_cost_layers(
                {"a": [[1]], "b": [[1, 2]]}, {"a": 0.5, "b": 0.5}
            )


if __name__ == "__main__":
    unittest.main()
