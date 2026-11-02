import time

from DaWay import Graph

CSV_PATH = "csv/graph_100.csv"


def nearest_insertion(graph):
    number_of_places = len(graph.list_lieux)
    if number_of_places == 0:
        raise ValueError("The graph must contain at least one place.")
    if number_of_places == 1:
        return [0, 0]

    nearest = min(
        range(1, number_of_places),
        key=lambda place: graph.distance_between(0, place),
    )
    route = [0, nearest, 0]
    included = {0, nearest}
    distance_to_route = [float("inf")] * number_of_places

    for place in range(1, number_of_places):
        if place not in included:
            distance_to_route[place] = min(
                graph.distance_between(place, route_city) for route_city in route[:-1]
            )

    while len(included) < number_of_places:
        place = min(
            (candidate for candidate in range(number_of_places) if candidate not in included),
            key=distance_to_route.__getitem__,
        )

        best_position = min(
            range(len(route) - 1),
            key=lambda index: (
                graph.distance_between(route[index], place)
                + graph.distance_between(place, route[index + 1])
                - graph.distance_between(route[index], route[index + 1])
            ),
        )
        route.insert(best_position + 1, place)
        included.add(place)

        for candidate in range(1, number_of_places):
            if candidate not in included:
                distance_to_route[candidate] = min(
                    distance_to_route[candidate],
                    graph.distance_between(candidate, place),
                )

    return route


def main():
    graph = Graph(csv_path=CSV_PATH)
    graph.charger_graph()
    graph.calcul_matrice_cout_od()
    print(f"Loaded {len(graph.list_lieux)} points from {CSV_PATH}")

    start_time = time.perf_counter()
    route = nearest_insertion(graph)
    elapsed = time.perf_counter() - start_time
    distance = graph.calcul_distance_route(route)

    graph.validate_route(route)
    print(f"Nearest Insertion distance: {distance:.2f}")
    print(f"Calculation time: {elapsed:.6f}s")
    print(f"Route: {route}")


if __name__ == "__main__":
    main()
