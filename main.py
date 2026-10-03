import pygame

from sandbox.config import (
    BACKGROUND_COLOR,
    FPS,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from sandbox.particles import ParticleSystem
from sandbox.physics import PhysicsSystem
from sandbox.renderer import Renderer


def main() -> None:
    """Boot Pygame, open the window, and run the main loop."""
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    particles = ParticleSystem()
    renderer = Renderer()
    physics = PhysicsSystem()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left click drops a permanent particle at the cursor.
                particles.spawn(*event.pos)
            elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                # Left button held while moving: paint a particle here too.
                particles.spawn(*event.pos)

        # tick() returns the milliseconds elapsed since the previous frame,
        # so physics advances by real time rather than by the FPS target.
        dt = clock.tick(FPS) / 1000.0
        physics.step(particles, dt)

        screen.fill(BACKGROUND_COLOR)
        renderer.draw_particles(screen, particles)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()