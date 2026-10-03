"""Rendering for Singularity Sandbox.

The renderer is a strict consumer of particle data. Given a Pygame surface
and a ParticleSystem it draws the active particles and nothing else: it
never spawns, removes, or otherwise modifies particles.
"""

from __future__ import annotations

import pygame

from sandbox.config import PARTICLE_COLOR, PARTICLE_RADIUS
from sandbox.particles import ParticleSystem


class Renderer:
    """Draws simulation state onto a Pygame surface.

    Attributes:
        radius: Circle radius in pixels used for every particle.
        color: RGB tuple used to fill each particle circle.
    """

    def __init__(
        self,
        radius: int = PARTICLE_RADIUS,
        color: tuple[int, int, int] = PARTICLE_COLOR,
    ) -> None:
        self.radius = radius
        self.color = color

    def draw_particles(
        self,
        surface: pygame.Surface,
        particles: ParticleSystem,
    ) -> None:
        """Draw every active particle as a small filled circle.

        Only the active slice of the position buffer is visited, so the
        unused preallocated slots cost nothing at draw time. The surface is
        drawn on top of: fill it with the background colour first.

        Args:
            surface: Target Pygame surface, typically the display screen.
            particles: The system to read positions from. Read only.
        """
        # Bind locals so the hot loop avoids attribute lookups per particle.
        draw_circle = pygame.draw.circle
        radius = self.radius
        color = self.color

        for x, y in particles.active_positions:
            # Pygame's draw calls want integer screen coordinates.
            draw_circle(surface, color, (int(x), int(y)), radius)