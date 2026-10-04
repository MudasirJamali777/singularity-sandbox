"""Singularity Sandbox - chhoti shuruaat."""

import pygame

from sandbox.config import (
    BACKGROUND_COLOR,
    FPS,
    PHYSICS_DT,
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

    # Bacha hua waqt - jab tak ek qadam ka na ho jaye.
    accumulator = 0.0

    running = True
    while running:
        # Pehle waqt naapo: tick() frame ko seemit karta hai.
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Click = nayi yaad.
                particles.spawn(*event.pos)
            elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                # Drag = yaadon ki lakeer.
                particles.spawn(*event.pos)

        # Jo waqt aaya, jama karo - phir barabar hisson mein kharch.
        accumulator += dt
        while accumulator >= PHYSICS_DT:
            physics.step(particles, PHYSICS_DT)
            accumulator -= PHYSICS_DT

        # Pehle saaf, phir dikhao, phir parda.
        screen.fill(BACKGROUND_COLOR)
        renderer.draw_particles(screen, particles)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()