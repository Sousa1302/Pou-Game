import pygame
from gsousa import Pou

#pygame.init()
janela = pygame.display.set_mode((1920, 1080))
pygame.display.set_caption("Pou")

pou = Pou(900, 500, pasta_sprites="sprites")




pygame.quit()
