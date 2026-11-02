import numpy as np
from random import randint
import time 
import pandas as pd
from tkinter import *
import csv

NB_LIEUX = 0
LARGEUR = 800 
HAUTEUR = 600 

class Lieu:
    x = 0
    y = 0
    def distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

class Graph:
    list_lieux = []
    def calcul_matrice_cout_od(self):
        return 0
    def plus_proche_voisin(self):

    def calcul_distance_route(self):

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