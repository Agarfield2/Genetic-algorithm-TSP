import csv
import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from DaWay import Graph, Lieu
from TSP_GA import TSP_GA
import main
from nearest_insertion import nearest_insertion


ROOT = Path(__file__).resolve().parents[1]


class RouteCost:
    def __init__(self, number_of_places=5):
        self.calls = 0
        self.list_lieux = [None] * number_of_places

    def calcul_distance_route(self, route):
        self.calls += 1
        return route[1]


class TSPGATests(unittest.TestCase):
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

        population = algorithm.init_population(graph=graph)

        self.assertEqual(len(population), 8)
        for route in population:
            self.assertEqual(len(route), 6)
            self.assertEqual((route[0], route[-1]), (0, 0))
            self.assertEqual(sorted(route[1:-1]), list(range(1, 5)))

    def test_population_contains_unique_cycles_when_routes_are_exhausted(self):
        graph = Graph(neighbor_count=0)
        graph.list_lieux = [Lieu(index, index % 2) for index in range(4)]
        algorithm = self.make_algorithm(population_size=20)

        algorithm.init_population(graph)
        expected_unique_cycles = {
            (0, 1, 2, 3, 0),
            (0, 1, 3, 2, 0),
            (0, 2, 1, 3, 0),
        }
        route_keys = {algorithm._route_key(route) for route in algorithm.population}

        self.assertEqual(algorithm.population_size, 3)
        self.assertEqual(len(algorithm.population), 3)
        self.assertEqual(route_keys, expected_unique_cycles)

        for _ in range(3):
            algorithm.reproduction(graph)
            route_keys = {
                algorithm._route_key(route) for route in algorithm.population
            }
            self.assertEqual(len(route_keys), len(algorithm.population))

    def test_crossover_and_mutation_keep_routes_as_permutations(self):
        algorithm = self.make_algorithm()
        parent1 = [0, 1, 2, 3, 4, 0]
        parent2 = [0, 4, 3, 2, 1, 0]

        child = algorithm.crossover(parent1, parent2)
        mutated_child = algorithm.mutation(child, mutation_rate=1.0)

        for route in (child, mutated_child):
            self.assertEqual((route[0], route[-1]), (0, 0))
            self.assertEqual(sorted(route[1:-1]), list(range(1, 5)))

    def test_reproduction_preserves_the_best_route(self):
        algorithm = self.make_algorithm()
        algorithm.population = [
            [0, 1, 2, 0],
            [0, 2, 1, 0],
            [0, 3, 1, 0],
            [0, 3, 2, 0],
            [0, 2, 3, 0],
        ]

        with patch.object(
            algorithm, "crossover", return_value=[0, 3, 2, 0]
        ), patch.object(algorithm, "mutation", return_value=[0, 3, 2, 0]):
            algorithm.reproduction(RouteCost())

        self.assertIn([0, 1, 2, 0], algorithm.population)
        self.assertEqual(len(algorithm.population), 5)

    def test_best_solution_keeps_each_strict_global_improvement(self):
        algorithm = self.make_algorithm()
        algorithm.population = [
            [0, 1, 2, 0],
            [0, 2, 1, 0],
        ]
        algorithm._fitness = [10, 12]
        algorithm._update_global_best()

        saved_route, saved_distance = algorithm.best_solution()
        saved_route[1] = 99
        self.assertEqual((algorithm.best_solution()[0], saved_distance), ([0, 1, 2, 0], 10))

        algorithm.population = [[0, 2, 1, 0]]
        algorithm._fitness = [8]
        algorithm._update_global_best()

        self.assertEqual(algorithm.best_solution(), ([0, 2, 1, 0], 8))

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
        algorithm = self.make_algorithm(population_size=5, immigrant_fraction=0.5)
        algorithm.init_population(graph=graph)
        algorithm.generations_without_improvement = 10

        with patch.object(
            algorithm,
            "_random_route",
            wraps=algorithm._random_route,
        ) as make_route:
            algorithm.reproduction(graph)

        self.assertGreaterEqual(make_route.call_count, 2)
        route_keys = {
            algorithm._route_key(route) for route in algorithm.population
        }
        self.assertEqual(len(route_keys), len(algorithm.population))

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

        with patch("genetic_operators.random.randrange", return_value=0):
            improved = algorithm.two_opt(route, graph, attempts=1)

        self.assertEqual(improved, [0, 1, 2, 3, 0])
        self.assertLess(
            graph.calcul_distance_route(improved),
            graph.calcul_distance_route([0, 2, 1, 3, 0]),
        )

    def test_route_distance_and_validation(self):
        graph = Graph()
        graph.list_lieux = [Lieu(0, 0), Lieu(1, 0), Lieu(3, 0)]

        self.assertEqual(graph.calcul_distance_route([0, 1, 2, 0]), 6)
        self.assertTrue(graph.validate_route([0, 1, 2, 0]))
        for route in ([0, 1, 2], [0, -1, 2, 0], [0, 1.5, 2, 0]):
            with self.subTest(route=route), self.assertRaises(ValueError):
                graph.calcul_distance_route(route)
        with self.assertRaises(ValueError):
            graph.validate_route([0, 1, 1, 0])

    def test_nearest_insertion_returns_a_valid_closed_tour(self):
        graph = Graph(matrix_limit=10, neighbor_count=0)
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
        ]
        graph.calcul_matrice_cout_od()

        route = nearest_insertion(graph)

        self.assertTrue(graph.validate_route(route))
        self.assertEqual(graph.calcul_distance_route(route), 4)

    def test_distance_matrix_and_neighbor_candidates_respect_limits(self):
        graph = Graph(
            matrix_limit=3,
            neighbor_count=2,
            neighbor_cell_radius=1,
            neighbor_sample_size=4,
        )
        graph.list_lieux = [Lieu(index, index % 2) for index in range(4)]

        self.assertIsNone(graph.calcul_matrice_cout_od())
        self.assertIsNone(graph.matrice_od)
        self.assertEqual(len(graph.neighbor_candidates), 4)
        self.assertTrue(
            all(
                len(candidates) <= 2
                for candidates in graph.neighbor_candidates
            )
        )

        small_graph = Graph(matrix_limit=4, neighbor_count=2)
        small_graph.list_lieux = graph.list_lieux
        self.assertEqual(small_graph.calcul_matrice_cout_od().shape, (4, 4))

    def test_space_filling_route_is_a_valid_closed_tour(self):
        graph = Graph(neighbor_count=0)
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
        ]

        route = graph.space_filling_route()

        self.assertTrue(graph.validate_route(route))

    def test_population_starts_with_a_spatially_seeded_route(self):
        graph = Graph(neighbor_count=0)
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
        ]
        algorithm = self.make_algorithm(population_size=10)
        expected_route = graph.space_filling_route()

        with patch.object(
            algorithm,
            "two_opt",
            side_effect=lambda route, _graph, _attempts: route,
        ):
            population = algorithm.init_population(graph)

        self.assertEqual(population[0], expected_route)
        self.assertTrue(graph.validate_route(population[0]))

    def test_large_graph_solver_budget_is_bounded(self):
        self.assertEqual(main.get_solver_budget(100), (1000, 1000))

        population_size, generations = main.get_solver_budget(10_000)

        self.assertGreater(population_size, 1)
        self.assertGreater(generations, 1)
        self.assertLessEqual(
            10_000 * population_size * generations,
            main.MAX_ROUTE_EVALUATIONS,
        )

    def test_generation_budget_is_split_without_losing_generations(self):
        counts = main._split_generations(10, 4)

        self.assertEqual(counts, [3, 3, 2, 2])
        self.assertEqual(sum(counts), 10)

    def test_csv_samples_have_expected_headers_and_rows(self):
        for filename, expected_rows in (
            ("graph_5.csv", 5),
            ("graph_20.csv", 20),
            ("graph_100.csv", 100),
        ):
            with self.subTest(filename=filename):
                path = ROOT / "csv" / filename
                with path.open(newline="", encoding="utf-8") as data:
                    reader = csv.DictReader(data)
                    rows = list(reader)

                self.assertEqual(reader.fieldnames, ["x", "y"])
                self.assertEqual(len(rows), expected_rows)
                for row in rows:
                    self.assertIsInstance(float(row["x"]), float)
                    self.assertIsInstance(float(row["y"]), float)

                graph = Graph(csv_path=path, matrix_limit=10)
                graph.charger_graph()
                self.assertEqual(len(graph.list_lieux), expected_rows)

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

    def test_main_reports_only_new_best_solutions(self):
        class FakeGraph:
            def __init__(self):
                self.list_lieux = [None] * 100

            def charger_graph(self):
                pass

            def calcul_matrice_cout_od(self):
                pass

        class FakeAlgorithm:
            def __init__(self, **parameters):
                self.scores = iter([10, 10, 8, 8, 7])
                self.best_route = None
                self.best_distance = float("inf")

            def init_population(self, graph):
                self._update_best(next(self.scores))

            def reproduction(self, graph):
                self._update_best(next(self.scores))

            def _update_best(self, score):
                if score < self.best_distance:
                    self.best_route = [0, score, 0]
                    self.best_distance = score

            def best_solution(self):
                return self.best_route, self.best_distance

        output = io.StringIO()
        with patch.object(main, "GENERATIONS", 4), patch.object(
            main, "POPULATION_SIZE", 20
        ), patch.object(main, "Graph", return_value=FakeGraph()), patch.object(
            main, "TSP_GA", FakeAlgorithm
        ), patch.object(
            main, "PARALLEL_WORKERS", 1
        ), redirect_stdout(output):
            main.main()

        improvements = [
            line
            for line in output.getvalue().splitlines()
            if line.startswith("New best")
        ]
        self.assertEqual(len(improvements), 3)
        self.assertIn("generation 0", improvements[0])
        self.assertIn("generation 2", improvements[1])
        self.assertIn("generation 4", improvements[2])


if __name__ == "__main__":
    unittest.main()
