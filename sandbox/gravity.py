"""Kuan jo waqt ke saath nahi hiltay - bas kheenchte rehte hain.

Wells particles nahi hain: yeh duniya mein tike rehte hain, aur jab tak
zinda hain tab tak har particle ko apni taraf bulaate rehte hain. Isliye
inki jagah alag rakhi jaati hai - particles ke dhundle mein nahi.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import MAX_WELLS, WELL_MASS


class GravityWells:
    """Chand gehre kuan - tay jagah, aur har ek ka apna wazan.

    Attributes:
        capacity: sabse zyada kitne kuan.
        count: abhi kitne zinda.
        positions: poora ``(capacity, 2)`` - kuan kahan hain.
        masses: poora ``(capacity,)`` - har kuan ka wazan.
    """

    def __init__(self, capacity: int = MAX_WELLS, mass: float = WELL_MASS) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")

        self.capacity = int(capacity)
        self.default_mass = float(mass)
        self.count = 0
        # Dono arrays yahin bane - khane khali pare hain jab tak kuan na aaye.
        self.positions: NDArray[np.float32] = np.zeros(
            (self.capacity, 2), dtype=np.float32
        )
        self.masses: NDArray[np.float32] = np.zeros(self.capacity, dtype=np.float32)

    # ------------------------------------------------------------------
    # Haal
    # ------------------------------------------------------------------
    @property
    def is_full(self) -> bool:
        """Aur jagah bachi hai ya nahi."""
        return self.count >= self.capacity

    @property
    def active_positions(self) -> NDArray[np.float32]:
        """Zinda kuanon ki jagah, shape ``(count, 2)`` - view, copy nahi."""
        return self.positions[: self.count]

    @property
    def active_masses(self) -> NDArray[np.float32]:
        """Zinda kuanon ke wazan, shape ``(count,)``."""
        return self.masses[: self.count]

    # ------------------------------------------------------------------
    # Badlaav
    # ------------------------------------------------------------------
    def add(self, x: float, y: float, mass: float | None = None) -> bool:
        """``(x, y)`` par naya kuan - jagah na ho to kuch nahi aur ``False``."""
        if self.count >= self.capacity:
            return False

        self.positions[self.count, 0] = x
        self.positions[self.count, 1] = y
        self.masses[self.count] = self.default_mass if mass is None else mass
        self.count += 1
        return True

    def clear(self) -> None:
        """Saare kuan gayab - sirf count zero, arrays waise hi."""
        self.count = 0

    # ------------------------------------------------------------------
    # Chhote helpers
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return f"GravityWells(capacity={self.capacity}, count={self.count})"