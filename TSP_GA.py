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
            route = list(range(number_of_places))
            random.shuffle(route)
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
        for i in range(len(route)):
            if random.random() < mutation_rate:
                j = random.randint(0, len(route) - 1)
                route[i], route[j] = route[j], route[i]
        return route

    def selection(self, graph):
        tournament_size = min(5, len(self.population))
        tournament = random.sample(self.population, tournament_size)
        best_route = min(tournament, key=lambda route: graph.calcul_distance_route(route))
        return best_route

    def crossover(self, parent1, parent2):
        start = random.randint(0, len(parent1) - 1)
        end = random.randint(start, len(parent1) - 1)
        child = [None] * len(parent1)
        child[start:end + 1] = parent1[start:end + 1]
        for i in range(len(parent2)):
            if parent2[i] not in child:
                for j in range(len(child)):
                    if child[j] is None:
                        child[j] = parent2[i]
                        break
        return child




    