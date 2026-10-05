"""Verlet - raftaar store kiye baghair.

    next = current + (current - previous) + acceleration * dt**2

Farq hi chalna hai. Gravity sirf y par; Pygame mein y neeche jaata hai.
Chaaron kinare aa gaye - har takraav par thoda sa uchhaal (BOUNCE).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import (
    BOUNCE,
    GRAVITY,
    PARTICLE_RADIUS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from sandbox.particles import ParticleSystem


class PhysicsSystem:
    """Ek chhoti dhadkan - sab ko aage badha dena.

    Attributes:
        gravity: neeche ki kheench, pixels per second squared.
        bounce: har takraav par kitni raftaar wapas, 0.0 se 1.0 tak.
        floor, ceiling, left_wall, right_wall: kinare, radius ke hisaab se.
    """

    def __init__(
        self,
        gravity: float = GRAVITY,
        bounce: float = BOUNCE,
        floor: float = WINDOW_HEIGHT - PARTICLE_RADIUS,
        ceiling: float = PARTICLE_RADIUS,
        left_wall: float = PARTICLE_RADIUS,
        right_wall: float = WINDOW_WIDTH - PARTICLE_RADIUS,
    ) -> None:
        self.gravity = float(gravity)
        self.bounce = float(bounce)
        # Radius ke hisaab se - warna aadhe particle bahar jhaankte hain.
        self.floor = float(floor)
        self.ceiling = float(ceiling)
        self.left_wall = float(left_wall)
        self.right_wall = float(right_wall)
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
        """Har zinda particle ko ``dt`` second aage badhao, phir kinare sambhalo.

        Tarteeb hi asal baat hai - dono views seedha storage mein jhankti hain:

        1. Pehle farq (current - previous) scratch mein.
        2. Phir current ko history mein likho. Yeh pehle kiya to wahi farq
           mit jaata - aur raftaar chupchaap kho jaati.
        3. Aakhir mein current aage badhao, phir deewaron se takrao.

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

        self._apply_boundaries(current, previous)

    # ------------------------------------------------------------------
    # Kinare
    # ------------------------------------------------------------------
    def _apply_boundaries(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
    ) -> None:
        """Chaaron kinare - dono axis, apne apne mask ke saath.

        Har kinara alag mask hai (hit_left / hit_right / hit_top /
        hit_bottom), isliye sirf takraane wale particles chhue jaate hain;
        hawa mein udte hue bilkul azad rehte hain.
        """
        # Y: ceiling (chhoti value) aur floor (bari value).
        self._bounce_axis(current, previous, 1, self.ceiling, self.floor)
        # X: left wall (chhoti value) aur right wall (bari value).
        self._bounce_axis(current, previous, 0, self.left_wall, self.right_wall)

    def _bounce_axis(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
        axis: int,
        low: float,
        high: float,
    ) -> None:
        """Ek axis ke dono kinare.

        Qaida har kinare par ek hi hai:

            purana displacement : d = current - previous
            naya  displacement : -BOUNCE * d

        Verlet mein displacement ``current - previous`` chhipa hua hai, isliye
        naya displacement ``previous`` ke zariye likha jaata hai:

            previous = current - naya_displacement

        ``current`` pehle kinare par clamp ho jata hai, to yeh yun banta hai:

            previous = kinara + BOUNCE * d

        BOUNCE = 0 par ``previous`` kinare par hi ruk jata hai (purana
        behaviour); BOUNCE = 1 par poori raftaar wapas. Dono current aur
        previous barabar kar dena ghalat hai - woh particle ko rook deta hai,
        uchhaal nahi.
        """
        positions = current[:, axis]
        previous_axis = previous[:, axis]
        # Purana displacement pehle pakdo, warna clamp karne par mit jayega.
        step_d = positions - previous_axis

        hit_low = positions < low
        if hit_low.any():
            positions[hit_low] = low
            outgoing = -self.bounce * step_d[hit_low]
            previous_axis[hit_low] = low - outgoing

        hit_high = positions > high
        if hit_high.any():
            positions[hit_high] = high
            outgoing = -self.bounce * step_d[hit_high]
            previous_axis[hit_high] = high - outgoing

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
            f"PhysicsSystem(gravity={self.gravity}, bounce={self.bounce}, "
            f"bounds=({self.left_wall}, {self.ceiling}, "
            f"{self.right_wall}, {self.floor}))"
        )