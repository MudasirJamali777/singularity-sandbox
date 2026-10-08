"""Verlet integration, boundary response, and optional particle collisions.

Verlet stores velocity implicitly as ``current - previous``. Particle
collisions are positional constraints found through :class:`SpatialHash`;
the hash itself has no physics-resolution logic.
"""

from __future__ import annotations

import math
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

from sandbox.config import (
    BOUNCE,
    CELL_SIZE,
    MATTER,
    COLLISION_DISTANCE_EPSILON_SQUARED,
    COLLISION_ITERATIONS,
    COLLISIONS_ENABLED,
    GRAVITY,
    PARTICLE_RADIUS,
    SPH_WALL_BOUNCE,
    WATER,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from sandbox.particles import ParticleSystem
from sandbox.spatial import SpatialHash
from sandbox.sph import SPHSystem


class PhysicsSystem:
    """Advance particles and apply optional equal-mass overlap constraints.

    Attributes:
        gravity: downward acceleration, in pixels per second squared.
        bounce: retained velocity after hitting a boundary, from 0 to 1.
        collisions_enabled: whether particle-particle corrections are active.
        candidate_pairs: nearby pairs checked in the most recent physics step,
            summed across its collision iterations.
        overlaps: overlap corrections made in that step, also summed across
            iterations (a pair may be corrected more than once).
        collision_time_ms: time spent rebuilding/querying the hash and
            resolving collisions during the most recent step.
        step_time_ms: complete SPH, Verlet, collision, and boundary step time.
        sph_system: preallocated SPH state and WATER-only force solver.
    """

    # A fixed, symmetric set avoids NaNs and avoids random motion when two
    # particles have identical positions. The selected direction depends only
    # on the stable pair indices.
    _FALLBACK_DIRECTIONS = (
        (1.0, 0.0),
        (0.7071067811865476, 0.7071067811865476),
        (0.0, 1.0),
        (-0.7071067811865476, 0.7071067811865476),
        (-1.0, 0.0),
        (-0.7071067811865476, -0.7071067811865476),
        (0.0, -1.0),
        (0.7071067811865476, -0.7071067811865476),
    )

    def __init__(
        self,
        gravity: float = GRAVITY,
        bounce: float = BOUNCE,
        floor: float = WINDOW_HEIGHT - PARTICLE_RADIUS,
        ceiling: float = PARTICLE_RADIUS,
        left_wall: float = PARTICLE_RADIUS,
        right_wall: float = WINDOW_WIDTH - PARTICLE_RADIUS,
        *,
        collisions_enabled: bool = COLLISIONS_ENABLED,
        collision_iterations: int = COLLISION_ITERATIONS,
        cell_size: float = CELL_SIZE,
        distance_epsilon_squared: float = COLLISION_DISTANCE_EPSILON_SQUARED,
    ) -> None:
        self.gravity = float(gravity)
        self.bounce = float(bounce)
        # Radius ke hisaab se - warna aadhe particle bahar jhaankte hain.
        self.floor = float(floor)
        self.ceiling = float(ceiling)
        self.left_wall = float(left_wall)
        self.right_wall = float(right_wall)

        if collision_iterations < 1:
            raise ValueError(
                f"collision_iterations must be at least 1, got {collision_iterations}"
            )
        if not math.isfinite(distance_epsilon_squared) or distance_epsilon_squared < 0:
            raise ValueError(
                "distance_epsilon_squared must be finite and non-negative, "
                f"got {distance_epsilon_squared}"
            )

        self.collisions_enabled = bool(collisions_enabled)
        self.collision_iterations = int(collision_iterations)
        self.minimum_distance = float(PARTICLE_RADIUS * 2)
        self._minimum_distance_squared = self.minimum_distance**2
        self._distance_epsilon_squared = float(distance_epsilon_squared)
        self.spatial_hash = SpatialHash(cell_size=cell_size)
        self.sph_system = SPHSystem()

        # Sirf y ki taraf kheench.
        self._acceleration: NDArray[np.float32] = np.array(
            (0.0, self.gravity), dtype=np.float32
        )
        # Scratch: ek baar bane, phir usi mein likhe.
        self._displacement: NDArray[np.float32] | None = None

        self.candidate_pairs = 0
        self.overlaps = 0
        self.collision_time_ms = 0.0
        self.step_time_ms = 0.0

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def step(self, particles: ParticleSystem, dt: float) -> None:
        """Compute SPH forces, integrate, resolve matter collisions, clamp walls.

        The SPH density/pressure/viscosity pipeline runs against positions and
        Verlet velocities at the start of the fixed step. Its acceleration is
        added to gravity before one Verlet integration. Hard particle
        collisions then involve MATTER only; water is pressure-driven. Walls
        are applied last to both materials.
        """
        step_started = perf_counter()
        self.reset_collision_stats()
        count = particles.count
        if count == 0:
            self.sph_system.compute(particles, self.spatial_hash, dt)
            self.step_time_ms = (perf_counter() - step_started) * 1000.0
            return

        current = particles.active_positions
        previous = particles.active_previous_positions
        materials = particles.active_materials

        sph_acceleration = self.sph_system.compute(particles, self.spatial_hash, dt)
        displacement = self._displacement_scratch(particles.capacity)[:count]
        np.subtract(current, previous, out=displacement)

        # Preserve the previous position before advancing (Verlet history).
        np.copyto(previous, current)
        current += displacement

        # Reuse the displacement scratch for gravity + SPH acceleration.
        np.copyto(displacement, self._acceleration)
        displacement += sph_acceleration
        displacement *= dt * dt
        current += displacement

        matter_count = count - self.sph_system.water_count
        if self.collisions_enabled and matter_count > 1:
            collision_started = perf_counter()
            self._solve_collisions(current, previous, materials)
            self.collision_time_ms = (perf_counter() - collision_started) * 1000.0

        self._apply_boundaries(current, previous, materials)
        self.step_time_ms = (perf_counter() - step_started) * 1000.0

    def toggle_collisions(self) -> bool:
        """Flip particle collisions and return the new state."""
        self.collisions_enabled = not self.collisions_enabled
        self.reset_collision_stats()
        return self.collisions_enabled

    def rebuild_spatial_hash(self, particles: ParticleSystem) -> None:
        """Refresh the neighbor index, e.g. for the debug overlay."""
        self.spatial_hash.rebuild(particles.active_positions)

    def _solve_collisions(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
        materials: NDArray[np.uint8],
    ) -> None:
        """Resolve overlaps with unique, spatially-local pairs only.

        The grid is rebuilt at the beginning of every pass because earlier
        corrections move particles. Only MATTER/MATTER pairs are considered;
        ``j > i`` means each unordered pair is processed once per pass.
        Corrections are also applied to the
        corresponding previous positions to preserve Verlet displacement and
        avoid manufacturing large velocities from positional separation.
        """
        particle_count = current.shape[0]
        for _ in range(self.collision_iterations):
            self.spatial_hash.rebuild(current)

            for index_a in range(particle_count):
                if materials[index_a] != MATTER:
                    continue
                position_a = current[index_a]
                previous_a = previous[index_a]
                query_x = float(position_a[0])
                query_y = float(position_a[1])
                candidates = self.spatial_hash.query_nearby(
                    query_x,
                    query_y,
                    self.minimum_distance,
                )

                for index_b in candidates:
                    if index_b <= index_a or materials[index_b] != MATTER:
                        continue

                    self.candidate_pairs += 1
                    position_b = current[index_b]
                    delta_x = float(position_b[0]) - float(position_a[0])
                    delta_y = float(position_b[1]) - float(position_a[1])
                    distance_squared = delta_x * delta_x + delta_y * delta_y

                    # Most local candidates are not colliding; avoid sqrt here.
                    if distance_squared >= self._minimum_distance_squared:
                        continue

                    distance = math.sqrt(distance_squared)
                    if distance_squared <= self._distance_epsilon_squared:
                        direction_index = (
                            (index_a * 73_856_093) ^ (index_b * 19_349_663)
                        ) & 7
                        normal_x, normal_y = self._FALLBACK_DIRECTIONS[direction_index]
                    else:
                        inverse_distance = 1.0 / distance
                        normal_x = delta_x * inverse_distance
                        normal_y = delta_y * inverse_distance

                    penetration = self.minimum_distance - distance
                    half_correction = 0.5 * penetration
                    correction_x = normal_x * half_correction
                    correction_y = normal_y * half_correction

                    # Equal masses: each gets half the positional correction.
                    position_a[0] -= correction_x
                    position_a[1] -= correction_y
                    position_b[0] += correction_x
                    position_b[1] += correction_y

                    # Preserve each particle's implicit Verlet velocity.
                    previous_b = previous[index_b]
                    previous_a[0] -= correction_x
                    previous_a[1] -= correction_y
                    previous_b[0] += correction_x
                    previous_b[1] += correction_y
                    self.overlaps += 1

    def reset_collision_stats(self) -> None:
        """Clear diagnostics, e.g. after the user resets all particles."""
        self.candidate_pairs = 0
        self.overlaps = 0
        self.collision_time_ms = 0.0
        self.step_time_ms = 0.0

    # ------------------------------------------------------------------
    # Kinare
    # ------------------------------------------------------------------
    def _apply_boundaries(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
        materials: NDArray[np.uint8],
    ) -> None:
        """Clamp both materials at walls with material-appropriate damping."""
        # Y: ceiling (chhoti value) aur floor (bari value).
        self._bounce_axis(current, previous, materials, 1, self.ceiling, self.floor)
        # X: left wall (chhoti value) aur right wall (bari value).
        self._bounce_axis(current, previous, materials, 0, self.left_wall, self.right_wall)

    def _bounce_axis(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
        materials: NDArray[np.uint8],
        axis: int,
        low: float,
        high: float,
    ) -> None:
        """Clamp one axis; Matter bounces, water dissipates at the walls."""
        positions = current[:, axis]
        previous_axis = previous[:, axis]
        step_d = positions - previous_axis

        for material, bounce in ((MATTER, self.bounce), (WATER, SPH_WALL_BOUNCE)):
            material_mask = materials == material
            hit_low = (positions < low) & material_mask
            if hit_low.any():
                positions[hit_low] = low
                previous_axis[hit_low] = low + bounce * step_d[hit_low]

            hit_high = (positions > high) & material_mask
            if hit_high.any():
                positions[hit_high] = high
                previous_axis[hit_high] = high + bounce * step_d[hit_high]

    # ------------------------------------------------------------------
    # Andar
    # ------------------------------------------------------------------
    def _displacement_scratch(self, capacity: int) -> NDArray[np.float32]:
        """Return a reusable ``capacity``-row float32 displacement buffer."""
        scratch = self._displacement
        if scratch is None or scratch.shape[0] < capacity:
            scratch = np.empty((capacity, 2), dtype=np.float32)
            self._displacement = scratch
        return scratch

    def __repr__(self) -> str:
        return (
            f"PhysicsSystem(gravity={self.gravity}, bounce={self.bounce}, "
            f"collisions_enabled={self.collisions_enabled}, "
            f"bounds=({self.left_wall}, {self.ceiling}, "
            f"{self.right_wall}, {self.floor}))"
        )