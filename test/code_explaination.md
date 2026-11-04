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

Le programme utilise plusieurs heuristiques et un algorithme génétique. Ce
sont des méthodes de recherche : elles produisent de bonnes solutions, mais
ne garantissent généralement pas de trouver l'optimum global.

## 2. Vue d'ensemble des fichiers

| Fichier | Responsabilité |
|---|---|
| [`main.py`](../main.py) | Paramètres, chargement des données, budget de calcul, lancement séquentiel ou parallèle et affichage du résultat. |
| [`DaWay.py`](../DaWay.py) | Modèle des lieux et du graphe, chargement CSV, distances, candidats voisins et validation des tournées. |
| [`TSP_GA.py`](../TSP_GA.py) | Classe publique du solveur génétique, paramètres, évaluation des scores et conservation du meilleur résultat. |
| [`genetic_evolution.py`](../genetic_evolution.py) | Création de la population initiale et construction des générations suivantes. |
| [`genetic_operators.py`](../genetic_operators.py) | Sélection, croisement, mutation et recherche locale 2-opt. |
| [`route_population.py`](../route_population.py) | Création de tournées et déduplication des cycles. |
| [`nearest_insertion.py`](../nearest_insertion.py) | Heuristique Nearest Insertion exécutable séparément. |
| [`csv/generate_graph.py`](../csv/generate_graph.py) | Génération d'un jeu de points aléatoires au format CSV. |
| [`test_heuristique.py`](../test_heuristique.py) | Implémentations de comparaison de plusieurs heuristiques et benchmark des exemples. |
| [`tests/test_tsp_ga.py`](../tests/test_tsp_ga.py) | Tests unitaires du graphe, du solveur et du programme principal. |
| [`requirements.txt`](../requirements.txt) | Dépendances Python externes ; actuellement NumPy. |

`multiprocessing`, `csv`, `random`, `time`, `argparse`, `itertools` et `tkinter`
sont fournis par Python. NumPy est la seule bibliothèque externe déclarée dans
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

### 4.2 `Graph.charger_graph`

Le constructeur de `Graph` reçoit le chemin du CSV et les paramètres de
voisinage et de matrice. `charger_graph()` :

1. vérifie qu'un chemin a été fourni ;
2. lit le CSV avec `csv.DictReader` ;
3. vérifie la présence des colonnes `x` et `y` ;
4. convertit ces colonnes en nombres réels et crée les `Lieu` ;
5. copie les coordonnées dans un tableau NumPy de forme `(nombre_de_lieux, 2)`.

Après un nouveau chargement, la matrice de distances et les voisins précédents
sont invalidés.

### 4.3 Matrice et distances à la demande

`calcul_matrice_cout_od()` prépare les structures de calcul :

- si le nombre de lieux est inférieur ou égal à `matrix_limit`, NumPy calcule
  une matrice carrée des distances entre chaque paire ;
- au-delà de cette limite, la matrice complète n'est pas allouée et les
  distances seront calculées à la demande ;
- dans les deux cas, la méthode prépare les voisins candidats utilisés par la
  recherche 2-opt.

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

### 4.4 Voisins candidats

`_build_neighbor_candidates()` découpe l'espace des coordonnées en cellules
spatiales. Pour chaque lieu, elle collecte des lieux des cellules proches,
échantillonne des cellules trop remplies et, si nécessaire, complète avec un
échantillon global. Les candidats sont ensuite classés par distance et limités
à `neighbor_count`.

Cette liste est une approximation pratique des voisins les plus proches, pas
une recherche exhaustive des voisins exacts. Elle permet à 2-opt d'examiner
moins de changements sur les grandes instances.

### 4.5 Tournée Hilbert et validation

`space_filling_route()` normalise les coordonnées sur une grille entière,
calcule un indice de courbe de Hilbert avec `_hilbert_index()`, trie les lieux
selon cet indice, puis fait pivoter l'ordre pour commencer par le lieu `0`.
La courbe de Hilbert tend à placer les points géographiquement proches près les
uns des autres dans la séquence. La méthode ferme la tournée en ajoutant `0` à
la fin.

`validate_route()` vérifie que la tournée :

- contient exactement un élément de plus que le nombre de lieux ;
- commence et finit à `0` ;
- visite chaque indice du graphe une fois avant le retour.

