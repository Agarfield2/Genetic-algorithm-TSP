# Genetic algorithm TSP

Projet Python qui cherche une tournée courte pour le problème du voyageur de commerce (TSP). Chaque point représente un lieu défini par ses coordonnées `x` et `y`. Une tournée visite chaque lieu une fois et revient au point de départ `0`, par exemple `[0, 3, 1, 2, 0]`.

L'algorithme génétique est une heuristique : il cherche une bonne solution, mais ne garantit pas de trouver l'optimum global.

## Installation

Python 3 et `pip` sont nécessaires. Installez la dépendance Python du projet depuis la racine du dépôt :

```bash
python -m pip install -r requirements.txt
```

Le calcul numérique utilise NumPy. Tkinter, importé par `DaWay.py` pour l'affichage graphique, fait partie de la bibliothèque standard de Python dans la plupart des installations Windows et macOS. Sous Linux, installez le paquet Tkinter fourni par votre distribution si nécessaire.

## Données

Un fichier de données est un CSV avec les colonnes `x` et `y`, et une ligne par lieu. Les distances sont les distances euclidiennes entre les coordonnées.

Le chemin du fichier utilisé par le solveur génétique est défini par `CSV_PATH` dans [main.py](./main.py). La valeur actuelle est `csv/graph_10000.csv`. Les grands fichiers générés (`graph_*.csv`, sauf les exemples `graph_5.csv` et `graph_20.csv`) sont ignorés par Git ; il faut donc les générer localement si nécessaire.

Le générateur écrit son fichier dans le répertoire courant. Pour générer le fichier de 10 000 points attendu par défaut, lancez-le depuis le dossier `csv/` :

```bash
cd csv
python generate_graph.py 10000 --seed 42
cd ..
```

L'option `--seed 42` est facultative et permet de reproduire le même jeu de données. Retirez `--seed 42` pour obtenir des points différents à chaque génération, ou remplacez `10000` par la taille souhaitée.

## Lancer le solveur génétique

Depuis la racine du dépôt, après avoir créé ou choisi le fichier indiqué par `CSV_PATH` :

```bash
python main.py
```

Le programme charge le graphe, affiche le nombre de points, prépare les distances et lance l'optimisation. À la fin, il affiche la meilleure distance trouvée et, pour les petites instances, la tournée elle-même. Le chronométrage affiché couvre les générations d'optimisation, pas le chargement du CSV ni l'initialisation de la population.

## Comparer avec Nearest Insertion

Le script [nearest_insertion.py](./nearest_insertion.py) calcule une solution de référence avec l'heuristique Nearest Insertion. Son chemin est défini séparément par `CSV_PATH` dans ce fichier et vaut actuellement `csv/graph_100.csv`.

```bash
python nearest_insertion.py
```

Il affiche la distance, le temps de calcul et la tournée fermée. Pour comparer les deux méthodes, configurez-les avec le même fichier CSV.

## Fonctionnement du projet

- [DaWay.py](./DaWay.py) charge les points depuis le CSV, calcule les distances euclidiennes, valide les tournées et prépare des voisins candidats pour la recherche locale. Pour les graphes jusqu'à `DISTANCE_MATRIX_LIMIT`, il peut stocker une matrice complète des distances ; au-delà, les distances sont calculées à la demande afin d'éviter une matrice quadratique.
- [TSP_GA.py](./TSP_GA.py) implémente l'algorithme génétique : initialisation de la population, sélection par tournoi, croisement, mutation, conservation des meilleurs individus, suivi de diversité et recherche locale 2-opt.
- [main.py](./main.py) configure les paramètres, charge le graphe, adapte le budget de calcul à sa taille et pilote les générations.
- [nearest_insertion.py](./nearest_insertion.py) fournit l'heuristique de comparaison Nearest Insertion.
- [csv/generate_graph.py](./csv/generate_graph.py) génère des CSV de points aléatoires.
- [tests/test_tsp_ga.py](./tests/test_tsp_ga.py) contient les tests automatisés.

## Paramètres et budget de calcul

Les paramètres principaux se trouvent en haut de `main.py` :

- `GENERATIONS` et `POPULATION_SIZE` définissent les plafonds du nombre de générations et de la taille de population.
- `ELITE_COUNT` et `TOURNAMENT_SIZE` règlent la sélection et la conservation des meilleurs individus.
- `MUTATION_RATE` et `MAX_MUTATION_RATE` déterminent le taux de mutation de base et son plafond lorsque la recherche stagne.
- `STAGNATION_GENERATIONS`, `IMMIGRANT_FRACTION` et `MIN_DIVERSITY` contrôlent le renouvellement de la population en cas de stagnation ou de faible diversité.
- `LOCAL_SEARCH_RATE` et `LOCAL_SEARCH_ATTEMPTS` règlent la fréquence et le nombre d'essais de la recherche locale 2-opt.
- `FITNESS_BATCH_SIZE` limite la mémoire temporaire utilisée lors de l'évaluation groupée des tournées.
- `DISTANCE_MATRIX_LIMIT` fixe le seuil d'utilisation d'une matrice complète de distances.
- `NEIGHBOR_COUNT`, `NEIGHBOR_CELL_RADIUS` et `NEIGHBOR_SAMPLE_SIZE` règlent la recherche des voisins candidats pour 2-opt.
- `MAX_ROUTE_EVALUATIONS` et `MAX_POPULATION_ROUTE_CELLS` plafonnent respectivement le travail et la mémoire de la population pour les grands graphes.

Pour les graphes au-dessus de `DISTANCE_MATRIX_LIMIT`, `get_solver_budget` dans `main.py` réduit la taille de population et le nombre de générations en fonction du nombre de lieux et des plafonds configurés. Le budget réellement choisi est affiché au lancement.

La population initiale contient des variantes d'une tournée ordonnée selon une courbe de Hilbert et améliorée par 2-opt, ainsi que des tournées aléatoires. La recherche locale 2-opt examine un échantillon de voisins proches plutôt que toutes les paires d'arêtes. Ces stratégies rendent la recherche plus praticable sur de grands graphes, sans garantir l'optimum global. La route complète n'est pas affichée pour les grandes instances.

## Tests

Depuis la racine du dépôt :

```bash
python -m unittest discover -s tests -v
```
