import random
from DaWay import NB_LIEUX

POP_SIZE = 100
ELITE_COUNT = 1


class TSP_GA:
    def __init__(self):
        self.population = []
        self._fitness = []
        self._population_ids = ()

    def init_population(self, population_size=POP_SIZE, graph=None):
        if population_size < 1:
            raise ValueError("population_size must be greater than zero.")

        self.population = []
        number_of_places = len(graph.list_lieux) if graph is not None else NB_LIEUX
        if number_of_places < 1:
            raise ValueError("The graph must contain at least one place.")

        for _ in range(population_size):
            route = list(range(1, number_of_places))
            random.shuffle(route)
            self.population.append([0, *route, 0])

        self._fitness = (
            [graph.calcul_distance_route(route) for route in self.population]
            if graph is not None
            else []
        )
        self._population_ids = tuple(id(route) for route in self.population)
        return self.population

    def reproduction(self, graph):
        self._ensure_fitness(graph)
        elite_count = min(ELITE_COUNT, len(self.population))
        ranked_indices = sorted(
            range(len(self.population)), key=self._fitness.__getitem__
        )
        new_population = [list(self.population[index]) for index in ranked_indices[:elite_count]]
        new_fitness = [self._fitness[index] for index in ranked_indices[:elite_count]]

        while len(new_population) < len(self.population):
            parent1 = self.selection()
            parent2 = self.selection()
            child = self.crossover(parent1, parent2)
            child = self.mutation(child)
            new_population.append(child)
            new_fitness.append(graph.calcul_distance_route(child))

        self.population = new_population
        self._fitness = new_fitness
        self._population_ids = tuple(id(route) for route in self.population)

    def mutation(self, route, mutation_rate=0.01):
        last_internal_position = len(route) - 2
        for i in range(1, last_internal_position + 1):
            if random.random() < mutation_rate:
                j = random.randint(1, last_internal_position)
                route[i], route[j] = route[j], route[i]
        return route

    def selection(self, graph=None):
        if not self.population:
            raise ValueError("Cannot select a parent from an empty population.")

        if graph is not None:
            self._ensure_fitness(graph)
        if len(self._fitness) != len(self.population):
            raise ValueError("Fitness scores are not initialized; provide a graph first.")
        return self._select_parent()

    def _select_parent(self):
        tournament_size = min(5, len(self.population))
        tournament = random.sample(range(len(self.population)), tournament_size)
        best_index = min(tournament, key=self._fitness.__getitem__)
        return self.population[best_index]

    def best_solution(self):
        if not self.population or len(self._fitness) != len(self.population):
            raise ValueError("The population has no evaluated solutions.")
        best_index = min(range(len(self.population)), key=self._fitness.__getitem__)
        return list(self.population[best_index]), self._fitness[best_index]

    def _ensure_fitness(self, graph):
        current_ids = tuple(id(route) for route in self.population)
        if not self.population:
            raise ValueError("Cannot reproduce an empty population.")
        if current_ids != self._population_ids or len(self._fitness) != len(self.population):
            self._fitness = [
                graph.calcul_distance_route(route) for route in self.population
            ]
            self._population_ids = current_ids

    def crossover(self, parent1, parent2):
        parent1_interior = parent1[1:-1]
        parent2_interior = parent2[1:-1]
        if not parent1_interior:
            return [0, 0]

        start = random.randint(0, len(parent1_interior) - 1)
        end = random.randint(start, len(parent1_interior) - 1)
        child_interior = [None] * len(parent1_interior)
        child_interior[start:end + 1] = parent1_interior[start:end + 1]
        selected_places = set(parent1_interior[start:end + 1])
        remaining_places = iter(
            place for place in parent2_interior if place not in selected_places
        )
        for index, place in enumerate(child_interior):
            if place is None:
                child_interior[index] = next(remaining_places)
        return [0, *child_interior, 0]




    