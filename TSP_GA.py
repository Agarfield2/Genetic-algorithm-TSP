import random
from DaWay import NB_LIEUX

POP_SIZE = 100
ELITE_COUNT = 1

class TSP_GA:
    def __init__(self):
        self.population = []

    def init_population(self, population_size=POP_SIZE, graph=None):
        self.population = []
        number_of_places = len(graph.list_lieux) if graph is not None else NB_LIEUX
        for _ in range(population_size):
            route = list(range(1, number_of_places))
            random.shuffle(route)
            route = [0, *route, 0]
            self.population.append(route)
        return self.population

    def reproduction(self, graph):
        elite_count = min(ELITE_COUNT, len(self.population))
        new_population = [
            list(route)
            for route in sorted(
                self.population,
                key=lambda route: graph.calcul_distance_route(route),
            )[:elite_count]
        ]

        while len(new_population) < len(self.population):
            parent1 = self.selection(graph)
            parent2 = self.selection(graph)
            child = self.crossover(parent1, parent2)
            child = self.mutation(child)
            new_population.append(child)
        self.population = new_population

    def mutation(self, route, mutation_rate=0.01):
        internal_positions = range(1, len(route) - 1)
        for i in internal_positions:
            if random.random() < mutation_rate:
                j = random.randint(1, len(route) - 2)
                route[i], route[j] = route[j], route[i]
        return route

    def selection(self, graph):
        tournament_size = min(5, len(self.population))
        tournament = random.sample(self.population, tournament_size)
        best_route = min(tournament, key=lambda route: graph.calcul_distance_route(route))
        return best_route

    def crossover(self, parent1, parent2):
        parent1_interior = parent1[1:-1]
        parent2_interior = parent2[1:-1]
        if not parent1_interior:
            return [0, 0]

        start = random.randint(0, len(parent1_interior) - 1)
        end = random.randint(start, len(parent1_interior) - 1)
        child_interior = [None] * len(parent1_interior)
        child_interior[start:end + 1] = parent1_interior[start:end + 1]
        remaining_places = [
            place for place in parent2_interior if place not in child_interior
        ]
        empty_positions = [
            index for index, place in enumerate(child_interior) if place is None
        ]
        for index, place in zip(empty_positions, remaining_places):
            child_interior[index] = place
        return [0, *child_interior, 0]




    