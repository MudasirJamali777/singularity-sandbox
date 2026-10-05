"""Jo bana hai, usay dikhana. Sirf padhna - chhedna nahi."""

from __future__ import annotations

import pygame

from sandbox.config import (
    HUD_COLOR,
    HUD_FONT_SIZE,
    HUD_MARGIN,
    HUD_PAUSED_COLOR,
    PARTICLE_COLOR,
    PARTICLE_RADIUS,
)
from sandbox.particles import ParticleSystem


class Renderer:
    """Particles aur HUD ko surface par utaarna.

    Attributes:
        radius: circle ki tajzi (radius), pixels mein.
        color: particle ka rang, (R, G, B).
        font_size: HUD ke text ka size.
        hud_color, paused_color: HUD ke rang.
    """

    def __init__(
        self,
        radius: int = PARTICLE_RADIUS,
        color: tuple[int, int, int] = PARTICLE_COLOR,
        font_size: int = HUD_FONT_SIZE,
        hud_color: tuple[int, int, int] = HUD_COLOR,
        paused_color: tuple[int, int, int] = HUD_PAUSED_COLOR,
    ) -> None:
        self.radius = radius
        self.color = color
        self.font_size = font_size
        self.hud_color = hud_color
        self.paused_color = paused_color
        # Font lazily banta hai - pygame.init() se pehle banaya to error.
        self._font: pygame.font.Font | None = None

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

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def draw_hud(
        self,
        surface: pygame.Surface,
        fps: float,
        particle_count: int,
        paused: bool = False,
    ) -> None:
        """FPS, particle count - aur agar ruka hua hai to ``PAUSED``.

        Sirf padhta hai: apni marzi se kuch nahi banata, na hisaab badalta.
        """
        font = self._hud_font()
        text = f"FPS {fps:4.0f}   Particles {particle_count}"
        label = font.render(text, True, self.hud_color)
        surface.blit(label, (HUD_MARGIN, HUD_MARGIN))

        if paused:
            note = font.render("PAUSED", True, self.paused_color)
            surface.blit(note, (HUD_MARGIN, HUD_MARGIN + label.get_height() + 4))

    def _hud_font(self) -> pygame.font.Font:
        """Font ek baar banao, phir wahi use karo.

        ``pygame.font`` khud check karke init karte hain, taake HUD kisi bhi
        order mein bulane par chale.
        """
        if not pygame.font.get_init():
            pygame.font.init()
        if self._font is None:
            self._font = pygame.font.Font(None, self.font_size)
        return self._font
