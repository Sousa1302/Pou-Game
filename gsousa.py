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

    def toggle_sleep(self):
        self.is_sleeping = not self.is_sleeping
        self.state = "sleep" if self.is_sleeping else "idle"

    def play_react(self): # Reaction from when he comes back from the minigame
        self.happiness = clamp(self.happiness + 8, 0, MAX_STAT)
        self.energy = clamp(self.energy - 12, 0, MAX_STAT)
        self.state = "happy"


    def update(self, delta_time: float):    # Decrease stats as the time goes by
        decay = delta_time * 0.8        # speed of decrease of stats 

        if not self.is_sleeping:
            self.hunger = clamp(self.hunger - decay, 0, MAX_STAT)
            self.energy = clamp(self.energy - decay * 0.4, 0, MAX_STAT)
            self.cleanliness = clamp(self.cleanliness - decay * 0.3, 0, MAX_STAT)
        else:
            self.energy = clamp(self.energy + decay * 1.2, 0, MAX_STAT)

        if self.is_sleeping:
            self.state = "sleep"
        else:
            bad = sum(s < 30 for s in [self.hunger, self.happiness, self.cleanliness, self.energy])
            if bad >= 1:
                self.state = "sad" if self.state != "eat" else self.state
            else:
                if self.state not in ("eat", "happy"):
                    self.state = "idle"

        self.anim_timer += delta_time



class MiniGame:
    def __init__(self):
        

        def start(self):

        
        def end(self):

        
        def update(self):





class Shop:
    def __init__(self):
    

    def toggle(self):
        self.visible = not self.visible
    

    def draw(self):




class SoundBank:
    def __init__(self):
        
    
    def play(self):




class HUD:
    def __init__(self):
        

    def draw_bar(self):
    

    def draw(self):




class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pou Arresacado")
        self.fullscreen = True
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)       # Width and height of the game window
        self.clock = pygame.time.Clock()


    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)

    
    def make_buttons(self):

    
    def save(self):

    
    def load(self):




        

