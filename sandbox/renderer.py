"""Jo bana hai, usay dikhana. Sirf padhna - chhedna nahi."""

from __future__ import annotations

import pygame

from sandbox.config import (
    ATTRACTOR_PREVIEW_COLOR,
    BACKGROUND_COLOR,
    BRUSH_PREVIEW_COLOR,
    DEBUG_CELL_ALPHA,
    DEBUG_CELL_COLORS,
    EXPLOSION_FLASH_COLOR,
    EXPLOSION_FLASH_SECONDS,
    EXPLOSION_PREVIEW_COLOR,
    HUD_ACTIVE_COLOR,
    HUD_COLOR,
    HUD_FONT_SIZE,
    HUD_HELP_COLOR,
    HUD_LINE_GAP,
    HUD_MARGIN,
    HUD_OFF_COLOR,
    HUD_PAUSED_COLOR,
    HUD_TOOL_COLOR,
    PARTICLE_COLOR,
    PARTICLE_RADIUS,
    WELL_CORE_COLOR,
    WELL_CORE_RADIUS,
    WELL_DOT_COLOR,
    WELL_DOT_RADIUS,
    WELL_FIELD_COLOR,
    WELL_FIELD_SCALE,
    WELL_PREVIEW_COLOR,
    WELL_RING_COLOR,
    WELL_VISUAL_RADIUS,
)
from sandbox.gravity import GravityWells
from sandbox.input import TOOL_ORDER, Tool
from sandbox.particles import ParticleSystem
from sandbox.spatial import SpatialHash


def _fade(
    color: tuple[int, int, int],
    background: tuple[int, int, int],
    k: float,
) -> tuple[int, int, int]:
    """Rang ko background ki taraf khiskao - jhalak dheemi hone ke liye."""
    return tuple(int(b + (c - b) * k) for c, b in zip(color, background))


