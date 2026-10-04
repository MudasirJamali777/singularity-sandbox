"""Jo bana hai, usay dikhana. Sirf padhna - chhedna nahi."""

from __future__ import annotations

import pygame

from sandbox.config import PARTICLE_COLOR, PARTICLE_RADIUS
from sandbox.particles import ParticleSystem


class Renderer:
    """Particles ko surface par utaarna.

    Attributes:
        radius: circle ki tajzi (radius), pixels mein.
        color: particle ka rang, (R, G, B).
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
        """Har zinda particle = chhota bhara circle.

        Sirf active slice par nazar. Drawing surface ke upar hoti hai,
        isliye pehle background se fill karna zaroori hai.

        Args:
            surface: jis par banayein, aam taur par screen.
            particles: sirf padha jaayega.
        """
        # Loop mein attribute dhoondhna mehnga - pehle pakad lo.
        draw_circle = pygame.draw.circle
        radius = self.radius
        color = self.color

        for x, y in particles.active_positions:
            # Pygame ko poore number chahiye, decimal nahi.
            draw_circle(surface, color, (int(x), int(y)), radius)