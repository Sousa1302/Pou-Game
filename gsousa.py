import pygame
import time
import os
import math
import random
from typing import Dict, List, Optional, Tuple

ASSETS_DIR = "assets"
DEFAULT_SKINS = [ru
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
    def __init__(self, assets: AssetLoader, pou: Pou):
        self.assets = assets
        self.pou = pou
        self.active = False
        self.items: List[pygame.Rect] = []
        self.item_speed = 220
        self.spawn_timer = 0.0
        self.duration = 30.0  # seconds
        self.time_left = self.duration
        self.basket = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 120, 120, 28)
        self.score = 0

        # images
        self.food_img = assets.load_image("icons/food.png", (32, 32))

    def start(self):
        self.active = True
        self.items.clear()
        self.time_left = self.duration
        self.score = 0

    def end(self) -> int:
        self.active = False
        # reward : coins
        earned = self.score
        self.pou.coins += earned
        self.pou.happiness = clamp(self.pou.happiness + min(20, earned * 1.2), 0, MAX_STAT)
        self.pou.energy = clamp(self.pou.energy - 8, 0, MAX_STAT)
        return earned

    def update(self, dt: float):
        if not self.active:
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self.end()
            return

        # move basket with mouse cursor
        mx, _ = pygame.mouse.get_pos()
        self.basket.centerx = mx
        self.basket.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        # item spawn
        self.spawn_timer += dt
        if self.spawn_timer >= 0.5:
            self.spawn_timer = 0
            x = random.randint(20, WIDTH - 20)
            r = pygame.Rect(x, -30, 32, 32)
            self.items.append(r)

        # move items and colissions
        for r in list(self.items):
            r.y += int(self.item_speed * dt)
            if r.colliderect(self.basket):
                self.items.remove(r)
                self.score += 1
                self.pou.hunger = clamp(self.pou.hunger + 3, 0, MAX_STAT)
            elif r.top > HEIGHT + 10:
                self.items.remove(r)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        if not self.active:
            return
        # background
        screen.fill((15, 30, 45))

        # items
        for r in self.items:
            screen.blit(self.food_img, r)

        # basket
        pygame.draw.rect(screen, YELLOW, self.basket, border_radius=8)

        # UI
        txt = font.render(f"Tempo: {self.time_left:0.1f}s  |  Pontos: {self.score}", True, WHITE)
        screen.blit(txt, (20, 20))



class Shop:
    def __init__(self, assets: AssetLoader, pou: Pou):
        self.assets = assets
        self.pou = pou
        self.visible = False
        self.items = DEFAULT_SKINS
        self.close_btn = pygame.Rect(0, 0, 40, 40)  # position in draw

    def toggle(self):
        self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event):
        if not self.visible:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_btn.collidepoint(event.pos):
                self.toggle()

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, big: pygame.font.Font):
        if not self.visible:
            return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Shop Window
        panel = pygame.Rect(160, 100, WIDTH - 320, HEIGHT - 200)
        pygame.draw.rect(screen, (30, 30, 35), panel, border_radius=16)
        pygame.draw.rect(screen, (80, 80, 90), panel, 4, border_radius=16)

        title = big.render("Loja de Skins", True, WHITE)
        screen.blit(title, (panel.x + 24, panel.y + 16))

        # X button to close the shop
        self.close_btn = pygame.Rect(panel.right - 56, panel.y + 16, 40, 40)
        mx, my = pygame.mouse.get_pos()
        x_hover = self.close_btn.collidepoint((mx, my))
        x_color = lighten(RED, 25) if x_hover else RED
        pygame.draw.rect(screen, x_color, self.close_btn, border_radius=8)
        x_txt = big.render("X", True, WHITE)
        screen.blit(x_txt, x_txt.get_rect(center=self.close_btn.center))

        # Items List
        y = panel.y + 90
        for it in self.items:
            skin_id = it["id"]
            name = it["name"]
            price = it["price"]
            owned = self.pou.owned_skins.get(skin_id, False)

            # skin icon : show idle
            icon = self.assets.load_image(os.path.join("pou", skin_id, "idle.png"), (110, 110))
            screen.blit(icon, (panel.x + 28, y))

            # name and price
            txt = font.render(f"{name}  —  {price} moedas", True, WHITE)
            screen.blit(txt, (panel.x + 160, y + 34))

            # Buy button and use button
            btxt = "Usar" if owned else "Comprar"
            base = (60, 130, 60) if owned else (60, 60, 130)
            btn_rect = pygame.Rect(panel.right - 220, y + 34, 160, 48)
            b_hover = btn_rect.collidepoint((mx, my))
            col = lighten(base, 25) if b_hover else base
            pygame.draw.rect(screen, col, btn_rect, border_radius=10)
            label = font.render(btxt, True, WHITE)
            screen.blit(label, label.get_rect(center=btn_rect.center))

            if b_hover and pygame.mouse.get_pressed(num_buttons=3)[0]:
                if owned:
                    self.pou.current_skin = skin_id
                else:
                    self.pou.buy_skin(skin_id, price)

            y += 150

        coins_txt = font.render(f"Moedas: {self.pou.coins}", True, YELLOW)
        screen.blit(coins_txt, (panel.x + 24, panel.bottom - 50))




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

        

