
import csv
import random
import argparse


def generate_graph(n, seed=None):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Générateur de graphes CSV"
    )

    parser.add_argument(
        "n",
        type=int,
        help="Nombre de points à générer"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Graine aléatoire (optionnelle)"
    )

    args = parser.parse_args()

    generate_graph(args.n, args.seed)
