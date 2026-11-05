import argparse
import json
import os
import platform
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from DaWay import Graph
from TSP_GA import TSP_GA
import main


HYPERPARAMETER_CONFIGS = {
    "current": {},
    "lower_mutation": {
        "mutation_rate": 0.005,
        "max_mutation_rate": 0.05,
    },
    "higher_mutation": {
        "mutation_rate": 0.02,
        "max_mutation_rate": 0.15,
    },
    "tournament_3": {
        "tournament_size": 3,
    },
    "elite_2": {
        "elite_count": 2,
    },
    "neighbors_disabled": {
        "neighbor_count": 0,
    },
    "neighbor_radius_1": {
        "neighbor_cell_radius": 1,
    },
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Compare genetic-algorithm hyperparameters on increasing TSP sizes."
        )
    )
    parser.add_argument("--cities", default="100,1000,10000")
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--workers", type=int, default=main.PARALLEL_WORKERS)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--output-dir", default=".performance")
    return parser.parse_args()


def _build_graph(csv_path, graph_parameters, seed):
    random.seed(seed)
    graph = Graph(
        matrix_limit=main.DISTANCE_MATRIX_LIMIT,
        neighbor_count=graph_parameters["neighbor_count"],
        neighbor_cell_radius=graph_parameters["neighbor_cell_radius"],
        csv_path=str(csv_path),
    )
    graph.charger_graph()
    graph.calcul_matrice_cout_od()
    return graph


def _run_search(
    csv_path,
    population_size,
    generations,
    seed,
    solver_parameters,
    graph_parameters,
):
    graph = _build_graph(csv_path, graph_parameters, seed)
    random.seed(seed)
    solver = TSP_GA(**solver_parameters)
    solver.init_population(graph)
    for _ in range(generations):
        solver.reproduction(graph)
    return solver.best_solution()


def _summarize(values):
    return {
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
        "values": values,
    }


def _evaluate_configuration(
    csv_path,
    number_of_places,
    repeats,
    seed,
    worker_count,
    config,
):
    population_size, generation_count = main.get_solver_budget(number_of_places)
    worker_count = min(worker_count, generation_count)
    generation_counts = main._split_generations(generation_count, worker_count)
    graph_parameters = {
        "neighbor_count": main.NEIGHBOR_COUNT,
        "neighbor_cell_radius": main.NEIGHBOR_CELL_RADIUS,
    }
    solver_parameters = main._solver_parameters(population_size)
    for name, value in config.items():
        if name in graph_parameters:
            graph_parameters[name] = value
        else:
            solver_parameters[name] = value
    solver_parameters["elite_count"] = min(
        solver_parameters["elite_count"],
        population_size,
    )

    distances = []
    elapsed_times = []
    for repeat in range(repeats):
        started = time.perf_counter()
        search_results = []
        for worker, generations in enumerate(generation_counts):
            trial_seed = seed + repeat * 10_000 + worker
            search_results.append(
                _run_search(
                    csv_path,
                    population_size,
                    generations,
                    trial_seed,
                    solver_parameters,
                    graph_parameters,
                )
            )
        elapsed_times.append(time.perf_counter() - started)
        distances.append(min(distance for _, distance in search_results))

    return {
        "parameters": {
            "population_size": population_size,
            "total_generations": generation_count,
            "searches_per_repeat": worker_count,
            **solver_parameters,
            **graph_parameters,
        },
        "best_distance": _summarize(distances),
        "elapsed_seconds": _summarize(elapsed_times),
        "paired_distance_delta_vs_current": [],
    }


