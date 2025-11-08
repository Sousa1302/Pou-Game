import pygame
import time
import os
import math
import random
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

ASSETS_DIR = "assets"
DEFAULT_SKINS = [
    {"id": "Toni", "name": "Antonio", "price": 0},
    {"id": "Alex", "name": "Alexandre", "price": 25},
]

SKIN_BACKGROUNDS = {
    "Toni": os.path.join("backgrounds", "windowsxp.png"),
    "Alex": os.path.join("backgrounds", "conservatorio.png"),
}

MUSIC_BY_SKIN = {
    "Toni": os.path.join("music", "toni_theme.wav"),   
    "Alex": os.path.join("music", "alex_theme.mp3"),   
}

WIDTH, HEIGHT = 1920, 1080
FPS = 60
SAVE_FILE = "save_pou.json"

EAT_TOTAL = 1.0        # full time of animation (secs)
EAT_SWITCH = 0.5       # time between switching sprites (0.5s)
HAPPINESS_DECAY_RATE_AWAKE = 1.0   # points by second when awake

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
    def __init__(self, assets: AssetLoader, x: int, y: int, scale: Tuple[int, int] = (1260, 1260)):
        self.x = x
        self.y = y
        self.assets = assets
        self.scale = scale

        self.eat_anim_timer = 0.0

        # Stats of POU
        self.hunger = 70
        self.happiness = 70
        self.cleanliness = 70
        self.energy = 80

        self.coins = 0  

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
        self.current_skin = data.get("current_skin", self.current_skin) 
        self.owned_skins.update(data.get("owned_skins", {}))



    def feed(self):
        self.state = "eat"
        self.eat_anim_timer = EAT_TOTAL           # activates the animation de 2 frames
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
        self.energy = clamp(self.energy - 6, 0, MAX_STAT)
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
        decay = delta_time * 0.6        # speed of decrease of stats 

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

        # eating animation 
        if self.state == "eat":
            self.eat_anim_timer = max(0.0, self.eat_anim_timer - delta_time)
            if self.eat_anim_timer == 0.0:
                self.state = "idle"

        # happiness decreases when awake
        if not self.is_sleeping:
            self.happiness = clamp(self.happiness - delta_time * HAPPINESS_DECAY_RATE_AWAKE, 0, MAX_STAT)

        self.anim_timer += delta_time


    def draw(self, screen: pygame.Surface):
        img = self.get_state_image()
        rect = img.get_rect(center=(self.x, self.y))
        screen.blit(img, rect)

    def get_state_image(self) -> pygame.Surface:
        # Standart path to assets
        base = os.path.join("pou", self.current_skin)

        # Eating animation 
        if self.state == "eat":
            # first 0,5 secs, mouth is open
            frame_path = "eat_open.png" if self.eat_anim_timer > (EAT_TOTAL - EAT_SWITCH) else "eat_close.png"

        
            full_path = os.path.join(base, frame_path)
            fallback_path = os.path.join(base, "eat.png")
            if os.path.isfile(os.path.join(self.assets.base_dir, full_path)):
                return self.assets.load_image(full_path, self.scale)
            else:
                return self.assets.load_image(fallback_path, self.scale)

        # normal states
        path = os.path.join(base, f"{self.state}.png")
        return self.assets.load_image(path, self.scale)


class MiniGame:
    def __init__(self, assets: AssetLoader, pou: Pou):
        self.assets = assets
        self.pou = pou
        self.active = False
        self.items: List[pygame.Rect] = []
        self.item_speed = 220
        self.spawn_timer = 0.0
        self.duration = 20.0  # seconds
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
            pygame.mouse.set_visible(True)
            return

        # move basket with mouse 
        mx, _ = pygame.mouse.get_pos()
        self.basket.centerx = mx
        self.basket.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        pygame.mouse.set_visible(False)

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


