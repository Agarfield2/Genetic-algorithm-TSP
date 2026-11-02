from DaWay import Graph
from TSP_GA import TSP_GA,POP_SIZE

GENERATIONS = 100


def main():
    graph = Graph()
    graph.charger_graph()
    graph.calcul_matrice_cout_od()

    tsp_ga = TSP_GA()
    tsp_ga.init_population(graph=graph)
<<<<<<< HEAD

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
=======
    oldest_distance, oldest_route = float('inf'), None
    list_best_route = []
    for generation in range(100): 
        tsp_ga.reproduction(graph)
        best_route = min(tsp_ga.population, key=lambda route: graph.calcul_distance_route(route))
        best_distance = graph.calcul_distance_route(best_route)
        
        if best_distance < oldest_distance:
            oldest_distance = best_distance
            oldest_route = best_route
            best_generation = generation
            list_best_route.append(best_route)
            print(f"Best route in generation {generation}: {best_route} with distance {best_distance}")
>>>>>>> cd31832e55199f2e3281f8333da42a983475ddc0


if __name__ == "__main__":
    main()
