import csv
import random
import tkinter as Tk
import numpy as np

MAX_DISTANCE_MATRIX_POINTS = 250
LARGEUR = 800
HAUTEUR = 600

class Lieu:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

class Route(list):

    __slots__ = ()

    @property
    def order(self):
        return self

    @order.setter
    def order(self, places):
        self[:] = places

    @property
    def ordre(self):
        return self

    @ordre.setter
    def ordre(self, places):
        self[:] = places

    def copy(self):
        return Route(self)

def _hilbert_indices(grid):
    x = grid[:, 0].copy()
    y = grid[:, 1].copy()
    indices = np.zeros(len(grid), dtype=np.int64)
    bits = 16
    maximum = (1 << bits) - 1
    scale = 1 << (bits - 1)

    while scale:
        x_bit = (x & scale) != 0
        y_bit = (y & scale) != 0
        indices += scale * scale * (
            (3 * x_bit.astype(np.int64)) ^ y_bit.astype(np.int64)
        )
        swap = ~y_bit
        reflect = swap & x_bit
        x = np.where(reflect, maximum - x, x)
        y = np.where(reflect, maximum - y, y)
        previous_x = x.copy()
        x = np.where(swap, y, x)
        y = np.where(swap, previous_x, y)
        scale >>= 1

    return indices

