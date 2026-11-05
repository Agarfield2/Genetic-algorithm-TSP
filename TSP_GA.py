from DaWay import Graph, Route
from genetic_evolution import GeneticEvolution

POP_SIZE = 100
ELITE_COUNT = 1


class TSP_GA(GeneticEvolution):
    """Manage a genetic search while retaining its best solution."""

    def __init__(
        self,
        population_size,
        elite_count,
        mutation_rate,
        tournament_size,
        max_mutation_rate,
        stagnation_generations,
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
        if fitness_batch_size < 1:
            raise ValueError("fitness_batch_size must be greater than zero.")

        self.population_size = population_size
        self.elite_count = elite_count
        self.mutation_rate = mutation_rate
        self.max_mutation_rate = max_mutation_rate
        self.tournament_size = tournament_size
        self.stagnation_generations = stagnation_generations
        self.fitness_batch_size = fitness_batch_size

        self.population = []
        self._fitness = []
        self._best_route = None
        self._best_distance = float("inf")
        self.generations_without_improvement = 0
        self.current_mutation_rate = mutation_rate

    def _calculate_fitness(
        self,
        graph: Graph,
        routes: list[Route],
    ) -> list[float]:
        if not routes:
            return []
        batch_calculator = getattr(graph, "calcul_distances_routes", None)
        if batch_calculator is not None:
            return batch_calculator(routes, batch_size=self.fitness_batch_size)
        return [graph.calcul_distance_route(route) for route in routes]

    def _ensure_fitness(self, graph: Graph) -> None:
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
            # Keep a snapshot because population routes can change later.
            self._best_route = Route(self.population[best_index])

    def best_solution(self) -> tuple[Route, float]:
        if self._best_route is None:
            raise ValueError("The population has no evaluated solutions.")
        return self._best_route.copy(), self._best_distance

    def _adaptive_mutation_rate(self):
        progress = min(
            self.generations_without_improvement / self.stagnation_generations,
            1.0,
        )
        return self.mutation_rate + (
            self.max_mutation_rate - self.mutation_rate
        ) * progress
