# Genetic algorithm TSP

Projet Python de recherche d’une tournée pour le problème du voyageur de commerce (TSP). Une tournée commence et se termine au point `0`, par exemple `[0, 3, 1, 2, 0]`.

## Installation

Python 3 et `pip` sont nécessaires. Installez NumPy :

```bash
python -m pip install -r requirements.txt
```

Tkinter est fourni avec la plupart des installations Python pour Windows et macOS. Sous Linux, installez le paquet Tkinter de votre distribution si nécessaire.

## Données et exécution

Les fichiers CSV doivent contenir les colonnes `x` et `y`, une ligne par point. Le fichier utilisé se choisit avec `CSV_PATH` en haut de [main.py](./main.py); le réglage actuel est `csv/graph_20.csv`. Le nombre de points est lu automatiquement depuis ce fichier, il n’y a pas de constante `NB_LIEUX` à synchroniser.

Depuis la racine du dépôt, lancez :

```bash
python main.py
```

Le programme affiche au démarrage le nombre de points réellement chargés et le fichier utilisé.

Pour calculer une solution de référence avec l’heuristique Nearest Insertion sur `csv/graph_100.csv`, lancez séparément :

```bash
python nearest_insertion.py
```

Le script affiche la distance de la tournée, son temps de calcul et la route fermée obtenue. La distance peut être comparée à celle du calcul génétique sur le même CSV.

## Paramètres

Les hyperparamètres et principaux réglages de performance se trouvent en haut de `main.py` :

- `GENERATIONS`, `POPULATION_SIZE`, `ELITE_COUNT` et `TOURNAMENT_SIZE` règlent l’évolution.
- `MUTATION_RATE` et `MAX_MUTATION_RATE` définissent la mutation de base et son plafond adaptatif.
- `STAGNATION_GENERATIONS`, `IMMIGRANT_FRACTION` et `MIN_DIVERSITY` règlent le renouvellement de la population en cas de stagnation ou de faible diversité.
- `LOCAL_SEARCH_RATE` et `LOCAL_SEARCH_ATTEMPTS` règlent la recherche locale 2-opt échantillonnée.
- `FITNESS_BATCH_SIZE` limite la mémoire temporaire utilisée lors du calcul groupé des scores.
- `DISTANCE_MATRIX_LIMIT` fixe le nombre maximal de points pour créer une matrice complète de distances.
- `NEIGHBOR_COUNT`, `NEIGHBOR_CELL_RADIUS` et `NEIGHBOR_SAMPLE_SIZE` règlent les voisins candidats utilisés par 2-opt.
- `MAX_ROUTE_EVALUATIONS` plafonne le travail génétique pour les graphes au-dessus de `DISTANCE_MATRIX_LIMIT`.
- `MAX_POPULATION_ROUTE_CELLS` limite la mémoire utilisée par la population de grandes tournées.

## Performances et limites

- Les scores de la population sont conservés; seuls les nouveaux enfants sont évalués, par lots NumPy.
- Le croisement utilise un ensemble pour les tests d’appartenance et parcourt les villes en temps linéaire.
- La matrice complète n’est créée que sous `DISTANCE_MATRIX_LIMIT`; au-delà, les distances sont calculées sans matrice quadratique.
- La validation complète d’une tournée est disponible via `Graph.validate_route`; le calcul fréquent vérifie la forme et les indices pour éviter un contrôle de permutation répété.
- Après stagnation, le taux de mutation augmente et des tournées aléatoires peuvent être injectées.
- Le 2-opt teste seulement des candidats proches et échantillonnés, pas toutes les paires d’arêtes.
- La population contient des variantes d’une tournée initiale ordonnée par courbe de Hilbert, améliorée par plusieurs passes 2-opt, plutôt que d’être entièrement aléatoire.
- Au-dessus de `DISTANCE_MATRIX_LIMIT`, la taille de population et le nombre de générations s’adaptent au nombre de points et au budget configuré. Le programme affiche ces valeurs au démarrage.
- Pour les grandes tournées, la route complète n’est pas écrite dans la console.

Ces optimisations réduisent le temps de calcul et donnent à la recherche une tournée initiale structurée, mais ne garantissent pas l’optimum global. Comparez les distances et les temps sur vos données; vous pouvez augmenter `MAX_ROUTE_EVALUATIONS` si vous acceptez un calcul plus long.

## Tests

```bash
python -m unittest discover -s tests -v
```
