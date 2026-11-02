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
    def calcul_distance_route(self, route):
        return route[1]


class TSPGATests(unittest.TestCase):
    def test_population_starts_and_ends_at_place_zero(self):
        graph = type("GraphStub", (), {"list_lieux": [None] * 5})()
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
            graph.calcul_distance_route([0, 1, 1, 0])

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
