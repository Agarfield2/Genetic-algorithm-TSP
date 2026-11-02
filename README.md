# Genetic algorithm TSP

Projet Python autour du problème du voyageur de commerce (TSP, *Traveling Salesperson Problem*). L’objectif est de représenter des lieux, calculer des distances et rechercher un itinéraire, avec une visualisation graphique.

> **État du projet :** le code est encore en cours de développement. `DaWay.py` contient des classes et des méthodes incomplètes; il ne peut pas encore être exécuté tel quel.

## Contenu

- `DaWay.py` : ébauche de l’application et de ses classes (`Lieu`, `Graph`, `Route` et `Affichage`).
- `csv/graph_5.csv` et `csv/graph_20.csv` : exemples de coordonnées de lieux au format CSV, avec les colonnes `x` et `y`.
- `requirements.txt` : dépendances Python externes.

## Prérequis

- Python 3
- `pip`
- Tkinter, généralement inclus avec Python sous Windows et macOS. Sous Linux, il peut être nécessaire d’installer le paquet Tkinter de la distribution.

## Installation

Depuis la racine du dépôt, installez les dépendances :

```bash
python -m pip install -r requirements.txt
```

Les modules `random`, `time` et `csv` font partie de la bibliothèque standard de Python. Tkinter est également fourni séparément de `pip` avec de nombreuses installations de Python.

## Exécution

L’application n’est pas encore exécutable : certaines méthodes de `DaWay.py` sont vides et le fichier comporte des blocs de code incomplets. Une commande de lancement sera documentée lorsque l’algorithme et l’interface seront implémentés.

## Format des données

Les fichiers d’exemple dans `csv/` contiennent une ligne d’en-tête (`x,y`), suivie d’une ligne par lieu. Les coordonnées sont des nombres décimaux destinés à représenter les positions des lieux.
