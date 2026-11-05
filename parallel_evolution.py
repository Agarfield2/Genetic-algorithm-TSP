import random

import numpy as np

from DaWay import Route
from TSP_GA import TSP_GA

_population_buffer = None
_fitness_buffer = None
_population_size = 0
_route_length = 0
_graph = None
_solver = None


def initialize_worker(
    population_buffer,
    fitness_buffer,
    population_size,
    route_length,
    graph,
    solver_parameters,
):
    global _population_buffer
    global _fitness_buffer
    global _population_size
    global _route_length
    global _graph
    global _solver

    _population_buffer = population_buffer
    _fitness_buffer = fitness_buffer
    _population_size = population_size
    _route_length = route_length
    _graph = graph
    _solver = TSP_GA(**solver_parameters)


def generate_offspring(task):
    child_count, mutation_rate, elite_count, seed = task
    random.seed(seed)

    population_array = np.frombuffer(
        _population_buffer,
        dtype=np.int64,
    ).reshape((_population_size, _route_length))
    fitness_array = np.frombuffer(_fitness_buffer, dtype=np.float64)
    population = [Route(route.tolist()) for route in population_array]
    fitness = fitness_array.tolist()

    _solver.population = population
    _solver._fitness = fitness
    _solver.current_mutation_rate = mutation_rate

    ranked_indices = sorted(
        range(len(population)),
        key=fitness.__getitem__,
    )
    elite_routes = [
        population[index] for index in ranked_indices[:elite_count]
    ]
    offspring = []
    seen_routes = {
        _solver._route_key(route)
        for route in elite_routes
    }

    for _ in range(child_count):
        for _ in range(10):
            parent1 = _solver.selection()
            parent2 = _solver.selection()
            child = _solver.crossover(parent1, parent2)
            child = _solver.mutation(child, mutation_rate)
            if _solver._append_unique_route(offspring, seen_routes, child):
                break

    return offspring
