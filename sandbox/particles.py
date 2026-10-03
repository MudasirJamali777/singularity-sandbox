"""Particle storage for Singularity Sandbox.

This module is pure data: it knows nothing about Pygame, gravity, velocity,
or rendering. Its only job is to hold particle positions in preallocated
NumPy arrays so later systems can operate on them in bulk.

Two arrays are kept per particle: the current position and the position it
held on the previous physics step. Their difference implies velocity, which
is what Verlet integration needs.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import MAX_PARTICLES


class ParticleSystem:
    """Fixed-capacity storage for particle positions.

    Positions live in two preallocated ``(capacity, 2)`` float32 arrays.
    Only the first ``count`` rows of each are meaningful; the remaining rows
    are unused slots that are simply waiting to be filled.

    The pair of arrays is what makes Verlet integration possible later:
    ``positions - previous_positions`` is the implied per-step displacement,
    so no velocity array ever has to be stored.

    Attributes:
        capacity: Maximum number of particles the system can hold.
        count: Number of particles currently active.
        positions: Full ``(capacity, 2)`` array of current positions.
        previous_positions: Full ``(capacity, 2)`` array of the positions
            held on the previous physics step.
    """

    def __init__(self, capacity: int = MAX_PARTICLES) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")

        self.capacity = int(capacity)
        self.count = 0
        # Both allocated once, up front. Never resized.
        self.positions: NDArray[np.float32] = np.zeros(
            (self.capacity, 2), dtype=np.float32
        )
        self.previous_positions: NDArray[np.float32] = np.zeros(
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

    @property
    def active_previous_positions(self) -> NDArray[np.float32]:
        """A view of just the live rows of the previous-position array.

        Mirrors :attr:`active_positions` so physics can read or write both
        halves of the Verlet pair without knowing about ``count``.
        """
        return self.previous_positions[: self.count]

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    def spawn(self, x: float, y: float) -> bool:
        """Place a particle at ``(x, y)`` in the next unused slot.

        Both the current and previous position are set to ``(x, y)``, which
        means the new particle starts with zero implied velocity.

        Does nothing and returns ``False`` if the system is already at
        capacity, so callers never have to guard against an overflow.
        """
        if self.count >= self.capacity:
            return False

        self.positions[self.count, 0] = x
        self.positions[self.count, 1] = y
        self.previous_positions[self.count, 0] = x
        self.previous_positions[self.count, 1] = y
        self.count += 1
        return True

    def clear(self) -> None:
        """Deactivate every particle without touching either allocation.

        Only the count is reset; the stale coordinates left in the arrays
        are unreachable and get overwritten as new particles are spawned.
        """
        self.count = 0

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return f"ParticleSystem(capacity={self.capacity}, count={self.count})"