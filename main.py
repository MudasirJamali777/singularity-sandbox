"""Singularity Sandbox - chhoti shuruaat."""
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
    """Pygame jagaao, khirki kholo, loop chalao."""
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # Teen saathi - yaadein, roshni, kheench.
    particles = ParticleSystem()
    renderer = Renderer()
    physics = PhysicsSystem()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Click = nayi yaad.
                particles.spawn(*event.pos)
            elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                # Drag = yaadon ki lakeer.
                particles.spawn(*event.pos)

        # tick() ka waqt sacch hai - FPS ka number nahi.
        dt = clock.tick(FPS) / 1000.0
        physics.step(particles, dt)

        # Pehle saaf, phir dikhao, phir parda.
        screen.fill(BACKGROUND_COLOR)
        renderer.draw_particles(screen, particles)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()