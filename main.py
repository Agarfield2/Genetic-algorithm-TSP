import time

from DaWay import Graph
from TSP_GA import TSP_GA

<<<<<<< Updated upstream
GENERATIONS = 100
REPORT_EVERY = 10
=======
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

DISTANCE_MATRIX_LIMIT = 250
NEIGHBOR_COUNT = 16
NEIGHBOR_CELL_RADIUS = 2
NEIGHBOR_SAMPLE_SIZE = 128
>>>>>>> Stashed changes


def main():
    graph = Graph(
        matrix_limit=DISTANCE_MATRIX_LIMIT,
        neighbor_count=NEIGHBOR_COUNT,
        neighbor_cell_radius=NEIGHBOR_CELL_RADIUS,
        neighbor_sample_size=NEIGHBOR_SAMPLE_SIZE,
        csv_path=CSV_PATH,
    )
    graph.charger_graph()
    print(f"Loaded {len(graph.list_lieux)} points from {CSV_PATH}")
    graph.calcul_matrice_cout_od()

<<<<<<< Updated upstream
    tsp_ga = TSP_GA()
=======
    tsp_ga = TSP_GA(
        population_size=POPULATION_SIZE,
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
>>>>>>> Stashed changes
    tsp_ga.init_population(graph=graph)
    best_route, best_distance = tsp_ga.best_solution()
    print(f"New best at generation 0: distance = {best_distance:.2f}")

<<<<<<< Updated upstream
    for generation in range(GENERATIONS):
        tsp_ga.reproduction(graph)
        if (generation + 1) % REPORT_EVERY == 0 or generation + 1 == GENERATIONS:
            _, best_distance = tsp_ga.best_solution()
            print(f"Generation {generation + 1}: best distance = {best_distance:.2f}")

    best_route, best_distance = tsp_ga.best_solution()
    print(
        f"Best solution: distance = {best_distance:.2f}, "
        f"visits = {len(best_route) - 1}"
    )

=======
    start_time = time.perf_counter()
    for generation in range(GENERATIONS):
        tsp_ga.reproduction(graph)
        current_best_route, current_best_distance = tsp_ga.best_solution()
        if current_best_distance < best_distance:
            best_route = current_best_route
            best_distance = current_best_distance
            print(
                f"New best at generation {generation + 1}: "
                f"distance = {best_distance:.2f}"
                f"liste = {best_route}"
            )

    print(
        f"Finished {GENERATIONS} generations in "
        f"{time.perf_counter() - start_time:.2f}s."
    )
    if len(best_route) <= 102:
        print(f"Best route: {best_route}")
    else:
        print(f"Best route contains {len(best_route) - 1} edges; not printed.")
>>>>>>> Stashed changes


if __name__ == "__main__":
    main()