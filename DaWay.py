import csv
from pathlib import Path
from tkinter import Canvas, Text, Tk

import numpy as np

NB_LIEUX = 20
MAX_DISTANCE_MATRIX_POINTS = 250
LARGEUR = 800
HAUTEUR = 600


class Lieu:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y


class Graph:
    def __init__(self, csv_path=None, matrix_limit=MAX_DISTANCE_MATRIX_POINTS):
        self.csv_path = Path(csv_path) if csv_path is not None else (
            Path(__file__).resolve().parent / "csv" / f"graph_{NB_LIEUX}.csv"
        )
        self.matrix_limit = matrix_limit
        self.list_lieux = []
        self.matrice_od = None
        self._coordinates = np.empty((0, 2), dtype=np.float64)

    def charger_graph(self, csv_path=None):
        path = Path(csv_path) if csv_path is not None else self.csv_path
        with path.open(newline="", encoding="utf-8") as data:
            reader = csv.DictReader(data)
            if not reader.fieldnames or not {"x", "y"}.issubset(reader.fieldnames):
                raise ValueError(f"CSV must contain x and y columns: {path}")
            self.list_lieux = [
                Lieu(float(row["x"]), float(row["y"])) for row in reader
            ]

        self._refresh_coordinates()
        self.matrice_od = None
        return self.list_lieux

    def _refresh_coordinates(self):
        self._coordinates = np.asarray(
            [(place.x, place.y) for place in self.list_lieux],
            dtype=np.float64,
        ).reshape((-1, 2))

    def calcul_matrice_cout_od(self):
        number_of_places = len(self.list_lieux)
        if number_of_places > self.matrix_limit:
            self.matrice_od = None
            return None

        if len(self._coordinates) != number_of_places:
            self._refresh_coordinates()

        delta_x = self._coordinates[:, 0, None] - self._coordinates[None, :, 0]
        delta_y = self._coordinates[:, 1, None] - self._coordinates[None, :, 1]
        self.matrice_od = np.hypot(delta_x, delta_y)
        return self.matrice_od

    def plus_proche_voisin(self, lieu, visites):
        visited = visites if isinstance(visites, set) else set(visites)
        min_distance = float("inf")
        nearest_lieu = None
        for i, other_lieu in enumerate(self.list_lieux):
            if i not in visited:
                distance = np.hypot(lieu.x - other_lieu.x, lieu.y - other_lieu.y)
                if distance < min_distance:
                    min_distance = distance
                    nearest_lieu = i
        return nearest_lieu

    def validate_route(self, route):
        number_of_places = len(self.list_lieux)
        if (
            number_of_places == 0
            or len(route) != number_of_places + 1
            or route[0] != 0
            or route[-1] != 0
            or set(route[:-1]) != set(range(number_of_places))
        ):
            raise ValueError(
                "A route must visit every place once and return to place 0."
            )
        return True

    def calcul_distance_route(self, route):
        number_of_places = len(self.list_lieux)
        if (
            number_of_places == 0
            or len(route) != number_of_places + 1
            or route[0] != 0
            or route[-1] != 0
        ):
            raise ValueError(
                "A route must start and end at place 0 and include every place."
            )

        if len(self._coordinates) != number_of_places:
            self._refresh_coordinates()

        indices = np.asarray(route, dtype=np.intp)
        if self.matrice_od is not None:
            return float(self.matrice_od[indices[:-1], indices[1:]].sum())

        route_coordinates = self._coordinates[indices]
        segments = np.diff(route_coordinates, axis=0)
        return float(np.hypot(segments[:, 0], segments[:, 1]).sum())


class Route:
    ordre = []


class Affichage:
    def affiche(self):
        app = Tk()
        canvas = Canvas(app, width=LARGEUR, height=HAUTEUR)
        zone_de_texte = Text(app, width=50, height=50)
        canvas.pack()
        zone_de_texte.pack()
        app.mainloop()
