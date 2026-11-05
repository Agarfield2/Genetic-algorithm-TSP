import argparse
import json
import multiprocessing
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
    "population_half": {
        "population_multiplier": 0.5,
    },
    "population_double": {
        "population_multiplier": 2.0,
    },
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
    "neighbor_count_8": {
        "neighbor_count": 8,
    },
    "neighbor_count_32": {
        "neighbor_count": 32,
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
    parser.add_argument("--configurations", default="")
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


def _run_search_task(task):
    return _run_search(*task)


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
    evaluation_budget = population_size * generation_count
    requested_population_multiplier = config.get("population_multiplier")
    if requested_population_multiplier is not None:
        maximum_population = min(
            main.POPULATION_SIZE,
            main.MAX_POPULATION_ROUTE_CELLS // number_of_places,
        )
        population_size = max(
            1,
            min(
                maximum_population,
                round(population_size * requested_population_multiplier),
            ),
        )
        generation_count = max(1, evaluation_budget // population_size)
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
        elif name == "population_multiplier":
            continue
        else:
            solver_parameters[name] = value
    solver_parameters["elite_count"] = min(
        solver_parameters["elite_count"],
        population_size,
    )

    distances = []
    elapsed_times = []
    pool = (
        multiprocessing.Pool(processes=worker_count)
        if worker_count > 1
        else None
    )
    try:
        for repeat in range(repeats):
            tasks = [
                (
                    str(csv_path),
                    population_size,
                    generations,
                    seed + repeat * 10_000 + worker,
                    solver_parameters,
                    graph_parameters,
                )
                for worker, generations in enumerate(generation_counts)
            ]
            started = time.perf_counter()
            search_results = (
                pool.map(_run_search_task, tasks)
                if pool is not None
                else [_run_search_task(task) for task in tasks]
            )
            elapsed_times.append(time.perf_counter() - started)
            distances.append(min(distance for _, distance in search_results))
    except BaseException:
        if pool is not None:
            pool.terminate()
            pool.join()
        raise
    else:
        if pool is not None:
            pool.close()
            pool.join()

    return {
        "parameters": {
            "population_size": population_size,
            "total_generations": generation_count,
            "route_evaluation_budget": population_size * generation_count,
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
    configuration_names,
    checkpoint=None,
):
    csv_path = Path("csv") / f"graph_{number_of_places}.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    configurations = {}
    for name in configuration_names:
        config = HYPERPARAMETER_CONFIGS[name]
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
        if checkpoint is not None:
            checkpoint(
                number_of_places,
                configurations,
                configuration_names,
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
    configuration_names = (
        [
            name.strip()
            for name in arguments.configurations.split(",")
            if name.strip()
        ]
        if arguments.configurations
        else list(HYPERPARAMETER_CONFIGS)
    )
    unknown_configurations = set(configuration_names) - set(
        HYPERPARAMETER_CONFIGS
    )
    if unknown_configurations:
        raise ValueError(
            "Unknown configurations: "
            + ", ".join(sorted(unknown_configurations))
        )
    if "current" not in configuration_names:
        raise ValueError("--configurations must include current.")
    if len(set(configuration_names)) != len(configuration_names):
        raise ValueError("--configurations cannot contain duplicates.")

    output_directory = Path(arguments.output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / (
        f"hyperparameter-tuning-{datetime.now():%Y%m%d-%H%M%S}.json"
    )
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
            "partition, and repeat seeds. Searches within a repeat run "
            "simultaneously in up to --workers processes, as in the solver's "
            "finite search mode."
        ),
        "status": "in_progress",
        "repeats_per_configuration": arguments.repeats,
        "worker_count": arguments.workers,
        "seed_base": arguments.seed,
        "configurations": {
            name: HYPERPARAMETER_CONFIGS[name]
            for name in configuration_names
        },
        "city_sizes": [],
    }

    def save_checkpoint(city_count=None, configs=None, selected_names=None):
        report["partial_city"] = (
            {
                "city_count": city_count,
                "configurations_completed": list(configs),
                "configurations_total": len(selected_names),
                "results": configs,
            }
            if configs is not None
            else None
        )
        checkpoint_path = report_path.with_suffix(".tmp")
        checkpoint_path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )
        checkpoint_path.replace(report_path)

    save_checkpoint()
    for city_count in city_counts:
        report["city_sizes"].append(
            optimize_city_size(
                city_count,
                arguments.repeats,
                arguments.seed,
                arguments.workers,
                configuration_names,
                checkpoint=save_checkpoint,
            )
        )
        report.pop("partial_city", None)
        save_checkpoint()

    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["status"] = "completed"
    save_checkpoint()
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
                f"wins/losses="
                f"{configuration['paired_wins_vs_current']}/"
                f"{configuration['paired_losses_vs_current']}, "
                f"median time="
                f"{configuration['elapsed_seconds']['median']:.2f}s"
            )


if __name__ == "__main__":
    main_cli()