Elle lève `ValueError` si la tournée n'est pas valide.

### 4.6 Autres classes de `DaWay.py`

`plus_proche_voisin()` cherche le lieu non visité le plus proche d'un objet
`Lieu`. C'est une méthode de support, distincte de l'heuristique
`nearest_neighbor_tour()` du benchmark.

`Route` est actuellement un simple conteneur avec un attribut `ordre` de
classe ; le solveur principal ne s'en sert pas.

`Affichage.affiche()` ouvre une fenêtre Tkinter rudimentaire avec un canvas,
une zone de texte et une boucle d'événements. Elle n'est pas appelée par
`main.py` et ne constitue pas encore l'interface d'affichage des tournées.

## 5. Solveur génétique — `TSP_GA.py`

`TSP_GA` est l'API du solveur. Elle hérite des fonctions d'évolution, des
opérateurs génétiques et des utilitaires de population définis dans les autres
modules.

Le constructeur vérifie les paramètres (tailles positives, taux entre 0 et 1,
etc.) puis conserve :

- `population` : les tournées de la génération courante ;
- `_fitness` : leurs distances, alignées par indice avec la population ;
- `_best_route` et `_best_distance` : meilleure solution globale trouvée par
  cette instance ;
- `generations_without_improvement` : compteur de stagnation ;
- `current_mutation_rate` : taux de mutation utilisé actuellement.

Une distance plus petite représente une solution meilleure.

### 5.1 Évaluation et meilleur résultat

`_calculate_fitness()` privilégie le calcul par lots de `Graph` lorsqu'il est
disponible, et utilise sinon une évaluation tournée par tournée.

`_update_global_best()` compare le meilleur score de la population au meilleur
historique. Lorsqu'il est strictement meilleur, il copie la tournée dans
`_best_route`. La copie est importante : les listes de la population peuvent
être modifiées ultérieurement.

`best_solution()` renvoie une nouvelle copie de la tournée et sa distance. Le
meilleur est conservé en mémoire dans chaque solveur ; il n'est pas écrit dans
un fichier.

### 5.2 Diversité et mutation adaptative

`_population_diversity()` compare des positions échantillonnées dans chaque
tournée et renvoie la proportion de signatures différentes dans la population.
C'est une estimation de diversité, pas une comparaison exhaustive de chaque
paire de tournées.

`_adaptive_mutation_rate()` augmente progressivement le taux de mutation après
des générations sans amélioration, du taux initial jusqu'à son plafond. Une
amélioration remet le compteur de stagnation à zéro.

## 6. Population et évolution — `genetic_evolution.py`

### 6.1 Initialisation

`init_population(graph)` :

1. refuse un graphe vide ;
2. réduit si besoin la taille de population au nombre de cycles distincts
   possibles (voir `route_population.py`) ;
3. demande une tournée de départ ordonnée par Hilbert ;
4. essaie de l'améliorer jusqu'à 50 fois avec 2-opt échantillonné, en arrêtant
   plus tôt si elle ne change plus ;
5. ajoute cette tournée et quelques versions mutées à faible taux ;
6. complète la population avec des tournées aléatoires sans doublons ;
7. énumère des permutations si le hasard n'a pas suffi à remplir la population ;
8. calcule les scores et enregistre le meilleur initial.

La population initiale est donc hybride : une solution spatiale structurée,
quelques variantes proches et des solutions aléatoires. Le nombre réservé aux
variantes de la tournée Hilbert est environ 10 % de la population, avec au
moins une route de départ.

### 6.2 Reproduction d'une génération

`reproduction(graph)` crée la génération suivante :

1. s'assure que les scores existants sont calculés ;
2. mesure la diversité et choisit le taux de mutation adaptatif ;
3. trie les individus par distance et copie les `elite_count` meilleures
   tournées dans la nouvelle génération ;
4. estime le nombre d'immigrants à injecter si la recherche stagne et que le
   seuil de diversité ou de stagnation est atteint ;
5. crée les autres enfants par sélection, croisement, mutation et parfois
   2-opt ;
6. rejette les enfants et immigrants qui dupliquent une tournée déjà présente ;
7. complète les places restantes avec des tournées uniques ;
8. calcule les scores des nouveaux enfants et met à jour le meilleur global ;
9. met à jour le compteur de stagnation et le taux de mutation.

