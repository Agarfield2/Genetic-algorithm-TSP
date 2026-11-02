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

## Performances et limites

- Une matrice complète de distances n’est créée que pour **250 points ou moins** (environ 0,5 Mo de données `float64` au seuil). Au-delà, les distances d’une tournée sont calculées à la demande avec NumPy, sans matrice quadratique.
- Les scores de la population courante sont conservés et les enfants sont évalués une seule fois à leur création.
- Le croisement parcourt les villes en temps linéaire et maintient le point `0` aux deux extrémités.
- La validation complète d’une tournée est disponible via `Graph.validate_route`; le calcul fréquent du score ne fait que les contrôles de forme peu coûteux.

Ces optimisations réduisent la mémoire et le coût inutile, mais elles ne rendent pas automatiquement un algorithme génétique classique performant à 10 000 points : chaque tournée comporte toujours 10 000 étapes, et la qualité comme le temps d’exécution dépendent fortement de la taille de population et du nombre de générations. Mesurez les performances sur vos données et votre machine avant de lancer de longs calculs.

## Tests

```bash
python -m unittest discover -s tests -v
```