class MiniGameTrumpet:
    def __init__(self, assets: AssetLoader, pou: Pou):
        self.assets = assets
        self.pou = pou
        self.active = False
        self.duration = 30.0
        self.time_left = self.duration
        self.score = 0

        # lanes X: 3 centered columns
        lane_w = 120
        gap = 40
        cx = WIDTH // 2
        self.lanes_x = [
            cx - lane_w - gap//2,  # J
            cx,                    # K
            cx + lane_w + gap//2,  # L
        ]
        self.note_speed = 370
        self.spawn_timer = 0.0
        self.spawn_every = 0.6

        # y of the line to hit the target on time
        self.hit_y = HEIGHT - 200
        self.hit_tol = 24  # tolerance

        self.notes: List[Tuple[int, pygame.Rect]] = []  # (lane_idx, rect)
        self.font = pygame.font.SysFont("Arial", 26)

    def start(self):
        self.active = True
        self.time_left = self.duration
        self.score = 0
        self.notes.clear()
        self.spawn_timer = 0.0


    def end(self) -> int:
        self.active = False
        earned = self.score
        self.pou.coins += earned
        self.pou.happiness = clamp(self.pou.happiness + min(20, earned * 0.7), 0, MAX_STAT)
        self.pou.energy = clamp(self.pou.energy - 6, 0, MAX_STAT)
        return earned

    def update(self, dt: float):
        if not self.active:
            return

        self.time_left -= dt
        if self.time_left <= 0:
            self.end()
            return

        # spawn
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_every:
            self.spawn_timer = 0.0
            lane = random.randint(0, 2)
            x = self.lanes_x[lane]
            r = pygame.Rect(x - 40, -30, 80, 24)
            self.notes.append((lane, r))

        # mover notes 
        for i in range(len(self.notes)-1, -1, -1):
            lane, r = self.notes[i]
            r.y += int(self.note_speed * dt)
            if r.top > HEIGHT + 40:
                self.notes.pop(i)

        # input (J, K, L)
        keys = pygame.key.get_pressed()
        key_map = [(pygame.K_j, 0), (pygame.K_k, 1), (pygame.K_l, 2)]
        for k, lane_idx in key_map:
            if keys[k]:
                self.try_hit(lane_idx)

    def try_hit(self, lane_idx: int):
        # finds the closest note
        best_i = -1
        best_dy = 9999
        for i, (ln, r) in enumerate(self.notes):
            if ln != lane_idx:
                continue
            dy = abs(r.centery - self.hit_y)
            if dy < best_dy:
                best_dy = dy
                best_i = i
        if best_i != -1 and best_dy <= self.hit_tol:
            # hit it
            _, r = self.notes.pop(best_i)
            self.score += 1

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        if not self.active:
            return

        screen.fill((10, 20, 28))

        # lanes
        lane_color = (70, 120, 200)
        for x in self.lanes_x:
            pygame.draw.rect(screen, lane_color, (x - 50, 120, 100, HEIGHT - 320), border_radius=12)

        # hitline
        pygame.draw.line(screen, (240, 220, 60), (self.lanes_x[0] - 60, self.hit_y),
                         (self.lanes_x[-1] + 60, self.hit_y), 4)

        # notes
        for _, r in self.notes:
            pygame.draw.rect(screen, (230, 230, 230), r, border_radius=8)

        # UI
        txt = font.render(f"Tempo: {self.time_left:0.1f}s  |  Pontos: {self.score}   (J K L)", True, WHITE)
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
    def __init__(self, assets: AssetLoader):
        self.s_eat    = assets.load_sound("sounds/eat.wav")
        self.s_sleep  = assets.load_sound("sounds/sleep.wav")
        self.s_happy  = assets.load_sound("sounds/happy.wav")
        self.s_sad    = assets.load_sound("sounds/sad.wav")
        self.s_shower = assets.load_sound("sounds/shower.wav")  

    @staticmethod
    def play(s: Optional[pygame.mixer.Sound], volume: float = 1.0):
        if s is None or not pygame.mixer.get_init():
            return
        try:
            s.set_volume(volume)
        except Exception:
            pass
        try:
            s.play()
        except Exception:
            pass





class HUD:
    def __init__(self, pou: Pou):
        self.pou = pou

    def draw_bar(self, screen: pygame.Surface, x: int, y: int, w: int, h: int, value: float, color: Tuple[int, int, int], label: str, font: pygame.font.Font):
        pygame.draw.rect(screen, (60, 60, 60), (x, y, w, h), border_radius=8)
        fill = int((value / MAX_STAT) * (w - 4))
        pygame.draw.rect(screen, color, (x + 2, y + 2, fill, h - 4), border_radius=6)
        txt = font.render(f"{label}: {int(value)}", True, WHITE)
        screen.blit(txt, (x + 6, y - 24))

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        w = 300
        x = 24
        y = 24
        self.draw_bar(screen, x, y, w, 22, self.pou.hunger, YELLOW, "Fome", font)
        self.draw_bar(screen, x, y + 44, w, 22, self.pou.happiness, GREEN, "Felicidade", font)
        self.draw_bar(screen, x, y + 88, w, 22, self.pou.cleanliness, BLUE, "Limpeza", font)
        self.draw_bar(screen, x, y + 132, w, 22, self.pou.energy, (160, 100, 240), "Energia", font)

        coins = font.render(f"Moedas: {self.pou.coins}", True, YELLOW)
        screen.blit(coins, (x, y + 168))




