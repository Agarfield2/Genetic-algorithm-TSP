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
<<<<<<< Updated upstream
    def test_population_starts_and_ends_at_place_zero(self):
        graph = RouteCost()
        algorithm = TSP_GA()
=======
    def make_algorithm(self, population_size=5, **overrides):
        parameters = {
            "population_size": population_size,
            "elite_count": 1,
            "mutation_rate": 0.01,
            "max_mutation_rate": 0.1,
            "tournament_size": 5,
            "stagnation_generations": 10,
            "immigrant_fraction": 0.1,
            "min_diversity": 0.2,
            "local_search_rate": 0,
            "local_search_attempts": 0,
            "fitness_batch_size": 4,
        }
        parameters.update(overrides)
        return TSP_GA(**parameters)

    def test_population_starts_and_ends_at_place_zero(self):
        graph = RouteCost()
        algorithm = self.make_algorithm(population_size=8)
>>>>>>> Stashed changes

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

    def test_population_fitness_is_cached_and_children_are_scored_once(self):
        graph = RouteCost()
        algorithm = self.make_algorithm(population_size=8)
        algorithm.init_population(graph=graph)
        self.assertEqual(graph.calls, 8)

        algorithm.selection()
        algorithm.selection()
        self.assertEqual(graph.calls, 8)

        algorithm.reproduction(graph)
        self.assertEqual(graph.calls, 15)

    def test_stagnation_inserts_random_immigrants(self):
        graph = RouteCost()
        algorithm = self.make_algorithm(
            population_size=5,
            immigrant_fraction=0.5,
            local_search_rate=0,
        )
        algorithm.init_population(graph=graph)
        algorithm.generations_without_improvement = 10

        with patch.object(algorithm, "_random_route", wraps=algorithm._random_route) as make_route:
            algorithm.reproduction(graph)

        self.assertEqual(make_route.call_count, 2)

    def test_two_opt_uses_neighbor_candidates_to_improve_route(self):
        graph = Graph()
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
        ]
        graph.neighbor_candidates = [[1], [0], [1], [2]]
        algorithm = self.make_algorithm(local_search_attempts=1)
        route = [0, 2, 1, 3, 0]

        with patch("TSP_GA.random.randrange", return_value=0):
            improved = algorithm.two_opt(route, graph, attempts=1)

        self.assertEqual(improved, [0, 1, 2, 3, 0])
        self.assertLess(
            graph.calcul_distance_route(improved),
            graph.calcul_distance_route([0, 2, 1, 3, 0]),
        )

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
<<<<<<< Updated upstream
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
=======
            graph.calcul_distance_route([0, -1, 2, 0])
        with self.assertRaises(ValueError):
            graph.calcul_distance_route([0, 1.5, 2, 0])
        with self.assertRaises(ValueError):
            graph.validate_route([0, 1, 1, 0])

    def test_distance_matrix_obeys_limit_and_candidates_are_bounded(self):
        graph = Graph(
            matrix_limit=3,
            neighbor_count=2,
            neighbor_cell_radius=1,
            neighbor_sample_size=4,
        )
        graph.list_lieux = [Lieu(index, index % 2) for index in range(4)]

        matrix = graph.calcul_matrice_cout_od()

        self.assertIsNone(matrix)
        self.assertIsNone(graph.matrice_od)
        self.assertEqual(len(graph.neighbor_candidates), 4)
        for candidates in graph.neighbor_candidates:
            self.assertLessEqual(len(candidates), 2)

        small_graph = Graph(matrix_limit=4, neighbor_count=2)
        small_graph.list_lieux = graph.list_lieux
        matrix = small_graph.calcul_matrice_cout_od()
        self.assertEqual(matrix.shape, (4, 4))
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
=======
    def test_main_reports_only_new_best_solutions(self):
        class FakeGraph:
            def __init__(self):
                self.list_lieux = [None] * 100

            def charger_graph(self):
                pass

            def calcul_matrice_cout_od(self):
                pass

            def calcul_distance_route(self, route):
                return route[1]

        class FakeAlgorithm:
            def __init__(self, **parameters):
                self.scores = iter([10, 10, 8, 8, 7])
                self.population = []
                self.best_route = None
                self.best_distance = float("inf")

            def init_population(self, graph):
                self.population = [[0, next(self.scores), 0]]
                self._update_best()

            def reproduction(self, graph):
                self.population = [[0, next(self.scores), 0]]
                self._update_best()

            def _update_best(self):
                route = self.population[0]
                if route[1] < self.best_distance:
                    self.best_route = route
                    self.best_distance = route[1]

            def best_solution(self):
                return self.best_route, self.best_distance

        output = io.StringIO()
        with patch.object(main, "GENERATIONS", 4), patch.object(
            main, "Graph", return_value=FakeGraph()
        ), patch.object(main, "TSP_GA", FakeAlgorithm), redirect_stdout(output):
            main.main()

        improvements = [
            line for line in output.getvalue().splitlines() if line.startswith("New best")
        ]
        self.assertEqual(len(improvements), 3)
        self.assertIn("generation 0", improvements[0])
        self.assertIn("generation 2", improvements[1])
        self.assertIn("generation 4", improvements[2])

>>>>>>> Stashed changes

if __name__ == "__main__":
    unittest.main()
