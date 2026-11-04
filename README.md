# Genetic algorithm TSP

Projet Python qui cherche une tournée courte pour le problème du voyageur de commerce (TSP). Chaque point représente un lieu défini par ses coordonnées `x` et `y`. Une tournée visite chaque lieu une fois et revient au point de départ `0`, par exemple `[0, 3, 1, 2, 0]`.

L'algorithme génétique est une heuristique : il cherche une bonne solution, mais ne garantit pas de trouver l'optimum global.

Une explication détaillée des modules, des algorithmes et des tests est disponible dans [`test/code_explaination.md`](./test/code_explaination.md).

## Installation

Python 3 et `pip` sont nécessaires. Installez la dépendance Python du projet depuis la racine du dépôt :

```bash
python -m pip install -r requirements.txt
```

Le calcul numérique utilise NumPy. Le solveur utilise aussi `multiprocessing`, fourni avec Python, pour lancer jusqu'à quatre recherches indépendantes sur plusieurs coeurs ; aucune dépendance supplémentaire n'est à installer pour cela. Tkinter n'est importé que si l'affichage graphique est utilisé. Il est fourni avec la plupart des installations Python Windows et macOS ; sous Linux, installez le paquet Tkinter de votre distribution si nécessaire.

## Données

Un fichier de données est un CSV avec les colonnes `x` et `y`, et une ligne par lieu. Les distances sont les distances euclidiennes entre les coordonnées.

Le chemin du fichier utilisé par le solveur génétique est défini par `CSV_PATH` dans [main.py](./main.py). La valeur actuelle est `csv/graph_10000.csv`. Les grands fichiers générés (`graph_*.csv`, sauf les exemples `graph_5.csv` et `graph_20.csv`) sont ignorés par Git ; il faut donc les générer localement si nécessaire.

Le générateur écrit un CSV de 10 000 points dans le répertoire courant par défaut. Pour le créer dans `csv/` :

```bash
cd csv
python generate_graph.py
cd ..
```

Pour changer le nombre de points ou fixer une graine aléatoire afin de reproduire les données, modifiez `DEFAULT_NUMBER_OF_PLACES` et `DEFAULT_SEED` dans [csv/generate_graph.py](./csv/generate_graph.py). Pour lancer ensuite le solveur sur ces données, choisissez leur chemin dans `CSV_PATH` dans `main.py`.

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
- [TSP_GA.py](./TSP_GA.py) expose le solveur génétique, ses paramètres, le calcul des scores et le suivi de la meilleure solution.
- [genetic_evolution.py](./genetic_evolution.py) initialise la population et construit les générations suivantes.
- [genetic_operators.py](./genetic_operators.py) contient la sélection, le croisement, la mutation et l'amélioration locale 2-opt.
- [route_population.py](./route_population.py) construit les tournées et empêche les cycles dupliqués ; une tournée et son parcours inversé sont considérés comme le même cycle. Si le graphe ne permet pas assez de cycles distincts, la population est réduite au nombre de cycles possibles.
- [main.py](./main.py) configure les paramètres, charge le graphe, adapte le budget de calcul à sa taille et pilote les générations.
- [nearest_insertion.py](./nearest_insertion.py) fournit l'heuristique de comparaison Nearest Insertion.
- [csv/generate_graph.py](./csv/generate_graph.py) génère des CSV de points aléatoires.
- [tests/test_tsp_ga.py](./tests/test_tsp_ga.py) contient les tests automatisés.
- [test_heuristique.py](./test_heuristique.py) compare plusieurs heuristiques de tournée sur les CSV `graph_5.csv`, `graph_20.csv` et `graph_100.csv`.

Pour afficher le tableau comparatif des heuristiques :

```bash
python test_heuristique.py
```

Le tableau donne la distance et le temps de calcul sur chaque jeu de points. Christofides utilise un appariement exact et est donc volontairement limité aux instances où le nombre de sommets impairs du MST reste petit. Le 3-opt explore toutes les coupures sur les petits jeux et échantillonne les coupures sur les plus grands. Lin-Kernighan est une recherche à échanges séquentiels bornée par les paramètres du script ; Chained Lin-Kernighan relance cette recherche après des perturbations double-bridge. Les résultats servent à comparer les heuristiques sur ces exemples, pas à garantir leur classement sur des jeux ou graines différents.

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
- `PARALLEL_WORKERS` fixe le nombre maximal de recherches indépendantes lancées en parallèle (4 par défaut pour une machine à quatre coeurs).

Pour les graphes au-dessus de `DISTANCE_MATRIX_LIMIT`, `get_solver_budget` dans `main.py` réduit la taille de population et le nombre de générations en fonction du nombre de lieux et des plafonds configurés. Le budget réellement choisi est affiché au lancement. Les générations sont réparties entre des recherches indépendantes : leur total reste identique au budget, et le meilleur résultat final est conservé. Cette stratégie parallélise le travail Python lié à la sélection, au croisement et aux mutations, que les threads ne répartiraient pas efficacement sur plusieurs coeurs dans Python standard.

La population initiale contient des variantes d'une tournée ordonnée selon une courbe de Hilbert et améliorée par 2-opt, ainsi que des tournées aléatoires. La recherche locale 2-opt examine un échantillon de voisins proches plutôt que toutes les paires d'arêtes. Chaque solveur conserve en mémoire sa meilleure tournée et sa distance dès qu'il trouve une amélioration stricte. En mode parallèle, chaque processus garde son propre meilleur résultat ; le processus principal compare ces résultats à la fin des recherches. Aucun historique des améliorations n'est actuellement écrit sur disque. Ces stratégies rendent la recherche plus praticable sur de grands graphes, sans garantir l'optimum global. La route complète n'est pas affichée pour les grandes instances.

## Tests

Depuis la racine du dépôt :

```bash
python -m unittest discover -s tests -v
```
