import pygame
import time
import os
import math

MAX_STAT = 100

class Pou:
    def __init__(self, x, y, pasta_sprites, tamanho=(460, 460)):
        self.x = x
        self.y_base = y  # base pos for jumping animation ( in development )
        self.y = y
        self.tamanho = tamanho


        # Stats of POU
        self.fome = 70
        self.felicidade = 80
        self.limpeza = 80
        self.energia = 80


