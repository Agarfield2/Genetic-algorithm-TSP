import itertools
import random
import time
import unittest

from DaWay import Graph
from nearest_insertion import nearest_insertion


DATASET_SIZES = (5, 20, 100,300)
CHRISTOFIDES_MAX_ODD_VERTICES = 20
LK_CANDIDATE_COUNT = 12
LK_MAX_DEPTH = 6
LK_MAX_IMPROVEMENTS = 20
LK_MAX_SEARCH_NODES = 2_000
CHAINED_LK_ROUNDS = 5
THREE_OPT_FULL_LIMIT = 30
THREE_OPT_TRIPLE_SAMPLES = 5_000
THREE_OPT_MAX_IMPROVEMENTS = 100


class ChristofidesLimitError(ValueError):
    """Raised when exact matching would make the Christofides test impractical."""


def _route_distance(graph, route):
    return graph.calcul_distance_route(route)


def _best_insertion(graph, route, place):
    best_position = min(
        range(len(route) - 1),
        key=lambda index: (
            graph.distance_between(route[index], place)
            + graph.distance_between(place, route[index + 1])
            - graph.distance_between(route[index], route[index + 1])
        ),
    )
    route.insert(best_position + 1, place)


def greedy_tour(graph):
    """Build a cycle by adding short edges without early cycles or degree > 2."""
    number_of_places = len(graph.list_lieux)
    if number_of_places < 1:
        raise ValueError("The graph must contain at least one place.")
    if number_of_places == 1:
        return [0, 0]

    edges = sorted(
        (
            graph.distance_between(first, second),
            first,
            second,
        )
        for first in range(number_of_places)
        for second in range(first + 1, number_of_places)
    )
    parent = list(range(number_of_places))
    degree = [0] * number_of_places
    selected = []

    def find(place):
        while parent[place] != place:
            parent[place] = parent[parent[place]]
            place = parent[place]
        return place

    for _, first, second in edges:
        if degree[first] == 2 or degree[second] == 2:
            continue
        first_root = find(first)
        second_root = find(second)
        if first_root == second_root and len(selected) != number_of_places - 1:
            continue
        if first_root == second_root and (
            degree[first] != 1 or degree[second] != 1
        ):
            continue

        selected.append((first, second))
        degree[first] += 1
        degree[second] += 1
        parent[first_root] = second_root
        if len(selected) == number_of_places:
            break

    adjacency = [[] for _ in range(number_of_places)]
    for first, second in selected:
        adjacency[first].append(second)
        adjacency[second].append(first)

    route = [0]
    previous = None
    current = 0
    while True:
        following = next(place for place in adjacency[current] if place != previous)
        route.append(following)
        if following == 0:
            return route
        previous, current = current, following


def nearest_neighbor_tour(graph, start=0):
    """Always visit the closest unvisited city, starting at the chosen city."""
    number_of_places = len(graph.list_lieux)
    if number_of_places < 1:
        raise ValueError("The graph must contain at least one place.")
    if not 0 <= start < number_of_places:
        raise ValueError("start must identify a place in the graph.")

    unvisited = set(range(number_of_places))
    unvisited.remove(start)
    route = [start]
    while unvisited:
        current = route[-1]
        following = min(
            unvisited,
            key=lambda place: graph.distance_between(current, place),
        )
        route.append(following)
        unvisited.remove(following)
    return [*route, start]


def cheapest_insertion_tour(graph):
    """Insert the city/edge pair with the smallest increase in tour length."""
    number_of_places = len(graph.list_lieux)
    if number_of_places < 1:
        raise ValueError("The graph must contain at least one place.")
    if number_of_places == 1:
        return [0, 0]

    nearest = min(
        range(1, number_of_places),
        key=lambda place: graph.distance_between(0, place),
    )
    route = [0, nearest, 0]
    unvisited = set(range(number_of_places)) - {0, nearest}
    while unvisited:
        _, place, position = min(
            (
                graph.distance_between(route[index], place)
                + graph.distance_between(place, route[index + 1])
                - graph.distance_between(route[index], route[index + 1]),
                place,
                index,
            )
            for place in unvisited
            for index in range(len(route) - 1)
        )
        route.insert(position + 1, place)
        unvisited.remove(place)
    return route


def random_insertion_tour(graph, seed=0):
    """Insert a random remaining city at its cheapest position."""
    number_of_places = len(graph.list_lieux)
    if number_of_places < 1:
        raise ValueError("The graph must contain at least one place.")
    if number_of_places == 1:
        return [0, 0]

    rng = random.Random(seed)
    unvisited = list(range(1, number_of_places))
    rng.shuffle(unvisited)
    route = [0, unvisited.pop(), 0]
    while unvisited:
        _best_insertion(graph, route, unvisited.pop())
    return route


