import random

from DaWay import NB_LIEUX

POP_SIZE = 100
ELITE_COUNT = 1


class TSP_GA:
    def __init__(
        self,
        population_size,
        elite_count,
        mutation_rate,
        tournament_size,
        max_mutation_rate,
        stagnation_generations,
        immigrant_fraction,
        min_diversity,
        local_search_rate,
        local_search_attempts,
        fitness_batch_size,
    ):
        if population_size < 1:
            raise ValueError("population_size must be greater than zero.")
        if not 0 <= elite_count <= population_size:
            raise ValueError("elite_count must be between zero and population_size.")
        if not 0 <= mutation_rate <= max_mutation_rate <= 1:
            raise ValueError(
                "Mutation rates must satisfy 0 <= mutation_rate <= max_mutation_rate <= 1."
            )
        if tournament_size < 1:
            raise ValueError("tournament_size must be greater than zero.")
        if stagnation_generations < 1:
            raise ValueError("stagnation_generations must be greater than zero.")
        if not 0 <= immigrant_fraction <= 1:
            raise ValueError("immigrant_fraction must be between zero and one.")
        if not 0 <= min_diversity <= 1:
            raise ValueError("min_diversity must be between zero and one.")
        if not 0 <= local_search_rate <= 1:
            raise ValueError("local_search_rate must be between zero and one.")
        if local_search_attempts < 0:
            raise ValueError("local_search_attempts cannot be negative.")
        if fitness_batch_size < 1:
            raise ValueError("fitness_batch_size must be greater than zero.")

        self.population_size = population_size
        self.elite_count = elite_count
        self.mutation_rate = mutation_rate
        self.max_mutation_rate = max_mutation_rate
        self.tournament_size = tournament_size
        self.stagnation_generations = stagnation_generations
        self.immigrant_fraction = immigrant_fraction
        self.min_diversity = min_diversity
        self.local_search_rate = local_search_rate
        self.local_search_attempts = local_search_attempts
        self.fitness_batch_size = fitness_batch_size

        self.population = []
        self._fitness = []
        self._best_route = None
        self._best_distance = float("inf")
        self.generations_without_improvement = 0
        self.current_mutation_rate = mutation_rate

    def init_population(self, graph=None):
        number_of_places = len(graph.list_lieux) if graph is not None else NB_LIEUX
        if number_of_places < 1:
            raise ValueError("The graph must contain at least one place.")

        self.population = []
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
            self.population.append(list(seed_route))
            seed_mutation_rate = min(
                self.mutation_rate,
                2 / max(1, number_of_places - 1),
            )
            for _ in range(seeded_count - 1):
                route = list(seed_route)
                self.mutation(route, mutation_rate=seed_mutation_rate)
                self.population.append(route)

        while len(self.population) < self.population_size:
            self.population.append(self._random_route(number_of_places))

        if graph is not None:
            self._fitness = self._calculate_fitness(graph, self.population)
            self._update_global_best()
        else:
            self._fitness = []
            self._best_route = None
            self._best_distance = float("inf")
        self.generations_without_improvement = 0
        return self.population

    def reproduction(self, graph):
        self._ensure_fitness(graph)
        previous_best_distance = self._best_distance
        diversity = self._population_diversity()
        mutation_rate = self._adaptive_mutation_rate()

        ranked_indices = sorted(
            range(len(self.population)), key=self._fitness.__getitem__
        )
        elite_count = min(self.elite_count, len(self.population))
        new_population = [
            list(self.population[index]) for index in ranked_indices[:elite_count]
        ]
        new_fitness = [self._fitness[index] for index in ranked_indices[:elite_count]]

        child_count = len(self.population) - elite_count
        immigrant_count = 0
        if (
            child_count
            and self.generations_without_improvement >= self.stagnation_generations
            and (
                self.generations_without_improvement
                % self.stagnation_generations
                == 0
                or diversity < self.min_diversity
            )
        ):
            immigrant_count = min(
                child_count,
                max(1, int(child_count * self.immigrant_fraction)),
            )

        offspring_count = child_count - immigrant_count
        offspring = []
        for _ in range(offspring_count):
            parent1 = self.selection()
            parent2 = self.selection()
            child = self.crossover(parent1, parent2)
            child = self.mutation(child, mutation_rate)
            if (
                self.local_search_attempts
                and random.random() < self.local_search_rate
            ):
                child = self.two_opt(
                    child,
                    graph,
                    self.local_search_attempts,
                )
            offspring.append(child)

        immigrants = [
            self._random_route(len(graph.list_lieux)) for _ in range(immigrant_count)
        ]
        children = offspring + immigrants
        child_fitness = self._calculate_fitness(graph, children)
        new_population.extend(children)
        new_fitness.extend(child_fitness)

        self.population = new_population
        self._fitness = new_fitness
        self._update_global_best()
        if self._best_distance < previous_best_distance:
            self.generations_without_improvement = 0
        else:
            self.generations_without_improvement += 1
        self.current_mutation_rate = self._adaptive_mutation_rate()

    def _random_route(self, number_of_places):
        route = list(range(1, number_of_places))
        random.shuffle(route)
        return [0, *route, 0]

    def _calculate_fitness(self, graph, routes):
        if not routes:
            return []
        batch_calculator = getattr(graph, "calcul_distances_routes", None)
        if batch_calculator is not None:
            return batch_calculator(routes, batch_size=self.fitness_batch_size)
        return [graph.calcul_distance_route(route) for route in routes]

    def _ensure_fitness(self, graph):
        if not self.population:
            raise ValueError("Cannot reproduce an empty population.")
        if len(self._fitness) != len(self.population):
            self._fitness = self._calculate_fitness(graph, self.population)
            self._update_global_best()

    def _update_global_best(self):
        if not self._fitness:
            return
        best_index = min(range(len(self._fitness)), key=self._fitness.__getitem__)
        best_distance = self._fitness[best_index]
        if best_distance < self._best_distance:
            self._best_distance = best_distance
            self._best_route = list(self.population[best_index])

    def best_solution(self):
        if self._best_route is None:
            raise ValueError("The population has no evaluated solutions.")
        return list(self._best_route), self._best_distance

    def _adaptive_mutation_rate(self):
        progress = min(
            self.generations_without_improvement / self.stagnation_generations,
            1.0,
        )
        return self.mutation_rate + (
            self.max_mutation_rate - self.mutation_rate
        ) * progress

    def _population_diversity(self):
        if not self.population:
            return 0.0
        route_length = len(self.population[0]) - 2
        if route_length <= 0:
            return 1.0

        sample_count = min(16, route_length)
        positions = {
            1 + (index * (route_length - 1) // max(sample_count - 1, 1))
            for index in range(sample_count)
        }
        signatures = {
            tuple(route[position] for position in positions)
            for route in self.population
        }
        return len(signatures) / len(self.population)

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
