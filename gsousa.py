import pygame
import time
import os
import math
from typing import Dict, List, Optional, Tuple

ASSETS_DIR = "assets"
DEFAULT_SKINS = [
    {"id": "Toni", "name": "Antonio", "price": 0},
    {"id": "Alex", "name": "Alexandre", "price": 20},
    {"id": "Unknown", "name": "Unknown", "price": 30},
]

SKIN_BACKGROUNDS = {
    "Toni": os.path.join("backgrounds", "windowsXP.png"),
    "Alex": os.path.join("backgrounds", "conservatorio.png"),
    "Unknown": os.path.join("backgrounds", "unknown.png"),
}

WIDTH, HEIGHT = 1920, 1080


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
DARK = (20, 20, 20)
GREEN = (0, 200, 0)
RED = (200, 50, 50)
BLUE = (60, 120, 220)
YELLOW = (230, 200, 0)

MAX_STAT = 100

POU_STATES = ["idle", "eat", "sleep", "happy", "sad"]

def clamp(topic: float, lowest_value: float, highest_value: float) -> float:
    return max(lowest_value, min(highest_value, topic))

def lighten(color: Tuple[int, int, int], amount: int = 30) -> Tuple[int, int, int]:
    r, g, b = color
    return (min(255, r + amount), min(255, g + amount), min(255, b + amount))


class AssetLoader:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.image_cache: Dict[str, pygame.Surface] = {}
        self.sound_cache: Dict[str, Optional[pygame.mixer.Sound]] = {}
        
    def load_image(self, path: str, size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
        key = f"{path}|{size}"
        if key in self.image_cache:
            return self.image_cache[key]

        full = os.path.join(self.base_dir, path)
        surf: pygame.Surface
        if os.path.isfile(full):
            try:
                surf = pygame.image.load(full).convert_alpha()
            except Exception:
                surf = pygame.Surface((size or (200, 200)), pygame.SRCALPHA)
                surf.fill((180, 180, 180, 255))
        else:
            # Fallback visual amigável
            w, h = size or (220, 220)
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.fill((70, 70, 70, 255))
            pygame.draw.rect(surf, (120, 120, 120), (0, 0, w, h), 6, border_radius=18)
            self.draw_text_on(surf, "(sprite\nfaltando)")

        if size:
            surf = pygame.transform.smoothscale(surf, size)

        self.image_cache[key] = surf
        return surf
    

    def draw_text_on(self, surface: pygame.Surface, text: str):
        font = pygame.font.SysFont("Arial", 16)
        lines = text.split("\n")
        y = surface.get_height() // 2 - len(lines) * 10
        for i, line in enumerate(lines):
            img = font.render(line, True, WHITE)
            rect = img.get_rect(center=(surface.get_width() // 2, y + i * 20))
            surface.blit(img, rect)


    def load_sound(self, path: str) -> Optional[pygame.mixer.Sound]:
        if path in self.sound_cache:
            return self.sound_cache[path]
        full = os.path.join(self.base_dir, path)
        if os.path.isfile(full):
            try:
                snd = pygame.mixer.Sound(full)
            except Exception:
                snd = None
        else:
            snd = None
        self.sound_cache[path] = snd
        return snd


class Pou:
    def __init__(self, assets: AssetLoader, x: int, y: int, scale: Tuple[int, int] = (260, 260)):
        self.x = x
        self.y = y
        self.assets = assets
        self.scale = scale


        # Stats of POU
        self.hunger = 70
        self.happiness = 70
        self.cleanliness = 70
        self.energy = 80

        self.coins = 0  # Costa developing the economic system

        self.state = "idle"  # idle / eat / sleep / happy / sad
        self.is_sleeping = False
        self.anim_timer = 0.0

        self.owned_skins = {"Toni": True}
        self.current_skin = "Toni"


    def to_dict(self) -> dict:
        return {
            "hunger": self.hunger,
            "happiness": self.happiness,
            "cleanliness": self.cleanliness,
            "energy": self.energy,
            "coins": self.coins,
            "is_sleeping": self.is_sleeping,
            "state": self.state,
            "current_skin": self.current_skin,
            "owned_skins": self.owned_skins,
        }
    
    def from_dict(self, data: dict):
        self.hunger = data.get("hunger", self.hunger)
        self.happiness = data.get("happiness", self.happiness)
        self.cleanliness = data.get("cleanliness", self.cleanliness)
        self.energy = data.get("energy", self.energy)
        self.coins = data.get("coins", self.coins)
        self.is_sleeping = data.get("is_sleeping", False)
        self.state = data.get("state", "idle")
        self.current_skin = data.get("current_skin", "classic")
        self.owned_skins.update(data.get("owned_skins", {}))



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

    def buy_skin(self, skin_id: str, price: int) -> bool:
        if self.owned_skins.get(skin_id):
            self.current_skin = skin_id
            return True
        if self.coins >= price:
            self.coins -= price
            self.owned_skins[skin_id] = True
            self.current_skin = skin_id
            return True
        return False


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


    def draw(self, screen: pygame.Surface):
        img = self.get_state_image()
        rect = img.get_rect(center=(self.x, self.y))
        screen.blit(img, rect)

    def get_state_image(self) -> pygame.Surface:
        # Path: assets/pou/<skin>/<state>.png
        path = os.path.join("pou", self.current_skin, f"{self.state}.png")
        return self.assets.load_image(path, self.scale)


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



class Button:

        

