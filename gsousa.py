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
        self.current_skin = data.get("current_skin", "classic")
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

        # sound
        self.snd = self.assets.load_sound("sounds/trumpet.wav")

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
            if self.snd:
                try:
                    self.snd.play()
                except Exception:
                    pass

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
        self.s_eat = assets.load_sound("sounds/eat.wav")
        self.s_sleep = assets.load_sound("sounds/sleep.wav")
        self.s_happy = assets.load_sound("sounds/happy.wav")
        self.s_sad = assets.load_sound("sounds/sad.wav")

    def play(self, s: Optional[pygame.mixer.Sound]):
        if s is not None:
            s.play()




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




class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("My Dumb@ss Pet")
        # starts on fullscreen
        self.fullscreen = True
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        try:
            pygame.mixer.init()
        except Exception:
            pass  # no sound if not device found 

        self.assets = AssetLoader(ASSETS_DIR)
        self.font = pygame.font.SysFont("Arial", 22)
        self.bigfont = pygame.font.SysFont("Arial", 34, bold=True)

        self.pou = Pou(self.assets, WIDTH // 2, HEIGHT // 2 + 40)
        self.hud = HUD(self.pou)
        self.shop = Shop(self.assets, self.pou)
        self.minigame_food = MiniGame(self.assets, self.pou)
        self.minigame_trumpet = MiniGameTrumpet(self.assets, self.pou)
        self.cur_minigame = None  # pointer for the active minigame

        self.sfx = SoundBank(self.assets)

        # background being used depeding on the character 
        self.bg_img: Optional[pygame.Surface] = None
        self.update_background()

        self.buttons: List[Button] = []
        self.make_buttons()

        self.load()

        self.running = True

    def update_background(self):
        path = SKIN_BACKGROUNDS.get(self.pou.current_skin)
        if path:
            self.bg_img = self.assets.load_image(path, (WIDTH, HEIGHT))
        else:
            self.bg_img = None  # uses smooth fallback

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
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

    # Callbacks of buttons
    def on_feed(self):
        self.pou.feed()
        SoundBank.play(self.sfx, self.sfx.s_eat)

    def on_bath(self):
        self.pou.bath()
        SoundBank.play(self.sfx, self.sfx.s_happy)

    def on_sleep(self):
        self.pou.toggle_sleep()
        if self.pou.is_sleeping:
            SoundBank.play(self.sfx, self.sfx.s_sleep)
        else:
            SoundBank.play(self.sfx, self.sfx.s_happy)

    def on_play(self):
    # enters / leaves the minigame
        if self.cur_minigame is None:
            # chooses the minigame if Alex skin
            if self.pou.current_skin in ("Alex", "alien"):  
                self.cur_minigame = self.minigame_trumpet
            else:
                self.cur_minigame = self.minigame_food
            self.cur_minigame.start()
        else:
            self.cur_minigame.end()
            self.cur_minigame = None
        self.pou.play_react()


    def on_shop(self):
        self.shop.toggle()

    # Save/Load
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

    # Loop
    def run(self):
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

                # shop events ( X button )
                if self.shop.visible:
                    self.shop.handle_event(event)

                # if changed skin on the shop, also changes the background
                pass

                # show buttons only if not on minigame
                if not self.shop.visible and (self.cur_minigame is None or not self.cur_minigame.active):
                    for b in self.buttons:
                        b.handle_event(event)

            # Update
            # if skin changes, background also does 
            self.update_background()

            if self.cur_minigame is not None and self.cur_minigame.active:
                self.cur_minigame.update(dt)
            else:
                self.pou.update(dt)

            # Draw
            if self.bg_img is not None:
                self.screen.blit(self.bg_img, (0, 0))
            else:
                self.screen.fill((32, 36, 40))

            if self.cur_minigame is not None and self.cur_minigame.active:
                self.cur_minigame.draw(self.screen, self.font)
            else:
                # floor / simple envirnment
                pygame.draw.rect(self.screen, (25, 25, 25), (0, HEIGHT - 110, WIDTH, 110))
                pygame.draw.rect(self.screen, (60, 60, 60), (0, HEIGHT - 110, WIDTH, 4))

                # pou
                self.pou.draw(self.screen)

                # HUD and buttons
                self.hud.draw(self.screen, self.font)
                if not self.shop.visible:
                    for b in self.buttons:
                        b.draw(self.screen, self.font)

                

                # Shop on top
                self.shop.draw(self.screen, self.font, self.bigfont)

            pygame.display.flip()
            self.clock.tick(FPS)

        # exit
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
        

