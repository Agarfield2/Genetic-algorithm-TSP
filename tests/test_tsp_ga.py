import ctypes
import csv
import io
import itertools
import multiprocessing
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import numpy as np

from DaWay import Graph, Lieu, Route
from TSP_GA import TSP_GA
import main
from parallel_evolution import initialize_worker


ROOT = Path(__file__).resolve().parents[1]


def reference_hilbert_index(x, y, bits=16):
    index = 0
    scale = 1 << (bits - 1)
    while scale:
        x_bit = 1 if x & scale else 0
        y_bit = 1 if y & scale else 0
        index += scale * scale * ((3 * x_bit) ^ y_bit)
        if y_bit == 0:
            if x_bit:
                x = (1 << bits) - 1 - x
                y = (1 << bits) - 1 - y
            x, y = y, x
        scale >>= 1
    return index


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
            "fitness_batch_size": 4,
        }
        parameters.update(overrides)
        return TSP_GA(**parameters)

    def test_route_exposes_its_order_and_copies_independently(self):
        route = Route([0, 2, 1, 0])

        self.assertIs(route.order, route)
        self.assertIs(route.ordre, route)
        self.assertEqual(route.order, [0, 2, 1, 0])

        route.order = [0, 1, 2, 0]
        copied_route = route.copy()
        copied_route[1] = 2

        self.assertIsInstance(copied_route, Route)
        self.assertEqual(route, [0, 1, 2, 0])
        self.assertEqual(copied_route, [0, 2, 2, 0])

    def test_population_starts_and_ends_at_place_zero(self):
        graph = RouteCost()
        algorithm = self.make_algorithm(population_size=8)

        population = algorithm.init_population(graph=graph)

        self.assertEqual(len(population), 8)
        for route in population:
            self.assertIsInstance(route, Route)
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

    def test_route_key_matches_reference_for_all_small_tours(self):
        def reference_route_key(route):
            forward = tuple(route)
            reverse = (route[0], *reversed(route[1:-1]), route[-1])
            return min(forward, reverse)

        algorithm = self.make_algorithm()
        routes = []
        for number_of_places in range(2, 9):
            for internal_places in itertools.permutations(
                range(1, number_of_places)
            ):
                routes.append([0, *internal_places, 0])

        for route in routes:
            with self.subTest(route=route):
                self.assertEqual(
                    algorithm._route_key(route),
                    reference_route_key(route),
                )
                self.assertEqual(
                    algorithm._route_key(route),
                    algorithm._route_key([0, *reversed(route[1:-1]), 0]),
                )

        malformed_routes = (
            [0, 1, 1, 0],
            [0, 2, 1, 2, 0],
        )
        for route in malformed_routes:
            with self.subTest(route=route):
                self.assertEqual(
                    algorithm._route_key(route),
                    reference_route_key(route),
                )

    def test_crossover_and_mutation_keep_routes_as_permutations(self):
        algorithm = self.make_algorithm()
        parent1 = [0, 1, 2, 3, 4, 0]
        parent2 = [0, 4, 3, 2, 1, 0]

        child = algorithm.crossover(parent1, parent2)
        mutated_child = algorithm.mutation(child, mutation_rate=1.0)

        for route in (child, mutated_child):
            self.assertIsInstance(route, Route)
            self.assertEqual((route[0], route[-1]), (0, 0))
            self.assertEqual(sorted(route[1:-1]), list(range(1, 5)))

    def test_mutation_batches_uniform_partner_draws(self):
        algorithm = self.make_algorithm()
        route = [0, 1, 2, 3, 4, 0]

        with patch(
            "genetic_operators.random.sample",
            return_value=[1, 3],
        ) as sample, patch(
            "genetic_operators.random.choices",
            return_value=[3, 2],
        ) as choices:
            result = algorithm.mutation(route, mutation_rate=0.5)

        self.assertIs(result, route)
        self.assertEqual(route, [0, 3, 1, 2, 4, 0])
        sample.assert_called_once_with(range(1, 5), 2)
        choices.assert_called_once_with(range(1, 5), k=2)

    def test_crossover_matches_reference_for_every_segment(self):
        algorithm = self.make_algorithm()
        for internal_count in range(1, 13):
            parent_orders = (
                list(range(1, internal_count + 1)),
                list(reversed(range(1, internal_count + 1))),
            )
            parent2_orders = (
                list(reversed(range(1, internal_count + 1))),
                list(range(2, internal_count + 1))
                + ([1] if internal_count else []),
            )
            for parent1_order in parent_orders:
                parent1 = [0, *parent1_order, 0]
                for parent2_order in parent2_orders:
                    parent2 = [0, *parent2_order, 0]
                    for start in range(1, internal_count + 1):
                        for end in range(start, internal_count + 1):
                            with self.subTest(
                                internal_count=internal_count,
                                parent1=parent1_order,
                                parent2=parent2_order,
                                start=start,
                                end=end,
                            ):
                                reference = [None] * (internal_count + 2)
                                reference[0] = reference[-1] = 0
                                reference[start:end + 1] = (
                                    parent1[start:end + 1]
                                )
                                selected = set(
                                    parent1[start:end + 1]
                                )
                                remaining = iter(
                                    place
                                    for place in parent2[1:-1]
                                    if place not in selected
                                )
                                for position in range(
                                    1,
                                    internal_count + 1,
                                ):
                                    if reference[position] is None:
                                        reference[position] = next(remaining)

                                with patch(
                                    "genetic_operators.random.randint",
                                    side_effect=[start, end],
                                ):
                                    child = algorithm.crossover(parent1, parent2)

                                self.assertEqual(child, reference)

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
        self.assertTrue(all(isinstance(route, Route) for route in algorithm.population))

    def test_best_solution_keeps_each_strict_global_improvement(self):
        algorithm = self.make_algorithm()
        algorithm.population = [
            [0, 1, 2, 0],
            [0, 2, 1, 0],
        ]
        algorithm._fitness = [10, 12]
        algorithm._update_global_best()

        saved_route, saved_distance = algorithm.best_solution()
        self.assertIsInstance(saved_route, Route)
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

    def test_stagnation_does_not_inject_random_routes(self):
        graph = RouteCost()
        algorithm = self.make_algorithm(population_size=5)
        algorithm.init_population(graph=graph)
        algorithm.generations_without_improvement = 10

        with patch.object(
            algorithm,
            "_random_route",
            wraps=algorithm._random_route,
        ) as make_route:
            algorithm.reproduction(graph)

        make_route.assert_not_called()
        self.assertEqual(len(algorithm.population), 5)
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
        algorithm = self.make_algorithm()
        route = [0, 2, 1, 3, 0]

        with patch("genetic_operators.random.randrange", return_value=0):
            improved = algorithm.two_opt(route, graph, attempts=1)

        self.assertEqual(improved, [0, 1, 2, 3, 0])
        self.assertLess(
            graph.calcul_distance_route(improved),
            graph.calcul_distance_route([0, 2, 1, 3, 0]),
        )

    def test_two_opt_reuses_distances_for_unchanged_route_edges(self):
        graph = Graph()
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
            Lieu(2, 0),
            Lieu(2, 1),
        ]
        graph.neighbor_candidates = [[2, 3, 4], [], [], [], [], []]
        algorithm = self.make_algorithm()
        route = [0, 1, 2, 3, 4, 5, 0]

        with (
            patch("genetic_operators.random.randrange", return_value=0),
            patch.object(
                graph, "distance_between", wraps=graph.distance_between
            ) as distance_between,
        ):
            algorithm.two_opt(route, graph, attempts=1)

        self.assertEqual(distance_between.call_count, 10)

    def test_two_opt_disables_edge_cache_above_city_limit(self):
        graph = Graph()
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
        ]
        graph.neighbor_candidates = [[1], [0], [1], [2]]
        algorithm = self.make_algorithm()
        route = [0, 2, 1, 3, 0]

        with (
            patch("genetic_operators.MAX_TWO_OPT_CACHE_CITIES", 3),
            patch("genetic_operators.random.randrange", return_value=0),
            patch.object(
                graph, "distance_between", wraps=graph.distance_between
            ) as distance_between,
        ):
            improved = algorithm.two_opt(route, graph, attempts=1)

        self.assertEqual(improved, [0, 1, 2, 3, 0])
        self.assertEqual(distance_between.call_count, 4)

    def test_route_distance_and_validation(self):
        graph = Graph()
        graph.list_lieux = [Lieu(0, 0), Lieu(1, 0), Lieu(3, 0)]

        self.assertEqual(graph.distance_between(0, 1), 1)
        self.assertEqual(graph.calcul_distance_route([0, 1, 2, 0]), 6)
        self.assertTrue(graph.validate_route([0, 1, 2, 0]))
        for route in ([0, 1, 2], [0, -1, 2, 0], [0, 1.5, 2, 0]):
            with self.subTest(route=route), self.assertRaises(ValueError):
                graph.calcul_distance_route(route)
        with self.assertRaises(ValueError):
            graph.validate_route([0, 1, 1, 0])

    def test_distance_matrix_and_neighbor_candidates_respect_limits(self):
        graph = Graph(
            matrix_limit=3,
            neighbor_count=2,
            neighbor_cell_radius=1,
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

        self.assertIsInstance(route, Route)
        self.assertTrue(graph.validate_route(route))

    def test_space_filling_route_preserves_scalar_hilbert_order(self):
        graph = Graph(neighbor_count=0)
        graph.list_lieux = [
            Lieu(-2, 0),
            Lieu(0, 0),
            Lieu(2, 0),
            Lieu(-2, 3),
            Lieu(0, 3),
            Lieu(2, 3),
            Lieu(0, 0),
        ]
        graph._ensure_coordinates()
        coordinates = graph._coordinates
        minimums = coordinates.min(axis=0)
        spans = coordinates.max(axis=0) - minimums
        safe_spans = np.where(spans == 0, 1, spans)
        grid = np.rint(
            (coordinates - minimums) / safe_spans * ((1 << 16) - 1)
        ).astype(np.int64)
        expected_places = sorted(
            range(len(graph.list_lieux)),
            key=lambda place: (
                reference_hilbert_index(
                    int(grid[place, 0]),
                    int(grid[place, 1]),
                ),
                place,
            ),
        )
        start = expected_places.index(0)
        expected_places = expected_places[start:] + expected_places[:start]

        self.assertEqual(graph.space_filling_route(), [*expected_places, 0])

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
        self.assertEqual(main.PARALLEL_WORKERS, 4)
        self.assertEqual(
            main.get_solver_budget(100),
            (main.POPULATION_SIZE, main.GENERATIONS),
        )

        population_size, generations = main.get_solver_budget(10_000)

        self.assertGreaterEqual(population_size, 1)
        self.assertGreaterEqual(generations, 1)
        self.assertLessEqual(
            10_000 * population_size * generations,
            main.MAX_ROUTE_EVALUATIONS,
        )

    def test_generation_budget_is_split_without_losing_generations(self):
        counts = main._split_generations(10, 4)

        self.assertEqual(counts, [3, 3, 2, 2])
        self.assertEqual(sum(counts), 10)

    def test_infinite_mode_population_uses_memory_limit_not_generation_budget(self):
        with patch.object(main, "POPULATION_SIZE", 1000), patch.object(
            main, "MAX_POPULATION_ROUTE_CELLS", 1_000_000
        ):
            self.assertEqual(main._infinite_population_size(10_000), 100)

    def test_infinite_mode_detects_when_all_distinct_routes_are_enumerated(self):
        self.assertTrue(main._population_covers_route_space(3, 1))
        self.assertTrue(main._population_covers_route_space(4, 3))
        self.assertFalse(main._population_covers_route_space(4, 2))
        self.assertFalse(main._population_covers_route_space(5, 8))

    def test_infinite_mode_restarts_after_more_than_100_stagnant_generations(self):
        graph = Graph(neighbor_count=0)
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
            Lieu(2, 0),
        ]
        algorithm = self.make_algorithm(population_size=8)
        algorithm.init_population(graph)
        previous_best_route, _ = algorithm.best_solution()
        algorithm._best_route = [0, 1, 2, 4, 3, 0]
        algorithm._best_distance = -1.0
        algorithm.generations_without_improvement = 100
        algorithm.current_mutation_rate = algorithm.max_mutation_rate

        self.assertFalse(
            main._restart_stagnated_population(graph, algorithm, generation=100)
        )
        algorithm.generations_without_improvement = 101
        self.assertTrue(
            main._restart_stagnated_population(graph, algorithm, generation=101)
        )

        self.assertEqual(algorithm.best_solution(), ([0, 1, 2, 4, 3, 0], -1.0))
        self.assertEqual(algorithm.generations_without_improvement, 0)
        self.assertEqual(algorithm.current_mutation_rate, algorithm.mutation_rate)
        self.assertEqual(len(algorithm.population), 8)
        self.assertTrue(graph.validate_route(previous_best_route))

    def test_cooperative_generation_uses_parallel_shared_population(self):
        graph = Graph(neighbor_count=0)
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
            Lieu(2, 0),
        ]
        graph.calcul_matrice_cout_od()
        algorithm = self.make_algorithm(population_size=8)
        algorithm.init_population(graph)

        route_length = len(algorithm.population[0])
        population_buffer = multiprocessing.RawArray(
            ctypes.c_longlong,
            len(algorithm.population) * route_length,
        )
        fitness_buffer = multiprocessing.RawArray(
            ctypes.c_double,
            len(algorithm.population),
        )
        np.frombuffer(population_buffer, dtype=np.int64).reshape(
            (len(algorithm.population), route_length)
        )[:] = algorithm.population
        np.frombuffer(fitness_buffer, dtype=np.float64)[:] = algorithm._fitness
        with multiprocessing.Pool(
            processes=4,
            initializer=initialize_worker,
            initargs=(
                population_buffer,
                fitness_buffer,
                len(algorithm.population),
                route_length,
                graph,
                main._solver_parameters(
                    len(algorithm.population),
                    algorithm.elite_count,
                ),
            ),
        ) as pool:
            main._make_infinite_generation(
                graph,
                algorithm,
                pool,
                population_buffer,
                fitness_buffer,
                worker_count=4,
                generation=1,
            )

        self.assertEqual(len(algorithm.population), 8)
        route_keys = {
            algorithm._route_key(route) for route in algorithm.population
        }
        self.assertEqual(len(route_keys), len(algorithm.population))
        for route in algorithm.population:
            self.assertIsInstance(route, Route)
            self.assertTrue(graph.validate_route(route))

    def test_best_solution_is_saved_as_route_csv(self):
        graph = Graph()
        graph.list_lieux = [Lieu(0, 0), Lieu(3, 4)]

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "best_route.csv"
            main.save_best_solution(
                graph,
                ([0, 1, 0], 10.0),
                path,
            )
            with path.open(newline="", encoding="utf-8") as output_file:
                reader = csv.DictReader(output_file)
                rows = list(reader)

        self.assertEqual(
            reader.fieldnames,
            ["position", "place_index", "x", "y", "total_distance"],
        )
        self.assertEqual([row["place_index"] for row in rows], ["0", "1", "0"])
        self.assertTrue(all(row["total_distance"] == "10.0" for row in rows))

    def test_infinite_search_saves_best_solution_when_interrupted(self):
        class InterruptingPool:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exception_type, exception, traceback):
                return False

            def map(self, *args, **kwargs):
                raise KeyboardInterrupt

        graph = Graph(neighbor_count=0)
        graph.list_lieux = [
            Lieu(0, 0),
            Lieu(0, 1),
            Lieu(1, 1),
            Lieu(1, 0),
            Lieu(2, 0),
        ]
        graph.calcul_matrice_cout_od()

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "best_route.csv"
            with patch.object(main, "POPULATION_SIZE", 8), patch.object(
                main, "ELITE_COUNT", 1
            ), patch.object(
                main, "BEST_ROUTE_CSV", str(output_path)
            ), patch.object(
                main.multiprocessing, "Pool", InterruptingPool
            ), redirect_stdout(io.StringIO()):
                solution = main._run_infinite_search(graph, 5)

            self.assertTrue(output_path.exists())
            with output_path.open(newline="", encoding="utf-8") as output_file:
                rows = list(csv.DictReader(output_file))

        self.assertEqual(len(rows), len(solution[0]))
        self.assertEqual(rows[0]["total_distance"], str(solution[1]))

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
