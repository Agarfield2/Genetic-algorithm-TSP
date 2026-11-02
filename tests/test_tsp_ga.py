import csv
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from TSP_GA import TSP_GA
from DaWay import Graph, Lieu


ROOT = Path(__file__).resolve().parents[1]


class RouteCost:
    def __init__(self, number_of_places=5):
        self.calls = 0
        self.list_lieux = [None] * number_of_places

    def calcul_distance_route(self, route):
        self.calls += 1
        return route[1]


class TSPGATests(unittest.TestCase):
    def test_population_starts_and_ends_at_place_zero(self):
        graph = RouteCost()
        algorithm = TSP_GA()

        population = algorithm.init_population(population_size=8, graph=graph)

        self.assertEqual(len(population), 8)
        for route in population:
            self.assertEqual(len(route), 6)
            self.assertEqual((route[0], route[-1]), (0, 0))
            self.assertEqual(sorted(route[1:-1]), list(range(1, 5)))

    def test_crossover_and_mutation_keep_routes_as_permutations(self):
        algorithm = TSP_GA()
        parent1 = [0, 1, 2, 3, 4, 0]
        parent2 = [0, 4, 3, 2, 1, 0]

        child = algorithm.crossover(parent1, parent2)
        mutated_child = algorithm.mutation(child, mutation_rate=1.0)

        for route in (child, mutated_child):
            self.assertEqual((route[0], route[-1]), (0, 0))
            self.assertEqual(sorted(route[1:-1]), list(range(1, 5)))

    def test_reproduction_preserves_the_best_route(self):
        algorithm = TSP_GA()
        algorithm.population = [
            [0, 1, 2, 0],
            [0, 2, 1, 0],
            [0, 3, 1, 0],
            [0, 3, 2, 0],
            [0, 2, 3, 0],
        ]

        with patch.object(algorithm, "crossover", return_value=[0, 3, 2, 0]), patch.object(
            algorithm, "mutation", return_value=[0, 3, 2, 0]
        ):
            algorithm.reproduction(RouteCost())

        self.assertIn([0, 1, 2, 0], algorithm.population)
        self.assertEqual(len(algorithm.population), 5)

    def test_route_distance_includes_return_to_start_and_rejects_invalid_routes(self):
        graph = Graph()
        graph.list_lieux = []
        for x in (0, 1, 3):
            place = Lieu()
            place.x = x
            place.y = 0
            graph.list_lieux.append(place)

        self.assertEqual(graph.calcul_distance_route([0, 1, 2, 0]), 6)
        with self.assertRaises(ValueError):
            graph.calcul_distance_route([0, 1, 2])
        with self.assertRaises(ValueError):
            graph.validate_route([0, 1, 1, 0])

    def test_distance_matrix_is_only_built_under_configured_limit(self):
        graph = Graph(matrix_limit=3)
        graph.list_lieux = [Lieu(index, index * 2) for index in range(3)]

        matrix = graph.calcul_matrice_cout_od()

        self.assertEqual(matrix.shape, (3, 3))
        self.assertAlmostEqual(graph.calcul_distance_route([0, 1, 2, 0]), 4 * 5**0.5)

        graph.list_lieux.append(Lieu(3, 6))
        graph.matrice_od = matrix
        self.assertIsNone(graph.calcul_matrice_cout_od())
        self.assertIsNone(graph.matrice_od)

    def test_population_route_scores_are_cached_until_children_are_created(self):
        graph = RouteCost()
        algorithm = TSP_GA()
        algorithm.init_population(population_size=8, graph=graph)
        self.assertEqual(graph.calls, 8)

        algorithm.selection(graph)
        algorithm.selection(graph)
        self.assertEqual(graph.calls, 8)

        algorithm.reproduction(graph)
        self.assertEqual(graph.calls, 15)

    def test_csv_samples_have_expected_headers_and_rows(self):
        for filename, expected_rows in (("graph_5.csv", 5), ("graph_20.csv", 20)):
            with self.subTest(filename=filename):
                with (ROOT / "csv" / filename).open(newline="", encoding="utf-8") as data:
                    reader = csv.DictReader(data)
                    rows = list(reader)

                self.assertEqual(reader.fieldnames, ["x", "y"])
                self.assertEqual(len(rows), expected_rows)
                for row in rows:
                    self.assertIsInstance(float(row["x"]), float)
                    self.assertIsInstance(float(row["y"]), float)

                graph = Graph(csv_path=ROOT / "csv" / filename, matrix_limit=10)
                graph.charger_graph()
                self.assertEqual(len(graph.list_lieux), expected_rows)
                self.assertEqual(graph.matrice_od, None)

    def test_importing_main_does_not_run_algorithm(self):
        result = subprocess.run(
            [sys.executable, "-c", "import main"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
