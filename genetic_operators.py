import random


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
            for position in positions:
                other = random.randint(1, last_position)
                route[position], route[other] = route[other], route[position]
        return route

    def crossover(self, parent1, parent2):
        number_of_internal_places = len(parent1) - 2
        if number_of_internal_places <= 0:
            return [0, 0]

        start = random.randint(1, number_of_internal_places)
        end = random.randint(start, number_of_internal_places)
        child = [None] * (number_of_internal_places + 2)
        child[0] = child[-1] = 0
        child[start:end + 1] = parent1[start:end + 1]
        selected_places = set(parent1[start:end + 1])
        remaining_places = iter(
            place for place in parent2[1:-1] if place not in selected_places
        )
        for position in range(1, number_of_internal_places + 1):
            if child[position] is None:
                child[position] = next(remaining_places)
        return child

    def two_opt(self, route, graph, attempts):
        number_of_places = len(route) - 1
        candidates = getattr(graph, "neighbor_candidates", None)
        if not candidates or number_of_places < 4:
            return route

        positions = [0] * number_of_places
        for position, place in enumerate(route[:-1]):
            positions[place] = position

        best_delta = 0.0
        best_i = None
        best_j = None
        for _ in range(attempts):
            i = random.randrange(0, number_of_places - 2)
            first = route[i]
            second = route[i + 1]
            for third in candidates[first]:
                j = positions[third]
                if j <= i + 1 or j >= number_of_places:
                    continue
                fourth = route[j + 1]
                delta = (
                    graph.distance_between(first, third)
                    + graph.distance_between(second, fourth)
                    - graph.distance_between(first, second)
                    - graph.distance_between(third, fourth)
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
