import math
import unittest

from ico_model.routing import NoPathError, route_least_cost


class RoutingTests(unittest.TestCase):
    def test_astar_and_dijkstra_find_same_cost_on_open_grid(self):
        grid = [[1.0] * 5 for _ in range(5)]
        astar = route_least_cost(grid, (0, 0), (4, 4), "astar")
        dijkstra = route_least_cost(grid, (0, 0), (4, 4), "dijkstra")
        self.assertAlmostEqual(astar.cost, dijkstra.cost)
        self.assertEqual(astar.path[0], (0, 0))
        self.assertEqual(astar.path[-1], (4, 4))
        self.assertLessEqual(astar.explored_cells, dijkstra.explored_cells)

    def test_high_penalty_changes_route(self):
        grid = [[1.0] * 5 for _ in range(5)]
        for row in range(1, 4):
            grid[row][2] = 100.0
        result = route_least_cost(grid, (2, 0), (2, 4))
        self.assertTrue(all(grid[row][col] < 100.0 for row, col in result.path))

    def test_infinite_cells_are_unavailable(self):
        grid = [[1.0, math.inf, 1.0]]
        with self.assertRaises(NoPathError):
            route_least_cost(grid, (0, 0), (0, 2))

    def test_diagonal_does_not_cut_between_blocked_corners(self):
        grid = [[1.0, math.inf, 1.0], [math.inf, 1.0, 1.0], [1.0, 1.0, 1.0]]
        with self.assertRaises(NoPathError):
            route_least_cost(grid, (0, 0), (1, 1))

    def test_invalid_algorithm_is_rejected(self):
        with self.assertRaises(ValueError):
            route_least_cost([[1.0]], (0, 0), (0, 0), "bellman-ford")


if __name__ == "__main__":
    unittest.main()
