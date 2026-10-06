from __future__ import annotations

import unittest

from sandbox.spatial import SpatialHash


class SpatialHashTests(unittest.TestCase):
    def test_rebuild_uses_floor_and_particle_indices(self) -> None:
        spatial = SpatialHash(cell_size=6)
        spatial.rebuild([(-0.1, 0.0), (0.0, 0.0), (5.999, 0.0), (6.0, 0.0)])

        self.assertEqual(spatial.particles_in_cell((-1, 0)), (0,))
        self.assertEqual(spatial.particles_in_cell((0, 0)), (1, 2))
        self.assertEqual(spatial.particles_in_cell((1, 0)), (3,))
        self.assertEqual(spatial.particle_count, 4)
        self.assertEqual(spatial.occupied_cell_count, 3)

    def test_query_returns_local_cell_candidates(self) -> None:
        spatial = SpatialHash(cell_size=6)
        spatial.rebuild([(5.5, 2.0), (6.2, 2.0), (20.0, 2.0)])

        candidates = set(spatial.query_nearby(5.5, 2.0, radius=1.0))
        self.assertEqual(candidates, {0, 1})

    def test_rebuild_and_clear_discard_old_cells(self) -> None:
        spatial = SpatialHash(cell_size=6)
        spatial.rebuild([(1.0, 1.0), (2.0, 2.0)])
        spatial.rebuild([(30.0, -7.0)])

        self.assertEqual(spatial.particles_in_cell((0, 0)), ())
        self.assertEqual(spatial.particles_in_cell((5, -2)), (0,))
        self.assertEqual(spatial.particle_count, 1)

        spatial.clear()
        self.assertEqual(spatial.particle_count, 0)
        self.assertEqual(spatial.occupied_cell_count, 0)

    def test_invalid_cell_size_and_query_radius_are_rejected(self) -> None:
        for cell_size in (0, -1, float("inf")):
            with self.subTest(cell_size=cell_size):
                with self.assertRaises(ValueError):
                    SpatialHash(cell_size=cell_size)

        spatial = SpatialHash(cell_size=6)
        with self.assertRaises(ValueError):
            list(spatial.query_nearby(0, 0, radius=-1))


if __name__ == "__main__":
    unittest.main()
