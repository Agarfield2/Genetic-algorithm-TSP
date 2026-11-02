from DaWay import *


POP_SIZE = 100

class TSP_GA:
    population = []

    def init_population(self, population_size = POP_SIZE, graph = None):
        for _ in range(population_size):
            route = list(range(NB_LIEUX))
            random.shuffle(route)
            self.population.append(route)
        return self.population

    def reproduction(self, graph):
        new_population = []
        for _ in range(len(self.population)):
            parent1 = self.selection(graph)
            parent2 = self.selection(graph)
            child = self.crossover(parent1, parent2)
            new_population.append(child)
        self.population = new_population

    def selection(self, graph):
        tournament_size = 5
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




    