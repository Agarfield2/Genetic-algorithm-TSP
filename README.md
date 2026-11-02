# Genetic algorithm TSP

Projet Python de recherche d’une tournée pour le problème du voyageur de commerce (TSP, *Traveling Salesperson Problem*). Les fichiers CSV doivent contenir les coordonnées des points dans les colonnes `x` et `y`.

## Installation

Python 3 et `pip` sont nécessaires. Installez NumPy :

```bash
python -m pip install -r requirements.txt
```

Tkinter est fourni avec la plupart des installations Python pour Windows et macOS. Sous Linux, installez le paquet Tkinter de votre distribution si nécessaire.

## Exécution

Depuis la racine du projet :

```bash
python main.py
```

## Paramètres de l’algorithme

Tous les hyperparamètres se règlent en haut de `main.py` :

- `GENERATIONS` : nombre de générations.
- `POPULATION_SIZE` : nombre de tournées dans la population.
- `ELITE_COUNT` : nombre de meilleures tournées conservées à chaque génération.
- `MUTATION_RATE` : probabilité de mutation de chaque position intérieure d’une tournée, entre `0` et `1`.
- `TOURNAMENT_SIZE` : nombre de candidats comparés pour sélectionner un parent.

Les valeurs sont transmises à `TSP_GA`; elles sont validées à sa création. `NB_LIEUX` dans `DaWay.py` choisit le CSV d’exemple chargé par défaut.

## Tests

```bash
python -m unittest discover -s tests -v
```
