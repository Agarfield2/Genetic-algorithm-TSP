import random

MAX_TWO_OPT_CACHE_CITIES = 1_000_000


class GeneticOperators:
    """Selection, crossover, mutation, and local-search operations for TSP_GA."""

    def selection(self, graph=None):
        if graph is not None:
            self._ensure_fitness(graph)
        if not self.population or len(self._fitness) != len(self.population):
            raise ValueError("Selection requires an evaluated, non-empty population.")

        tournament_size = min(self.tournament_size, len(self.population))
        candidates = random.sample(range(len(self.population)), tournament_size)
        winner = min(candidates, key=self._fitness.__getitem__)
        return self.population[winner]

    def mutation(self, route, mutation_rate=None):
        rate = self.current_mutation_rate if mutation_rate is None else mutation_rate
        if not 0 <= rate <= 1:
            raise ValueError("mutation_rate must be between zero and one.")

        internal_count = len(route) - 2
        expected_swaps = internal_count * rate
        swap_count = int(expected_swaps)
        if random.random() < expected_swaps - swap_count:
            swap_count += 1
        swap_count = min(internal_count, swap_count)
        if swap_count:
            positions = random.sample(range(1, len(route) - 1), swap_count)
            last_position = len(route) - 2
            partners = random.choices(range(1, last_position + 1), k=swap_count)
            for position, other in zip(positions, partners):
                route[position], route[other] = route[other], route[position]
        return route

    def crossover(self, parent1, parent2):
        number_of_internal_places = len(parent1) - 2
        if number_of_internal_places <= 0:
            return [0, 0]

        start = random.randint(1, number_of_internal_places)
        end = random.randint(start, number_of_internal_places)
        segment = parent1[start:end + 1]
        child = [None] * (number_of_internal_places + 2)
        child[0] = child[-1] = 0
        child[start:end + 1] = segment
        selected_places = [False] * (number_of_internal_places + 1)
        for place in segment:
            selected_places[place] = True
        position = 1
        for place in parent2[1:-1]:
            if selected_places[place]:
                continue
            if position == start:
                position = end + 1
            child[position] = place
            position += 1
        return child

    def two_opt(self, route, graph, attempts):
        number_of_places = len(route) - 1
        candidates = getattr(graph, "neighbor_candidates", None)
        if not candidates or number_of_places < 4:
            return route

        positions = [0] * number_of_places
        for position, place in enumerate(route[:-1]):
            positions[place] = position

        edge_distances = (
            [None] * number_of_places
            if number_of_places <= MAX_TWO_OPT_CACHE_CITIES
            else None
        )
        best_delta = 0.0
        best_i = None
        best_j = None
        for _ in range(attempts):
            i = random.randrange(0, number_of_places - 2)
            first = route[i]
            second = route[i + 1]
            first_edge_distance = (
                edge_distances[i] if edge_distances is not None else None
            )
            if first_edge_distance is None:
                first_edge_distance = graph.distance_between(first, second)
                if edge_distances is not None:
                    edge_distances[i] = first_edge_distance

            for third in candidates[first]:
                j = positions[third]
                if j <= i + 1 or j >= number_of_places:
                    continue
                fourth = route[j + 1]
                second_edge_distance = (
                    edge_distances[j] if edge_distances is not None else None
                )
                if second_edge_distance is None:
                    second_edge_distance = graph.distance_between(third, fourth)
                    if edge_distances is not None:
                        edge_distances[j] = second_edge_distance

                delta = (
                    graph.distance_between(first, third)
                    + graph.distance_between(second, fourth)
                    - first_edge_distance
                    - second_edge_distance
                )
                if delta < best_delta:
                    best_delta = delta
                    best_i = i
                    best_j = j

        if best_i is not None:
            route[best_i + 1 : best_j + 1] = reversed(
                route[best_i + 1 : best_j + 1]
            )
        return route
