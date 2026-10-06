"""Jo bana hai, usay dikhana. Sirf padhna - chhedna nahi."""

from __future__ import annotations

import math

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
from sandbox.spatial import SpatialHash


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
    # Spatial-hash debug overlay
    # ------------------------------------------------------------------
    def draw_spatial_grid(
        self,
        surface: pygame.Surface,
        spatial_hash: SpatialHash,
    ) -> None:
        """Outline occupied cells without changing the spatial hash.

        Cell outlines are blue for sparse cells, yellow for busy cells, and
        red for especially crowded cells. The overlay is intentionally an
        observer: the renderer only consumes cell coordinates/populations.
        """
        cell_size = spatial_hash.cell_size
        screen_rect = surface.get_rect()

        for (cell_x, cell_y), population in spatial_hash.iter_occupied_cells():
            left = math.floor(cell_x * cell_size)
            top = math.floor(cell_y * cell_size)
            right = math.ceil((cell_x + 1) * cell_size)
            bottom = math.ceil((cell_y + 1) * cell_size)
            rect = pygame.Rect(left, top, max(1, right - left), max(1, bottom - top))
            if not screen_rect.colliderect(rect):
                continue

            if population <= 2:
                color = (55, 115, 185)       # sparse: blue
            elif population <= 5:
                color = (70, 195, 205)       # filling: cyan
            elif population <= 10:
                color = (245, 195, 65)       # crowded: yellow
            else:
                color = (245, 85, 75)        # very crowded: red
            pygame.draw.rect(surface, color, rect, 1)

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
        collisions_enabled: bool = False,
        candidate_pairs: int = 0,
        overlaps: int = 0,
        collision_time_ms: float = 0.0,
        spatial_debug: bool = False,
        occupied_cells: int = 0,
    ) -> None:
        """Show performance, simulation state, and collision diagnostics.

        Collision counts/time are from the most recent fixed physics step;
        overlap counts are resolution events summed across solver iterations.
        """
        font = self._font
        y = HUD_MARGIN
        collision_color = self.active_color if collisions_enabled else self.hud_color
        grid_color = self.active_color if spatial_debug else self.hud_color
        lines = (
            (f"FPS: {fps:.0f}", self.hud_color),
            (f"Particles: {particle_count:,} / {capacity:,}", self.hud_color),
            (
                "Physics: PAUSED" if paused else "Physics: RUNNING",
                self.paused_color if paused else self.active_color,
            ),
            (
                f"Collisions: {'ON' if collisions_enabled else 'OFF'}  (C)",
                collision_color,
            ),
            (
                f"Spatial grid: {'ON' if spatial_debug else 'OFF'}  (F1)"
                + (f" - {occupied_cells:,} cells" if spatial_debug else ""),
                grid_color,
            ),
            (
                f"Collision step: {candidate_pairs:,} candidates | "
                f"{overlaps:,} overlaps | {collision_time_ms:.2f} ms",
                self.hud_color,
            ),
        )

        for text, color in lines:
            surface.blit(font.render(text, True, color), (HUD_MARGIN, y))
            y += self._line_height
