# Genetic algorithm TSP

Projet Python qui cherche une tournée courte pour le problème du voyageur de commerce (TSP). Chaque point représente un lieu défini par ses coordonnées `x` et `y`. Une tournée visite chaque lieu une fois et revient au point de départ `0`, par exemple `[0, 3, 1, 2, 0]`.

L'algorithme génétique est une heuristique : il cherche une bonne solution, mais ne garantit pas de trouver l'optimum global.

Une explication détaillée des modules, des algorithmes et des tests est disponible dans [`test/code_explaination.md`](./test/code_explaination.md).
Le déroulement pas à pas de la recherche génétique, y compris le mode coopératif, est décrit dans [`test/genetique.md`](./test/genetique.md).

## Installation

Python 3 et `pip` sont nécessaires. Installez la dépendance Python du projet depuis la racine du dépôt :

```bash
python -m pip install -r requirements.txt
```

Le calcul numérique utilise NumPy. Le solveur utilise aussi `multiprocessing`, fourni avec Python, pour répartir le travail sur plusieurs coeurs ; aucune dépendance supplémentaire n'est à installer pour cela. Tkinter n'est importé que si l'affichage graphique est utilisé. Il est fourni avec la plupart des installations Python Windows et macOS ; sous Linux, installez le paquet Tkinter de votre distribution si nécessaire.

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

Pour lancer la recherche sans limite de générations, avec une population commune évoluant par générations et des descendants produits en parallèle :

```bash
python main.py --infinite
```

Les processus lisent la même population de départ de chaque génération. Le processus principal rassemble ensuite leurs descendants, supprime les doublons, complète et évalue la génération suivante. Après plus de 100 générations consécutives sans amélioration globale, le solveur recrée une population et remet le taux de mutation à sa valeur initiale, tout en conservant le meilleur trajet historique. La recherche continue jusqu'à `Ctrl+C`, puis écrit la meilleure tournée dans `best_route.csv` dans le répertoire courant. Ce mode n'a pas de limite de générations, mais la taille de population reste limitée par les paramètres de mémoire configurés dans `main.py`.

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
- [main.py](./main.py) configure les paramètres, charge le graphe, adapte le budget du mode fini et pilote les modes fini et infini.
- [parallel_evolution.py](./parallel_evolution.py) fait produire en parallèle des descendants à partir d'une même population partagée en mémoire.
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
- `RESTART_AFTER_STAGNATION` fixe le nombre de générations sans amélioration avant la réinitialisation complète de la population dans le mode `--infinite` (100 par défaut ; le redémarrage survient après ce seuil).
- `LOCAL_SEARCH_RATE` et `LOCAL_SEARCH_ATTEMPTS` règlent la fréquence et le nombre d'essais de la recherche locale 2-opt.
- `FITNESS_BATCH_SIZE` limite la mémoire temporaire utilisée lors de l'évaluation groupée des tournées.
- `DISTANCE_MATRIX_LIMIT` fixe le seuil d'utilisation d'une matrice complète de distances.
- `NEIGHBOR_COUNT`, `NEIGHBOR_CELL_RADIUS` et `NEIGHBOR_SAMPLE_SIZE` règlent la recherche des voisins candidats pour 2-opt.
- `MAX_ROUTE_EVALUATIONS` et `MAX_POPULATION_ROUTE_CELLS` plafonnent respectivement le travail et la mémoire de la population pour les grands graphes.
- `PARALLEL_WORKERS` fixe le nombre maximal de processus (4 par défaut).

Le mode par défaut est fini : pour les graphes au-dessus de `DISTANCE_MATRIX_LIMIT`, `get_solver_budget` réduit la population et les générations en fonction des plafonds configurés. Il lance plusieurs recherches indépendantes et compare leurs meilleurs résultats à la fin. Le mode `--infinite`, lui, n'applique pas de budget de générations : il fait évoluer une population commune par étapes synchronisées. Les processus créent des descendants à partir de la même population et le processus principal compose la génération suivante. Après plus de 100 générations sans progrès, il redémarre la population sans oublier le meilleur trajet historique. La taille de cette population est limitée pour contrôler la mémoire.

La population initiale contient des variantes d'une tournée ordonnée selon une courbe de Hilbert et améliorée par 2-opt, ainsi que des tournées aléatoires. La recherche locale 2-opt examine un échantillon de voisins proches plutôt que toutes les paires d'arêtes. Le solveur conserve en mémoire sa meilleure tournée et sa distance dès qu'il trouve une amélioration stricte. Le mode fini indépendant compare les meilleurs résultats à la fin ; en mode infini, une population commune est recomposée à chaque génération. À l'interruption par `Ctrl+C`, le meilleur trajet et ses coordonnées sont enregistrés dans `best_route.csv`. Ces stratégies rendent la recherche plus praticable sur de grands graphes, sans garantir l'optimum global. La route complète n'est pas affichée pour les grandes instances.

## Tests

Depuis la racine du dépôt :

```bash
python -m unittest discover -s tests -v
```
