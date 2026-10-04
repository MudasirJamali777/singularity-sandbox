"""Verlet - raftaar store kiye baghair.

    next = current + (current - previous) + acceleration * dt**2

Farq hi chalna hai. Gravity sirf y par; Pygame mein y neeche jaata hai.
Farsh aa gaya - magar bounce nahi, sirf tham jaana.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import BOUNCE, GRAVITY, PARTICLE_RADIUS, WINDOW_HEIGHT
from sandbox.particles import ParticleSystem


class PhysicsSystem:
    """Ek chhoti dhadkan - sab ko aage badha dena.

    Attributes:
        gravity: neeche ki kheench, pixels per second squared.
        floor: sabse neeche wala y, jahan particle ka markaz rukta hai.
        bounce: farsh se kitni raftaar wapas, 0.0 se 1.0 tak.
    """

    def __init__(
        self,
        gravity: float = GRAVITY,
        floor: float = WINDOW_HEIGHT - PARTICLE_RADIUS,
        bounce: float = BOUNCE,
    ) -> None:
        self.gravity = float(gravity)
        # Radius jitna upar - warna aadha particle screen se bahar jhaankega.
        self.floor = float(floor)
        self.bounce = float(bounce)
        # Sirf y ki taraf kheench.
        self._acceleration: NDArray[np.float32] = np.array(
            (0.0, self.gravity), dtype=np.float32
        )
        # Scratch: ek baar bane, phir usi mein likhe.
        self._displacement: NDArray[np.float32] | None = None

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def step(self, particles: ParticleSystem, dt: float) -> None:
        """Har zinda particle ko ``dt`` second aage badhao, phir farsh sambhalo.

        Tarteeb hi asal baat hai - dono views seedha storage mein jhankti hain:

        1. Pehle farq (current - previous) scratch mein.
        2. Phir current ko history mein likho. Yeh pehle kiya to wahi farq
           mit jaata - aur raftaar chupchaap kho jaati.
        3. Aakhir mein current aage badhao, phir farsh par utaaro.

        ``count`` se aage wale khane kabhi chhue nahi jaate.
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
        """Farsh se takraane wale sab ko chhota sa uchhaal do.

        Verlet mein raftaar ``current - previous`` hai - isliye bounce sirf
        ``previous`` badal kar banaya jaata hai.

        Iss qadam ka displacement ``m = current - previous`` hai (Pygame
        mein +y neeche, to neeche aate waqt m > 0). Agla qadam
        ``floor - previous`` chalega, aur woh ulte rukh mein ``-BOUNCE * m``
        hona chahiye:

            previous = floor + BOUNCE * m

        m = 0 (chhoo kar ruk gaya) par previous = floor - yani BOUNCE = 0
        bilkul purane behaviour par laut jata hai. BOUNCE = 1 par poori
        raftaar wapas - perfect elastic.

        Mask mein sirf neeche wale particles aate hain, isliye hawa mein
        udte hue bilkul na chhue jaate hain.
        """
        below = current[:, 1] > self.floor
        if not below.any():
            return

        # Iss qadam ka displacement (+y = neeche, to girte waqt positive).
        step_dy = current[below, 1] - previous[below, 1]

        current[below, 1] = self.floor
        # `floor - previous` == -BOUNCE * step_dy, yani agla qadam upar.
        previous[below, 1] = self.floor + self.bounce * step_dy

    # ------------------------------------------------------------------
    # Andar
    # ------------------------------------------------------------------
    def _displacement_scratch(self, capacity: int) -> NDArray[np.float32]:
        """``capacity`` rows ka float32 buffer.

        Jagah capacity se li jaati hai, count se nahi - warna painting
        har frame resize karti.
        """
        scratch = self._displacement
        if scratch is None or scratch.shape[0] < capacity:
            scratch = np.empty((capacity, 2), dtype=np.float32)
            self._displacement = scratch
        return scratch

    def __repr__(self) -> str:
        return (
            f"PhysicsSystem(gravity={self.gravity}, floor={self.floor}, "
            f"bounce={self.bounce})"
        )