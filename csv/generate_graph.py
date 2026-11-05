import csv
import argparse
import random


DEFAULT_NUMBER_OF_PLACES = 500
DEFAULT_SEED = None


def generate_graph(n, seed=None):
    if n < 1:
        raise ValueError("The number of places must be greater than zero.")
    random.seed(seed)

    filename = f"graph_{n}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # En-tête du CSV
        writer.writerow(["x", "y"])

        # Génération des n points
        for _ in range(n):
            x = random.uniform(0, 800)
            y = random.uniform(0, 600)

            writer.writerow([x, y])

    print(f"Fichier {filename} généré avec {n} points.")


def positive_integer(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a CSV of random places.")
    parser.add_argument(
        "n",
        nargs="?",
        type=positive_integer,
        default=DEFAULT_NUMBER_OF_PLACES,
        help=f"number of places (default: {DEFAULT_NUMBER_OF_PLACES})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="optional random seed for reproducible coordinates",
    )
    args = parser.parse_args()
    generate_graph(args.n, args.seed)
