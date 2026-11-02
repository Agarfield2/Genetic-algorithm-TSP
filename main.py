from DaWay import Graph
from TSP_GA import TSP_GA

GENERATIONS = 100


def main():
    graph = Graph()
    graph.charger_graph()
    graph.calcul_matrice_cout_od()

    tsp_ga = TSP_GA()
    tsp_ga.init_population(graph=graph)

    best_route = min(
        tsp_ga.population,
        key=lambda route: graph.calcul_distance_route(route),
    )
    best_distance = graph.calcul_distance_route(best_route)
    print(
        f"New best at generation 0: distance = {best_distance:.2f}, "
        f"route = {best_route}"
    )

    for generation in range(GENERATIONS):
        tsp_ga.reproduction(graph)
        current_best_route = min(
            tsp_ga.population,
            key=lambda route: graph.calcul_distance_route(route),
        )
        current_best_distance = graph.calcul_distance_route(current_best_route)

        if current_best_distance < best_distance:
            best_route = current_best_route
            best_distance = current_best_distance
            print(
                f"New best at generation {generation + 1}: "
                f"distance = {best_distance:.2f}, route = {best_route}"
            )


if __name__ == "__main__":
    main()
