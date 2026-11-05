import argparse
import csv
import ctypes
import multiprocessing
import random
import sys
import time

import numpy as np

from DaWay import Graph
from TSP_GA import TSP_GA
from parallel_evolution import generate_offspring, initialize_worker

GENERATIONS = 1000
CSV_PATH = "csv/graph_100.csv"
POPULATION_SIZE = 100
ELITE_COUNT = 5
MUTATION_RATE = 0.01
MAX_MUTATION_RATE = 0.10
TOURNAMENT_SIZE = 5
STAGNATION_GENERATIONS = 25
RESTART_AFTER_STAGNATION = 100
FITNESS_BATCH_SIZE = 16
PARALLEL_WORKERS = 4
BEST_ROUTE_CSV = "best_route.csv"

DISTANCE_MATRIX_LIMIT = 250
NEIGHBOR_COUNT = 16
NEIGHBOR_CELL_RADIUS = 2
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
        csv_path=CSV_PATH,
    )


def _solver_parameters(population_size, elite_count=None):
    if elite_count is None:
        elite_count = min(ELITE_COUNT, population_size)
    return {
        "population_size": population_size,
        "elite_count": elite_count,
        "mutation_rate": MUTATION_RATE,
        "max_mutation_rate": MAX_MUTATION_RATE,
        "tournament_size": TOURNAMENT_SIZE,
        "stagnation_generations": STAGNATION_GENERATIONS,
        "fitness_batch_size": FITNESS_BATCH_SIZE,
    }


def _create_solver(population_size):
    return TSP_GA(**_solver_parameters(population_size))


