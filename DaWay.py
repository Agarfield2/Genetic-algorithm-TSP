import numpy as np
from random import shuffle, randint
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
        expected_places = set(range(len(self.list_lieux)))
        if (
            len(route) != len(self.list_lieux) + 1
            or not route
            or route[0] != 0
            or route[-1] != 0
            or set(route[:-1]) != expected_places
        ):
            raise ValueError("A route must visit every place once and return to place 0.")

        distance = 0
        for i in range(len(route) - 1):
            distance += self.list_lieux[route[i]].distance(self.list_lieux[route[i + 1]])
        return distance
        
class Route:
    ordre = []

class Affichage:
    def __init__(self, graph, best_route, best_distance, list_best_route):
        self.list_lieux = graph.list_lieux
        self.best_route = best_route
        self.best_distance = best_distance
        self.list_best_route = list_best_route

    def affiche(self):
        app=Tk()
        canvas=Canvas(app,width=LARGEUR,height=HAUTEUR)
        for lieu in self.list_lieux:
            if lieu.x < LARGEUR and lieu.y < HAUTEUR and lieu.y > 0 and lieu.x > 0:
                canvas.create_oval(lieu.x-5, lieu.y-5, lieu.x+5, lieu.y+5, fill="red")
        meilleur_route = self.best_route
        compteur=0
        for meilleur in meilleur_route:
            lieu1 = self.list_lieux[meilleur]
            canvas.create_text(lieu1.x, lieu1.y - 10, text=str(compteur))
            compteur += 1
            lieu2 = self.list_lieux[meilleur_route[(meilleur_route.index(meilleur)+1)]]
            canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,  dash=(4, 8), fill="blue", width=3)
        Zone_de_texte=Text(app,width=50,height=50)
        Zone_de_texte.insert(END, "Performances :\n")#ajout dans la zone de texte 
        def esc(event):
            print("20/20")
            app.destroy()


        def action(event):
            for x, liste in enumerate(self.list_best_route):
                for j in range(len(liste)-1):
                    a = liste[j]
                    b = liste[(j+1)]    
                    val = False     # boucle sur le segment
                    for i in range(len(meilleur_route)-1):  # boucle sur le meilleur chemin
                        if (a == meilleur_route[i] and b == meilleur_route[i+1]):
                            val = True
                            break
                    if val== True:
                        val = False
                        continue                            # déjà dessiné en bleu
                    lieu1 = self.list_lieux[a]
                    lieu2 = self.list_lieux[b]
                    if x == 0:
                        canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="green", width=2)
                    elif x == 1:
                        canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="orange", width=2)
                    elif x == 2:
                        canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="purple", width=2)
                    else:
                        canvas.create_line(lieu1.x, lieu1.y, lieu2.x, lieu2.y,
                                    dash=(5, 5), fill="pink", width=2)


        app.bind("q", action) 
           # Entrée
        app.bind("<Escape>", esc)

        canvas.pack()
        Zone_de_texte.pack()
        app.mainloop()
        #pour chaque lieu du graphe on creer un cercle compris dans la fenetre 
    
