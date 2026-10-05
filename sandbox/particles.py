"""Sirf yaadein rakhna - Pygame nahi, gravity nahi, velocity nahi.

Do float32 arrays: ``positions`` (ab ka pata) aur ``previous_positions``
(pichhla lamha). Dono ka farq hi raftaar hai.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import MAX_PARTICLES


class ParticleSystem:
    """Fixed jagah, badalti yaadein.

    Sirf pehli ``count`` rows zinda hain; baaki khali khanay.

    Attributes:
        capacity: kul kitni jagah.
        count: abhi kitne zinda.
        positions: poora ``(capacity, 2)``, ab ke pata ke saath.
        previous_positions: poora ``(capacity, 2)``, pichhle lamhe ke saath.
    """

    def __init__(self, capacity: int = MAX_PARTICLES, seed: int | None = None) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")

        self.capacity = int(capacity)
        self.count = 0
        # Brush ke bikhre hue nishaan yahin se ugte hain.
        self.rng = np.random.default_rng(seed)
        # Dono arrays yahin bane - ab na bade, na badle.
        self.positions: NDArray[np.float32] = np.zeros(
            (self.capacity, 2), dtype=np.float32
        )
        self.previous_positions: NDArray[np.float32] = np.zeros(
            (self.capacity, 2), dtype=np.float32
        )

    # ------------------------------------------------------------------
    # Haal
    # ------------------------------------------------------------------
    @property
    def is_full(self) -> bool:
        """Khali jagah bachi hai ya nahi."""
        return self.count >= self.capacity

    @property
    def active_positions(self) -> NDArray[np.float32]:
        """Zinda particles ke ab ke pate, shape ``(count, 2)``.

        View hai, copy nahi - isliye bulk kaam sasta. Abhi liya view aage
        spawn honay par khud nahi barhta.
        """
        return self.positions[: self.count]

    @property
    def active_previous_positions(self) -> NDArray[np.float32]:
        """Wahi baat, pichhle lamhe ki - shape ``(count, 2)``."""
        return self.previous_positions[: self.count]

    # ------------------------------------------------------------------
    # Badlaav
    # ------------------------------------------------------------------
    def spawn(self, x: float, y: float) -> bool:
        """``(x, y)`` par nayi yaad.

        Ab aur pichhla lamha dono wahi - yani raftaar zero. Jagah na ho to
        kuch nahi hota aur ``False`` laut aata hai.
        """
        if self.count >= self.capacity:
            return False

        self.positions[self.count, 0] = x
        self.positions[self.count, 1] = y
        self.previous_positions[self.count, 0] = x
        self.previous_positions[self.count, 1] = y
        self.count += 1
        return True

    def spawn_disk(
        self,
        x: float,
        y: float,
        radius: float,
        count: int,
    ) -> int:
        """``(x, y)`` ke gird disk bhar ke particles - ek hi baar mein.

        Radius ko ``sqrt`` se sample karte hain: seedha random lene par
        particles markaz par zyada aur kinaron par kam girte hain. Isi liye
        yeh asli disk banata hai, square nahi.

        Jagah kam pad jaye to jitne aa sakein utne hi. Lautata hai kitne bane.
        """
        free = self.capacity - self.count
        if count <= 0 or free <= 0 or radius <= 0.0:
            return 0

        n = min(count, free)
        # Even disk: r = R * sqrt(u), warna markaz bhar jata hai.
        r = radius * np.sqrt(self.rng.random(n))
        angle = self.rng.random(n) * (2.0 * np.pi)

        lo = self.count
        hi = lo + n
        self.positions[lo:hi, 0] = x + r * np.cos(angle)
        self.positions[lo:hi, 1] = y + r * np.sin(angle)
        # Pichhla lamha bhi wahi - naye particles raftaar zero se shuru.
        self.previous_positions[lo:hi] = self.positions[lo:hi]
        self.count = hi
        return n

    def clear(self) -> None:
        """Sab bhool jao - sirf count zero, arrays waise hi."""
        self.count = 0

    # ------------------------------------------------------------------
    # Chhote helpers
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return f"ParticleSystem(capacity={self.capacity}, count={self.count})"
