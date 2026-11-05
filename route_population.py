import random


class UniqueRoutePopulation:
    """Helpers for building populations without duplicate undirected cycles."""

    def _random_route(self, number_of_places):
        route = list(range(1, number_of_places))
        random.shuffle(route)
        return [0, *route, 0]

    def _unique_route_limit(self, number_of_places):
        if number_of_places < 3:
            return 1

        possible_routes = 1
        limit = self.population_size
        for place_count in range(2, number_of_places):
            possible_routes *= place_count
            if possible_routes >= 2 * limit:
                return limit
        return min(limit, max(1, possible_routes // 2))

    @staticmethod
    def _route_key(route):
        if len(route) > 3:
            if route[1] < route[-2]:
                return tuple(route)
            if route[1] > route[-2]:
                return (route[0], *reversed(route[1:-1]), route[-1])

        forward = tuple(route)
        reverse = (route[0], *reversed(route[1:-1]), route[-1])
        # A cycle and its reverse describe the same undirected TSP route.
        return min(forward, reverse)

    def _append_unique_route(self, population, seen_routes, route):
        route_key = self._route_key(route)
        if route_key in seen_routes:
            return False
        population.append(list(route))
        seen_routes.add(route_key)
        return True

    def _fill_unique_population(self, population, seen_routes, number_of_places):
        internal_route = list(range(1, number_of_places))
        while len(population) < self.population_size:
            route = [0, *internal_route, 0]
            self._append_unique_route(population, seen_routes, route)
            if not self._next_permutation(internal_route):
                break

    @staticmethod
    def _next_permutation(values):
        pivot = len(values) - 2
        while pivot >= 0 and values[pivot] >= values[pivot + 1]:
            pivot -= 1
        if pivot < 0:
            return False

        successor = len(values) - 1
        while values[successor] <= values[pivot]:
            successor -= 1
        values[pivot], values[successor] = values[successor], values[pivot]
        values[pivot + 1 :] = reversed(values[pivot + 1 :])
        return True