def farthest_insertion_tour(graph):
    """Insert the city farthest from the current circuit at its cheapest position."""
    number_of_places = len(graph.list_lieux)
    if number_of_places < 1:
        raise ValueError("The graph must contain at least one place.")
    if number_of_places == 1:
        return [0, 0]

    farthest = max(
        range(1, number_of_places),
        key=lambda place: graph.distance_between(0, place),
    )
    route = [0, farthest, 0]
    unvisited = set(range(number_of_places)) - {0, farthest}
    while unvisited:
        place = max(
            unvisited,
            key=lambda candidate: min(
                graph.distance_between(candidate, route_city)
                for route_city in route[:-1]
            ),
        )
        _best_insertion(graph, route, place)
        unvisited.remove(place)
    return route


def _minimum_spanning_tree(graph):
    """Prim's algorithm for the complete Euclidean graph."""
    number_of_places = len(graph.list_lieux)
    in_tree = {0}
    best_edge = {
        place: (graph.distance_between(0, place), 0)
        for place in range(1, number_of_places)
    }
    edges = []

    while len(in_tree) < number_of_places:
        place = min(
            (candidate for candidate in best_edge if candidate not in in_tree),
            key=lambda candidate: best_edge[candidate][0],
        )
        distance, parent = best_edge[place]
        edges.append((parent, place, distance))
        in_tree.add(place)
        for candidate in best_edge:
            if candidate not in in_tree:
                candidate_distance = graph.distance_between(place, candidate)
                if candidate_distance < best_edge[candidate][0]:
                    best_edge[candidate] = (candidate_distance, place)
    return edges


def _minimum_perfect_matching(graph, odd_places):
    """Find an exact minimum matching by bitmask dynamic programming."""
    if len(odd_places) > CHRISTOFIDES_MAX_ODD_VERTICES:
        raise ChristofidesLimitError(
            f"Found {len(odd_places)} odd vertices; exact Christofides matching "
            f"is limited to {CHRISTOFIDES_MAX_ODD_VERTICES}."
        )
    memo = {0: (0.0, ())}

    def solve(mask):
        if mask in memo:
            return memo[mask]

        first_bit = mask & -mask
        first_index = first_bit.bit_length() - 1
        remaining = mask ^ first_bit
        best_cost = float("inf")
        best_pairs = ()
        partner_bits = remaining
        while partner_bits:
            partner_bit = partner_bits & -partner_bits
            partner_index = partner_bit.bit_length() - 1
            next_mask = remaining ^ partner_bit
            sub_cost, sub_pairs = solve(next_mask)
            cost = (
                sub_cost
                + graph.distance_between(
                    odd_places[first_index],
                    odd_places[partner_index],
                )
            )
            if cost < best_cost:
                best_cost = cost
                best_pairs = (
                    (odd_places[first_index], odd_places[partner_index]),
                    *sub_pairs,
                )
            partner_bits ^= partner_bit

        memo[mask] = (best_cost, best_pairs)
        return memo[mask]

    return solve((1 << len(odd_places)) - 1)[1]


def christofides_tour(graph):
    """Christofides tour with exact matching for instances small enough to solve."""
    number_of_places = len(graph.list_lieux)
    if number_of_places < 1:
        raise ValueError("The graph must contain at least one place.")
    if number_of_places == 1:
        return [0, 0]

    tree_edges = _minimum_spanning_tree(graph)
    tree_adjacency = [[] for _ in range(number_of_places)]
    for first, second, _ in tree_edges:
        tree_adjacency[first].append(second)
        tree_adjacency[second].append(first)
    odd_places = [
        place
        for place, neighbors in enumerate(tree_adjacency)
        if len(neighbors) % 2
    ]
    matching = _minimum_perfect_matching(graph, odd_places)

    # Keep parallel MST/matching edges distinct while finding an Euler circuit.
    multigraph = [[] for _ in range(number_of_places)]
    edge_id = 0
    for first, second, _ in tree_edges:
        multigraph[first].append((second, edge_id))
        multigraph[second].append((first, edge_id))
        edge_id += 1
    for first, second in matching:
        multigraph[first].append((second, edge_id))
        multigraph[second].append((first, edge_id))
        edge_id += 1

    used_edges = set()
    stack = [0]
    euler_circuit = []
    while stack:
        current = stack[-1]
        while multigraph[current] and multigraph[current][-1][1] in used_edges:
            multigraph[current].pop()
        if not multigraph[current]:
            euler_circuit.append(stack.pop())
        else:
            following, current_edge = multigraph[current].pop()
            used_edges.add(current_edge)
            stack.append(following)

    route = []
    seen_places = set()
    for place in reversed(euler_circuit):
        if place not in seen_places:
            route.append(place)
            seen_places.add(place)
    route.append(route[0])
    return route


