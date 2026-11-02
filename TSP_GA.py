import random
from DaWay import NB_LIEUX


class TSP_GA:
    def __init__(
        self,
        population_size,
        elite_count,
        mutation_rate,
        tournament_size,
    ):
        if population_size < 1:
            raise ValueError("population_size must be greater than zero.")
        if not 0 <= elite_count <= population_size:
            raise ValueError("elite_count must be between zero and population_size.")
        if not 0 <= mutation_rate <= 1:
            raise ValueError("mutation_rate must be between zero and one.")
        if tournament_size < 1:
            raise ValueError("tournament_size must be greater than zero.")

        self.population_size = population_size
        self.elite_count = elite_count
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.population = []

    def init_population(self, graph=None):
        self.population = []
        number_of_places = len(graph.list_lieux) if graph is not None else NB_LIEUX
        for _ in range(self.population_size):
            route = list(range(1, number_of_places))
            random.shuffle(route)
            route = [0, *route, 0]
            self.population.append(route)
        return self.population

    def reproduction(self, graph):
        elite_count = min(self.elite_count, len(self.population))
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
            child = self.mutation(child, self.mutation_rate)
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
        tournament_size = min(self.tournament_size, len(self.population))
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




    