from __future__ import annotations

import math
import unittest

import numpy as np

from sandbox.particles import ParticleSystem
from sandbox.physics import PhysicsSystem


class ParticleCollisionTests(unittest.TestCase):
    def make_physics(self, **kwargs: object) -> PhysicsSystem:
        return PhysicsSystem(
            gravity=0.0,
            bounce=0.0,
            **kwargs,
        )

    def test_coincident_particles_separate_without_non_finite_values(self) -> None:
        particles = ParticleSystem(capacity=2, seed=1)
        particles.spawn(100.0, 100.0)
        particles.spawn(100.0, 100.0)
        physics = self.make_physics(collisions_enabled=True, collision_iterations=2)

        physics.step(particles, 0.0)

        positions = particles.active_positions
        separation = float(np.linalg.norm(positions[0] - positions[1]))
        self.assertAlmostEqual(separation, 6.0, places=4)
        self.assertTrue(np.isfinite(positions).all())
        self.assertTrue(np.isfinite(particles.active_previous_positions).all())
        self.assertGreater(physics.overlaps, 0)

    def test_spread_particles_only_check_local_candidates(self) -> None:
        particles = ParticleSystem(capacity=100, seed=2)
        for x_index in range(10):
            for y_index in range(10):
                particles.spawn(100.0 + 12.0 * x_index, 100.0 + 12.0 * y_index)
        physics = self.make_physics(collisions_enabled=True, collision_iterations=1)

        physics.step(particles, 0.0)

        # A full all-pairs scan would consider 4,950 pairs; the hash finds none
        # in the local 3x3 cell neighborhoods for this deliberately sparse set.
        self.assertEqual(physics.candidate_pairs, 0)
        self.assertEqual(physics.overlaps, 0)

    def test_each_candidate_pair_is_counted_once_per_pass(self) -> None:
        particles = ParticleSystem(capacity=3, seed=3)
        for x in (100.0, 101.0, 102.0):
            particles.spawn(x, 100.0)
        physics = self.make_physics(collisions_enabled=True, collision_iterations=1)

        physics.step(particles, 0.0)

        self.assertEqual(physics.candidate_pairs, 3)
        self.assertEqual(physics.overlaps, 3)

    def test_collision_correction_does_not_add_verlet_velocity(self) -> None:
        particles = ParticleSystem(capacity=2, seed=3)
        particles.spawn(100.0, 100.0)
        particles.spawn(104.0, 100.0)
        physics = self.make_physics(collisions_enabled=True, collision_iterations=1)

        physics.step(particles, 0.0)

        implicit_velocity = particles.active_positions - particles.active_previous_positions
        np.testing.assert_allclose(implicit_velocity, np.zeros((2, 2)), atol=1e-6)

    def test_collision_correction_is_clamped_back_inside_walls(self) -> None:
        particles = ParticleSystem(capacity=2, seed=4)
        particles.spawn(3.0, 100.0)
        particles.spawn(5.0, 100.0)
        physics = self.make_physics(
            collisions_enabled=True,
            collision_iterations=1,
            left_wall=3.0,
            right_wall=200.0,
            ceiling=3.0,
            floor=200.0,
        )

        physics.step(particles, 0.0)

        self.assertGreaterEqual(float(particles.active_positions[:, 0].min()), 3.0)
        self.assertTrue(np.isfinite(particles.active_positions).all())

    def test_disabled_collisions_preserve_overlaps_and_report_no_work(self) -> None:
        particles = ParticleSystem(capacity=2, seed=5)
        particles.spawn(100.0, 100.0)
        particles.spawn(100.0, 100.0)
        physics = self.make_physics(collisions_enabled=False)

        physics.step(particles, 0.0)

        np.testing.assert_array_equal(particles.active_positions[0], particles.active_positions[1])
        self.assertEqual(physics.candidate_pairs, 0)
        self.assertEqual(physics.overlaps, 0)
        self.assertEqual(physics.collision_time_ms, 0.0)

    def test_many_coincident_particles_remain_finite(self) -> None:
        count = 128
        particles = ParticleSystem(capacity=count, seed=6)
        for _ in range(count):
            particles.spawn(300.0, 200.0)
        physics = self.make_physics(collisions_enabled=True, collision_iterations=3)

        physics.step(particles, 0.0)

        self.assertTrue(np.isfinite(particles.active_positions).all())
        self.assertTrue(np.isfinite(particles.active_previous_positions).all())
        self.assertGreater(physics.candidate_pairs, 0)
        self.assertTrue(math.isfinite(physics.collision_time_ms))

    def test_collision_toggle_resets_stats(self) -> None:
        physics = self.make_physics(collisions_enabled=False)
        physics.candidate_pairs = 12
        physics.overlaps = 4
        physics.collision_time_ms = 1.5

        self.assertTrue(physics.toggle_collisions())
        self.assertEqual(physics.candidate_pairs, 0)
        self.assertEqual(physics.overlaps, 0)
        self.assertEqual(physics.collision_time_ms, 0.0)
        self.assertFalse(physics.toggle_collisions())


if __name__ == "__main__":
    unittest.main()
