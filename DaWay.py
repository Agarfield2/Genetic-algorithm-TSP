import numpy as np
from tkinter import Canvas, Text, Tk
import csv

NB_LIEUX = 100
MAX_DISTANCE_MATRIX_POINTS = 250
LARGEUR = 800
HAUTEUR = 600

class Lieu:
    x = 0
    y = 0
    def distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

class Graph:
    def __init__(
        self,
        matrix_limit=MAX_DISTANCE_MATRIX_POINTS,
        neighbor_count=16,
        neighbor_cell_radius=2,
        neighbor_sample_size=128,
        csv_path=None,
    ):
        if matrix_limit < 0:
            raise ValueError("matrix_limit cannot be negative.")
        if neighbor_count < 0 or neighbor_cell_radius < 0 or neighbor_sample_size < 0:
            raise ValueError("Neighbor search settings cannot be negative.")

        self.matrix_limit = matrix_limit
        self.neighbor_count = neighbor_count
        self.neighbor_cell_radius = neighbor_cell_radius
        self.neighbor_sample_size = neighbor_sample_size
        self.csv_path = csv_path or f"csv/graph_{NB_LIEUX}.csv"
        self.list_lieux = []
        self.matrice_od = None
        self.neighbor_candidates = []
        self._coordinates = np.empty((0, 2), dtype=np.float64)

    def charger_graph(self):
        with open(self.csv_path, newline="", encoding="utf-8") as data:
            lecteur_csv = csv.DictReader(data)
            if not lecteur_csv.fieldnames or not {"x", "y"}.issubset(
                lecteur_csv.fieldnames
            ):
                raise ValueError("The CSV file must contain x and y columns.")

            self.list_lieux = [
                Lieu(float(ligne["x"]), float(ligne["y"]))
                for ligne in lecteur_csv
            ]

        self._coordinates = np.asarray(
            [(lieu.x, lieu.y) for lieu in self.list_lieux],
            dtype=np.float64,
        ).reshape((-1, 2))
        self.matrice_od = None
        self.neighbor_candidates = []
        return self.list_lieux

    def _ensure_coordinates(self):
        if self._coordinates.shape[0] != len(self.list_lieux):
            self._coordinates = np.asarray(
                [(lieu.x, lieu.y) for lieu in self.list_lieux],
                dtype=np.float64,
            ).reshape((-1, 2))

    def calcul_matrice_cout_od(self):
        self._ensure_coordinates()
        number_of_places = len(self.list_lieux)
        if number_of_places <= self.matrix_limit:
            delta_x = (
                self._coordinates[:, 0, None] - self._coordinates[None, :, 0]
            )
            delta_y = (
                self._coordinates[:, 1, None] - self._coordinates[None, :, 1]
            )
            self.matrice_od = np.hypot(delta_x, delta_y)
        else:
            self.matrice_od = None

        self._build_neighbor_candidates()
        return self.matrice_od

    def _build_neighbor_candidates(self):
        number_of_places = len(self.list_lieux)
        self.neighbor_candidates = [[] for _ in range(number_of_places)]
        if number_of_places < 2 or self.neighbor_count < 1:
            return

        coordinates = self._coordinates
        minimums = coordinates.min(axis=0)
        spans = coordinates.max(axis=0) - minimums
        cell_size = max(float(spans.max()) / max(number_of_places**0.5, 1), 1e-12)
        cells = {}
        point_cells = []
        for index, (x, y) in enumerate(coordinates):
            cell = (
                int((x - minimums[0]) / cell_size),
                int((y - minimums[1]) / cell_size),
            )
            point_cells.append(cell)
            cells.setdefault(cell, []).append(index)

        candidate_limit = max(self.neighbor_count * 8, self.neighbor_count)
        for index, (x, y) in enumerate(coordinates):
            cell_x, cell_y = point_cells[index]
            candidates = set()
            for radius in range(self.neighbor_cell_radius + 1):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if radius and max(abs(dx), abs(dy)) != radius:
                            continue
                        bucket = cells.get((cell_x + dx, cell_y + dy), ())
                        remaining = candidate_limit - len(candidates)
                        if remaining <= 0:
                            break
                        if len(bucket) <= remaining + 1:
                            available = [
                                place for place in bucket if place != index
                            ]
                        else:
                            available = [
                                place
                                for place in random.sample(
                                    bucket,
                                    min(len(bucket), remaining + 1),
                                )
                                if place != index
                            ]
                        candidates.update(available)
                    if len(candidates) >= candidate_limit:
                        break
                if len(candidates) >= candidate_limit:
                    break

            if len(candidates) < self.neighbor_count:
                fallback_count = min(
                    self.neighbor_sample_size,
                    number_of_places - len(candidates) - 1,
                )
                if fallback_count > 0:
                    candidates.update(
                        place
                        for place in random.sample(
                            range(number_of_places), fallback_count
                        )
                        if place != index
                    )

            ranked = sorted(
                candidates,
                key=lambda place: (
                    (coordinates[place, 0] - x) ** 2
                    + (coordinates[place, 1] - y) ** 2
                ),
            )
            self.neighbor_candidates[index] = ranked[: self.neighbor_count]

    def distance_between(self, first, second):
        self._ensure_coordinates()
        if self.matrice_od is not None:
            return float(self.matrice_od[first, second])

        delta_x = self._coordinates[first, 0] - self._coordinates[second, 0]
        delta_y = self._coordinates[first, 1] - self._coordinates[second, 1]
        return float(np.hypot(delta_x, delta_y))

    def plus_proche_voisin(self, lieu, visites):
        visited = visites if isinstance(visites, set) else set(visites)
        nearest_lieu = None
        min_distance = float("inf")
        for index, other_lieu in enumerate(self.list_lieux):
            if index not in visited:
                distance = np.hypot(
                    lieu.x - other_lieu.x,
                    lieu.y - other_lieu.y,
                )
                if distance < min_distance:
                    nearest_lieu = index
                    min_distance = distance
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

    def calcul_distances_routes(self, routes, batch_size=16):
        self._ensure_coordinates()
        number_of_places = len(self.list_lieux)
        if number_of_places == 0:
            raise ValueError("The graph must contain at least one place.")
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero.")

        results = []
        for offset in range(0, len(routes), batch_size):
            batch = np.asarray(routes[offset : offset + batch_size])
            if (
                batch.ndim != 2
                or batch.shape[1] != number_of_places + 1
                or not np.issubdtype(batch.dtype, np.integer)
                or np.any(batch[:, 0] != 0)
                or np.any(batch[:, -1] != 0)
                or np.any(batch < 0)
                or np.any(batch >= number_of_places)
            ):
                raise ValueError(
                    "Routes must start and end at place 0 and include every place."
                )
            batch = batch.astype(np.intp, copy=False)

            if self.matrice_od is not None:
                costs = self.matrice_od[batch[:, :-1], batch[:, 1:]].sum(axis=1)
            else:
                x = self._coordinates[batch, 0]
                y = self._coordinates[batch, 1]
                costs = np.hypot(np.diff(x, axis=1), np.diff(y, axis=1)).sum(axis=1)
            results.extend(costs.tolist())
        return results

    def calcul_distance_route(self, route):
        return self.calcul_distances_routes([route])[0]

    
