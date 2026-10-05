"""Singularity Sandbox - chhoti shuruaat."""

import pygame

from sandbox.config import (
    BACKGROUND_COLOR,
    FPS,
    PARTICLES_PER_STROKE,
    PHYSICS_DT,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from sandbox.input import Brush
from sandbox.particles import ParticleSystem
from sandbox.physics import PhysicsSystem
from sandbox.renderer import Renderer

def main() -> None:
    """Pygame jagaao, khirki kholo, loop chalao."""
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # Chaar saathi - yaadein, roshni, kheench, aur brush.
    particles = ParticleSystem()
    renderer = Renderer()
    physics = PhysicsSystem()
    brush = Brush()

    # Bacha hua waqt - jab tak ek qadam ka na ho jaye.
    accumulator = 0.0
    paused = False

    def paint(centers: list[tuple[float, float]]) -> None:
        """Har nishaan par brush bhar do - particles ka kaam ParticleSystem ka."""
        for cx, cy in centers:
            particles.spawn_disk(cx, cy, brush.radius, PARTICLES_PER_STROKE)

    running = True
    while running:
        # Pehle waqt naapo: tick() frame ko seemit karta hai.
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # Samaan wahi rahe - bas waqt ruk jaye. Toggle par bacha hua
                # waqt bhi saaf, warna unpause par chhota sa jhatka aata.
                paused = not paused
                accumulator = 0.0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # Sab kuch gayab - aur waqt ka hisaab bhi saaf.
                particles.clear()
                accumulator = 0.0
                brush.lift()
            elif event.type == pygame.MOUSEWHEEL:
                brush.resize(event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Nayi lakeer - purane nishaan se rishta nahi.
                brush.lift()
                paint(brush.centers_to(event.pos))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Haath chhod diya - lakeer yahin tamam.
                brush.lift()
            elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                # Drag = yaadon ki lakeer (beech ke nishaan bhi).
                paint(brush.centers_to(event.pos))

        # Jo waqt aaya, jama karo - phir barabar hisson mein kharch.
        # Ruke hue waqt mein kuch jama nahi hota, warna chhutte par toofan aata.
        if not paused:
            accumulator += dt
            while accumulator >= PHYSICS_DT:
                physics.step(particles, PHYSICS_DT)
                accumulator -= PHYSICS_DT

        # Pehle saaf, phir dikhao, phir nishaan, phir khabar, phir parda.
        screen.fill(BACKGROUND_COLOR)
        renderer.draw_particles(screen, particles)

        mouse = pygame.mouse.get_pos()
        if pygame.mouse.get_focused() and 0 <= mouse[0] < WINDOW_WIDTH and 0 <= mouse[1] < WINDOW_HEIGHT:
            renderer.draw_brush_preview(screen, brush.radius, mouse)

        renderer.draw_hud(screen, clock.get_fps(), particles.count, particles.capacity, paused)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()