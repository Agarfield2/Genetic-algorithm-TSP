# Explication complète du projet Genetic Algorithm TSP

## 1. Objectif et vocabulaire

Le projet cherche une tournée courte pour le problème du voyageur de commerce
(TSP, *Traveling Salesperson Problem*). Chaque ligne du CSV représente un lieu
repéré par ses coordonnées `x` et `y`. La distance entre deux lieux est leur
distance euclidienne.

Une tournée valide passe par chaque lieu exactement une fois et revient au
lieu `0`. Pour quatre lieux, une tournée possible est `[0, 2, 1, 3, 0]`. Son
coût est la somme des distances de chaque paire de lieux consécutifs, retour au
départ compris.

Le programme utilise un algorithme génétique et des heuristiques de recherche
locale. Ces méthodes produisent de bonnes solutions, mais ne garantissent pas
de trouver l'optimum global.

Pour le déroulement pas à pas de l'algorithme génétique, de la population
initiale jusqu'au résultat final, voir [`genetique.md`](./genetique.md).

## 2. Vue d'ensemble des fichiers

| Fichier | Responsabilité |
|---|---|
| [`main.py`](../main.py) | Paramètres, chargement des données, budget de calcul, lancement séquentiel ou parallèle et affichage du résultat. |
| [`DaWay.py`](../DaWay.py) | Classes `Lieu`, `Route` et `Graph`, chargement CSV, distances, candidats voisins et validation des tournées. |
| [`TSP_GA.py`](../TSP_GA.py) | Classe publique du solveur génétique, paramètres, évaluation des scores et conservation du meilleur résultat. |
| [`genetic_evolution.py`](../genetic_evolution.py) | Création de la population initiale et construction des générations suivantes. |
| [`genetic_operators.py`](../genetic_operators.py) | Sélection, croisement, mutation et recherche locale 2-opt. |
| [`route_population.py`](../route_population.py) | Création de tournées et déduplication des cycles. |
| [`parallel_evolution.py`](../parallel_evolution.py) | Production parallèle des descendants à partir d'une population partagée en mode infini. |
| [`csv/generate_graph.py`](../csv/generate_graph.py) | Génération d'un jeu de points aléatoires au format CSV. |
| [`tests/test_tsp_ga.py`](../tests/test_tsp_ga.py) | Tests unitaires du graphe, du solveur et du programme principal. |
| [`requirements.txt`](../requirements.txt) | Dépendances Python externes ; actuellement NumPy. |

`multiprocessing`, `csv`, `random`, `time`, `argparse` et `itertools` sont
fournis par Python. NumPy est la seule bibliothèque externe déclarée dans
`requirements.txt`.

## 3. Format des données et commandes courantes

Un CSV de graphe possède un en-tête `x,y`, puis une ligne par lieu, par exemple :

```csv
x,y
100.0,250.0
700.0,400.0
```

Depuis la racine du dépôt :

```bash
python -m pip install -r requirements.txt
python main.py
```

Le fichier du solveur principal est sélectionné par `CSV_PATH` dans
`main.py`. Sa valeur actuelle est `csv/graph_100.csv`. Le chemin est relatif au
répertoire courant, donc lancer le programme depuis la racine du dépôt est
important.

Le générateur peut être exécuté depuis le dossier `csv` :

```bash
cd csv
python generate_graph.py 50 --seed 42
```

Cela crée `graph_50.csv` avec 50 points. `--seed` est facultatif : une graine
fixe rend les données reproductibles. Sans argument de taille, le générateur
utilise `DEFAULT_NUMBER_OF_PLACES` (10 000). La fonction refuse les tailles
inférieures à un lieu.

## 4. Chargement du graphe et calcul des distances — `DaWay.py`

### 4.1 `Lieu`

`Lieu` est un petit objet contenant les coordonnées `x` et `y` d'un point.
L'indice du lieu dans `Graph.list_lieux` sert d'identifiant entier dans les
tournées.

### 4.2 `Route`

`Route` est une sous-classe de `list` qui stocke l'ordre des indices de lieux
dans une tournée. Elle reste compatible avec les accès et modifications par
indice utilisés par le solveur génétique. Les alias `route.order` et
`route.ordre` renvoient la même séquence ; les copies avec `route.copy()` sont
des objets `Route` indépendants. Les populations, les descendants et la
meilleure solution du solveur utilisent cette classe.

### 4.3 `Graph.charger_graph`

Le constructeur de `Graph` reçoit le chemin du CSV et les paramètres de
voisinage et de matrice. `charger_graph()` :

