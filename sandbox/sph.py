"""A compact two-dimensional SPH solver for WATER particles only.

This module owns density, pressure, and viscosity calculations. It receives
an already-created spatial hash from PhysicsSystem; it does not integrate,
draw, or handle input.
"""

from __future__ import annotations

import math
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

from sandbox.config import (
    MAX_PARTICLES,
    SPH_DENSITY_EPSILON,
    SPH_GAS_CONSTANT,
    SPH_H,
    SPH_MASS,
    SPH_REST_DENSITY,
    SPH_VISCOSITY,
    WATER,
)
from sandbox.particles import ParticleSystem
from sandbox.spatial import SpatialHash


class SPHSystem:
    """Preallocated density/pressure/acceleration buffers for 2D water SPH.

    The 2D Poly6 kernel computes density. Pressure uses the 2D spiky-kernel
    gradient, and viscosity uses the 2D viscosity-kernel Laplacian. Candidate
    neighbors are gathered once through the radius-aware spatial hash and retained
    as dynamically grown int32 directed-pair arrays. Numerical float scratch is
    processed in bounded chunks; pair-index memory still scales with candidate
    count, which depends on WATER density and the broad-phase cell queries.

    Negative pressure is clamped to zero to avoid tensile clumping in this
    small prototype. This is a stability guard, not a complete equation of state
    or surface-tension model.
    """

    def __init__(
        self,
        capacity: int = MAX_PARTICLES,
        *,
        smoothing_length: float = SPH_H,
        mass: float = SPH_MASS,
        rest_density: float = SPH_REST_DENSITY,
        gas_constant: float = SPH_GAS_CONSTANT,
        viscosity: float = SPH_VISCOSITY,
        density_epsilon: float = SPH_DENSITY_EPSILON,
    ) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        values = (
            smoothing_length,
            mass,
            rest_density,
            gas_constant,
            viscosity,
            density_epsilon,
        )
        if not all(math.isfinite(float(value)) for value in values):
            raise ValueError("SPH parameters must be finite")
        if smoothing_length <= 0.0 or mass <= 0.0 or density_epsilon <= 0.0:
            raise ValueError("SPH_H, SPH_MASS, and density epsilon must be positive")
        if rest_density < 0.0 or gas_constant < 0.0 or viscosity < 0.0:
            raise ValueError("SPH rest density, gas constant, and viscosity cannot be negative")

        self.capacity = int(capacity)
        self.smoothing_length = float(smoothing_length)
        self.mass = float(mass)
        self.rest_density = float(rest_density)
        self.gas_constant = float(gas_constant)
        self.viscosity = float(viscosity)
        self.density_epsilon = float(density_epsilon)
        self._h_squared = self.smoothing_length**2

        # Normalized 2D kernels:
        # Poly6: 4/(pi*h^8) * (h^2-r^2)^3
        # Spiky gradient magnitude: 30/(pi*h^5) * (h-r)^2
        # Viscosity Laplacian: 40/(pi*h^5) * (h-r)
        self._poly6_coefficient = 4.0 / (math.pi * self.smoothing_length**8)
        self._spiky_gradient_coefficient = 30.0 / (math.pi * self.smoothing_length**5)
        self._viscosity_laplacian_coefficient = (
            40.0 / (math.pi * self.smoothing_length**5)
        )

        self.density: NDArray[np.float32] = np.zeros(self.capacity, dtype=np.float32)
        self.pressure: NDArray[np.float32] = np.zeros(self.capacity, dtype=np.float32)
        self.accelerations: NDArray[np.float32] = np.zeros(
            (self.capacity, 2), dtype=np.float32
        )
        self._velocities: NDArray[np.float32] = np.zeros(
            (self.capacity, 2), dtype=np.float32
        )
        self._water_indices: NDArray[np.int32] = np.empty(
            self.capacity, dtype=np.int32
        )
        self._water_values: NDArray[np.float32] = np.empty(
            self.capacity, dtype=np.float32
        )

        # Neighbor-index storage grows to the actual broad-phase pair count.
        # Vector kernel scratch is bounded to chunks and allocated on first
        # water use, so dense 10k scenes don't need scratch for every pair.
        self._pair_capacity = 0
        self._pair_i = np.empty(0, dtype=np.int32)
        self._pair_j = np.empty(0, dtype=np.int32)
        self._neighbor_capacity = 0
        self._neighbor_indices = np.empty(0, dtype=np.int32)
        self._chunk_capacity = 0
        self._allocate_pair_scratch(0)

        self.water_count = 0
        self.average_density = 0.0
        self.maximum_density = 0.0
        self.neighbor_visits = 0
        self.compute_time_ms = 0.0

    def compute(
        self,
        particles: ParticleSystem,
        spatial_hash: SpatialHash,
        dt: float,
    ) -> NDArray[np.float32]:
        """Compute SPH accelerations from current WATER positions.

        Called before Verlet integration. The returned array is a view of the
        preallocated ``(capacity, 2)`` acceleration buffer, sliced to active
        particles. Matter entries are always zero.
        """
        started = perf_counter()
        self._ensure_capacity(particles.capacity)
        count = particles.count
        current = particles.active_positions
        previous = particles.active_previous_positions
        materials = particles.active_materials

        self.density[:count].fill(0.0)
        self.pressure[:count].fill(0.0)
        self.accelerations[:count].fill(0.0)
        self.neighbor_visits = 0
        self.average_density = 0.0
        self.maximum_density = 0.0

        water_count = 0
        for particle_index in range(count):
            if materials[particle_index] == WATER:
                self._water_indices[water_count] = particle_index
                water_count += 1
        self.water_count = water_count

        if water_count == 0:
            self.compute_time_ms = (perf_counter() - started) * 1000.0
            return self.accelerations[:count]

        self._ensure_pair_storage(water_count)
        # Keep original particle IDs in the grid, but omit MATTER entirely.
        water_indices = self._water_indices[:water_count]
        spatial_hash.rebuild(current, particle_indices=water_indices)
        pair_count = self._build_directed_neighbor_pairs(
            current, spatial_hash, water_count
        )
        pair_count = self._filter_pairs_within_radius(current, pair_count)
        self.neighbor_visits = pair_count
        self._density_pass(current, count, pair_count)
        self._pressure_pass(water_count)
        self._compute_velocities(current, previous, count, dt)
        self._force_pass(current, pair_count)

        self.compute_time_ms = (perf_counter() - started) * 1000.0
        return self.accelerations[:count]

    def reset_diagnostics(self) -> None:
        """Forget active-water diagnostics after a user reset."""
        self.density.fill(0.0)
        self.pressure.fill(0.0)
        self.accelerations.fill(0.0)
        self.water_count = 0
        self.average_density = 0.0
        self.maximum_density = 0.0
        self.neighbor_visits = 0
        self.compute_time_ms = 0.0

    def _density_pass(
        self,
        current: NDArray[np.float32],
        active_count: int,
        pair_count: int,
    ) -> None:
        for pair_start in range(0, pair_count, self._chunk_capacity):
            chunk_count = min(self._chunk_capacity, pair_count - pair_start)
            self._density_from_pair_chunk(current, active_count, pair_start, chunk_count)

    def _density_from_pair_chunk(
        self,
        current: NDArray[np.float32],
        active_count: int,
        pair_start: int,
        pair_count: int,
    ) -> None:
        pair_i = self._pair_i[pair_start : pair_start + pair_count]
        pair_j = self._pair_j[pair_start : pair_start + pair_count]
        dx = self._pair_dx[:pair_count]
        dy = self._pair_dy[:pair_count]
        distance_squared = self._pair_distance_squared[:pair_count]
        work = self._pair_work[:pair_count]
        support = self._pair_support[:pair_count]
        positions_x = current[:, 0]
        positions_y = current[:, 1]

        np.take(positions_x, pair_i, out=dx)
        np.take(positions_x, pair_j, out=work)
        np.subtract(dx, work, out=dx)
        np.take(positions_y, pair_i, out=dy)
        np.take(positions_y, pair_j, out=work)
        np.subtract(dy, work, out=dy)
        np.multiply(dx, dx, out=distance_squared)
        np.multiply(dy, dy, out=work)
        np.add(distance_squared, work, out=distance_squared)

        # q=max(h^2-r^2,0); density is sum mass * 4/(pi*h^8) * q^3.
        np.subtract(self._h_squared, distance_squared, out=support)
        np.maximum(support, 0.0, out=support)
        np.multiply(support, support, out=work)
        np.multiply(work, support, out=support)
        support *= self.mass * self._poly6_coefficient
        np.add.at(self.density[:active_count], pair_i, support)

    def _pressure_pass(self, water_count: int) -> None:
        water_indices = self._water_indices[:water_count]
        water_density = self._water_values[:water_count]
        np.take(self.density, water_indices, out=water_density)

        self.average_density = float(np.mean(water_density, dtype=np.float64))
        self.maximum_density = float(np.max(water_density))
        np.subtract(water_density, self.rest_density, out=water_density)
        np.maximum(water_density, 0.0, out=water_density)
        water_density *= self.gas_constant
        np.put(self.pressure, water_indices, water_density)

    def _compute_velocities(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
        count: int,
        dt: float,
    ) -> None:
        velocities = self._velocities[:count]
        if dt <= 0.0:
            velocities.fill(0.0)
            return
        np.subtract(current, previous, out=velocities)
        velocities *= 1.0 / dt

    def _force_pass(
        self,
        current: NDArray[np.float32],
        pair_count: int,
    ) -> None:
        for pair_start in range(0, pair_count, self._chunk_capacity):
            chunk_count = min(self._chunk_capacity, pair_count - pair_start)
            self._forces_from_pair_chunk(current, pair_start, chunk_count)

    def _forces_from_pair_chunk(
        self,
        current: NDArray[np.float32],
        pair_start: int,
        pair_count: int,
    ) -> None:
        pair_i = self._pair_i[pair_start : pair_start + pair_count]
        pair_j = self._pair_j[pair_start : pair_start + pair_count]
        dx = self._pair_dx[:pair_count]
        dy = self._pair_dy[:pair_count]
        distance_squared = self._pair_distance_squared[:pair_count]
        distance = self._pair_distance[:pair_count]
        support = self._pair_support[:pair_count]
        work = self._pair_work[:pair_count]
        work_2 = self._pair_work_2[:pair_count]
        density_i = self._pair_density_i[:pair_count]
        density_j = self._pair_density_j[:pair_count]
        pressure_term = self._pair_pressure_term[:pair_count]
        contribution_x = self._pair_contribution_x[:pair_count]
        contribution_y = self._pair_contribution_y[:pair_count]

        positions_x = current[:, 0]
        positions_y = current[:, 1]
        np.take(positions_x, pair_i, out=dx)
        np.take(positions_x, pair_j, out=work)
        np.subtract(dx, work, out=dx)
        np.take(positions_y, pair_i, out=dy)
        np.take(positions_y, pair_j, out=work)
        np.subtract(dy, work, out=dy)
        np.multiply(dx, dx, out=distance_squared)
        np.multiply(dy, dy, out=work)
        np.add(distance_squared, work, out=distance_squared)
        np.sqrt(distance_squared, out=distance)
        np.subtract(self.smoothing_length, distance, out=support)
        np.maximum(support, 0.0, out=support)

        # rho_i, rho_j are protected before the symmetric pressure term.
        np.take(self.density, pair_i, out=density_i)
        np.maximum(density_i, self.density_epsilon, out=density_i)
        np.take(self.density, pair_j, out=density_j)
        np.maximum(density_j, self.density_epsilon, out=density_j)
        np.take(self.pressure, pair_i, out=work)
        np.multiply(density_i, density_i, out=work_2)
        np.divide(work, work_2, out=work)
        np.take(self.pressure, pair_j, out=pressure_term)
        np.multiply(density_j, density_j, out=work_2)
        np.divide(pressure_term, work_2, out=pressure_term)
        pressure_term += work

        # With r_ij = x_i - x_j, -grad(W_spiky) points along r_ij. A safe
        # denominator handles r=0; dx=dy=0 makes that gradient contribution 0.
        np.maximum(distance, 1e-6, out=work_2)
        np.multiply(support, support, out=work)
        np.multiply(work, pressure_term, out=work)
        work *= self.mass * self._spiky_gradient_coefficient
        np.divide(work, work_2, out=work)
        np.multiply(work, dx, out=contribution_x)
        np.multiply(work, dy, out=contribution_y)
        np.add.at(self.accelerations[:, 0], pair_i, contribution_x)
        np.add.at(self.accelerations[:, 1], pair_i, contribution_y)

        if self.viscosity <= 0.0:
            return

        # Standard 2D viscosity Laplacian and Verlet relative velocities.
        np.multiply(support, self._viscosity_laplacian_coefficient, out=work)
        work *= self.viscosity * self.mass
        np.divide(work, density_j, out=work)
        velocities_x = self._velocities[:, 0]
        velocities_y = self._velocities[:, 1]
        np.take(velocities_x, pair_j, out=contribution_x)
        np.take(velocities_x, pair_i, out=work_2)
        np.subtract(contribution_x, work_2, out=contribution_x)
        np.multiply(contribution_x, work, out=contribution_x)
        np.take(velocities_y, pair_j, out=contribution_y)
        np.take(velocities_y, pair_i, out=work_2)
        np.subtract(contribution_y, work_2, out=contribution_y)
        np.multiply(contribution_y, work, out=contribution_y)
        np.add.at(self.accelerations[:, 0], pair_i, contribution_x)
        np.add.at(self.accelerations[:, 1], pair_i, contribution_y)

    def _build_directed_neighbor_pairs(
        self,
        current: NDArray[np.float32],
        spatial_hash: SpatialHash,
        water_count: int,
    ) -> int:
        """Collect conservative cell candidates; exact-radius filtering follows."""
        pair_count = 0
        for water_offset in range(water_count):
            index_i = int(self._water_indices[water_offset])
            x_i = float(current[index_i, 0])
            y_i = float(current[index_i, 1])
            candidate_count = 0
            for index_j in spatial_hash.query_nearby(
                x_i, y_i, self.smoothing_length
            ):
                self._neighbor_indices[candidate_count] = index_j
                candidate_count += 1

            if candidate_count == 0:
                raise RuntimeError("SPH neighbor query returned no self-neighbor")
            self._ensure_pair_list_capacity(pair_count + candidate_count, used=pair_count)
            end = pair_count + candidate_count
            self._pair_i[pair_count:end].fill(index_i)
            self._pair_j[pair_count:end] = self._neighbor_indices[:candidate_count]
            pair_count = end
        return pair_count

    def _filter_pairs_within_radius(
        self,
        current: NDArray[np.float32],
        pair_count: int,
    ) -> int:
        """Compact conservative hash candidates to exact ``r < SPH_H`` pairs."""
        write_start = 0
        positions_x = current[:, 0]
        positions_y = current[:, 1]
        for read_start in range(0, pair_count, self._chunk_capacity):
            chunk_count = min(self._chunk_capacity, pair_count - read_start)
            read_end = read_start + chunk_count
            pair_i = self._pair_i[read_start:read_end]
            pair_j = self._pair_j[read_start:read_end]
            dx = self._pair_dx[:chunk_count]
            dy = self._pair_dy[:chunk_count]
            distance_squared = self._pair_distance_squared[:chunk_count]
            work = self._pair_work[:chunk_count]
            mask = self._pair_mask[:chunk_count]

            np.take(positions_x, pair_i, out=dx)
            np.take(positions_x, pair_j, out=work)
            np.subtract(dx, work, out=dx)
            np.take(positions_y, pair_i, out=dy)
            np.take(positions_y, pair_j, out=work)
            np.subtract(dy, work, out=dy)
            np.multiply(dx, dx, out=distance_squared)
            np.multiply(dy, dy, out=work)
            np.add(distance_squared, work, out=distance_squared)
            np.less(distance_squared, self._h_squared, out=mask)

            in_radius = int(np.count_nonzero(mask))
            if in_radius:
                write_end = write_start + in_radius
                self._pair_i[write_start:write_end] = pair_i[mask]
                self._pair_j[write_start:write_end] = pair_j[mask]
                write_start = write_end
        return write_start

    def _ensure_capacity(self, required: int) -> None:
        if required <= self.capacity:
            return
        self.capacity = int(required)
        self.density = np.zeros(self.capacity, dtype=np.float32)
        self.pressure = np.zeros(self.capacity, dtype=np.float32)
        self.accelerations = np.zeros((self.capacity, 2), dtype=np.float32)
        self._velocities = np.zeros((self.capacity, 2), dtype=np.float32)
        self._water_indices = np.empty(self.capacity, dtype=np.int32)
        self._water_values = np.empty(self.capacity, dtype=np.float32)

    def _ensure_pair_storage(self, water_count: int) -> None:
        if water_count > self._neighbor_capacity:
            self._neighbor_capacity = int(water_count)
            self._neighbor_indices = np.empty(self._neighbor_capacity, dtype=np.int32)

        chunk_capacity = max(1024, water_count * 32)
        if chunk_capacity > self._chunk_capacity:
            self._chunk_capacity = int(chunk_capacity)
            self._allocate_pair_scratch(self._chunk_capacity)

        initial_pair_capacity = max(1024, water_count * 32)
        self._ensure_pair_list_capacity(initial_pair_capacity, used=0)

    def _ensure_pair_list_capacity(self, required: int, used: int) -> None:
        if required <= self._pair_capacity:
            return
        new_capacity = max(required, max(1024, self._pair_capacity * 2))
        pair_i = np.empty(new_capacity, dtype=np.int32)
        pair_j = np.empty(new_capacity, dtype=np.int32)
        if used:
            pair_i[:used] = self._pair_i[:used]
            pair_j[:used] = self._pair_j[:used]
        self._pair_i = pair_i
        self._pair_j = pair_j
        self._pair_capacity = new_capacity

    def _allocate_pair_scratch(self, capacity: int) -> None:
        self._pair_dx = np.empty(capacity, dtype=np.float32)
        self._pair_dy = np.empty(capacity, dtype=np.float32)
        self._pair_distance_squared = np.empty(capacity, dtype=np.float32)
        self._pair_distance = np.empty(capacity, dtype=np.float32)
        self._pair_support = np.empty(capacity, dtype=np.float32)
        self._pair_work = np.empty(capacity, dtype=np.float32)
        self._pair_work_2 = np.empty(capacity, dtype=np.float32)
        self._pair_density_i = np.empty(capacity, dtype=np.float32)
        self._pair_density_j = np.empty(capacity, dtype=np.float32)
        self._pair_pressure_term = np.empty(capacity, dtype=np.float32)
        self._pair_contribution_x = np.empty(capacity, dtype=np.float32)
        self._pair_contribution_y = np.empty(capacity, dtype=np.float32)
        self._pair_mask = np.empty(capacity, dtype=np.bool_)