from DaWay import Graph
from TSP_GA import TSP_GA

def main():
    graph = Graph()
    graph.charger_graph()
    graph.calcul_matrice_cout_od()

    tsp_ga = TSP_GA()
    tsp_ga.init_population(graph=graph)

    for generation in range(100): 
        tsp_ga.reproduction(graph)
        best_route = min(tsp_ga.population, key=lambda route: graph.calcul_distance_route(route))
        best_distance = graph.calcul_distance_route(best_route)
        print(f"Generation {generation}: Best distance = {best_distance}")



if __name__ == "__main__":
    main()