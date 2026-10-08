"""Jo bana hai, usay dikhana. Sirf padhna - chhedna nahi."""

from __future__ import annotations

import math

import pygame
from numpy.typing import NDArray

from sandbox.config import (
    BRUSH_PREVIEW_COLOR,
    HUD_ACTIVE_COLOR,
    HUD_COLOR,
    HUD_FONT_SIZE,
    HUD_LINE_GAP,
    HUD_MARGIN,
    HUD_PAUSED_COLOR,
    MATTER,
    PARTICLE_COLOR,
    PARTICLE_RADIUS,
    SPH_REST_DENSITY,
    WATER,
    WATER_COLOR,
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
        water_color: tuple[int, int, int] = WATER_COLOR,
    ) -> None:
        self.radius = radius
        self.color = color
        self.water_color = water_color
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
        density: NDArray | None = None,
        density_debug: bool = False,
    ) -> None:
        """Draw matter and water, optionally coloring water by SPH density."""
        draw_circle = pygame.draw.circle
        radius = self.radius
        positions = particles.active_positions
        materials = particles.active_materials

        for index, (x, y) in enumerate(positions):
            if materials[index] == MATTER:
                color = self.color
            elif density_debug:
                water_density = float(density[index]) if density is not None else 0.0
                color = self._density_color(water_density)
            else:
                color = self.water_color
            draw_circle(surface, color, (int(x), int(y)), radius)

    @staticmethod
    def _density_color(density: float) -> tuple[int, int, int]:
        """Map low density to navy, rest density to cyan, and high to red."""
        ratio = max(0.0, density / max(SPH_REST_DENSITY, 1e-12))
        if ratio < 1.0:
            return Renderer._mix_color((8, 28, 105), (25, 225, 245), ratio)
        if ratio < 2.0:
            return Renderer._mix_color((25, 225, 245), (255, 220, 55), ratio - 1.0)
        return Renderer._mix_color((255, 220, 55), (250, 55, 45), min(1.0, (ratio - 2.0) / 2.0))

    @staticmethod
    def _mix_color(
        color_a: tuple[int, int, int],
        color_b: tuple[int, int, int],
        amount: float,
    ) -> tuple[int, int, int]:
        amount = min(1.0, max(0.0, amount))
        return (
            round(color_a[0] + (color_b[0] - color_a[0]) * amount),
            round(color_a[1] + (color_b[1] - color_a[1]) * amount),
            round(color_a[2] + (color_b[2] - color_a[2]) * amount),
        )

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
        tool_material: int = MATTER,
        water_count: int = 0,
        average_water_density: float = 0.0,
        sph_density_debug: bool = False,
        physics_step_time_ms: float = 0.0,
        sph_compute_time_ms: float = 0.0,
    ) -> None:
        """Show performance, simulation state, and collision diagnostics.

        Collision counts/time are from the most recent fixed physics step;
        overlap counts are corrections summed across solver iterations.
        Water density is the mean across active WATER particles.
        """
        font = self._font
        y = HUD_MARGIN
        collision_color = self.active_color if collisions_enabled else self.hud_color
        grid_color = self.active_color if spatial_debug else self.hud_color
        density_color = self.active_color if sph_density_debug else self.hud_color
        tool_name = "WATER" if tool_material == WATER else "MATTER"
        density_text = (
            f"Water density: {average_water_density:.4f} ({water_count:,})"
            if water_count
            else "Water density: --"
        )
        lines = (
            (f"FPS: {fps:.0f}", self.hud_color),
            (f"Particles: {particle_count:,} / {capacity:,}", self.hud_color),
            (
                "Physics: PAUSED" if paused else "Physics: RUNNING",
                self.paused_color if paused else self.active_color,
            ),
            (f"Tool: {tool_name}", self.active_color if tool_material == WATER else self.hud_color),
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
                f"SPH density view: {'ON' if sph_density_debug else 'OFF'}  (F2)",
                density_color,
            ),
            (density_text, self.hud_color),
            (
                f"Physics step: {physics_step_time_ms:.2f} ms "
                f"(SPH {sph_compute_time_ms:.2f} ms)",
                self.hud_color,
            ),
            (
                f"Collision step: {candidate_pairs:,} candidates | "
                f"{overlaps:,} corrections | {collision_time_ms:.2f} ms",
                self.hud_color,
            ),
        )

        for text, color in lines:
            surface.blit(font.render(text, True, color), (HUD_MARGIN, y))
            y += self._line_height