def save_best_solution(graph, solution, output_path=None):
    if output_path is None:
        output_path = BEST_ROUTE_CSV
    route, distance = solution
    with open(output_path, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(
            ["position", "place_index", "x", "y", "total_distance"]
        )
        for position, place_index in enumerate(route):
            place = graph.list_lieux[place_index]
            writer.writerow(
                [
                    position,
                    place_index,
                    place.x,
                    place.y,
                    distance,
                ]
            )


def _infinite_population_size(number_of_places):
    memory_limited_size = MAX_POPULATION_ROUTE_CELLS // number_of_places
    return max(1, min(POPULATION_SIZE, memory_limited_size))


def _population_covers_route_space(number_of_places, population_size):
    if number_of_places < 3:
        return True

    route_count_factorial = 1
    for place_count in range(2, number_of_places):
        route_count_factorial *= place_count
        if route_count_factorial > 2 * population_size:
            return False
    return route_count_factorial // 2 <= population_size


def _restart_stagnated_population(graph, solver, generation):
    if solver.generations_without_improvement <= RESTART_AFTER_STAGNATION:
        return False

    best_route, best_distance = solver.best_solution()
    solver.init_population(graph)
    if best_distance <= solver._best_distance:
        solver._best_route = best_route
        solver._best_distance = best_distance
    solver.current_mutation_rate = solver.mutation_rate
    print(
        f"No global improvement for more than "
        f"{RESTART_AFTER_STAGNATION} generations; "
        f"restarting population at generation {generation} "
        f"(best distance remains {solver._best_distance:.2f})."
    )
    return True


def _make_infinite_generation(
    graph,
    solver,
    pool,
    population_buffer,
    fitness_buffer,
    worker_count,
    generation,
):
    previous_best_distance = solver._best_distance
    mutation_rate = solver._adaptive_mutation_rate()

    ranked_indices = sorted(
        range(len(solver.population)),
        key=solver._fitness.__getitem__,
    )
    elite_count = min(solver.elite_count, len(solver.population))
    new_population = [
        list(solver.population[index])
        for index in ranked_indices[:elite_count]
    ]
    seen_routes = {solver._route_key(route) for route in new_population}

    child_count = len(solver.population) - elite_count
    if child_count:
        population_view = np.frombuffer(
            population_buffer,
            dtype=np.int64,
        ).reshape((len(solver.population), len(solver.population[0])))
        fitness_view = np.frombuffer(fitness_buffer, dtype=np.float64)
        population_view[:] = solver.population
        fitness_view[:] = solver._fitness
        offspring_counts = _split_generations(
            child_count,
            worker_count,
        )
        tasks = [
            (
                count,
                mutation_rate,
                elite_count,
                random.randrange(1 << 32),
            )
            for count in offspring_counts
        ]
        for worker_offspring in pool.map(
            generate_offspring,
            tasks,
            chunksize=1,
        ):
            for route in worker_offspring:
                solver._append_unique_route(
                    new_population,
                    seen_routes,
                    route,
                )

    solver._fill_unique_population(
        new_population,
        seen_routes,
        len(graph.list_lieux),
    )
    children = new_population[elite_count:]
    child_fitness = solver._calculate_fitness(graph, children)
    new_fitness = [
        solver._fitness[index]
        for index in ranked_indices[:elite_count]
    ]
    new_fitness.extend(child_fitness)
    solver.population = new_population
    solver._fitness = new_fitness
    solver._update_global_best()

    if solver._best_distance < previous_best_distance:
        solver.generations_without_improvement = 0
    else:
        solver.generations_without_improvement += 1
    solver.current_mutation_rate = solver._adaptive_mutation_rate()

    current_best_route, current_best_distance = solver.best_solution()
    if current_best_distance < previous_best_distance:
        print(
            f"New best at generation {generation}: "
            f"distance = {current_best_distance:.2f}"
        )
        if len(current_best_route) <= 102:
            print(f"Route: {current_best_route}")
        else:
            print(
                f"Route with {len(current_best_route) - 1} edges not printed."
            )
    elif generation % 100 == 0:
        print(
            f"Generation {generation}: "
            f"best distance = {current_best_distance:.2f}"
        )
    _restart_stagnated_population(graph, solver, generation)


def _run_infinite_search(graph, number_of_places):
    requested_population_size = _infinite_population_size(number_of_places)
    solver = _create_solver(requested_population_size)
    solver.init_population(graph=graph)
    population_size = len(solver.population)
    best_route, best_distance = solver.best_solution()
    print(
        f"Starting unbounded cooperative search: "
        f"population={population_size}, workers={PARALLEL_WORKERS}"
    )
    print(f"New best at generation 0: distance = {best_distance:.2f}")

    if _population_covers_route_space(number_of_places, population_size):
        print("The complete set of distinct routes has been evaluated.")
        save_best_solution(graph, solver.best_solution())
        print(f"Best solution saved to {BEST_ROUTE_CSV}")
        return solver.best_solution()

    solver.elite_count = min(ELITE_COUNT, max(0, population_size - 1))
    route_length = number_of_places + 1
    population_buffer = multiprocessing.RawArray(
        ctypes.c_longlong,
        population_size * route_length,
    )
    fitness_buffer = multiprocessing.RawArray(
        ctypes.c_double,
        population_size,
    )
    worker_count = min(PARALLEL_WORKERS, population_size)
    generation = 0

    try:
        with multiprocessing.Pool(
            processes=worker_count,
            initializer=initialize_worker,
            initargs=(
                population_buffer,
                fitness_buffer,
                population_size,
                route_length,
                graph,
                _solver_parameters(population_size, solver.elite_count),
            ),
        ) as pool:
            while True:
                generation += 1
                _make_infinite_generation(
                    graph,
                    solver,
                    pool,
                    population_buffer,
                    fitness_buffer,
                    worker_count,
                    generation,
                )
    except KeyboardInterrupt:
        print("\nStopping infinite search.")

    best_solution = solver.best_solution()
    save_best_solution(graph, best_solution)
    print(
        f"Best distance: {best_solution[1]:.2f}; "
        f"saved to {BEST_ROUTE_CSV}"
    )
    return best_solution


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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Solve a TSP instance.")
    parser.add_argument(
        "--infinite",
        action="store_true",
        help="Run an unbounded cooperative search until Ctrl+C.",
    )
    arguments = parser.parse_args(argv if argv is not None else [])

    if PARALLEL_WORKERS < 1:
        raise ValueError("PARALLEL_WORKERS must be at least one.")

    graph = _create_graph()
    graph.charger_graph()
    number_of_places = len(graph.list_lieux)
    if number_of_places < 1:
        raise ValueError("The graph must contain at least one place.")
    print(f"Loaded {number_of_places} points from {CSV_PATH}")

    if arguments.infinite:
        graph.calcul_matrice_cout_od()
        return _run_infinite_search(graph, number_of_places)

    population_size, generations = get_solver_budget(number_of_places)
    print(
        f"Solver budget: population={population_size}, "
        f"generations={generations}"
    )

    worker_count = min(PARALLEL_WORKERS, generations)
    if worker_count == 1:
        graph.calcul_matrice_cout_od()
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


if __name__ == "__main__":
    main(sys.argv[1:])