def two_opt_tour(graph, route):
    """Apply best-improvement 2-opt until no tested edge pair shortens the tour."""
    route = list(route)
    place_count = len(route) - 1
    while True:
        best_delta = 0.0
        best_i = None
        best_j = None
        for first_edge in range(place_count - 1):
            first = route[first_edge]
            second = route[first_edge + 1]
            for second_edge in range(first_edge + 2, place_count):
                if first_edge == 0 and second_edge == place_count - 1:
                    continue
                third = route[second_edge]
                fourth = route[second_edge + 1]
                delta = (
                    graph.distance_between(first, third)
                    + graph.distance_between(second, fourth)
                    - graph.distance_between(first, second)
                    - graph.distance_between(third, fourth)
                )
                if delta < best_delta:
                    best_delta = delta
                    best_i = first_edge
                    best_j = second_edge
        if best_i is None:
            return route
        route[best_i + 1 : best_j + 1] = reversed(
            route[best_i + 1 : best_j + 1]
        )


def three_opt_tour(graph, route):
    """Best-improvement 3-opt; exhaustive on small and sampled on large tours."""
    route = list(route)
    place_count = len(route) - 1
    rng = random.Random(0)
    for _ in range(THREE_OPT_MAX_IMPROVEMENTS):
        best_delta = 0.0
        best_route = None
        cycle = route[:-1]
        if place_count <= THREE_OPT_FULL_LIMIT:
            cut_triples = itertools.combinations(range(place_count), 3)
        else:
            sampled_triples = set()
            while len(sampled_triples) < THREE_OPT_TRIPLE_SAMPLES:
                triple = tuple(sorted(rng.sample(range(place_count), 3)))
                first_cut, second_cut, third_cut = triple
                if (
                    second_cut - first_cut >= 2
                    and third_cut - second_cut >= 2
                    and place_count - third_cut + first_cut >= 2
                ):
                    sampled_triples.add(triple)
            cut_triples = iter(sorted(sampled_triples))

        for first_cut, second_cut, third_cut in cut_triples:
            if (
                second_cut - first_cut < 2
                or third_cut - second_cut < 2
                or place_count - third_cut + first_cut < 2
            ):
                continue
            prefix = cycle[: first_cut + 1]
            segment_a_start = first_cut + 1
            segment_a = cycle[segment_a_start : second_cut + 1]
            segment_b_start = second_cut + 1
            segment_b = cycle[segment_b_start : third_cut + 1]
            suffix = cycle[third_cut + 1 :]
            removed = (
                graph.distance_between(cycle[first_cut], segment_a[0])
                + graph.distance_between(segment_a[-1], segment_b[0])
                + graph.distance_between(
                    segment_b[-1],
                    suffix[0] if suffix else cycle[0],
                )
            )

            for order in ((segment_a, segment_b), (segment_b, segment_a)):
                for reverse_a in (False, True):
                    for reverse_b in (False, True):
                        if (
                            order == (segment_a, segment_b)
                            and not reverse_a
                            and not reverse_b
                        ):
                            continue
                        first_segment = (
                            list(reversed(order[0])) if reverse_a else order[0]
                        )
                        second_segment = (
                            list(reversed(order[1])) if reverse_b else order[1]
                        )
                        added = (
                            graph.distance_between(prefix[-1], first_segment[0])
                            + graph.distance_between(
                                first_segment[-1],
                                second_segment[0],
                            )
                            + graph.distance_between(
                                second_segment[-1],
                                suffix[0] if suffix else prefix[0],
                            )
                        )
                        delta = added - removed
                        if delta < best_delta:
                            best_delta = delta
                            best_route = (
                                prefix + first_segment + second_segment + suffix
                            )
        if best_route is None:
            return [*cycle, cycle[0]]
        route = [*best_route, best_route[0]]
    return route


