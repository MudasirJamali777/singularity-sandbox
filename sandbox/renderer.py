"""Jo bana hai, usay dikhana. Sirf padhna - chhedna nahi."""

from __future__ import annotations

import pygame

from sandbox.config import (
    BRUSH_PREVIEW_COLOR,
    HUD_ACTIVE_COLOR,
    HUD_COLOR,
    HUD_FONT_SIZE,
    HUD_LINE_GAP,
    HUD_MARGIN,
    HUD_PAUSED_COLOR,
    PARTICLE_COLOR,
    PARTICLE_RADIUS,
)
from sandbox.particles import ParticleSystem


class Renderer:
    """Particles, brush ka nishaan, aur HUD - sab surface par.

    Attributes:
        radius: particle circle ki tajzi (radius), pixels mein.
        color: particle ka rang, (R, G, B).
        font_size: HUD ke text ka size.
    """

    def __init__(
        self,
        radius: int = PARTICLE_RADIUS,
        color: tuple[int, int, int] = PARTICLE_COLOR,
        font_size: int = HUD_FONT_SIZE,
        hud_color: tuple[int, int, int] = HUD_COLOR,
        paused_color: tuple[int, int, int] = HUD_PAUSED_COLOR,
        active_color: tuple[int, int, int] = HUD_ACTIVE_COLOR,
        preview_color: tuple[int, int, int] = BRUSH_PREVIEW_COLOR,
    ) -> None:
        self.radius = radius
        self.color = color
        self.font_size = font_size
        self.hud_color = hud_color
        self.paused_color = paused_color
        self.active_color = active_color
        self.preview_color = preview_color
        # Font ek hi baar - har frame naya banane ka koi faida nahi.
        # pygame.font khud sambhal leta hai agar abhi init na hua ho.
        if not pygame.font.get_init():
            pygame.font.init()
        self._font: pygame.font.Font = pygame.font.Font(None, self.font_size)
        self._line_height = self._font.get_height() + HUD_LINE_GAP

    # ------------------------------------------------------------------
    # Particles
    # ------------------------------------------------------------------
    def draw_particles(
        self,
        surface: pygame.Surface,
        particles: ParticleSystem,
    ) -> None:
        """Har zinda particle = chhota bhara circle.

        Sirf active slice par nazar. Drawing surface ke upar hoti hai,
        isliye pehle background se fill karna zaroori hai.
        """
        # Loop mein attribute dhoondhna mehnga - pehle pakad lo.
        draw_circle = pygame.draw.circle
        radius = self.radius
        color = self.color

        for x, y in particles.active_positions:
            # Pygame ko poore number chahiye, decimal nahi.
            draw_circle(surface, color, (int(x), int(y)), radius)

    # ------------------------------------------------------------------
    # Brush ka nishaan
    # ------------------------------------------------------------------
    def draw_brush_preview(
        self,
        surface: pygame.Surface,
        radius: float,
        center: tuple[int, int],
    ) -> None:
        """Cursor ke gird patla sa circle - sirf nazar ke liye.

        Yahan kuch banta nahi, kuch badalta nahi - bas dikhaya jata hai.
        """
        pygame.draw.circle(surface, self.preview_color, center, int(radius), 1)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def draw_hud(
        self,
        surface: pygame.Surface,
        fps: float,
        particle_count: int,
        capacity: int,
        paused: bool = False,
    ) -> None:
        """FPS, particle ka hisaab, aur physics ka haal.

        Sirf padhta hai: apni marzi se kuch nahi banata, na hisaab badalta.

            FPS: 60
            Particles: 1,247 / 10,000
            Physics: RUNNING
        """
        font = self._font
        y = HUD_MARGIN

        for text, color in (
            (f"FPS: {fps:.0f}", self.hud_color),
            (f"Particles: {particle_count:,} / {capacity:,}", self.hud_color),
            (
                "Physics: PAUSED" if paused else "Physics: RUNNING",
                self.paused_color if paused else self.active_color,
            ),
        ):
            surface.blit(font.render(text, True, color), (HUD_MARGIN, y))
            y += self._line_height
