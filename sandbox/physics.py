"""Verlet - raftaar store kiye baghair.

    next = current + (current - previous) + acceleration * dt**2

Farq hi chalna hai. Gravity sirf y par; Pygame mein y neeche jaata hai.
Farsh aa gaya - magar bounce nahi, sirf tham jaana.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import GRAVITY, PARTICLE_RADIUS, WINDOW_HEIGHT
from sandbox.particles import ParticleSystem


class PhysicsSystem:
    """Ek chhoti dhadkan - sab ko aage badha dena.

    Attributes:
        gravity: neeche ki kheench, pixels per second squared.
        floor: sabse neeche wala y, jahan particle ka markaz rukta hai.
    """

    def __init__(
        self,
        gravity: float = GRAVITY,
        floor: float = WINDOW_HEIGHT - PARTICLE_RADIUS,
    ) -> None:
        self.gravity = float(gravity)
        # Radius jitna upar - warna aadha particle screen se bahar jhaankega.
        self.floor = float(floor)
        # Sirf y ki taraf kheench.
        self._acceleration: NDArray[np.float32] = np.array(
            (0.0, self.gravity), dtype=np.float32
        )
        # Scratch: ek baar bane, phir usi mein likhe.
        self._displacement: NDArray[np.float32] | None = None

    def step(self, particles: ParticleSystem, dt: float) -> None:
        """Har zinda particle ko ``dt`` second aage badhao, phir farsh sambhalo.
        ...
        """
        count = particles.count
        if count == 0:
            return

        current = particles.active_positions
        previous = particles.active_previous_positions

        displacement = self._displacement_scratch(particles.capacity)[:count]
        np.subtract(current, previous, out=displacement)

        # History: qadam se pehle kahan tha.
        np.copyto(previous, current)

        current += displacement
        current += self._acceleration * (dt * dt)

        self._apply_floor(current, previous)

    # ------------------------------------------------------------------
    # Farsh
    # ------------------------------------------------------------------
    def _apply_floor(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
    ) -> None:
        """Farsh se neeche wale sab ko farsh par rok do.

        Sirf ``current`` dabana kaafi nahi. Verlet mein raftaar
        ``current - previous`` hai, isliye ``previous`` bhi farsh par laana
        padta hai - warna farq ulta reh jaata aur particle farsh se takra
        kar wapas uchhal padta. Dono barabar = y ki raftaar zero.

        Mask mein sirf wahi particles aate hain jo farsh se neeche hain,
        isliye hawa mein udte hue bilkul na chhue jaate hain.
        """
        below = current[:, 1] > self.floor
        if below.any():
            current[below, 1] = self.floor
            previous[below, 1] = self.floor