def lin_kernighan_tour(graph, route):
    """Candidate-restricted variable-depth LK sequential edge-exchange search."""
    current = two_opt_tour(graph, route)
    place_count = len(current) - 1
    neighbor_count = min(LK_CANDIDATE_COUNT, max(2, place_count - 1))
    neighbors = [
        sorted(
            (
                place
                for place in range(place_count)
                if place != source
            ),
            key=lambda place: graph.distance_between(source, place),
        )[:neighbor_count]
        for source in range(place_count)
    ]

    def exchange_search(tour):
        edges = {
            tuple(sorted((tour[index], tour[index + 1])))
            for index in range(place_count)
        }
        tour_positions = [0] * place_count
        for position, place in enumerate(tour[:-1]):
            tour_positions[place] = position
        search_nodes = 0
        for start in range(place_count):
            for second in (tour[(start + 1) % place_count], tour[start - 1]):
                removed = {(min(start, second), max(start, second))}
                visited = {start, second}
                def extend(current_place, gain, depth, added):
                    nonlocal search_nodes
                    search_nodes += 1
                    if search_nodes > LK_MAX_SEARCH_NODES:
                        return None

                    for next_place in neighbors[current_place]:
                        added_edge = tuple(sorted((current_place, next_place)))
                        if (
                            next_place in visited
                            or added_edge in edges
                            or added_edge in removed
                            or added_edge in added
                        ):
                            continue
                        next_gain = gain - graph.distance_between(
                            current_place,
                            next_place,
                        )
                        if next_gain <= 0:
                            continue

                        closing_edge = tuple(sorted((next_place, start)))
                        if (
                            next_place != start
                            and closing_edge not in edges
                            and closing_edge not in removed
                            and closing_edge not in added
                            and next_gain
                            > graph.distance_between(next_place, start)
                        ):
                            candidate_edges = (
                                (edges - removed)
                                | added
                                | {added_edge, closing_edge}
                            )
                            candidate = _tour_from_edges(
                                place_count,
                                candidate_edges,
                                start,
                            )
                            if candidate is not None:
                                return candidate

                        if depth >= LK_MAX_DEPTH:
                            continue
                        visited.add(next_place)
                        position = tour_positions[next_place]
                        for following in (
                            tour[(position + 1) % place_count],
                            tour[(position - 1) % place_count],
                        ):
                            removed_edge = tuple(sorted((next_place, following)))
                            if following in visited or removed_edge in removed:
                                continue
                            removed.add(removed_edge)
                            visited.add(following)
                            result = extend(
                                following,
                                next_gain
                                + graph.distance_between(next_place, following),
                                depth + 1,
                                added | {added_edge},
                            )
                            visited.remove(following)
                            if result is not None:
                                return result
                            removed.remove(removed_edge)
                        visited.remove(next_place)
                    return None

                initial_gain = graph.distance_between(start, second)
                result = extend(second, initial_gain, 1, set())
                if result is not None:
                    return result
        return None

    for _ in range(LK_MAX_IMPROVEMENTS):
        improved = exchange_search(current)
        if improved is None:
            break
        current = improved
    return current


def _tour_from_edges(place_count, edges, start):
    adjacency = [[] for _ in range(place_count)]
    for first, second in edges:
        adjacency[first].append(second)
        adjacency[second].append(first)
    if any(len(neighbors) != 2 for neighbors in adjacency):
        return None

    route = [start]
    previous = None
    current = start
    while True:
        following = next(
            (place for place in adjacency[current] if place != previous),
            None,
        )
        if following is None:
            return None
        if following == start:
            break
        if following in route:
            return None
        route.append(following)
        previous, current = current, following
    if len(route) != place_count:
        return None
    return [*route, start]


def _double_bridge(route, rng):
    """Perturb a tour with a 4-edge exchange before another LK descent."""
    cycle = route[:-1]
    place_count = len(cycle)
    if place_count < 8:
        return list(route)

    cuts = sorted(rng.sample(range(1, place_count), 3))
    first, second, third = cuts
    a = cycle[:first]
    b = cycle[first:second]
    c = cycle[second:third]
    d = cycle[third:]
    return [*a, *c, *b, *d, a[0]]


def chained_lin_kernighan_tour(graph, route, seed=0):
    """Repeat LK descent from double-bridge perturbations, retaining the best."""
    rng = random.Random(seed)
    best = lin_kernighan_tour(graph, route)
    best_distance = _route_distance(graph, best)
    current = best

    for _ in range(CHAINED_LK_ROUNDS):
        current = _double_bridge(current, rng)
        current = lin_kernighan_tour(graph, current)
        current_distance = _route_distance(graph, current)
        if current_distance < best_distance:
            best = list(current)
            best_distance = current_distance
    return best


