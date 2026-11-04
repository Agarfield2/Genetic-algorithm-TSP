import csv
import random


DEFAULT_NUMBER_OF_PLACES = 500
DEFAULT_SEED = None


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
    generate_graph(DEFAULT_NUMBER_OF_PLACES, DEFAULT_SEED)
