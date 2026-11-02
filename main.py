from DaWay import Graph
from TSP_GA import TSP_GA

GENERATIONS = 100
REPORT_EVERY = 10


def main():
    graph = Graph()
    graph.charger_graph()
    graph.calcul_matrice_cout_od()

    tsp_ga = TSP_GA()
    tsp_ga.init_population(graph=graph)

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



if __name__ == "__main__":
    main()