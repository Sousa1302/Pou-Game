import pygame
import sys

class Menu:
    def __init__(self, width=1920, height=1080, background_path=None):
        # Initialization
        pygame.init()
        self.WIDTH = width
        self.HEIGHT = height
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Tony vs Trompete")

        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BUTTON_BG = (240, 245, 255)
        self.BUTTON_BORDER = (100, 100, 100)
        self.EXIT_BUTTON_BG = (200, 0, 0)
        self.TITLE_COLOR = (255, 255, 0)  # Yellow
        self.TITLE_SHADOW = (0, 0, 0)     # Black shadow

        # Fonts
        self.TITLE_FONT = pygame.font.SysFont("comicsansms", 70, bold=True)
        self.BUTTON_FONT = pygame.font.SysFont("comicsansms", 40, bold=True)

        # Background
        if background_path:
            self.background = pygame.image.load(background_path)
            self.background = pygame.transform.scale(self.background, (self.WIDTH, self.HEIGHT))
        else:
            self.background = None

        # Clock
        self.clock = pygame.time.Clock()
        self.FPS = 60

        # Buttons
        self.buttons = []
        self.create_buttons()

    class Button:
        def __init__(self, rect, text, bg_color):
            self.rect = pygame.Rect(rect)
            self.text = text
            self.bg_color = bg_color

        def draw(self, surf, font, border_color):
            mouse_pos = pygame.mouse.get_pos()
            is_hover = self.rect.collidepoint(mouse_pos)

            # Darker color on hover
            color = tuple(max(0, c - 30) for c in self.bg_color) if is_hover else self.bg_color

            pygame.draw.rect(surf, color, self.rect, border_radius=15)
            pygame.draw.rect(surf, border_color, self.rect, 3, border_radius=15)

            txt = font.render(self.text, True, (0, 0, 0))
            txt_rect = txt.get_rect(center=self.rect.center)
            surf.blit(txt, txt_rect)

        def is_clicked(self, pos):
            return self.rect.collidepoint(pos)

    def create_buttons(self):
        button_width = 400
        button_height = 80
        center_x = self.WIDTH // 2 - button_width // 2
        start_y = 400
        spacing = 150

        self.buttons.append(self.Button((center_x, start_y, button_width, button_height), "Create Game", self.BUTTON_BG))
        self.buttons.append(self.Button((center_x, start_y + spacing, button_width, button_height), "Join Game", self.BUTTON_BG))
        self.buttons.append(self.Button((center_x, start_y + 2 * spacing, button_width, button_height), "Exit", self.EXIT_BUTTON_BG))

    def run(self):
        running = True
        while running:
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill(self.WHITE)

            # Title with shadow
            title_text = "Tony vs Trompete"
            title_render = self.TITLE_FONT.render(title_text, True, self.TITLE_COLOR)
            title_shadow = self.TITLE_FONT.render(title_text, True, self.TITLE_SHADOW)

            x = self.WIDTH // 2 - title_render.get_width() // 2
            y = 100

            # Draw shadow first (offset)
            self.screen.blit(title_shadow, (x + 4, y + 4))
            # Draw main title
            self.screen.blit(title_render, (x, y))

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if self.buttons[0].is_clicked(pos):
                        print("Create Game clicked")
                    elif self.buttons[1].is_clicked(pos):
                        print("Join Game clicked")
                    elif self.buttons[2].is_clicked(pos):
                        print("Exit clicked")
                        running = False

            # Draw buttons
            for btn in self.buttons:
                btn.draw(self.screen, self.BUTTON_FONT, self.BUTTON_BORDER)

            pygame.display.flip()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()

# Save game
import os
import json

class GameSave:
    def __init__(self, save_file="pou_save.json"):
        self.save_file = save_file

    def save(self, status, visual):
        """Guarda o estado atual do jogo num ficheiro JSON."""
        data = {
            "status": status,
            "visual": visual
        }
        with open(self.save_file, "w") as f:
            json.dump(data, f)
        print("💾 Jogo guardado com sucesso!")

    def load(self):
        """Carrega o estado do jogo a partir do ficheiro JSON, se existir."""
        if os.path.exists(self.save_file):
            with open(self.save_file, "r") as f:
                data = json.load(f)
                print("📂 Jogo carregado com sucesso!")
                return (
                    data.get("status", {
                        "hunger": 100,
                        "clean": 100,
                        "sleep": 100,
                        "happy": 100
                    }),
                    data.get("visual", {
                        "color": (139, 69, 19),
                        "hat": None,
                        "glasses": None
                    })
                )
        else:
            print("⚠️ Nenhum ficheiro de gravação encontrado. A iniciar novo jogo.")
            return (
                {
                    "hunger": 100,
                    "clean": 100,
                    "sleep": 100,
                    "happy": 100
                },
                {
                    "color": (139, 69, 19),
                    "hat": None,
                    "glasses": None
                }
            )



# Example usage
if __name__ == "__main__":
    menu = Menu(background_path=r"C:\Users\gmf40\Desktop\Pou_pyG\Pou-Game\brancoback-fotor-enhance-20251020161916.jpg")
    menu.run()
