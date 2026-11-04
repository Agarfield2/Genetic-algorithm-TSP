from DaWay import Affichage, Graph
from TSP_GA import TSP_GA,POP_SIZE

def main():
    graph = Graph()
    graph.charger_graph()
    graph.calcul_matrice_cout_od()

    tsp_ga = TSP_GA()
    tsp_ga.init_population(graph=graph)
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


    affichage= Affichage(graph, best_route,best_distance,list_best_route[-3:])#,best_generation,nb_pop
    affichage.affiche() 


if __name__ == "__main__":
    main()