def _exact_tour_distance(graph):
    route = [0]
    best_route = None
    best_distance = float("inf")

    def visit(current, remaining, distance):
        nonlocal best_route, best_distance
        if not remaining:
            total = distance + graph.distance_between(current, 0)
            if total < best_distance:
                best_distance = total
                best_route = [*route, 0]
            return
        for place in remaining:
            next_remaining = remaining - {place}
            route.append(place)
            visit(
                place,
                next_remaining,
                distance + graph.distance_between(current, place),
            )
            route.pop()

    visit(0, set(range(1, len(graph.list_lieux))), 0.0)
    return best_distance


HEURISTICS = (
    ("Greedy", greedy_tour),
    ("Nearest Neighbor", nearest_neighbor_tour),
    ("Nearest Insertion", nearest_insertion),
    ("Cheapest Insertion", cheapest_insertion_tour),
    ("Random Insertion", random_insertion_tour),
    ("Farthest Insertion", farthest_insertion_tour),
    ("Christofides", christofides_tour),
)


def benchmark():
    """Print distances and runtimes for all implemented methods and datasets."""
    for size in DATASET_SIZES:
        graph = Graph(
            csv_path=f"csv/graph_{size}.csv",
            neighbor_count=0,
        )
        graph.charger_graph()
        graph.calcul_matrice_cout_od()
        initial_route = graph.space_filling_route()
        methods = [
            *HEURISTICS,
            ("2-Opt (Hilbert start)", lambda g: two_opt_tour(g, initial_route)),
            (
                "2-Opt + 3-Opt (full)"
                if size <= THREE_OPT_FULL_LIMIT
                else "2-Opt + 3-Opt (sampled)",
                lambda g: three_opt_tour(
                    g,
                    two_opt_tour(g, initial_route),
                ),
            ),
            ("Lin-Kernighan", lambda g: lin_kernighan_tour(g, initial_route)),
            (
                "Chained Lin-Kernighan",
                lambda g: chained_lin_kernighan_tour(g, initial_route, seed=42),
            ),
        ]
        print(f"\n{size} places ({graph.csv_path})")
        print(f"{'Heuristic':<26} {'Distance':>12} {'Time (s)':>10}")
        print("-" * 50)
        for name, method in methods:
            start_time = time.perf_counter()
            try:
                route = method(graph)
            except ChristofidesLimitError as error:
                print(f"{name:<26} {'SKIPPED':>12} {str(error)}")
                continue
            elapsed = time.perf_counter() - start_time
            graph.validate_route(route)
            print(
                f"{name:<26} "
                f"{_route_distance(graph, route):>12.2f} "
                f"{elapsed:>10.4f}"
            )


class HeuristiqueTests(unittest.TestCase):
    def setUp(self):
        self.graph = Graph(csv_path="csv/graph_20.csv", neighbor_count=0)
        self.graph.charger_graph()
        self.graph.calcul_matrice_cout_od()

    def test_construction_heuristics_return_closed_tours(self):
        methods = [
            greedy_tour,
            nearest_neighbor_tour,
            nearest_insertion,
            cheapest_insertion_tour,
            lambda graph: random_insertion_tour(graph, seed=42),
            farthest_insertion_tour,
            christofides_tour,
        ]
        for method in methods:
            with self.subTest(method=method):
                self.graph.validate_route(method(self.graph))

    def test_local_search_heuristics_do_not_worsen_the_starting_tour(self):
        route = self.graph.space_filling_route()
        initial_distance = _route_distance(self.graph, route)
        methods = [
            two_opt_tour,
            three_opt_tour,
            lin_kernighan_tour,
            lambda graph, candidate: chained_lin_kernighan_tour(
                graph,
                candidate,
                seed=42,
            ),
        ]
        for method in methods:
            with self.subTest(method=method):
                improved = method(self.graph, route)
                self.graph.validate_route(improved)
                self.assertLessEqual(
                    _route_distance(self.graph, improved),
                    initial_distance,
                )

    def test_exact_christofides_matching_is_limited_explicitly(self):
        with self.assertRaisesRegex(ValueError, "limited to"):
            _minimum_perfect_matching(
                self.graph,
                list(range(CHRISTOFIDES_MAX_ODD_VERTICES + 2)),
            )

    def test_christofides_meets_bound_on_five_city_instance(self):
        graph = Graph(csv_path="csv/graph_5.csv", neighbor_count=0)
        graph.charger_graph()
        graph.calcul_matrice_cout_od()

        route = christofides_tour(graph)

        self.assertLessEqual(
            _route_distance(graph, route),
            1.5 * _exact_tour_distance(graph) + 1e-9,
        )


if __name__ == "__main__":
    benchmark()
