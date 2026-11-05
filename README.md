# Genetic algorithm TSP

Projet Python qui cherche une tournée courte pour le problème du voyageur de commerce (TSP). Chaque point représente un lieu défini par ses coordonnées `x` et `y`. Une tournée visite chaque lieu une fois et revient au point de départ `0`, par exemple `[0, 3, 1, 2, 0]`.

L'algorithme génétique est une heuristique : il cherche une bonne solution, mais ne garantit pas de trouver l'optimum global.

Une explication détaillée des modules, des algorithmes et des tests est disponible dans [`test/code_explaination.md`](./test/code_explaination.md).
Le déroulement pas à pas de la recherche génétique, y compris le mode coopératif, est décrit dans [`test/genetique.md`](./test/genetique.md).

## Installation

Depuis la racine du dépôt, installez les dépendances :
>>>>>>>>> Temporary merge branch 2

```bash
python -m pip install -r requirements.txt
```

Le calcul numérique utilise NumPy. Le solveur utilise aussi `multiprocessing`, fourni avec Python, pour répartir le travail sur plusieurs coeurs ; aucune dépendance supplémentaire n'est à installer pour cela.

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

## Optimiser les hyperparamètres

Le script [tune_hyperparameters.py](./tune_hyperparameters.py) compare les réglages actuels à des variantes de mutation, de tournoi, d'élitisme et de recherche locale sur 100, 1 000 et 10 000 villes. Il utilise 15 répétitions appariées par configuration par défaut, conserve le même budget de générations et répartit les recherches comme le mode fini normal. Les recherches sont exécutées séquentiellement pour éviter que les configurations se perturbent en se partageant le CPU. Une variante n'est recommandée que si elle gagne au moins 80 % des répétitions appariées, perd au plus 20 % et améliore la médiane des différences de coût ; sinon, les paramètres actuels sont conservés.

```bash
python tune_hyperparameters.py
```

Le rapport JSON est créé dans `.performance/`, qui est ignoré par Git. La recommandation minimise la médiane de la meilleure distance trouvée ; le temps médian départage uniquement les égalités. Pour réduire le temps d'un essai, utilisez par exemple `--repeats 3`; pour choisir les tailles à tester, utilisez `--cities 100,1000,10000`. Les recommandations mesurées sur les CSV fournis ne garantissent pas le même classement sur d'autres jeux de points.

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

## Fonctionnement du projet

- [DaWay.py](./DaWay.py) charge les points depuis le CSV, calcule les distances euclidiennes, valide les tournées et prépare des voisins candidats pour la recherche locale. Le calcul des clés Hilbert est vectorisé et les décalages de cellules des voisins sont pré-calculés. Pour les graphes jusqu'à `DISTANCE_MATRIX_LIMIT`, il peut stocker une matrice complète des distances ; au-delà, les distances sont calculées à la demande afin d'éviter une matrice quadratique.
- [TSP_GA.py](./TSP_GA.py) expose le solveur génétique, ses paramètres, le calcul des scores et le suivi de la meilleure solution.
- [genetic_evolution.py](./genetic_evolution.py) initialise la population et construit les générations suivantes.
- [genetic_operators.py](./genetic_operators.py) contient la sélection, le croisement, la mutation et l'amélioration locale 2-opt.
- [route_population.py](./route_population.py) construit les tournées et empêche les cycles dupliqués ; une tournée et son parcours inversé sont considérés comme le même cycle. Si le graphe ne permet pas assez de cycles distincts, la population est réduite au nombre de cycles possibles.
- [main.py](./main.py) configure les paramètres, charge le graphe, adapte le budget du mode fini et pilote les modes fini et infini.
- [parallel_evolution.py](./parallel_evolution.py) fait produire en parallèle des descendants à partir d'une même population partagée en mémoire.
- [csv/generate_graph.py](./csv/generate_graph.py) génère des CSV de points aléatoires.
- [tests/test_tsp_ga.py](./tests/test_tsp_ga.py) contient les tests automatisés.

## Paramètres et budget de calcul

Les paramètres principaux se trouvent en haut de `main.py` :

