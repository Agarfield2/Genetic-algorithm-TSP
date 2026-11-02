import csv
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from TSP_GA import TSP_GA


ROOT = Path(__file__).resolve().parents[1]


class RouteCost:
    def calcul_distance_route(self, route):
        return route[0]


class TSPGATests(unittest.TestCase):
    def test_population_contains_permutations_of_graph_places(self):
        graph = type("GraphStub", (), {"list_lieux": [None] * 5})()
        algorithm = TSP_GA()

        population = algorithm.init_population(population_size=8, graph=graph)

        self.assertEqual(len(population), 8)
        for route in population:
            self.assertEqual(sorted(route), list(range(5)))

    def test_crossover_and_mutation_keep_routes_as_permutations(self):
        algorithm = TSP_GA()
        parent1 = [0, 1, 2, 3, 4]
        parent2 = [4, 3, 2, 1, 0]

        child = algorithm.crossover(parent1, parent2)
        mutated_child = algorithm.mutation(child, mutation_rate=1.0)

        self.assertEqual(sorted(child), list(range(5)))
        self.assertEqual(sorted(mutated_child), list(range(5)))

    def test_reproduction_preserves_the_best_route(self):
        algorithm = TSP_GA()
        algorithm.population = [
            [0, 1, 2],
            [1, 0, 2],
            [2, 0, 1],
            [1, 2, 0],
            [2, 1, 0],
        ]

        with patch.object(algorithm, "crossover", return_value=[2, 1, 0]), patch.object(
            algorithm, "mutation", return_value=[2, 1, 0]
        ):
            algorithm.reproduction(RouteCost())

        self.assertIn([0, 1, 2], algorithm.population)
        self.assertEqual(len(algorithm.population), 5)

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