Les nouveaux individus sont évalués une seule fois puis leur score est gardé
pour la génération suivante. Les élites gardent leurs scores déjà connus.

## 7. Opérateurs génétiques — `genetic_operators.py`

### Sélection par tournoi

`selection()` tire au hasard jusqu'à `tournament_size` indices distincts, puis
retourne celui dont la distance est la plus faible. Les bons individus sont
favorisés, mais les moins bons peuvent également être sélectionnés.

### Croisement

`crossover(parent1, parent2)` choisit un segment intérieur du premier parent et
le copie dans l'enfant. Il remplit les cases restantes dans l'ordre du second
parent en sautant les lieux déjà présents. Le dépôt et la fermeture par `0`
sont préservés.

### Mutation

`mutation(route, mutation_rate)` calcule un nombre moyen d'échanges
proportionnel au nombre de lieux intérieurs. La partie fractionnaire est
appliquée avec un tirage aléatoire. Les échanges ne modifient que l'ordre des
lieux, pas le départ ni le retour `0`.

### Recherche locale 2-opt

2-opt sélectionne des arêtes candidates à partir des voisins préparés par
`Graph`. Il évalue le remplacement de deux arêtes par deux nouvelles arêtes.
Si le changement réduit la distance, le segment compris entre ces arêtes est
inversé.

Dans le solveur principal, 2-opt est appelé :

- sur la tournée Hilbert initiale, jusqu'à 50 passes au maximum ;
- sur certains enfants, selon `local_search_rate`, avec
  `local_search_attempts` essais par appel.

Cette version est volontairement échantillonnée et ne teste pas toutes les
paires d'arêtes.

## 8. Unicité des routes — `route_population.py`

`_route_key(route)` compare les deux orientations du cycle et choisit la plus
petite représentation lexicographique. Ainsi `[0, 1, 2, 3, 0]` et
`[0, 3, 2, 1, 0]` sont considérées comme le même cycle non orienté.

`_append_unique_route()` ajoute une copie d'une tournée seulement si sa clé
n'est pas déjà présente. Cette règle est appliquée à l'initialisation et à la
reproduction.

Pour `n` lieux, le nombre théorique de cycles non orientés fixant le départ à
`0` est `(n - 1)! / 2` pour `n >= 3`. `_unique_route_limit()` calcule juste ce
qu'il faut pour limiter la taille de population au nombre possible, sans
calculer une factorielle énorme lorsque ce nombre dépasse déjà la population
configurée.

Si les enfants uniques obtenus par mutation et croisement ne suffisent pas,
`_fill_unique_population()` parcourt les permutations lexicographiques des
lieux pour compléter la population. Cela garantit l'absence de doublons, mais
peut donner une population plus petite que prévu pour de très petits graphes.

## 9. Programme principal et parallélisme — `main.py`

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

### Mode séquentiel et mode parallèle

`_create_graph()` et `_create_solver()` construisent les objets avec les
paramètres de configuration.

`_split_generations()` répartit les générations entre les travailleurs, en
distribuant le reste aux premiers processus. `_run_parallel_search()` reçoit
un nombre de générations et une graine, crée son propre graphe et son propre
solveur, puis effectue une recherche indépendante.

Dans `main()` :

- si un seul travailleur est nécessaire, une seule recherche effectue les
  générations et le programme affiche les améliorations successives ;
- sinon, un `multiprocessing.Pool` lance jusqu'à quatre recherches en parallèle
  et le processus principal choisit le meilleur résultat retourné.

Les travailleurs ne partagent pas leurs populations ni leurs meilleurs
résultats pendant le calcul. Le meilleur général entre processus est comparé à
la fin seulement. Le meilleur propre à chaque processus est conservé en mémoire
jusqu'à ce que son résultat soit renvoyé au processus principal.

Le programme actuel n'est pas infini : il effectue le nombre configuré de
générations et se termine. Il n'enregistre pas d'historique durable des
améliorations et ne pilote pas de bouton ou d'affichage Tkinter. Ces fonctions
ne sont pas implémentées dans le code décrit ici.