class Renderer:
    """Particles, kuan, dhamake ki jhalak, auzaar ka hala, aur HUD.

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
        well_color: tuple[int, int, int] = WELL_PREVIEW_COLOR,
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
            Tool.WELL: well_color,
        }
        # Font ek hi baar - har frame naya banane ka koi faida nahi.
        # pygame.font khud sambhal leta hai agar abhi init na hua ho.
        if not pygame.font.get_init():
            pygame.font.init()
        self._font: pygame.font.Font = pygame.font.Font(None, self.font_size)
        self._line_height = self._font.get_height() + HUD_LINE_GAP
        # HUD ke neeche chhota sa ishara - kaunsa number kis auzaar ka.
        self._help_text = "  ".join(
            f"[{i}] {tool.value.title()}" for i, tool in enumerate(TOOL_ORDER, 1)
        )
        # Dhamakon ki yaadein - sirf nazar, koi particle nahi.
        self._flashes: list[tuple[float, float, float]] = []
        # Debug grid yahan banta hai (ek hi baar), taake har frame naya
        # surface na ho. Yeh sirf padha jaata hai - naqsha waisa hi rehta
        # hai jaisa physics ne chhoda tha.
        self._overlay: pygame.Surface | None = None
        # Chhota ishara - kaunsi key kaunsa kaam karti hai.
        self._keys_text = (
            "[Space] Pause  [R] Reset  [G] Gravity  [B] Walls  "
            "[C] Collisions  [F1] Grid"
        )

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
    # Kuan
    # ------------------------------------------------------------------
    def draw_wells(self, surface: pygame.Surface, wells: GravityWells) -> None:
        """Har kuan apni alag shakal mein - particles jaise bilkul nahi.

        Andar kala dil, upar banafshi ring, aur bahar dheemi field ka hala -
        isse nazar turant pehchaan leti hai ke yeh duniya ka hissa hai, koi
        particle nahi. Yahan sirf padha jaata hai, kuch banaya nahi jaata.
        """
        for x, y in wells.active_positions:
            center = (int(x), int(y))
            pygame.draw.circle(surface, WELL_FIELD_COLOR, center, int(WELL_VISUAL_RADIUS * WELL_FIELD_SCALE), 1)
            pygame.draw.circle(surface, WELL_CORE_COLOR, center, WELL_CORE_RADIUS)
            pygame.draw.circle(surface, WELL_RING_COLOR, center, WELL_VISUAL_RADIUS, 2)
            pygame.draw.circle(surface, WELL_DOT_COLOR, center, WELL_DOT_RADIUS)

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
    # Debug grid
    # ------------------------------------------------------------------
    def draw_debug_grid(
        self,
        surface: pygame.Surface,
        spatial: SpatialHash,
    ) -> None:
        """Bhare hue khane - jo naqsha padosi dhoondhta hai, wohi nazar aaye.

        Sirf bhare khane khinchay jaate hain (khaali screen par 25,000 se
        zyada khane hote hain - sab par rect lagana waqt ka zaya). Rang
        batata hai ke khana kitna bhara hai: halka neela se lal tak.

        Yahan naqsha sirf padha jaata hai: ``occupied_cells`` se aayi hui
        fehristen chhui nahi jaati, na ``rebuild`` idhar hota hai.
        """
        cells_x, cells_y, counts = spatial.occupied_cells()
        if counts.size == 0:
            return

        overlay = self._overlay
        if overlay is None or overlay.get_size() != surface.get_size():
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._overlay = overlay
        # Pichhle frame ke khane yahin mit jate hain.
        overlay.fill((0, 0, 0, 0))

        size = max(1, int(round(spatial.cell_size)))
        steps = len(DEBUG_CELL_COLORS)
        draw_rect = pygame.draw.rect
        colors, alphas = DEBUG_CELL_COLORS, DEBUG_CELL_ALPHA
        for cx, cy, filled in zip(cells_x.tolist(), cells_y.tolist(), counts.tolist()):
            # Ek particle = sabse thanda, aur zyada par garam rang.
            rank = min(filled, steps) - 1
            rect = (cx * size, cy * size, size, size)
            draw_rect(overlay, (*colors[rank], alphas[rank]), rect)
            # Patla kinara: bhare hue khane dher ke upar bhi nazar aayein,
            # warna particles khud hi unhe dhaanp dete hain.
            draw_rect(overlay, (*colors[rank], min(255, alphas[rank] + 80)), rect, 1)
        surface.blit(overlay, (0, 0))

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
        well_count: int = 0,
        well_capacity: int = 0,
        world_gravity: bool = True,
        boundaries: bool = True,
        collisions: bool = True,
        debug_grid: bool = False,
    ) -> None:
        """FPS, hisaab, switches, aur haath ka auzaar - sab ek jagah.

        Sirf padhta hai: apni marzi se kuch nahi banata, na hisaab badalta.

            FPS: 60
            Particles: 1,247 / 10,000
            Wells: 2 / 32
            Physics: RUNNING
            World Gravity: ON   Boundaries: ON
            Collisions: ON   Grid: OFF
            Tool: GRAVITY WELL
            [1] Brush  [2] Attractor  [3] Explosion  [4] Gravity Well
            [Space] Pause  [R] Reset  [G] Gravity  ...
        """
        font = self._font
        on, off = self.hud_color, HUD_OFF_COLOR
        lines = (
            [(f"FPS: {fps:.0f}", self.hud_color)],
            [(f"Particles: {particle_count:,} / {capacity:,}", self.hud_color)],
            [(f"Wells: {well_count} / {well_capacity}", self.hud_color)],
            [
                (
                    "Physics: PAUSED" if paused else "Physics: RUNNING",
                    self.paused_color if paused else self.active_color,
                )
            ],
            [
                ("World Gravity: ON" if world_gravity else "World Gravity: OFF", self.active_color if world_gravity else HUD_OFF_COLOR),
                ("   Boundaries: ON" if boundaries else "   Boundaries: OFF", on if boundaries else off),
            ],
            [
                ("Collisions: ON" if collisions else "Collisions: OFF", self.active_color if collisions else HUD_OFF_COLOR),
                ("   Grid: ON" if debug_grid else "   Grid: OFF", on if debug_grid else off),
            ],
            [(f"Tool: {tool_label}", HUD_TOOL_COLOR)],
            [(self._help_text, HUD_HELP_COLOR)],
            [(self._keys_text, HUD_HELP_COLOR)],
        )

        y = HUD_MARGIN
        for segments in lines:
            x = HUD_MARGIN
            for text, color in segments:
                image = font.render(text, True, color)
                surface.blit(image, (x, y))
                x += image.get_width()
            y += self._line_height