# Genetic algorithm TSP

Projet Python de recherche d’une tournée pour le problème du voyageur de commerce (TSP). Une tournée commence et se termine au point `0`, par exemple `[0, 3, 1, 2, 0]`.

## Installation

Python 3 et `pip` sont nécessaires. Installez NumPy :

```bash
python -m pip install -r requirements.txt
```

Tkinter est fourni avec la plupart des installations Python pour Windows et macOS. Sous Linux, installez le paquet Tkinter de votre distribution si nécessaire.

## Données et exécution

Les fichiers CSV doivent contenir les colonnes `x` et `y`, une ligne par point. Le fichier utilisé se choisit avec `CSV_PATH` en haut de [main.py](./main.py); le réglage actuel est `csv/graph_100.csv`.

Depuis la racine du dépôt, lancez :

```bash
python main.py
```

Le programme affiche au démarrage le nombre de points réellement chargés et le fichier utilisé.

## Paramètres

Les hyperparamètres et principaux réglages de performance se trouvent en haut de `main.py` :

- `GENERATIONS`, `POPULATION_SIZE`, `ELITE_COUNT` et `TOURNAMENT_SIZE` règlent l’évolution.
- `MUTATION_RATE` et `MAX_MUTATION_RATE` définissent la mutation de base et son plafond adaptatif.
- `STAGNATION_GENERATIONS`, `IMMIGRANT_FRACTION` et `MIN_DIVERSITY` règlent le renouvellement de la population en cas de stagnation ou de faible diversité.
- `LOCAL_SEARCH_RATE` et `LOCAL_SEARCH_ATTEMPTS` règlent la recherche locale 2-opt échantillonnée.
- `FITNESS_BATCH_SIZE` limite la mémoire temporaire utilisée lors du calcul groupé des scores.
- `DISTANCE_MATRIX_LIMIT` fixe le nombre maximal de points pour créer une matrice complète de distances.
- `NEIGHBOR_COUNT`, `NEIGHBOR_CELL_RADIUS` et `NEIGHBOR_SAMPLE_SIZE` règlent les voisins candidats utilisés par 2-opt.

## Performances et limites

- Les scores de la population sont conservés; seuls les nouveaux enfants sont évalués, par lots NumPy.
- Le croisement utilise un ensemble pour les tests d’appartenance et parcourt les villes en temps linéaire.
- La matrice complète n’est créée que sous `DISTANCE_MATRIX_LIMIT`; au-delà, les distances sont calculées sans matrice quadratique.
- La validation complète d’une tournée est disponible via `Graph.validate_route`; le calcul fréquent vérifie la forme et les indices pour éviter un contrôle de permutation répété.
- Après stagnation, le taux de mutation augmente et des tournées aléatoires peuvent être injectées.
- Le 2-opt teste seulement des candidats proches et échantillonnés, pas toutes les paires d’arêtes.
- Pour les grandes tournées, la route complète n’est pas écrite dans la console.

Ces optimisations réduisent certains coûts mais ne rendent pas instantanée une recherche sur 10 000 points. Une population de 1 000 tournées de cette taille demande beaucoup de temps et de mémoire; adaptez `POPULATION_SIZE` et `GENERATIONS` à la machine et mesurez les résultats sur vos données.

## Tests

```bash
python -m unittest discover -s tests -v
```