La condition `if __name__ == "__main__":` empêche le lancement automatique de
`main()` lors d'un import. C'est également nécessaire au bon fonctionnement du
`multiprocessing` avec le mode de démarrage Windows.

## 10. Heuristique Nearest Insertion — `nearest_insertion.py`

`nearest_insertion(graph)` construit un cycle fermé :

1. commence par le lieu `0` et son plus proche voisin ;
2. maintient, pour chaque lieu non visité, sa distance au lieu déjà visité le
   plus proche ;
3. choisit le lieu dont cette distance est la plus faible ;
4. l'insère à la position du cycle qui augmente le moins la distance totale ;
5. met à jour les distances des lieux restants.

Le script autonome charge le CSV défini par son propre `CSV_PATH`, prépare le
graphe, chronomètre la construction, vérifie la route et affiche la distance et
la tournée. Il ne fait pas partie de la boucle du solveur génétique.

## 11. Comparaison des heuristiques — `test_heuristique.py`

Ce fichier contient des implémentations de benchmark pour :

1. **Greedy** : trie toutes les arêtes par longueur et choisit les plus courtes
   tant qu'elles ne donnent pas un degré supérieur à deux ou ne ferment pas un
   sous-cycle prématuré ; termine ainsi un cycle hamiltonien.
2. **Nearest Neighbor** : depuis `0`, visite à chaque étape le lieu non visité
   le plus proche.
3. **Nearest Insertion** : réutilise la fonction du module dédié ci-dessus.
4. **Cheapest Insertion** : choisit globalement le couple lieu/arête qui donne
   la plus faible augmentation immédiate de longueur.
5. **Random Insertion** : mélange les lieux non visités avec une graine, puis
   insère chaque lieu à son emplacement le moins coûteux.
6. **Farthest Insertion** : prend le lieu le plus éloigné du cycle courant et
   l'insère là où l'augmentation du coût est minimale.
7. **Christofides** : calcule un arbre couvrant minimal avec Prim, apparie les
   sommets de degré impair, construit un circuit eulérien et le raccourcit en
   sautant les visites répétées.
8. **2-opt** : recherche locale best-improvement sur toutes les paires d'arêtes
   jusqu'à ce qu'aucune amélioration ne soit trouvée.
9. **3-opt** : coupe trois arêtes et teste plusieurs ordres et orientations
   des segments. Le test est exhaustif jusqu'à 30 villes ; au-delà, il
   échantillonne au plus 5 000 triples et limite à 100 améliorations.
10. **Lin-Kernighan** : version de recherche séquentielle à profondeur,
    candidats et nombre de nœuds explorés limités par les constantes du
    fichier.
11. **Chained Lin-Kernighan** : répète cette recherche après des perturbations
    de type double-bridge et conserve le meilleur des résultats.

Les implémentations Lin-Kernighan du fichier sont des versions expérimentales
bornées pour le benchmark, pas une bibliothèque ou une implémentation de
référence certifiée de toutes les variantes canoniques. De même, Christofides
utilise un appariement parfait exact par programmation dynamique sur masque de
bits ; il est refusé si l'arbre a plus de 20 sommets impairs, car son coût
croît exponentiellement. Dans ce cas le benchmark affiche `SKIPPED` au lieu
d'échouer ou de donner un faux résultat.

Le benchmark essaie les CSV de 5, 20 et 100 lieux, valide chaque tournée et
affiche son coût et son temps. Les temps dépendent de la machine ; ces exemples
ne suffisent pas à établir un classement général.

Commandes :

```bash
python test_heuristique.py
python -m unittest test_heuristique -v
```

La première commande affiche le benchmark. La seconde lance les tests unitaires
du fichier.

## 12. Tests du projet

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

## 13. Limites importantes à garder en tête

- Le meilleur résultat du solveur est en mémoire, pas sauvegardé durablement.
- Les recherches parallèles sont indépendantes ; elles ne s'échangent pas leurs
  bons individus avant la fin.
- La recherche 2-opt du solveur principal est échantillonnée, contrairement au
  2-opt exhaustif du petit benchmark.
- L'heuristique du benchmark peut avoir des limites de calcul ou d'approximation
  indiquées dans la section précédente.
- Le code actuel s'arrête après un nombre fixe de générations et l'affichage
  Tkinter reste un squelette non relié au solveur.
