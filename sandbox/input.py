"""Brush - haath ki harkat ko yaadon ki lakeer mein badalna.

Yeh sirf sochta hai ke *kahan* paint karna hai. Particles banane ka kaam
``ParticleSystem`` ka hai - input data nahi likhta, sirf nishaan deta hai.
"""

from __future__ import annotations

import math
from enum import Enum

from sandbox.config import (
    BRUSH_MAX_RADIUS,
    BRUSH_MAX_SAMPLES,
    BRUSH_MIN_RADIUS,
    BRUSH_RADIUS,
    BRUSH_SPACING,
    BRUSH_WHEEL_STEP,
)


class Tool(Enum):
    """Chaar auzaar - banane, kheenchne, udaane, aur kuan gerna."""

    BRUSH = "BRUSH"
    ATTRACTOR = "ATTRACTOR"
    EXPLOSION = "EXPLOSION"
    WELL = "GRAVITY WELL"


# HUD aur keyboard dono isi tarteeb par chalte hain: 1, 2, 3, 4.
TOOL_ORDER: tuple[Tool, ...] = (Tool.BRUSH, Tool.ATTRACTOR, Tool.EXPLOSION, Tool.WELL)


class ToolState:
    """Haath mein kaunsa auzaar hai.

    Sirf brush particles banata hai. Doosre auzaaron mein uski ``nav`` band
    ho jaati hai (radius 0) - isliye galti se drag karne par particles nahi
    baraste, chahe koi bhi event aaye.
    """

    def __init__(self, tool: Tool = Tool.BRUSH, brush: Brush | None = None) -> None:
        self._tool = tool
        self._brush_radius = brush.radius if brush is not None else BRUSH_RADIUS
        self._apply(brush)

    @property
    def selected(self) -> Tool:
        """Abhi chuna hua auzaar."""
        return self._tool

    @property
    def label(self) -> str:
        """Auzaar ka naam - HUD ke liye, aur bas."""
        return self._tool.value

    def select(self, tool: Tool, brush: Brush | None = None) -> bool:
        """Auzaar badlo - ``True`` agar waqai badla."""
        if tool is self._tool:
            return False
        self._tool = tool
        self._apply(brush)
        return True

    def _apply(self, brush: Brush | None) -> None:
        """Brush ki nav sirf brush mode mein chalti hai - warna band.

        Yaad sirf chalti hui nav se rakhi jaati hai - ek auzaar se doosra
        auzaar chunte waqt band nav (0) purane radius par daagh nahi lagati.
        """
        if brush is None:
            return
        if self._tool is Tool.BRUSH:
            brush.restore(self._brush_radius)
        else:
            if brush.radius > 0:
                self._brush_radius = brush.radius
            brush.disable()

    def __repr__(self) -> str:
        return f"ToolState(selected={self._tool.value})"


class Brush:
    """Brush ka dil - radius, aur pichhli lakeer ka nishaan.

    Attributes:
        radius: spawn area ka radius, pixels mein (particle ke radius se alag).
        last_pos: pichhla brush center, taake tez jhatke mein beech ke
            nishaan bhi ban sakein.
    """

    def __init__(
        self,
        radius: int = BRUSH_RADIUS,
        min_radius: int = BRUSH_MIN_RADIUS,
        max_radius: int = BRUSH_MAX_RADIUS,
        wheel_step: int = BRUSH_WHEEL_STEP,
    ) -> None:
        self.min_radius = int(min_radius)
        self.max_radius = int(max_radius)
        self.wheel_step = int(wheel_step)
        self.radius = self._clamp(radius)
        self.last_pos: tuple[float, float] | None = None

    # ------------------------------------------------------------------
    # Size
    # ------------------------------------------------------------------
    def _clamp(self, radius: float) -> int:
        return int(max(self.min_radius, min(self.max_radius, radius)))

    def resize(self, direction: int) -> None:
        """Wheel ghumao, brush bada ya chhota karo.

        ``direction``: +1 upar (bada), -1 neeche (chhota). Nav band ho to
        wheel bilkul khamosh rehta hai.
        """
        if self.radius <= 0:
            return
        steps = 1 if direction > 0 else -1 if direction < 0 else 0
        if steps:
            self.radius = self._clamp(self.radius + steps * self.wheel_step)

    def disable(self) -> None:
        """Nav band - ab koi nishaan nahi banega (doosra auzaar chal raha hai)."""
        self.lift()
        self.radius = 0

    def restore(self, radius: int | None = None) -> None:
        """Nav wapas - pichhla radius, ya default agar yaad na ho."""
        self.radius = self._clamp(BRUSH_RADIUS if radius is None else radius)

    @property
    def spacing(self) -> float:
        """Do brush nishanon ke beech ki doori.

        Radius se bandhi hai - bada brush zyada overlap deta hai, chhota
        brush halki lakeer. Kam se kam 1 pixel, warna bekaar ke samples.
        """
        return max(self.radius * BRUSH_SPACING, 1.0)

    # ------------------------------------------------------------------
    # Lakeer
    # ------------------------------------------------------------------
    def centers_to(self, pos: tuple[int, int]) -> list[tuple[float, float]] | None:
        """Pichhle nishaan se yahan tak ke brush centers.

        Sirf centers interpolate hote hain - particles nahi. Isse tez drag
        mein bhi lakeer tootti nahi. Ek event par samples ki hadd rehti hai,
        warna ek jhatke se hazaron particles aa jate.

        Nav band ho (doosra auzaar) to ``None`` - is haath ka koi kaam nahi.
        """
        if self.radius <= 0:
            return None

        x, y = float(pos[0]), float(pos[1])
        if self.last_pos is None:
            self.last_pos = (x, y)
            return [(x, y)]

        x0, y0 = self.last_pos
        dx, dy = x - x0, y - y0
        dist = math.hypot(dx, dy)

        if dist < 1e-6:
            # Wahi jagah - dobara nishaan banao, taake brush bharta rahe.
            return [(x, y)]

        steps = min(max(int(dist / self.spacing), 1), BRUSH_MAX_SAMPLES)
        centers = [
            (x0 + dx * (i / steps), y0 + dy * (i / steps))
            for i in range(1, steps + 1)
        ]
        self.last_pos = (x, y)
        return centers

    def lift(self) -> None:
        """Brush utha liya - ab lakeer nayi jagah se shuru hogi."""
        self.last_pos = None

    def __repr__(self) -> str:
        return f"Brush(radius={self.radius}, spacing={self.spacing:.1f})"