class Menu:
    class ButtonObj:
        def __init__(self, rect, text, bg_color):
            self.rect = pygame.Rect(rect)
            self.text = text
            self.bg_color = bg_color

        def is_clicked(self, pos):
            return self.rect.collidepoint(pos)

        def draw(self, surf, font, border_color):
            mouse_pos = pygame.mouse.get_pos()
            is_hover = self.rect.collidepoint(mouse_pos)
            color = tuple(max(0, c - 30) for c in self.bg_color) if is_hover else self.bg_color
            pygame.draw.rect(surf, color, self.rect, border_radius=30)
            pygame.draw.rect(surf, border_color, self.rect, 3, border_radius=30)
            txt = font.render(self.text, True, (0, 0, 0))
            txt_rect = txt.get_rect(center=self.rect.center)
            surf.blit(txt, txt_rect)

    def __init__(self, width=1920, height=1080, background_path=None):
        pygame.init()
        self.WIDTH = width
        self.HEIGHT = height
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.SCALED)
        pygame.display.set_caption("My GoodBoy")

        # Colors
        self.WHITE = (255, 255, 255)
        self.BUTTON_BG = (240, 245, 255)
        self.BUTTON_BORDER = (100, 100, 100)
        self.EXIT_BUTTON_BG = (200, 0, 0)
        self.TITLE_COLOR = (50, 50, 50)
        self.TITLE_SHADOW = (100, 100, 100)

        # Fonts
        self.TITLE_FONT = pygame.font.SysFont("bitstreamverasans", 70, bold=True)
        self.BUTTON_FONT = pygame.font.SysFont("bitstreamverasans", 40, bold=True)
        self.NOTIFY_FONT = pygame.font.SysFont("bitstreamverasans", 35, bold=True)

        # Background
        self.background = None
        if background_path and os.path.isfile(background_path):
            try:
                img = pygame.image.load(background_path).convert()
                self.background = pygame.transform.smoothscale(img, (self.WIDTH, self.HEIGHT))
            except Exception:
                self.background = None

        self.clock = pygame.time.Clock()
        self.FPS = 60

        self.game_status: dict = {}
        self.notification: str = ""

        self.buttons: List[Menu.ButtonObj] = []
        self.create_buttons()

    def create_buttons(self):
        button_width = 400
        button_height = 80
        center_x = self.WIDTH // 2 - button_width // 2
        start_y = 500
        spacing = 150

        self.buttons.append(Menu.ButtonObj((center_x, start_y, button_width, button_height), "Create Game", self.BUTTON_BG))
        self.buttons.append(Menu.ButtonObj((center_x, start_y + spacing, button_width, button_height), "Join Game", self.BUTTON_BG))
        self.buttons.append(Menu.ButtonObj((center_x, start_y + 2 * spacing, button_width, button_height), "Exit", self.EXIT_BUTTON_BG))

    def reset_game(self):
        self.game_status = {
            "hunger": 100, "happiness": 100, "cleanliness": 100, "energy": 100,
            "coins": 0, "is_sleeping": False, "state": "idle",
            "current_skin": "Toni", "owned_skins": {"Toni": True, "Alex": True}
        }
        self.notification = "Game Reset!"

    def load_game(self, filepath=SAVE_FILE):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.game_status = json.load(f)
            self.notification = "Game Loaded!"
        except FileNotFoundError:
            self.notification = "Save file not found!"
            self.game_status = {}
        except json.JSONDecodeError:
            self.notification = "Error decoding JSON!"
            self.game_status = {}

    def draw_notification(self):
        if self.notification:
            txt = self.NOTIFY_FONT.render(self.notification, True, (0, 0, 0))
            txt_rect = txt.get_rect(center=(self.WIDTH // 2, 60))
            self.screen.blit(txt, txt_rect)

    def run(self) -> Tuple[str, Optional[dict]]:
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ("exit", None)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if self.buttons[0].is_clicked(pos):
                        self.reset_game()
                        return ("create", self.game_status)
                    elif self.buttons[1].is_clicked(pos):
                        self.load_game()
                        return ("join", self.game_status if self.game_status else {})
                    elif self.buttons[2].is_clicked(pos):
                        return ("exit", None)

            # Draw
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill(self.WHITE)

            title_text = "My GoodBoy"
            title_render = self.TITLE_FONT.render(title_text, True, self.TITLE_COLOR)
            title_shadow = self.TITLE_FONT.render(title_text, True, self.TITLE_SHADOW)
            x = self.WIDTH // 2 - title_render.get_width() // 2
            y = 200
            self.screen.blit(title_shadow, (x + 4, y + 4))
            self.screen.blit(title_render, (x, y))

            for btn in self.buttons:
                btn.draw(self.screen, self.BUTTON_FONT, self.BUTTON_BORDER)

            self.draw_notification()
            pygame.display.flip()
            self.clock.tick(self.FPS)

        return ("exit", None)



class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("My Goodboy")
        self.fullscreen = True
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        self.clock = pygame.time.Clock()

        try:
            pygame.mixer.init()
        except Exception:
            pass

        self.music_skin: Optional[str] = None
        self.music_volume = 0.5

        self.assets = AssetLoader(ASSETS_DIR)
        self.font = pygame.font.SysFont("Arial", 22)
        self.bigfont = pygame.font.SysFont("Arial", 34, bold=True)

        self.pou = Pou(self.assets, WIDTH // 2, HEIGHT // 2 + 40)   
        self._last_state = self.pou.state                            
        self._state_sfx_cooldown = 0.0

        self.hud = HUD(self.pou)
        self.shop = Shop(self.assets, self.pou)
        self.minigame_food = MiniGame(self.assets, self.pou)
        self.minigame_trumpet = MiniGameTrumpet(self.assets, self.pou)
        self.cur_minigame = None

        self.sfx = SoundBank(self.assets)
        self.bg_img: Optional[pygame.Surface] = None
        self.update_background()

        self.buttons: List[Button] = []
        self.make_buttons()
        self.running = True

    
    def hydrate_from_menu_state(self, state: Optional[dict]):
        if not state:
            return
        self.pou.from_dict(state)
        self.update_background()
        self.play_skin_music()


    def update_background(self):
        prev = getattr(self, "_bg_for_skin", None)
        cur = self.pou.current_skin
        if cur == prev:
            return
        self._bg_for_skin = cur
        path = SKIN_BACKGROUNDS.get(cur)
        if path:
            self.bg_img = self.assets.load_image(path, (WIDTH, HEIGHT))
        else:
            self.bg_img = None
        self.play_skin_music()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = (pygame.FULLSCREEN | pygame.SCALED) if self.fullscreen else (pygame.SCALED)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)

    def make_buttons(self):
        def mk(x, y, w, label, cb):
            self.buttons.append(Button(pygame.Rect(x, y, w, 52), label, on_click=cb))

        y = HEIGHT - 80
        spacing = 16
        bw = 220
        labels_cbs = [
            ("Dar comida", self.on_feed),
            ("Banho", self.on_bath),
            ("Dormir/Lev.", self.on_sleep),
            ("Jogar", self.on_play),
            ("Loja", self.on_shop),
            ("Guardar", self.save),
        ]
        total_w = len(labels_cbs) * bw + (len(labels_cbs) - 1) * spacing
        bx = (WIDTH - total_w) // 2
        for i, (label, cb) in enumerate(labels_cbs):
            mk(bx + i * (bw + spacing), y, bw, label, cb)

    
    def on_feed(self):
        self.pou.feed()
        SoundBank.play(self.sfx.s_eat)
        self._state_sfx_cooldown = 0.35  # evita duplo "happy" logo a seguir

    def on_bath(self):
        self.pou.bath()
        SoundBank.play(self.sfx.s_shower)  # duche
        self._state_sfx_cooldown = 0.35

    def on_sleep(self):
        self.pou.toggle_sleep()
        if self.pou.is_sleeping:
            SoundBank.play(self.sfx.s_sleep)
        else:
            SoundBank.play(self.sfx.s_happy)
        self._state_sfx_cooldown = 0.35


    def on_play(self):
        if self.cur_minigame is None:
            if self.pou.current_skin in ("Alex"):
                self.cur_minigame = self.minigame_trumpet
            else:
                self.cur_minigame = self.minigame_food
            self.cur_minigame.start()
        else:
            self.cur_minigame.end()
            self.cur_minigame = None
            self.music_skin = None 
        self.pou.play_react()

    def on_shop(self):
        self.shop.toggle()

    
    def save(self):
        data = self.pou.to_dict()
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Erro a guardar:", e)

    def load(self):
        if os.path.isfile(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.pou.from_dict(data)
                self.update_background()
            except Exception as e:
                print("Erro a carregar save:", e)

    def play_skin_music(self):
        if not pygame.mixer.get_init():
            return
        skin = self.pou.current_skin
        if skin == self.music_skin:
            return
        rel = MUSIC_BY_SKIN.get(skin)
        if not rel:
            pygame.mixer.music.stop()
            self.music_skin = None
            return
        full = os.path.join(self.assets.base_dir, rel)
        if os.path.isfile(full):
            try:
                pygame.mixer.music.load(full)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)
                self.music_skin = skin
            except Exception as e:
                print("Erro a carregar música:", e)
                self.music_skin = None
        else:
            print("Música não encontrada:", full)
            pygame.mixer.music.stop()
            self.music_skin = None

    
    def run(self):
        menu = Menu(width=WIDTH, height=HEIGHT,  background_path=os.path.join(ASSETS_DIR, "backgrounds", "start_background.jpg"))  
        action, state = menu.run()

        if action == "exit":
            pygame.quit()
            return
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        self.buttons.clear()
        self.make_buttons()
        pygame.mouse.set_visible(True)

        if action in ("create", "join"):
            if state:
                self.hydrate_from_menu_state(state)
            elif action == "join":
                self.load()

        last_time = time.time()
        while self.running:
            now = time.time()
            dt = now - last_time
            last_time = now

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.shop.visible:
                            self.shop.visible = False
                        elif self.cur_minigame is not None:
                            self.cur_minigame.end()
                            self.cur_minigame = None
                        else:
                            self.running = False
                    elif event.key == pygame.K_F11:
                        self.toggle_fullscreen()

                if self.shop.visible:
                    self.shop.handle_event(event)

                if not self.shop.visible and (self.cur_minigame is None or not self.cur_minigame.active):
                    for b in self.buttons:
                        b.handle_event(event)

            self.update_background()
            if not (self.cur_minigame and self.cur_minigame.active):
                self.play_skin_music()

            if self.cur_minigame is not None and self.cur_minigame.active:
                self.cur_minigame.update(dt)
            else:
                self.pou.update(dt)

            self._state_sfx_cooldown = max(0.0, self._state_sfx_cooldown - dt)

            new_state = self.pou.state
            if new_state != self._last_state and self._state_sfx_cooldown <= 0.0:
                if new_state == "happy":
                    SoundBank.play(self.sfx.s_happy, 0.9)
                elif new_state == "sad":
                    SoundBank.play(self.sfx.s_sad, 0.9)
                self._state_sfx_cooldown = 0.35
            self._last_state = new_state    


            if self.bg_img is not None:
                self.screen.blit(self.bg_img, (0, 0))
            else:
                self.screen.fill((32, 36, 40))

            if self.cur_minigame is not None and self.cur_minigame.active:
                self.cur_minigame.draw(self.screen, self.font)
            else:
                pygame.draw.rect(self.screen, (25, 25, 25), (0, HEIGHT - 110, WIDTH, 110))
                pygame.draw.rect(self.screen, (60, 60, 60), (0, HEIGHT - 110, WIDTH, 4))
                self.pou.draw(self.screen)
                self.hud.draw(self.screen, self.font)
                if not self.shop.visible:
                    for b in self.buttons:
                        b.draw(self.screen, self.font)
                self.shop.draw(self.screen, self.font, self.bigfont)

            pygame.display.flip()
            self.clock.tick(FPS)

        self.save()
        pygame.quit()



@dataclass
class Button:
    rect: pygame.Rect
    label: str
    bg: Tuple[int, int, int] = BLUE
    fg: Tuple[int, int, int] = WHITE
    on_click: Optional[callable] = None

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        mx, my = pygame.mouse.get_pos()
        hover = self.rect.collidepoint((mx, my))
        col = lighten(self.bg, 25) if hover else self.bg
        pygame.draw.rect(screen, col, self.rect, border_radius=10)
        text_img = font.render(self.label, True, self.fg)
        screen.blit(text_img, text_img.get_rect(center=self.rect.center))

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
        

