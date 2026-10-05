"""Jo bana hai, usay dikhana. Sirf padhna - chhedna nahi."""

from __future__ import annotations

import pygame

from sandbox.config import (
    ATTRACTOR_PREVIEW_COLOR,
    BACKGROUND_COLOR,
    BRUSH_PREVIEW_COLOR,
    EXPLOSION_FLASH_COLOR,
    EXPLOSION_FLASH_SECONDS,
    EXPLOSION_PREVIEW_COLOR,
    HUD_ACTIVE_COLOR,
    HUD_COLOR,
    HUD_FONT_SIZE,
    HUD_HELP_COLOR,
    HUD_LINE_GAP,
    HUD_MARGIN,
    HUD_PAUSED_COLOR,
    HUD_TOOL_COLOR,
    PARTICLE_COLOR,
    PARTICLE_RADIUS,
)
from sandbox.input import TOOL_ORDER, Tool
from sandbox.particles import ParticleSystem

def _fade(
    color: tuple[int, int, int],
    background: tuple[int, int, int],
    k: float,
) -> tuple[int, int, int]:
    """Rang ko background ki taraf khiskao - jhalak dheemi hone ke liye."""
    return tuple(int(b + (c - b) * k) for c, b in zip(color, background))

class Renderer:
    """Particles, brush ka nishaan, dhamake ki jhalak, aur HUD.

    Attributes:
        radius: particle circle ki tajzi (radius), pixels mein.
        color: particle ka rang, (R, G, B).
        font_size: HUD ke text ka size.
        preview_colors: har auzaar ke hale ka rang.
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
        attractor_color: tuple[int, int, int] = ATTRACTOR_PREVIEW_COLOR,
        explosion_color: tuple[int, int, int] = EXPLOSION_PREVIEW_COLOR,
    ) -> None:
        self.radius = radius
        self.color = color
        self.font_size = font_size
        self.hud_color = hud_color
        self.paused_color = paused_color
        self.active_color = active_color
        self.preview_colors: dict[Tool, tuple[int, int, int]] = {
            Tool.BRUSH: preview_color,
            Tool.ATTRACTOR: attractor_color,
            Tool.EXPLOSION: explosion_color,
        }
        # Font ek hi baar - har frame naya banane ka koi faida nahi.
        # pygame.font khud sambhal leta hai agar abhi init na hua ho.
        if not pygame.font.get_init():
            pygame.font.init()
        self._font: pygame.font.Font = pygame.font.Font(None, self.font_size)
        self._line_height = self._font.get_height() + HUD_LINE_GAP
        # HUD ke neeche chhota sa ishara - kaunsa number kis auzaar ka.
        self._help_text = "  ".join(
            f"[{i}] {tool.value.capitalize()}" for i, tool in enumerate(TOOL_ORDER, 1)
        )
        # Dhamakon ki yaadein - sirf nazar, koi particle nahi.
        self._flashes: list[tuple[float, float, float]] = []

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
    # Dhamake ki jhalak
    # ------------------------------------------------------------------
    def add_flash(self, center: tuple[float, float], now: float) -> None:
        """Ek dhamaka hua - is lamhe ka nishaan yaad rakho."""
        self._flashes.append((float(center[0]), float(center[1]), float(now)))

    def clear_flashes(self) -> None:
        """Saari jhalak mitao - jaise reset par."""
        self._flashes.clear()

    def draw_flashes(
        self,
        surface: pygame.Surface,
        now: float,
        radius: float,
    ) -> None:
        """Kholta hua, dheema hota hala - pal bhar ka ujala.

        Purani jhalak yahin chhaant di jaati hai, isliye list khud saaf
        rehti hai. ``radius`` wohi hai jahan tak dhamake ka asar gaya tha.
        """
        ttl = EXPLOSION_FLASH_SECONDS
        self._flashes = [flash for flash in self._flashes if now - flash[2] < ttl]

        for x, y, born in self._flashes:
            # k: 1 se 0 tak - shuru mein tez, aakhir mein ghaib.
            k = max(1.0 - (now - born) / ttl, 0.0)
            ring = radius * (0.45 + 0.75 * (1.0 - k))
            width = 1 + int(3 * k)
            pygame.draw.circle(
                surface,
                _fade(EXPLOSION_FLASH_COLOR, BACKGROUND_COLOR, k),
                (int(x), int(y)),
                int(ring),
                width,
            )

    # ------------------------------------------------------------------
    # Auzaar ka hala
    # ------------------------------------------------------------------
    def draw_preview(
        self,
        surface: pygame.Surface,
        tool: Tool,
        radius: float,
        center: tuple[int, int],
    ) -> None:
        """Cursor ke gird patla sa hala - chune hue auzaar ka nishaan.

        Sirf nazar ka kaam: rang batata hai kaunsa auzaar haath mein hai,
        aur hala batata hai uska asar kahan tak pahunchega. Yahan kuch banta
        nahi, kuch badalta nahi.
        """
        color = self.preview_colors.get(tool, self.preview_colors[Tool.BRUSH])
        pygame.draw.circle(surface, color, center, max(1, int(radius)), 1)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def draw_hud(
        self,
        surface: pygame.Surface,
        fps: float,
        particle_count: int,
        capacity: int,
        tool_label: str,
        paused: bool = False,
    ) -> None:
        """FPS, particle ka hisaab, physics ka haal, aur haath ka auzaar.

        Sirf padhta hai: apni marzi se kuch nahi banata, na hisaab badalta.

            FPS: 60
            Particles: 1,247 / 10,000
            Physics: RUNNING
            Tool: ATTRACTOR
            [1] Brush  [2] Attractor  [3] Explosion
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
            (f"Tool: {tool_label}", HUD_TOOL_COLOR),
            (self._help_text, HUD_HELP_COLOR),
        ):
            surface.blit(font.render(text, True, color), (HUD_MARGIN, y))
            y += self._line_height