class Route:
    ordre = []

class Affichage:
    def __init__(self, graph, best_route, best_distance, list_best_route):
        self.list_lieux = graph.list_lieux
        self.best_route = best_route
        self.best_distance = best_distance
        self.list_best_route = list_best_route

    def affiche(self):
        app=Tk()
        canvas=Canvas(app,width=LARGEUR,height=HAUTEUR)
        for lieu in self.list_lieux:
            if lieu.x < LARGEUR and lieu.y < HAUTEUR and lieu.y > 0 and lieu.x > 0:
                canvas.create_oval(lieu.x-5, lieu.y-5, lieu.x+5, lieu.y+5, fill="red")
        meilleur_route = self.best_route
        compteur=0
        for meilleur in meilleur_route:
            lieu1 = self.list_lieux[meilleur]
            canvas.create_text(lieu1.x, lieu1.y - 10, text=str(compteur))
            compteur += 1
            lieu2 = self.list_lieux[meilleur_route[(meilleur_route.index(meilleur)+1)]]
            canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,  dash=(4, 8), fill="blue", width=3)
        Zone_de_texte=Text(app,width=50,height=50)
        Zone_de_texte.insert(END, "Performances :\n")#ajout dans la zone de texte 
        def esc(event):
            print("20/20")
            app.destroy()


        def action(event):
<<<<<<< HEAD
            for liste in self.list_best_route:
=======
            for x, liste in enumerate(self.list_best_route):
>>>>>>> pol
                for j in range(len(liste)-1):
                    a = liste[j]
                    b = liste[(j+1)]    
                    val = False     # boucle sur le segment
                    for i in range(len(meilleur_route)-1):  # boucle sur le meilleur chemin
                        if (a == meilleur_route[i] and b == meilleur_route[i+1]):
                            val = True
                            break
                    if val== True:
                        val = False
                        continue                            # déjà dessiné en bleu
                    lieu1 = self.list_lieux[a]
                    lieu2 = self.list_lieux[b]
<<<<<<< HEAD
                    canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="gray", width=2)
=======
                    if x == 0:
                        canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="green", width=2)
                    elif x == 1:
                        canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="orange", width=2)
                    elif x == 2:
                        canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="purple", width=2)
                    else:
                        canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="pink", width=2)
>>>>>>> pol


        app.bind("q", action) 
           # Entrée
        app.bind("<Escape>", esc)

        canvas.pack()
        Zone_de_texte.pack()
        app.mainloop()
        #pour chaque lieu du graphe on creer un cercle compris dans la fenetre 
    