- `GENERATIONS` et `POPULATION_SIZE` définissent les plafonds du nombre de générations et de la taille de population.
- `ELITE_COUNT` et `TOURNAMENT_SIZE` règlent la sélection et la conservation des meilleurs individus.
- `MUTATION_RATE` et `MAX_MUTATION_RATE` déterminent le taux de mutation de base et son plafond lorsque la recherche stagne.
- `STAGNATION_GENERATIONS` détermine après combien de générations sans amélioration le taux de mutation commence à augmenter.
- `RESTART_AFTER_STAGNATION` fixe le nombre de générations sans amélioration avant la réinitialisation complète de la population dans le mode `--infinite` (100 par défaut ; le redémarrage survient après ce seuil).
- La recherche locale 2-opt est conservée pour améliorer la tournée spatiale de départ ; elle n'est plus appliquée aux descendants, car les benchmarks appariés n'ont pas montré de meilleur coût et ont mesuré un surcoût de 4 à 7 %.
- Le cache des distances d'arêtes inchangées de 2-opt est désactivé au-delà de `MAX_TWO_OPT_CACHE_CITIES` (1 000 000 villes), afin de borner sa mémoire. Avec les 4 processus configurés et une estimation conservatrice de 40 octets par ville et par cache, cela représente au plus environ 160 Mo pour les caches.
- `FITNESS_BATCH_SIZE` limite la mémoire temporaire utilisée lors de l'évaluation groupée des tournées.
- `DISTANCE_MATRIX_LIMIT` fixe le seuil d'utilisation d'une matrice complète de distances.
- `NEIGHBOR_COUNT` et `NEIGHBOR_CELL_RADIUS` règlent la recherche des voisins candidats pour 2-opt. Les essais appariés ont confirmé l'intérêt de 16 voisins et du rayon 2 ; l'échantillonnage global de remplissage a été retiré, car il n'améliorait pas la qualité mesurée.
- `MAX_ROUTE_EVALUATIONS` et `MAX_POPULATION_ROUTE_CELLS` plafonnent respectivement le travail et la mémoire de la population pour les grands graphes.
- `PARALLEL_WORKERS` fixe le nombre maximal de processus (4 par défaut, adapté à une machine à 4 cœurs).

Le mode par défaut est fini : pour les graphes au-dessus de `DISTANCE_MATRIX_LIMIT`, `get_solver_budget` réduit la population et les générations en fonction des plafonds configurés. Il lance plusieurs recherches indépendantes et compare leurs meilleurs résultats à la fin. Le mode `--infinite`, lui, n'applique pas de budget de générations : il fait évoluer une population commune par étapes synchronisées. Les processus créent des descendants à partir de la même population et le processus principal compose la génération suivante. Après plus de 100 générations sans progrès, il redémarre la population sans oublier le meilleur trajet historique. La taille de cette population est limitée pour contrôler la mémoire.

La population initiale contient des variantes d'une tournée ordonnée selon une courbe de Hilbert et améliorée par 2-opt, ainsi que des tournées aléatoires. Le solveur conserve en mémoire sa meilleure tournée et sa distance dès qu'il trouve une amélioration stricte. Le mode fini indépendant compare les meilleurs résultats à la fin ; en mode infini, une population commune est recomposée à chaque génération. À l'interruption par `Ctrl+C`, le meilleur trajet et ses coordonnées sont enregistrés dans `best_route.csv`. Ces stratégies rendent la recherche plus praticable sur de grands graphes, sans garantir l'optimum global. La route complète n'est pas affichée pour les grandes instances.

## Complexité des traitements

Avec `n` villes, `P` individus, `A` essais 2-opt, `K` voisins retenus, `C` la taille maximale du bassin de candidats avant tri, `B` routes par lot et `r` le rayon de recherche des cellules :

- La préparation des voisins candidats coûte `O(n × (r² + C log C))` en moyenne et utilise `O(n × K + C + r²)` mémoire. Avec les paramètres actuels, `r`, `C` et `K` sont bornés, donc son coût croît pratiquement de façon linéaire en `n`.
- Le calcul de la tournée Hilbert coûte `O(n log n + 16n)` ; les 16 étapes de calcul des indices sont maintenant vectorisées avec NumPy. Le tri reste le terme asymptotique dominant.
- Le croisement, la mutation, la clé de déduplication et la validation d'une tournée coûtent `O(n)`. Le croisement utilise une table booléenne indexée par ville plutôt qu'une recherche dans un set.
- Une génération coûte `O(P × n + P log P)` hors évaluation des scores ; les tentatives de remplacement de doublons sont plafonnées à 10 par enfant. Le calcul groupé du fitness coûte `O(P × n)` et réserve `O(B × n)` mémoire temporaire.
- 2-opt coûte `O(n + A × K)` et utilise `O(n)` mémoire temporaire lorsqu'il active son cache.

## Tests

Depuis la racine du dépôt :

```bash
python -m unittest discover -s tests -v
```
=========
Les modules `random`, `time` et `csv` font partie de la bibliothèque standard de Python. Tkinter est également fourni séparément de `pip` avec de nombreuses installations de Python.

## Exécution

L’application n’est pas encore exécutable : certaines méthodes de `DaWay.py` sont vides et le fichier comporte des blocs de code incomplets. Une commande de lancement sera documentée lorsque l’algorithme et l’interface seront implémentés.

## Format des données

Les fichiers d’exemple dans `csv/` contiennent une ligne d’en-tête (`x,y`), suivie d’une ligne par lieu. Les coordonnées sont des nombres décimaux destinés à représenter les positions des lieux.
>>>>>>>>> Temporary merge branch 2