class Graph:
    def __init__(
        self,
        matrix_limit=MAX_DISTANCE_MATRIX_POINTS,
        neighbor_count=16,
        neighbor_cell_radius=2,
        csv_path=None,
    ):
        if matrix_limit < 0:
            raise ValueError("matrix_limit cannot be negative.")
        if neighbor_count < 0 or neighbor_cell_radius < 0:
            raise ValueError("Neighbor search settings cannot be negative.")

        self.matrix_limit = matrix_limit
        self.neighbor_count = neighbor_count
        self.neighbor_cell_radius = neighbor_cell_radius
        self.csv_path = csv_path
        self.list_lieux: list[Lieu] = []
        self.matrice_od = None
        self.neighbor_candidates = []
        self._coordinates = np.empty((0, 2), dtype=np.float64)

    def charger_graph(self):
        if self.csv_path is None:
            raise ValueError("csv_path must be provided to load a graph.")
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
        cell_offsets = []
        for radius in range(self.neighbor_cell_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if radius and max(abs(dx), abs(dy)) != radius:
                        continue
                    cell_offsets.append((dx, dy))

        for index, (x, y) in enumerate(coordinates):
            cell_x, cell_y = point_cells[index]
            candidates = set()
            for dx, dy in cell_offsets:
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

    def space_filling_route(self):
        self._ensure_coordinates()
        number_of_places = len(self.list_lieux)
        if number_of_places == 0:
            raise ValueError("The graph must contain at least one place.")
        if number_of_places == 1:
            return Route([0, 0])

        minimums = self._coordinates.min(axis=0)
        spans = self._coordinates.max(axis=0) - minimums
        safe_spans = np.where(spans == 0, 1, spans)
        grid = np.rint(
            (self._coordinates - minimums) / safe_spans * ((1 << 16) - 1)
        ).astype(np.int64)
        hilbert_indices = _hilbert_indices(grid)
        ordered_places = np.lexsort(
            (np.arange(number_of_places), hilbert_indices)
        ).tolist()
        start = ordered_places.index(0)
        ordered_places = ordered_places[start:] + ordered_places[:start]
        route = Route(ordered_places)
        route.append(0)
        return route

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

class Affichage:
    MAX_LABELS = 150  # au-delà, on n'écrit plus les numéros des lieux

    def __init__(self, graph, best_route, best_distance, list_best_route=None):
        self.list_lieux = graph.list_lieux
        self.best_route = list(best_route)
        self.best_distance = best_distance
        self.list_best_route = [
            list(route) for route in (list_best_route or [])
        ]
        # État utilisé par l'affichage en direct (ouvrir_live).
        self.initial_distance = best_distance
        self.closed = False
        self.app = None
        self.canvas = None
        self.status = None
        self._route_line = None
        self._canvas_coordinates = []

    def _compute_canvas_coordinates(self):
        if not self.list_lieux:
            raise ValueError("Cannot display a graph without places.")

        coordinates = [(lieu.x, lieu.y) for lieu in self.list_lieux]
        min_x = min(x for x, _ in coordinates)
        max_x = max(x for x, _ in coordinates)
        min_y = min(y for _, y in coordinates)
        max_y = max(y for _, y in coordinates)
        margin = 20
        drawable_width = LARGEUR - 2 * margin
        drawable_height = HAUTEUR - 2 * margin
        x_span = max(max_x - min_x, 1)
        y_span = max(max_y - min_y, 1)
        scale = min(drawable_width / x_span, drawable_height / y_span)
        offset_x = (LARGEUR - (max_x - min_x) * scale) / 2
        offset_y = (HAUTEUR - (max_y - min_y) * scale) / 2
        return [
            (
                offset_x + (x - min_x) * scale,
                offset_y + (y - min_y) * scale,
            )
            for x, y in coordinates
        ]

    # ------------------------------------------------------------------
    # Affichage final (bloquant)
    # ------------------------------------------------------------------
    def affiche(self):
        canvas_coordinates = self._compute_canvas_coordinates()

        app = Tk.Tk()
        app.title("TSP - meilleures tournées")
        canvas = Tk.Canvas(app, width=LARGEUR, height=HAUTEUR, bg="white")
        canvas.pack()

        best_edges = {
            frozenset((place, next_place))
            for place, next_place in zip(self.best_route, self.best_route[1:])
        }
        for place, next_place in zip(self.best_route, self.best_route[1:]):
            x1, y1 = canvas_coordinates[place]
            x2, y2 = canvas_coordinates[next_place]
            canvas.create_line(x1, y1, x2, y2, fill="blue", width=3)

        route_colors = ("green", "orange", "purple", "pink", "brown")
        alternative_line_ids = []
        for route_index, route in enumerate(self.list_best_route):
            color = route_colors[route_index % len(route_colors)]
            for place, next_place in zip(route, route[1:]):
                if frozenset((place, next_place)) in best_edges:
                    continue
                x1, y1 = canvas_coordinates[place]
                x2, y2 = canvas_coordinates[next_place]
                line_id = canvas.create_line(
                    x1, y1, x2, y2, dash=(5, 5), fill=color, width=2
                )
                alternative_line_ids.append(line_id)
        for line_id in alternative_line_ids:
            canvas.itemconfigure(line_id, state="hidden")

        for place, (x, y) in enumerate(canvas_coordinates):
            canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4, fill="red", outline="red"
            )
            canvas.create_text(x, y - 10, text=str(place), fill="black")

        details = Tk.Text(app, width=60, height=5)
        details.insert(
            "end",
            f"Meilleure distance : {self.best_distance:.2f}\n"
            "Appuyez sur q pour afficher/masquer les autres meilleures tournées.\n"
            "Appuyez sur Échap pour fermer.",
        )
        details.configure(state="disabled")
        details.pack()

        alternatives_visible = False

        def toggle_alternatives(event):
            nonlocal alternatives_visible
            alternatives_visible = not alternatives_visible
            state = "normal" if alternatives_visible else "hidden"
            for line_id in alternative_line_ids:
                canvas.itemconfigure(line_id, state=state)

        app.bind_all("<KeyPress-q>", toggle_alternatives)
        app.bind_all("<KeyPress-Q>", toggle_alternatives)
        app.bind("<Escape>", lambda event: app.destroy())
        app.mainloop()

    # ------------------------------------------------------------------
    # Affichage en direct (non bloquant)
    # ------------------------------------------------------------------
    def ouvrir_live(self, generation=0):
        """Ouvre la fenêtre et affiche la tournée de départ (best_route)."""
        self._canvas_coordinates = self._compute_canvas_coordinates()

        self.closed = False
        self.app = Tk.Tk()
        self.app.title("TSP - recherche en direct")
        self.canvas = Tk.Canvas(
            self.app, width=LARGEUR, height=HAUTEUR, bg="white"
        )
        self.canvas.pack()
        self.status = Tk.Label(self.app, text="", anchor="w", justify="left")
        self.status.pack(fill="x", padx=8, pady=4)
        self.app.protocol("WM_DELETE_WINDOW", self._on_close)
        self.app.bind("<Escape>", lambda event: self._on_close())

        self._route_line = self.canvas.create_line(
            0, 0, 0, 0, fill="blue", width=2
        )
        with_labels = len(self._canvas_coordinates) <= self.MAX_LABELS
        for place, (x, y) in enumerate(self._canvas_coordinates):
            self.canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3, fill="red", outline="red"
            )
            if with_labels:
                self.canvas.create_text(x, y - 10, text=str(place))

        return self.mettre_a_jour(
            self.best_route, self.best_distance, generation
        )

    def mettre_a_jour(self, route, distance, generation):
        """Remplace la tournée affichée par la nouvelle meilleure tournée."""
        if self.closed:
            return False
        self.best_route = list(route)
        self.best_distance = distance

        flat = [
            value
            for place in route
            for value in self._canvas_coordinates[place]
        ]
        self.canvas.coords(self._route_line, *flat)

        gain = 0.0
        if self.initial_distance > 0:
            gain = (
                (self.initial_distance - distance) / self.initial_distance * 100
            )
        self.status.configure(
            text=(
                f"Génération {generation} | distance : {distance:.2f} | "
                f"départ : {self.initial_distance:.2f} | gain : {gain:.1f} %"
            )
        )
        return self.rafraichir()

    def rafraichir(self):
        """Traite les événements Tk. Renvoie False si la fenêtre est fermée."""
        if self.closed:
            return False
        try:
            self.app.update()
        except Tk.TclError:
            self.closed = True
        return not self.closed

    def attendre_fermeture(self, message=""):
        """Garde la fenêtre ouverte (bloquant) une fois la recherche finie."""
        if self.closed:
            return
        if message:
            self.status.configure(
                text=self.status.cget("text") + "\n" + message
            )
        self.app.mainloop()
        self.closed = True

    def _on_close(self):
        self.closed = True
        try:
            self.app.destroy()
        except Tk.TclError:
            pass