"""Verlet integration for Singularity Sandbox.

Each step advances every active particle with the velocity-free Verlet form:

    next = current + (current - previous) + acceleration * dt**2

The difference between the two position buffers *is* the implied motion, so
no velocity array is ever stored. Gravity is a constant acceleration on the
Y axis; Pygame's Y axis points down, so a positive value makes particles
fall toward the bottom of the window.

Nothing else is modelled yet: no floor, no damping, no boundaries.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import GRAVITY
from sandbox.particles import ParticleSystem


class PhysicsSystem:
    """Advances particle positions one timestep at a time.

    Attributes:
        gravity: Downward acceleration in pixels per second squared.
    """

    def __init__(self, gravity: float = GRAVITY) -> None:
        self.gravity = float(gravity)
        # Constant acceleration vector: none on X, gravity on Y.
        self._acceleration: NDArray[np.float32] = np.array(
            (0.0, self.gravity), dtype=np.float32
        )
        # Scratch space for the displacement term, allocated on first use so
        # a steady-state step never allocates (or reallocates) anything.
        self._displacement: NDArray[np.float32] | None = None

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def step(self, particles: ParticleSystem, dt: float) -> None:
        """Advance every active particle of ``particles`` by ``dt`` seconds.

        The ordering below is the whole point of this method. The two
        active views are windows directly into the storage buffers, so:

        1. The implied displacement (current - previous) is materialised
           into scratch space *first*, while both buffers still hold last
           step's numbers.
        2. Only then is the current position copied into the history buffer.
           Doing this earlier would erase the very difference the next step
           needs, and the particles would silently lose all momentum.
        3. Finally the current positions are moved in place, which also
           leaves the history buffer untouched from here on.

        Inactive slots beyond ``count`` are never touched.
        """
        count = particles.count
        if count == 0:
            return

        current = particles.active_positions
        previous = particles.active_previous_positions

        displacement = self._displacement_scratch(particles.capacity)[:count]
        np.subtract(current, previous, out=displacement)

        # History: where every particle was before this step.
        np.copyto(previous, current)

        current += displacement
        current += self._acceleration * (dt * dt)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _displacement_scratch(self, capacity: int) -> NDArray[np.float32]:
        """Return a float32 buffer of at least ``capacity`` rows.

        Sized by capacity rather than by the live count: painting spawns
        particles one at a time, and resizing per spawn would allocate on
        almost every frame.
        """
        scratch = self._displacement
        if scratch is None or scratch.shape[0] < capacity:
            scratch = np.empty((capacity, 2), dtype=np.float32)
            self._displacement = scratch
        return scratch

    def __repr__(self) -> str:
        return f"PhysicsSystem(gravity={self.gravity})"