1. vérifie qu'un chemin a été fourni ;
2. lit le CSV avec `csv.DictReader` ;
3. vérifie la présence des colonnes `x` et `y` ;
4. convertit ces colonnes en nombres réels et crée les `Lieu` ;
5. copie les coordonnées dans un tableau NumPy de forme `(nombre_de_lieux, 2)`.

Après un nouveau chargement, la matrice de distances et les voisins précédents
sont invalidés.

### 4.4 Matrice et distances à la demande

`calcul_matrice_cout_od()` prépare les structures de calcul :

- si le nombre de lieux est inférieur ou égal à `matrix_limit`, NumPy calcule
  une matrice carrée des distances entre chaque paire ;
- au-delà de cette limite, la matrice complète n'est pas allouée et les
  distances seront calculées à la demande ;
- dans les deux cas, la méthode prépare les voisins candidats utilisés par la
  recherche 2-opt. Cette recherche s'appuie uniquement sur les cellules
  locales ; aucun échantillon global n'est ajouté si elles fournissent trop
  peu de candidats.

La matrice complète prend une mémoire proportionnelle au carré du nombre de
lieux. Éviter cette matrice est important pour les grandes instances.

`distance_between(a, b)` renvoie la distance entre deux indices. Elle utilise
la matrice si elle existe, sinon calcule `hypot(dx, dy)` directement.

`calcul_distances_routes(routes, batch_size)` calcule en lots les coûts d'une
liste de tournées. Il contrôle que chaque ligne a la bonne longueur, commence
et termine à `0`, et contient des indices entiers dans les limites du graphe.
Le calcul vectorisé évite une boucle Python pour chaque arête. Cette validation
contrôle la forme et les bornes, mais `validate_route()` est la méthode qui
vérifie aussi que tous les lieux apparaissent une fois.

`calcul_distance_route(route)` est le raccourci pour calculer le coût d'une
seule tournée.

### 4.5 Voisins candidats

`_build_neighbor_candidates()` découpe l'espace des coordonnées en cellules
spatiales. Pour chaque lieu, elle collecte des lieux des cellules proches,
échantillonne les cellules trop remplies, puis classe les candidats par
distance et les limite à `neighbor_count`. Elle n'ajoute pas d'échantillon
global lorsque les cellules proches fournissent trop peu de candidats.

Cette liste est une approximation pratique des voisins les plus proches, pas
une recherche exhaustive des voisins exacts. Elle permet à 2-opt d'examiner
moins de changements sur les grandes instances.

### 4.6 Tournée Hilbert et validation

`space_filling_route()` normalise les coordonnées sur une grille entière,
calcule un indice de courbe de Hilbert avec `_hilbert_indices()`, trie les lieux
selon cet indice, puis fait pivoter l'ordre pour commencer par le lieu `0`.
La courbe de Hilbert tend à placer les points géographiquement proches près les
uns des autres dans la séquence. La méthode renvoie une instance de `Route`,
fermée en ajoutant `0` à la fin.

`validate_route()` vérifie que la tournée :

- contient exactement un élément de plus que le nombre de lieux ;
- commence et finit à `0` ;
- visite chaque indice du graphe une fois avant le retour.

Elle lève `ValueError` si la tournée n'est pas valide.

## 5. Solveur génétique — `TSP_GA.py`

`TSP_GA` est l'API du solveur. Elle hérite des fonctions d'évolution, des
opérateurs génétiques et des utilitaires de population définis dans les autres
modules. Le guide détaillé de son fonctionnement, de l'initialisation à la fin
de la recherche, se trouve dans [`genetique.md`](./genetique.md).

Le constructeur vérifie les paramètres (tailles positives, taux entre 0 et 1,
etc.) puis conserve :

- `population` : les tournées de la génération courante ;
- `_fitness` : leurs distances, alignées par indice avec la population ;
- `_best_route` et `_best_distance` : meilleure solution globale trouvée par
  cette instance ;
- `generations_without_improvement` : compteur de stagnation ;
- `current_mutation_rate` : taux de mutation utilisé actuellement.

Une distance plus petite représente une solution meilleure.

`_calculate_fitness()` évalue les tournées, de préférence par lots.
`_update_global_best()` copie toute amélioration stricte afin de la conserver
malgré le remplacement des générations. `best_solution()` renvoie une copie
du meilleur trajet et son score.

`genetic_evolution.py` assemble les étapes : initialisation hybride à partir
d'une tournée Hilbert, variantes mutées et routes aléatoires, puis création
des générations successives. `genetic_operators.py` fournit sélection,
croisement, mutation et recherche locale 2-opt. `route_population.py` assure
l'unicité des cycles, en considérant une tournée et son inverse comme le même
cycle. Les détails et un exemple d'exécution sont présentés dans le guide
dédié.

