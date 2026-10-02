import pygame
import numpy as np


pygame.init()

screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Singularity Sandbox")

print("Pygame:", pygame.version.ver)
print("NumPy:", np.__version__)

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((8, 10, 18))

    pygame.display.flip()

pygame.quit()