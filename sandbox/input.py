"""Brush - haath ki harkat ko yaadon ki lakeer mein badalna.

Yeh sirf sochta hai ke *kahan* paint karna hai. Particles banane ka kaam
``ParticleSystem`` ka hai - input data nahi likhta, sirf nishaan deta hai.
"""

from __future__ import annotations

import math

from sandbox.config import (
    BRUSH_MAX_RADIUS,
    BRUSH_MAX_SAMPLES,
    BRUSH_MIN_RADIUS,
    BRUSH_RADIUS,
    BRUSH_SPACING,
    BRUSH_WHEEL_STEP,
    MATTER,
    WATER,
)


class Brush:
    """Brush ka dil - radius, aur pichhli lakeer ka nishaan.

    Attributes:
        radius: spawn area ka radius, pixels mein (particle ke radius se alag).
        material: material ID selected for subsequent strokes.
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
        self.material = MATTER
        self.last_pos: tuple[float, float] | None = None

    def _clamp(self, radius: float) -> int:
        return int(max(self.min_radius, min(self.max_radius, radius)))

    def resize(self, direction: int) -> None:
        """Wheel ghumao, brush bada ya chhota karo.

        ``direction``: +1 upar (bada), -1 neeche (chhota).
        """
        steps = 1 if direction > 0 else -1 if direction < 0 else 0
        if steps:
            self.radius = self._clamp(self.radius + steps * self.wheel_step)

    def select_material(self, material: int) -> None:
        """Select MATTER or WATER for new particles."""
        if material not in (MATTER, WATER):
            raise ValueError(f"unsupported material ID: {material}")
        self.material = int(material)

    @property
    def spacing(self) -> float:
        """Do brush nishanon ke beech ki doori.

        Radius se bandhi hai - bada brush zyada overlap deta hai, chhota
        brush meen bara. Kam se kam 1 pixel, warna bekaar ke samples.
        """
        return max(self.radius * BRUSH_SPACING, 1.0)

    def centers_to(self, pos: tuple[int, int]) -> list[tuple[float, float]]:
        """Pichhle nishaan se yahan tak ke brush centers.

        Sirf centers interpolate hote hain - particles nahi. Isse tez drag
        mein bhi lakeer tootti nahi. Ek event par samples ki hadd rehti hai,
        warna ek jhatke se hazaron particles aa jate.
        """
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