## 6. Programme principal et parallélisme — `main.py`

### Paramètres

Les constantes au début de `main.py` définissent le CSV, la population, les
générations, les opérateurs, le voisinage, les plafonds de calcul et le nombre
de processus (`PARALLEL_WORKERS = 4`).

### Budget

`get_solver_budget(number_of_places)` refuse un graphe vide. Jusqu'à
`DISTANCE_MATRIX_LIMIT`, il retourne les plafonds standards. Pour les graphes
plus grands, il limite le produit population × générations selon :

- `MAX_ROUTE_EVALUATIONS`, lié au nombre de lieux dans les tournées ;
- `MAX_POPULATION_ROUTE_CELLS`, qui limite la mémoire utilisée par la
  population ;
- les maxima globaux configurés.

Le programme affiche la population et le nombre de générations effectivement
choisis.

### Mode fini

`_create_graph()` et `_create_solver()` construisent les objets avec les
paramètres de configuration.

`_split_generations()` répartit les générations entre les travailleurs, en
distribuant le reste aux premiers processus. `_run_parallel_search()` reçoit
un nombre de générations et une graine, crée son propre graphe et son propre
solveur, puis effectue une recherche indépendante.

Dans le mode fini par défaut, un seul travailleur exécute une recherche dans
le processus principal. Avec plusieurs travailleurs, `multiprocessing.Pool`
lance plusieurs recherches indépendantes ; elles ne partagent pas leurs
populations et le processus principal compare leurs meilleurs résultats à la
fin.

### Mode coopératif sans limite de générations

`python main.py --infinite` lance une population unique qui continue jusqu'à
`Ctrl+C`. `parallel_evolution.py` permet aux processus de lire le même état de
population et de scores depuis des tableaux en mémoire partagée. Chaque
processus produit un lot de descendants à partir de cette population. Après la
fin des tâches, le processus principal rassemble les enfants, élimine les
cycles en double, complète et évalue la génération suivante.

Après plus de `RESTART_AFTER_STAGNATION` générations consécutives sans
amélioration globale, le mode infini recrée la population et remet le taux de
mutation à sa valeur initiale. Le meilleur historique est conservé pendant
cette réinitialisation.

Il n'y a pas de limite de générations dans ce mode, mais la taille de la
population est limitée par `POPULATION_SIZE` et `MAX_POPULATION_ROUTE_CELLS`
pour contrôler la mémoire. À l'interruption par `Ctrl+C`, le meilleur trajet,
ses coordonnées et sa distance sont écrits dans `best_route.csv`.

La condition `if __name__ == "__main__":` empêche le lancement automatique de
`main()` lors d'un import. C'est également nécessaire au bon fonctionnement du
`multiprocessing` avec le mode de démarrage Windows.

## 7. Tests du projet

Depuis la racine du dépôt :

```bash
python -m unittest discover -s tests -v
```

`tests/test_tsp_ga.py` vérifie notamment :

- que les routes sont fermées et couvrent les lieux ;
- que croisement et mutation préservent les permutations ;
- qu'aucun cycle dupliqué n'entre dans la population, y compris à l'envers ;
- que la reproduction conserve les élites et calcule les scores attendus ;
- que le meilleur global est mis à jour et retourné en copie ;
- que 2-opt améliore un exemple contrôlé ;
- que la matrice, les distances, le budget et le chargement CSV respectent leurs
  contraintes ;
- que le programme principal ne s'exécute pas lors d'un import.

Les tests démontrent les propriétés qu'ils vérifient sur leurs cas d'essai ;
ils ne garantissent pas la qualité optimale d'une tournée sur tout jeu de
données.

## 10. Limites importantes à garder en tête

- En mode fini, le meilleur résultat reste en mémoire et n'est pas sauvegardé
  dans un fichier. En mode `--infinite`, il est écrit en CSV lors d'un arrêt
  propre par `Ctrl+C`.
- Les recherches parallèles du mode fini sont indépendantes. Le mode
  `--infinite` fait évoluer une seule population partagée entre générations.
- La recherche 2-opt du solveur principal est échantillonnée, contrairement au
  2-opt exhaustif du petit benchmark.
- L'heuristique du benchmark peut avoir des limites de calcul ou d'approximation
  indiquées dans la section précédente.
- Le mode par défaut s'arrête après un nombre fixe de générations ; le mode
  `--infinite` continue jusqu'à `Ctrl+C`. L'affichage Tkinter reste un
  squelette non relié au solveur.
