"""Verlet - raftaar store kiye baghair.

    next = current + (current - previous) + acceleration * dt**2

Farq hi chalna hai. Gravity sirf y par; Pygame mein y neeche jaata hai.
Abhi na farsh hai, na bounce.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import GRAVITY
from sandbox.particles import ParticleSystem


class PhysicsSystem:
    """Ek chhoti dhadkan - sab ko aage badha dena.

    Attributes:
        gravity: neeche ki kheench, pixels per second squared.
    """

    def __init__(self, gravity: float = GRAVITY) -> None:
        self.gravity = float(gravity)
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
        """Har zinda particle ko ``dt`` second aage badhao.

        Tarteeb hi asal baat hai - dono views seedha storage mein jhankti hain:

        1. Pehle farq (current - previous) scratch mein.
        2. Phir current ko history mein likho. Yeh pehle kiya to wahi farq
           mit jaata - aur raftaar chupchaap kho jaati.
        3. Aakhir mein current aage badhao.

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
        return f"PhysicsSystem(gravity={self.gravity})"