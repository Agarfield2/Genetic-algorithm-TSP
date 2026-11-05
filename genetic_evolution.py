import random

from genetic_operators import GeneticOperators
from route_population import UniqueRoutePopulation


class GeneticEvolution(UniqueRoutePopulation, GeneticOperators):
    """Build populations and advance them using the genetic operators."""

    def init_population(self, graph):
        number_of_places = len(graph.list_lieux)
        if number_of_places < 1:
            raise ValueError("The graph must contain at least one place.")

        self.population_size = self._unique_route_limit(number_of_places)
        self.population = []
        seen_routes = set()
        route_builder = getattr(graph, "space_filling_route", None)
        if route_builder is not None:
            seed_route = route_builder()
            seed_search_attempts = min(256, max(8, number_of_places // 4))
            for _ in range(50):
                previous_route = seed_route.copy()
                seed_route = self.two_opt(
                    seed_route,
                    graph,
                    seed_search_attempts,
                )
                if seed_route == previous_route:
                    break

            seeded_count = min(
                self.population_size,
                max(1, self.population_size // 10),
            )
            self._append_unique_route(self.population, seen_routes, seed_route)
            seed_mutation_rate = min(
                self.mutation_rate,
                2 / max(1, number_of_places - 1),
            )
            for _ in range(seeded_count - 1):
                route = list(seed_route)
                self.mutation(route, mutation_rate=seed_mutation_rate)
                self._append_unique_route(self.population, seen_routes, route)

        random_attempts = self.population_size * 10
        for _ in range(random_attempts):
            if len(self.population) >= self.population_size:
                break
            route = self._random_route(number_of_places)
            self._append_unique_route(self.population, seen_routes, route)

        self._fill_unique_population(self.population, seen_routes, number_of_places)

        self._fitness = self._calculate_fitness(graph, self.population)
        self._update_global_best()
        self.generations_without_improvement = 0
        return self.population

    def reproduction(self, graph):
        self._ensure_fitness(graph)
        previous_best_distance = self._best_distance
        mutation_rate = self._adaptive_mutation_rate()

        ranked_indices = sorted(
            range(len(self.population)), key=self._fitness.__getitem__
        )
        elite_count = min(self.elite_count, len(self.population))
        new_population = [
            list(self.population[index]) for index in ranked_indices[:elite_count]
        ]
        seen_routes = {self._route_key(route) for route in new_population}
        new_fitness = [self._fitness[index] for index in ranked_indices[:elite_count]]

        child_count = len(self.population) - elite_count
        for _ in range(child_count):
            for _ in range(10):
                parent1 = self.selection()
                parent2 = self.selection()
                child = self.crossover(parent1, parent2)
                child = self.mutation(child, mutation_rate)
                if self._append_unique_route(new_population, seen_routes, child):
                    break

        # Enumerate any remaining cycles if random offspring produced duplicates.
        self._fill_unique_population(
            new_population,
            seen_routes,
            len(graph.list_lieux),
        )
        children = new_population[elite_count:]
        child_fitness = self._calculate_fitness(graph, children)
        new_fitness.extend(child_fitness)

        self.population = new_population
        self._fitness = new_fitness
        self._update_global_best()
        if self._best_distance < previous_best_distance:
            self.generations_without_improvement = 0
        else:
            self.generations_without_improvement += 1
        self.current_mutation_rate = self._adaptive_mutation_rate()
