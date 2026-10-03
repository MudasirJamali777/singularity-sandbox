import pygame

from sandbox.config import (
    BACKGROUND_COLOR,
    FPS,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from sandbox.particles import ParticleSystem
from sandbox.renderer import Renderer


def main() -> None:
    """Boot Pygame, open the window, and run the main loop."""
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    particles = ParticleSystem()
    renderer = Renderer()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left click drops a permanent particle at the cursor.
                particles.spawn(*event.pos)

        screen.fill(BACKGROUND_COLOR)
        renderer.draw_particles(screen, particles)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()