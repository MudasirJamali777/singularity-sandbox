"""Particle storage only - no Pygame, forces, or velocity objects.

Positions use Verlet's current/previous float32 arrays. Material IDs live in
one preallocated integer array, so spawning does not create per-particle
Python objects.
"""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import MATTER, MAX_PARTICLES, WATER


class ParticleSystem:
    """Fixed jagah, badalti yaadein.

    Sirf pehli ``count`` rows zinda hain; baaki khali khanay.

    Attributes:
        capacity: kul kitni jagah.
        count: abhi kitne zinda.
        positions: poora ``(capacity, 2)``, ab ke pata ke saath.
        previous_positions: poora ``(capacity, 2)``, pichhle lamhe ke saath.
        materials: poora ``(capacity,)`` integer array of MATTER/WATER IDs.
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
        self.materials: NDArray[np.uint8] = np.zeros(
            self.capacity, dtype=np.uint8
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
        """Wahi baat, pichhle lamhe ki - shape ``(count, 2``."""
        return self.previous_positions[: self.count]

    @property
    def active_materials(self) -> NDArray[np.uint8]:
        """Material IDs for live particles, shape ``(count,)``."""
        return self.materials[: self.count]

    # ------------------------------------------------------------------
    # Badlaav
    # ------------------------------------------------------------------
    def spawn(self, x: float, y: float, material: int = MATTER) -> bool:
        """Spawn one particle at ``(x, y)`` with zero initial velocity.

        Slots are reused after ``clear()``, so the material is always written
        when a particle is spawned. Returns ``False`` when storage is full.
        """
        if material not in (MATTER, WATER):
            raise ValueError(f"unsupported material ID: {material}")
        if self.count >= self.capacity:
            return False

        self.positions[self.count, 0] = x
        self.positions[self.count, 1] = y
        self.previous_positions[self.count, 0] = x
        self.previous_positions[self.count, 1] = y
        self.materials[self.count] = material
        self.count += 1
        return True

    def spawn_disk(
        self,
        x: float,
        y: float,
        radius: float,
        count: int,
        material: int = MATTER,
    ) -> int:
        """``(x, y)`` ke gird disk bhar ke particles - ek hi baar mein.

        Radius ko ``sqrt`` se sample karte hain: seedha random lene par
        particles markaz par zyada aur kinaron par kam girte hain. Isi liye
        yeh asli disk banata hai, square nahi.

        ``material`` defaults to MATTER for the existing brush. If storage is
        short, as many particles as fit are spawned; return the number made.
        """
        if material not in (MATTER, WATER):
            raise ValueError(f"unsupported material ID: {material}")
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
        self.materials[lo:hi] = material
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