def optimize_city_size(
    number_of_places,
    repeats,
    seed,
    worker_count,
):
    csv_path = Path("csv") / f"graph_{number_of_places}.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    configurations = {}
    for name, config in HYPERPARAMETER_CONFIGS.items():
        print(
            f"{number_of_places} cities: testing {name} "
            f"({repeats} repeats)",
            flush=True,
        )
        configurations[name] = _evaluate_configuration(
            csv_path,
            number_of_places,
            repeats,
            seed,
            worker_count,
            config,
        )

    baseline_distances = configurations["current"]["best_distance"]["values"]
    required_wins = (4 * repeats + 4) // 5
    maximum_losses = repeats // 5
    for name, result in configurations.items():
        result["paired_distance_delta_vs_current"] = [
            distance - baseline
            for distance, baseline in zip(
                result["best_distance"]["values"],
                baseline_distances,
            )
        ]
        result["median_paired_distance_delta_vs_current"] = statistics.median(
            result["paired_distance_delta_vs_current"]
        )
        result["paired_wins_vs_current"] = sum(
            distance < baseline
            for distance, baseline in zip(
                result["best_distance"]["values"],
                baseline_distances,
            )
        )
        result["paired_losses_vs_current"] = sum(
            distance > baseline
            for distance, baseline in zip(
                result["best_distance"]["values"],
                baseline_distances,
            )
        )

    improving_configurations = [
        name
        for name, result in configurations.items()
        if name != "current"
        and result["paired_wins_vs_current"] >= required_wins
        and result["paired_losses_vs_current"] <= maximum_losses
        and result["median_paired_distance_delta_vs_current"] < 0
    ]
    best_name = min(
        improving_configurations,
        key=lambda name: (
            configurations[name]["best_distance"]["median"],
            configurations[name]["elapsed_seconds"]["median"],
        ),
    ) if improving_configurations else "current"
    return {
        "city_count": number_of_places,
        "csv": str(csv_path),
        "repeats_per_configuration": repeats,
        "budget": main.get_solver_budget(number_of_places),
        "selection_rule": (
            f"A non-default configuration is recommended only if it wins at "
            f"least {required_wins} of {repeats} paired repeats, loses at "
            f"most {maximum_losses}, and has a negative median paired "
            "distance delta. The qualifying "
            "configuration with the lowest median distance is selected; "
            "otherwise current defaults are retained."
        ),
        "recommended_configuration": best_name,
        "configurations": configurations,
    }


def main_cli():
    arguments = parse_arguments()
    if arguments.repeats < 1:
        raise ValueError("--repeats must be at least one.")
    if arguments.workers < 1:
        raise ValueError("--workers must be at least one.")
    city_counts = [
        int(value.strip()) for value in arguments.cities.split(",")
    ]
    if not city_counts or any(count < 1 for count in city_counts):
        raise ValueError("--cities must contain positive city counts.")
    if len(set(city_counts)) != len(city_counts):
        raise ValueError("--cities cannot contain duplicates.")

    report = {
        "benchmark": "paired genetic algorithm hyperparameter tuning",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
            "numpy": np.__version__,
        },
        "method": (
            "Every configuration uses the same generation budget, worker "
            "partition, and repeat seeds. Independent searches are executed "
            "sequentially to avoid CPU contention during measurement."
        ),
        "repeats_per_configuration": arguments.repeats,
        "worker_count": arguments.workers,
        "seed_base": arguments.seed,
        "configurations": HYPERPARAMETER_CONFIGS,
        "city_sizes": [],
    }
    for city_count in city_counts:
        report["city_sizes"].append(
            optimize_city_size(
                city_count,
                arguments.repeats,
                arguments.seed,
                arguments.workers,
            )
        )

    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    output_directory = Path(arguments.output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / (
        f"hyperparameter-tuning-{datetime.now():%Y%m%d-%H%M%S}.json"
    )
    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(f"\nDetailed report: {report_path}")
    for result in report["city_sizes"]:
        print(
            f"{result['city_count']} cities: "
            f"recommended={result['recommended_configuration']}"
        )
        for name, configuration in result["configurations"].items():
            print(
                f"  {name}: median distance="
                f"{configuration['best_distance']['median']:.2f}, "
                f"paired delta="
                f"{configuration['median_paired_distance_delta_vs_current']:+.2f}, "
                f"median time="
                f"{configuration['elapsed_seconds']['median']:.2f}s"
            )


if __name__ == "__main__":
    main_cli()
