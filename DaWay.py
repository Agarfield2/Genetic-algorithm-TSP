import csv
import random

import numpy as np

MAX_DISTANCE_MATRIX_POINTS = 250


class Lieu:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y


class Route(list):
    """A list-compatible TSP tour, also exposed as order and ordre."""

    def __init__(self, order=()):
        super().__init__(order)

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
        self.list_lieux = []
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
