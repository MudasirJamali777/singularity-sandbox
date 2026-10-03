"""Particle storage for Singularity Sandbox.

This module is pure data: it knows nothing about Pygame, gravity, velocity,
or rendering. Its only job is to hold particle positions in a single
preallocated NumPy array so later systems can operate on them in bulk.
"""

from __future__ import annotations
from sandbox.config import MAX_PARTICLES
import numpy as np
from numpy.typing import NDArray



class ParticleSystem:
    """Fixed-capacity storage for particle positions.

    All positions live in one preallocated ``(capacity, 2)`` float32 array.
    Only the first ``count`` rows are meaningful; the remaining rows are
    unused slots that are simply waiting to be filled.

    Attributes:
        capacity: Maximum number of particles the system can hold.
        count: Number of particles currently active.
        positions: The full ``(capacity, 2)`` array, slot 0 at the top.
    """

    def __init__(self, capacity: int = MAX_PARTICLES) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")

        self.capacity = int(capacity)
        self.count = 0
        # Allocated once, up front. Never resized.
        self.positions: NDArray[np.float32] = np.zeros(
            (self.capacity, 2), dtype=np.float32
        )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    @property
    def is_full(self) -> bool:
        """True when no unused slots remain."""
        return self.count >= self.capacity

    @property
    def active_positions(self) -> NDArray[np.float32]:
        """A view of just the live rows, shaped ``(count, 2)``.

        This is a slice, not a copy, so bulk NumPy work on it is cheap and
        any in-place writes flow back into the underlying array. Note that
        a view taken now does not grow when more particles are spawned.
        """
        return self.positions[: self.count]

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    def spawn(self, x: float, y: float) -> bool:
        """Place a particle at ``(x, y)`` in the next unused slot.

        Does nothing and returns ``False`` if the system is already at
        capacity, so callers never have to guard against an overflow.
        """
        if self.count >= self.capacity:
            return False

        self.positions[self.count, 0] = x
        self.positions[self.count, 1] = y
        self.count += 1
        return True

    def clear(self) -> None:
        """Deactivate every particle without touching the allocation."""
        self.count = 0

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return f"ParticleSystem(capacity={self.capacity}, count={self.count})"