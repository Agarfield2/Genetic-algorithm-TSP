import numpy as np
from random import randint
import time 
import pandas as pd
from tkinter import *
import csv

NB_LIEUX = 20
LARGEUR = 800 
HAUTEUR = 600

class Lieu:
    x = 0
    y = 0
    def distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

class Graph:
    list_lieux = []
    matrice_od = np.zeros((NB_LIEUX, NB_LIEUX))

    def charger_graph(self):
        name = "csv/graph_"+str(NB_LIEUX)+".csv"
        print(name)
        with open(name, "r") as data:
            lecteur_csv = csv.DictReader(data)
            for ligne in lecteur_csv:
                lieu = Lieu()
                lieu.x = float(ligne["x"])
                lieu.y = float(ligne["y"])
                self.list_lieux.append(lieu)

    def calcul_matrice_cout_od(self):
        for i in range(NB_LIEUX):
            for j in range(NB_LIEUX):
                self.matrice_od[i][j] = self.list_lieux[i].distance(self.list_lieux[j])

    def plus_proche_voisin(self,lieu,visites):
        min_distance = float('inf')
        nearest_lieu = None
        for i, other_lieu in enumerate(self.list_lieux):
            if i not in visites:
                distance = lieu.distance(other_lieu)
                if distance < min_distance:
                    min_distance = distance
                    nearest_lieu = i
        return nearest_lieu
 
    def calcul_distance_route(self, route):
        distance = 0
        for i in range(len(route) - 1):
            distance += self.list_lieux[route[i]].distance(self.list_lieux[route[i + 1]])
        return distance
        
class Route:
    order = []
    

class Affichage:
    def affiche(self):
        app=Tk()
        canvas=Canvas(app,width=LARGEUR,height=HAUTEUR)
        Zone_de_texte=Text(app,width=50,height=50)
        canvas.pack()
        Zone_de_texte.pack()
        app.mainloop()

class TSP_GA:
    x = 0 


graph = Graph()
graph.charger_graph()
graph.print_graph()