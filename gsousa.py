import pygame
import time
import os
import math

ASSETS_DIR = "assets"

MAX_STAT = 100

POU_STATES = ["idle", "eat", "sleep", "happy", "sad"]

def clamp(topic: float, lowest_value: float, highest_value: float) -> float:
    return max(lowest_value, min(highest_value, topic))

class Pou:
    def __init__(self, x, y, sprites_folder, size=(460, 460)):
        self.x = x
        self.y_base = y  # base pos for jumping animation ( in development )
        self.y = y
        self.size = size


        # Stats of POU
        self.hunger = 70
        self.happiness = 70
        self.cleanliness = 70
        self.energy = 80

        self.coins = 0  # Costa developing the economic system

        self.state = "idle"  # idle / eat / sleep / happy / sad
        self.is_sleeping = False
        

        def feed(self):
            self.state = "eat"
            self.hunger = clamp(self.hunger + 20, 0, MAX_STAT)
            self.happiness = clamp(self.happiness + 5, 0, MAX_STAT)
        
        def bath(self):
            self.cleanliness = clamp(self.cleanliness + 25, 0, MAX_STAT)
            self.happiness = clamp(self.happiness + 3, 0, MAX_STAT)
            self.state = "happy"

        

