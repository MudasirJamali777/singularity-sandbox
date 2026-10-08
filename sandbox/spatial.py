"""A small, Pygame-independent uniform spatial hash for 2D neighbors.

The hash only indexes points and returns nearby particle indices. Physics
resolution belongs to :mod:`sandbox.physics`.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator, Sequence

from sandbox.config import CELL_SIZE

Cell = tuple[int, int]
Position = Sequence[float]


class SpatialHash:
    """Map 2D positions into uniform cells and query nearby candidates.

    Args:
        cell_size: Width and height of each square cell, in world units.

    Positions are indexed with ``floor(position / cell_size)`` so negative
    coordinates are handled correctly too. The class knows nothing about
    Pygame, particle forces, or collision resolution.
    """

    def __init__(self, cell_size: float = CELL_SIZE) -> None:
        cell_size = float(cell_size)
        if not math.isfinite(cell_size) or cell_size <= 0.0:
            raise ValueError(f"cell_size must be finite and positive, got {cell_size}")

        self.cell_size = cell_size
        self._cells: dict[Cell, list[int]] = {}
        self.particle_count = 0

    @property
    def occupied_cell_count(self) -> int:
        """Number of cells containing at least one indexed position."""
        return len(self._cells)

    def clear(self) -> None:
        """Remove all indexed positions."""
        self._cells.clear()
        self.particle_count = 0

    def rebuild(
        self,
        positions: Sequence[Position],
        particle_indices: Iterable[int] | None = None,
    ) -> None:
        """Rebuild the index from selected current positions.

        By default, each position's enumeration index is stored. An optional
        sequence of indices lets a caller (such as SPH) index only one
        material while retaining the original particle indices in buckets.
        Passing an active NumPy slice works, but NumPy is not a dependency.
        """
        self.clear()
        if particle_indices is None:
            indexed_positions = enumerate(positions)
        else:
            indexed_positions = (
                (int(particle_index), positions[int(particle_index)])
                for particle_index in particle_indices
            )

        for particle_index, position in indexed_positions:
            cell_x = math.floor(float(position[0]) / self.cell_size)
            cell_y = math.floor(float(position[1]) / self.cell_size)
            self._cells.setdefault((cell_x, cell_y), []).append(particle_index)
            self.particle_count += 1

    def query_nearby(
        self,
        x: float,
        y: float,
        radius: float | None = None,
    ) -> Iterator[int]:
        """Yield indices in cells intersecting a square around ``(x, y)``.

        The query is deliberately conservative: it returns candidates from
        the axis-aligned square with the requested radius. The caller should
        perform its own exact-distance test. If omitted, ``radius`` defaults
        to one cell width, which checks the same and adjacent cells for the
        usual collision diameter-sized cell.
        """
        query_radius = self.cell_size if radius is None else float(radius)
        if not math.isfinite(query_radius) or query_radius < 0.0:
            raise ValueError(f"radius must be finite and non-negative, got {query_radius}")

        center_cell_x = math.floor(float(x) / self.cell_size)
        center_cell_y = math.floor(float(y) / self.cell_size)
        # Any intersecting cell differs by no more than ceil(radius / cell).
        # This is conservative at cell boundaries and avoids four additional
        # floor/division operations for the common diameter-sized query.
        reach = math.ceil(query_radius / self.cell_size)

        for cell_y in range(center_cell_y - reach, center_cell_y + reach + 1):
            for cell_x in range(center_cell_x - reach, center_cell_x + reach + 1):
                yield from self._cells.get((cell_x, cell_y), ())

    def iter_occupied_cells(self) -> Iterator[tuple[Cell, int]]:
        """Yield each occupied cell and its population, without exposing edits."""
        for cell, indices in self._cells.items():
            yield cell, len(indices)

    def particles_in_cell(self, cell: Cell) -> tuple[int, ...]:
        """Return a read-only snapshot of the indices in ``cell``."""
        return tuple(self._cells.get(cell, ()))

    def __repr__(self) -> str:
        return (
            f"SpatialHash(cell_size={self.cell_size}, "
            f"particles={self.particle_count}, cells={self.occupied_cell_count})"
        )