# Genetic algorithm TSP

Projet Python de recherche d’une tournée pour le problème du voyageur de commerce (TSP). Une tournée est représentée par une liste qui commence et se termine au point `0`, par exemple `[0, 3, 1, 2, 0]`.

## Installation

Python 3 et `pip` sont nécessaires. Installez NumPy :

```bash
python -m pip install -r requirements.txt
```

Tkinter est utilisé par le module d’affichage. Il est fourni avec la plupart des installations Python pour Windows et macOS; sous Linux, installez le paquet Tkinter de votre distribution si nécessaire.

## Données

Les fichiers CSV doivent contenir les colonnes `x` et `y`, une ligne par point. Par défaut, le programme charge `csv/graph_5.csv`. Pour charger un autre fichier depuis Python :

```python
from DaWay import Graph

graph = Graph(csv_path="chemin/vers/points.csv")
graph.charger_graph()
```

Le nombre de points est déduit des lignes du fichier.

## Exécution

Depuis la racine du projet :

```bash
python main.py
```

La taille de population et le nombre de générations sont configurés dans `TSP_GA.py` et `main.py`.

<<<<<<< Updated upstream
## Performances et limites

- Une matrice complète de distances n’est créée que pour **250 points ou moins** (environ 0,5 Mo de données `float64` au seuil). Au-delà, les distances d’une tournée sont calculées à la demande avec NumPy, sans matrice quadratique.
- Les scores de la population courante sont conservés et les enfants sont évalués une seule fois à leur création.
- Le croisement parcourt les villes en temps linéaire et maintient le point `0` aux deux extrémités.
- La validation complète d’une tournée est disponible via `Graph.validate_route`; le calcul fréquent du score ne fait que les contrôles de forme peu coûteux.

Ces optimisations réduisent la mémoire et le coût inutile, mais elles ne rendent pas automatiquement un algorithme génétique classique performant à 10 000 points : chaque tournée comporte toujours 10 000 étapes, et la qualité comme le temps d’exécution dépendent fortement de la taille de population et du nombre de générations. Mesurez les performances sur vos données et votre machine avant de lancer de longs calculs.
=======
Le fichier de données et les hyperparamètres se règlent en haut de `main.py` :

- `CSV_PATH` : chemin du CSV contenant les points (`x`,`y`).
- `GENERATIONS` : nombre de générations.
- `POPULATION_SIZE` : nombre de tournées dans la population.
- `ELITE_COUNT` : nombre de meilleures tournées conservées à chaque génération.
- `MUTATION_RATE` et `MAX_MUTATION_RATE` : taux de mutation de base et plafond adaptatif, entre `0` et `1`.
- `TOURNAMENT_SIZE` : nombre de candidats comparés pour sélectionner un parent.
- `STAGNATION_GENERATIONS` : nombre de générations sans progrès avant d’intensifier la mutation et d’injecter des tournées aléatoires.
- `IMMIGRANT_FRACTION` et `MIN_DIVERSITY` : contrôle du renouvellement et de la diversité estimée de la population.
- `LOCAL_SEARCH_RATE` et `LOCAL_SEARCH_ATTEMPTS` : fréquence et budget de recherche locale 2-opt.
- `FITNESS_BATCH_SIZE` : taille des lots pour calculer les scores avec NumPy sans construire de grands tableaux temporaires.
- `DISTANCE_MATRIX_LIMIT` : nombre maximal de points pour conserver une matrice complète de distances.
- `NEIGHBOR_COUNT`, `NEIGHBOR_CELL_RADIUS` et `NEIGHBOR_SAMPLE_SIZE` : paramètres des candidats spatiaux utilisés par 2-opt.

Les valeurs sont transmises aux classes `TSP_GA` et `Graph`; les paramètres génétiques sont validés à leur création. `NB_LIEUX` dans `DaWay.py` choisit le CSV chargé par défaut.

## Optimisations

- Les scores de la population sont conservés et les enfants sont évalués une seule fois, par lots NumPy.
- Le croisement utilise un ensemble pour les tests d’appartenance et parcourt les villes en temps linéaire.
- La matrice des distances est construite seulement sous `DISTANCE_MATRIX_LIMIT`; au-delà, les longueurs de routes sont calculées à la demande.
- La validation complète d’une tournée est disponible avec `Graph.validate_route`. La mesure fréquente ne refait pas le contrôle coûteux de toutes les villes.
- Après stagnation, le taux de mutation augmente et une fraction des moins bons descendants est remplacée par des tournées aléatoires.
- Une recherche 2-opt échantillonnée utilise des voisins spatiaux candidats pour limiter son coût; elle ne teste pas toutes les paires d’arêtes.
- L’affichage ne produit pas la tournée complète pour les grands graphes, afin d’éviter des sorties console volumineuses.

Ces optimisations bornent certains coûts mais ne rendent pas instantanée une recherche sur 10 000 points. En particulier, une population de 1 000 tournées de cette taille utilise beaucoup de mémoire et demande un calcul important à chaque génération; adaptez `POPULATION_SIZE` et `GENERATIONS` à la machine et mesurez le temps réel.
>>>>>>> Stashed changes

## Tests

```bash
python -m unittest discover -s tests -v
```
