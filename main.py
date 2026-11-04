import multiprocessing
import random
import time

import numpy as np

from DaWay import Graph
from DaWay import Affichage
from TSP_GA import TSP_GA

GENERATIONS = 1000
CSV_PATH = "csv/graph_100.csv"
POPULATION_SIZE = 1000
ELITE_COUNT = 5
MUTATION_RATE = 0.01
MAX_MUTATION_RATE = 0.10
TOURNAMENT_SIZE = 5
STAGNATION_GENERATIONS = 25
IMMIGRANT_FRACTION = 0.10
MIN_DIVERSITY = 0.20
LOCAL_SEARCH_RATE = 0.05
LOCAL_SEARCH_ATTEMPTS = 8
FITNESS_BATCH_SIZE = 16
PARALLEL_WORKERS = 4

DISTANCE_MATRIX_LIMIT = 250
NEIGHBOR_COUNT = 16
NEIGHBOR_CELL_RADIUS = 2
NEIGHBOR_SAMPLE_SIZE = 128
MAX_ROUTE_EVALUATIONS = 20_000_000
MAX_POPULATION_ROUTE_CELLS = 1_000_000


def get_solver_budget(number_of_places):
    if number_of_places < 1:
        raise ValueError("The graph must contain at least one place.")
    if number_of_places <= DISTANCE_MATRIX_LIMIT:
        return POPULATION_SIZE, GENERATIONS

    max_population_generations = min(
        POPULATION_SIZE * GENERATIONS,
        MAX_ROUTE_EVALUATIONS // number_of_places,
    )
    balanced_population = int(
        np.sqrt(max_population_generations * POPULATION_SIZE // GENERATIONS)
    )
    population_size = max(
        1,
        min(
            POPULATION_SIZE,
            balanced_population,
            MAX_POPULATION_ROUTE_CELLS // number_of_places,
        ),
    )
    generations = max(
        1,
        min(
            GENERATIONS,
            max_population_generations // population_size,
        ),
    )
    return population_size, generations


def _create_graph():
    return Graph(
        matrix_limit=DISTANCE_MATRIX_LIMIT,
        neighbor_count=NEIGHBOR_COUNT,
        neighbor_cell_radius=NEIGHBOR_CELL_RADIUS,
        neighbor_sample_size=NEIGHBOR_SAMPLE_SIZE,
        csv_path=CSV_PATH,
    )


def _create_solver(population_size):
    return TSP_GA(
        population_size=population_size,
        elite_count=ELITE_COUNT,
        mutation_rate=MUTATION_RATE,
        max_mutation_rate=MAX_MUTATION_RATE,
        tournament_size=TOURNAMENT_SIZE,
        stagnation_generations=STAGNATION_GENERATIONS,
        immigrant_fraction=IMMIGRANT_FRACTION,
        min_diversity=MIN_DIVERSITY,
        local_search_rate=LOCAL_SEARCH_RATE,
        local_search_attempts=LOCAL_SEARCH_ATTEMPTS,
        fitness_batch_size=FITNESS_BATCH_SIZE,
    )


def _run_single_search(graph, generations, population_size):
    tsp_ga = _create_solver(population_size)
    tsp_ga.init_population(graph=graph)
    best_route, best_distance = tsp_ga.best_solution()
    best_route_list = []
    print(f"New best at generation 0: distance = {best_distance:.2f}")
    start_time = time.perf_counter()
    for generation in range(generations):
        tsp_ga.reproduction(graph)
        current_best_route, current_best_distance = tsp_ga.best_solution()
        if current_best_distance < best_distance:
            best_route = current_best_route
            best_distance = current_best_distance
            print(
                f"New best at generation {generation + 1}: "
                f"distance = {best_distance:.2f}"
            )
            if len(best_route) <= 102:
                best_route_list.append(best_route)
                print(f"Route: {best_route}")
            else:
                print(f"Route with {len(best_route) - 1} edges not printed.")


def _run_parallel_search(task):
    generations, seed, population_size = task
    random.seed(seed)
    graph = _create_graph()
    graph.charger_graph()
    graph.calcul_matrice_cout_od()
    solver = _create_solver(population_size)
    solver.init_population(graph=graph)
    for _ in range(generations):
        solver.reproduction(graph)
    return solver.best_solution()


def _split_generations(generations, worker_count):
    base_generations, remainder = divmod(generations, worker_count)
    return [
        base_generations + (worker < remainder)
        for worker in range(worker_count)
    ]


def main():
    if PARALLEL_WORKERS < 1:
        raise ValueError("PARALLEL_WORKERS must be at least one.")

    graph = _create_graph()
    graph.charger_graph()
    number_of_places = len(graph.list_lieux)
    print(f"Loaded {number_of_places} points from {CSV_PATH}")
    population_size, generations = get_solver_budget(number_of_places)
    print(
        f"Solver budget: population={population_size}, "
        f"generations={generations}"
    )

    worker_count = min(PARALLEL_WORKERS, generations)
    best_route_list = []
    if worker_count == 1:
        graph.calcul_matrice_cout_od()
        tsp_ga = _create_solver(population_size)
        tsp_ga.init_population(graph=graph)
        best_route, best_distance = tsp_ga.best_solution()
        print(f"New best at generation 0: distance = {best_distance:.2f}")
        start_time = time.perf_counter()
        for generation in range(generations):
            tsp_ga.reproduction(graph)
            current_best_route, current_best_distance = tsp_ga.best_solution()
            if current_best_distance < best_distance:
                best_route = current_best_route
                best_distance = current_best_distance
                print(
                    f"New best at generation {generation + 1}: "
                    f"distance = {best_distance:.2f}"
                )
                if len(best_route) <= 102:
                    best_route_list.append(best_route)
                    print(f"Route: {best_route}")
                else:
                    print(f"Route with {len(best_route) - 1} edges not printed.")

        print(
            f"Finished {generations} generations in "
            f"{time.perf_counter() - start_time:.2f}s."
        )
    else:
        generation_counts = _split_generations(generations, worker_count)
        tasks = [
            (count, random.randrange(1 << 32), population_size)
            for count in generation_counts
        ]
        print(
            f"Running {worker_count} independent searches "
            f"across {generations} total generations."
        )
        start_time = time.perf_counter()
        with multiprocessing.Pool(processes=worker_count) as pool:
            results = pool.map(_run_parallel_search, tasks)
        best_route, best_distance = min(results, key=lambda result: result[1])
        best_route_list = [
            list(route)
            for _, (route, _) in sorted(
                zip(generation_counts, results),
                key=lambda worker_result: worker_result[0],
                reverse=True,
            )
            if len(route) <= 102
        ]
        print(
            f"Finished {generations} generations across {worker_count} workers "
            f"in {time.perf_counter() - start_time:.2f}s."
        )
        for run_number, (_, distance) in enumerate(results, start=1):
            print(f"Search {run_number} best distance: {distance:.2f}")

    if len(best_route) <= 102:
        print(f"Best route: {best_route}")
        print(f"Best distance: {best_distance:.2f}")
        if worker_count == 1:
            print(f"List of 5 last best routes: {best_route_list[-5:]}")
    else:
        print(f"Best route contains {len(best_route) - 1} edges; not printed.")

    routes_for_display = (
        best_route_list if worker_count > 1 else best_route_list[-3:]
    )
    affichage = Affichage(
        graph, best_route, best_distance, routes_for_display
    )
    affichage.affiche()


if __name__ == "__main__":
    main()