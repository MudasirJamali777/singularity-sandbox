"""Padosiyon ka naqsha - har particle apne khane mein.

Duniya ko chhote chhote khano mein baant dete hain, aur har khane ko yaad
rakhte hain ke us mein kaun hai. Phir kisi ka padosi dhoondhna poore dhundle
ko chhanna nahi hota - sirf apne aas paas ke nau khane dekhne hote hain.
Isi liye yeh O(N^2) ki jagah O(N) jaisa kaam hai.

Naqsha ek saada table hai: har khane ki ek khaana, jis mein likha hota hai
ke uska pehla particle kahan hai. Isi liye padosi dhoondhne mein na koi
sawaal, na koi dhoondh - bas table se ek value utha li jaati hai.

Yeh khud kuch faesla nahi karta: na takraav, na gravity, na simt. Sirf itna
batata hai ke kaun kahan hai aur kaun kaun paas paas hai.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator

import numpy as np
from numpy.typing import NDArray

from sandbox.config import CELL_SIZE, MAX_CANDIDATE_PAIRS_PER_CELL, WINDOW_HEIGHT, WINDOW_WIDTH

# Table screen ke bahar bhi itne khane yaad rakhti hai (40 * 6 = 240 px).
# Is se zyada door wale particles kinare ke khane mein sata diye jaate hain:
# unke jore ginnay ka koi faida nahi, aur naqsha chhota rehta hai.
_MARGIN_CELLS = 40

# Aage ke khane: dahina, neeche, neeche-dahina, neeche-baya. In chaar simton
# se har padosi khana theek ek baar aata hai - (1,0) apne ulte (-1,0) ko bhi
# dhaanp leta hai, aur isi tarah baaki.
_FORWARD = ((1, 0), (0, 1), (1, 1), (-1, 1))

_EMPTY_INDEX: NDArray[np.int64] = np.empty(0, dtype=np.int64)
_EMPTY_PAIRS: tuple[NDArray[np.int64], NDArray[np.int64]] = (_EMPTY_INDEX, _EMPTY_INDEX)


def _expand(pairs_per: NDArray[np.int64], cap: int) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    """Har group ke jore gin kar unki fehrist - repeat aur cumsum ka jaadu.

    ``group`` batata hai jora kis group ka hai, aur ``k`` us group ke andar
    0 se shuru hota hai. Isi liye aage ka hisaab (``k // n``, ``k % n``,
    ya triangle) bina kisi Python loop ke seedha ho jata hai.

    ``cap`` sirf patle haadsay ke liye hai: ek hi khane mein hazaron
    particles hon to unke jore ginne se pehle hi ruk jao.
    """
    capped = np.minimum(pairs_per, cap)
    total = int(capped.sum())
    if total == 0:
        return _EMPTY_INDEX, _EMPTY_INDEX
    group = np.repeat(np.arange(capped.size, dtype=np.int64), capped)
    k = np.arange(total, dtype=np.int64) - np.repeat(np.cumsum(capped) - capped, capped)
    return group, k


def _row_in_triangle(k: NDArray[np.int64], n: NDArray[np.int64]) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    """Triangle ka ``k``-wan jora - ``(i, j)`` jahan ``j > i``.

    Ek khane mein ``n`` particles hon to jore ``n(n-1)/2`` hi hote hain, aur
    row ``i`` mein ``n-1-i``. Yeh seedha quadratic hai: andaza float se lagta
    hai, phir do chhote sudhaar usay poora theek kar dete hain.
    """
    i = np.floor(((2.0 * n - 1.0) - np.sqrt((2.0 * n - 1.0) ** 2 - 8.0 * k)) / 2.0).astype(np.int64)
    np.clip(i, 0, n - 2, out=i)
    for _ in range(2):
        offset = i * n - i * (i + 1) // 2
        i -= offset > k
        next_offset = (i + 1) * n - (i + 1) * (i + 2) // 2
        i += next_offset <= k
    offset = i * n - i * (i + 1) // 2
    return i, i + 1 + (k - offset)


class SpatialHash:
    """Ek uniform grid - har khana, aur us mein baithay hue particles.

    Attributes:
        cell_size: khane ka naap, pixels mein (takraav ke diameter jitna).
        count: pichhle ``rebuild`` mein kitne particles the.
        keys: bharay hue khano ki keys, tarteeb se.
        cells_x, cells_y: un khano ki asli grid wali jagah.
        counts: har bhare khane mein kitne particles.
        starts: har khane ka pehla particle ``order`` mein kahan hai.
        order: particles ki fehlist, khane ke hisaab se tarteeb di hui.
        candidate_count: pichhli baar kitne jore banaye.
    """

    def __init__(
        self,
        cell_size: float = CELL_SIZE,
        max_pairs_per_cell: int = MAX_CANDIDATE_PAIRS_PER_CELL,
    ) -> None:
        cell_size = float(cell_size)
        if not math.isfinite(cell_size) or cell_size <= 0.0:
            raise ValueError(f"cell_size must be finite and positive, got {cell_size}")
        if max_pairs_per_cell <= 0:
            raise ValueError(
                f"max_pairs_per_cell must be positive, got {max_pairs_per_cell}"
            )

        self.cell_size = cell_size
        self.max_pairs_per_cell = int(max_pairs_per_cell)
        self.count = 0
        self.candidate_count = 0
        self.order: NDArray[np.int64] = _EMPTY_INDEX
        self.keys: NDArray[np.int64] = _EMPTY_INDEX
        self.cells_x: NDArray[np.int64] = _EMPTY_INDEX
        self.cells_y: NDArray[np.int64] = _EMPTY_INDEX
        self.counts: NDArray[np.int64] = _EMPTY_INDEX
        self.starts: NDArray[np.int64] = _EMPTY_INDEX
        self._pairs: tuple[NDArray[np.int64], NDArray[np.int64]] | None = None
        # Table: har khane ki ek khaana, is mein uska slot (ya -1).
        self._inside_w = int(math.ceil(WINDOW_WIDTH / self.cell_size))
        self._inside_h = int(math.ceil(WINDOW_HEIGHT / self.cell_size))
        self._table_w = self._inside_w + 2 * _MARGIN_CELLS
        self._table_h = self._inside_h + 2 * _MARGIN_CELLS
        self._table = np.full((self._table_h + 1, self._table_w + 1), -1, dtype=np.int32)

    # ------------------------------------------------------------------
    # Naqsha dobara
    # ------------------------------------------------------------------
    @property
    def particle_count(self) -> int:
        """Number of indices in the most recently built index."""
        return self.count

    @property
    def occupied_cell_count(self) -> int:
        """Number of nonempty grid cells."""
        return int(self.keys.size)

    def clear(self) -> None:
        """Forget indexed particles and cached pairs."""
        self.count = 0
        self.candidate_count = 0
        self.order = _EMPTY_INDEX
        self.keys = _EMPTY_INDEX
        self.cells_x = _EMPTY_INDEX
        self.cells_y = _EMPTY_INDEX
        self.counts = _EMPTY_INDEX
        self.starts = _EMPTY_INDEX
        self._pairs = None
        self._table.fill(-1)

    def rebuild(
        self,
        positions: NDArray[np.float32],
        particle_indices: Iterable[int] | None = None,
    ) -> None:
        """Build the grid from all positions or a selected index subset.

        A subset retains original particle IDs in the grid, which lets the
        WATER-only SPH pass query neighbors without renumbering particles.
        """
        positions = np.asarray(positions, dtype=np.float32)
        if particle_indices is None:
            indices = np.arange(positions.shape[0], dtype=np.int64)
        elif isinstance(particle_indices, np.ndarray):
            indices = np.asarray(particle_indices, dtype=np.int64)
        else:
            indices = np.fromiter(particle_indices, dtype=np.int64)
        count = int(indices.size)
        self.count = count
        self.candidate_count = 0
        self._pairs = None

        if count == 0:
            self.order = _EMPTY_INDEX
            self.keys = _EMPTY_INDEX
            self.cells_x = _EMPTY_INDEX
            self.cells_y = _EMPTY_INDEX
            self.counts = _EMPTY_INDEX
            self.starts = _EMPTY_INDEX
            self._table.fill(-1)
            return

        selected = positions[indices]
        tx = np.floor(selected[:, 0] / self.cell_size).astype(np.int32) + _MARGIN_CELLS
        ty = np.floor(selected[:, 1] / self.cell_size).astype(np.int32) + _MARGIN_CELLS
        np.clip(tx, 0, self._table_w - 1, out=tx)
        np.clip(ty, 0, self._table_h - 1, out=ty)
        keys = ty * self._table_w + tx

        # Keep the original particle IDs in sorted cell order.
        sort_order = np.argsort(keys)
        self.order = indices[sort_order]
        sorted_keys = keys[sort_order]

        # Bhare hue khane: tarteeb pehle se hai, isliye sirf badlaav dhoondho
        # - poora unique dobara sort karne ki zaroorat nahi.
        change = np.empty(count, dtype=bool)
        change[0] = True
        np.not_equal(sorted_keys[1:], sorted_keys[:-1], out=change[1:])
        starts = np.flatnonzero(change)

        self.starts = starts
        self.counts = np.diff(np.append(starts, count))
        self.keys = sorted_keys[starts].astype(np.int64)
        self.cells_x = self.keys % self._table_w - _MARGIN_CELLS
        self.cells_y = self.keys // self._table_w - _MARGIN_CELLS

        self._table.fill(-1)
        self._table[self.cells_y + _MARGIN_CELLS, self.cells_x + _MARGIN_CELLS] = np.arange(
            self.keys.size, dtype=np.int32
        )

    # ------------------------------------------------------------------
    # Padosi
    # ------------------------------------------------------------------
    def candidate_pairs(self) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
        """Woh saare jore jo takra sakte hain - har jora sirf ek baar.

        Ek hi khane ke jore bhi shamil hain (bas ``j > i`` wale), aur aage
        ke aathwan khane bhi. Poora kaam NumPy ka hai - particles par koi
        loop nahi. Nateeja yaad rakha jata hai, isliye solver ke pass ek
        hi qadam mein kai baar isay maangna sasta hai.
        """
        if self._pairs is None:
            self._pairs = self._build_pairs()
            self.candidate_count = int(self._pairs[0].size)
        return self._pairs

    def _build_pairs(self) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
        """Naqshe se jore - NumPy ke andar, particles par koi loop nahi."""
        if self.count < 2:
            return _EMPTY_PAIRS

        order = self.order
        starts = self.starts
        counts = self.counts
        parts_i: list[NDArray[np.int64]] = []
        parts_j: list[NDArray[np.int64]] = []

        # 1) Apna hi khana: sirf j > i, warna har jora do baar banta. Jahan
        #    ek ya do particle hain wahan jora seedha hai; teen se zyada par
        #    triangle ka hisaab.
        big = counts >= 3
        if big.any():
            rows = np.flatnonzero(big)
            group, k = _expand(counts[rows] * (counts[rows] - 1) // 2, self.max_pairs_per_cell)
            if k.size:
                i_local, j_local = _row_in_triangle(k, counts[rows][group])
                base = starts[rows][group]
                parts_i.append(order[base + i_local])
                parts_j.append(order[base + j_local])
        pairs = np.flatnonzero(counts == 2)
        if pairs.size:
            parts_i.append(order[starts[pairs]])
            parts_j.append(order[starts[pairs] + 1])

        # 2) Aage ke khane - table se seedha slot, koi dhoondh nahi.
        cols = self.cells_x + _MARGIN_CELLS
        rows = self.cells_y + _MARGIN_CELLS
        table = self._table
        for step_x, step_y in _FORWARD:
            slots = table[rows + step_y, cols + step_x]
            here = np.flatnonzero(slots >= 0)
            if not here.size:
                continue
            there = slots[here].astype(np.int64)
            here_counts = counts[here]
            there_counts = counts[there]

            # Jahan dono khane ek ek particle ke - jora seedha hai, koi
            # ginna nahi. Yeh sabse aam haal hai.
            single = (here_counts == 1) & (there_counts == 1)
            if single.any():
                rows_one = here[single]
                cols_one = there[single]
                parts_i.append(order[starts[rows_one]])
                parts_j.append(order[starts[cols_one]])

            many = ~single
            if many.any():
                rows_many = here[many]
                cols_many = there[many]
                group, k = _expand(counts[rows_many] * counts[cols_many], self.max_pairs_per_cell)
                if k.size:
                    other = counts[cols_many][group]
                    parts_i.append(order[starts[rows_many][group] + k // other])
                    parts_j.append(order[starts[cols_many][group] + k % other])

        if not parts_i:
            return _EMPTY_PAIRS
        first = np.concatenate(parts_i)
        second = np.concatenate(parts_j)
        # Har jora chhote index se shuru: i < j. Do alag khano ke jore mein
        # tarteeb particle ke number se aati hai, khane se nahi - isliye
        # ek hi jora (3, 7) aur (7, 3) dono shaklon mein aa sakta hai.
        # Yahan ek hi baar tarteeb theek kar dete hain.
        return np.minimum(first, second), np.maximum(first, second)

    def query_nearby(
        self,
        x: float,
        y: float,
        radius: float | None = None,
    ) -> Iterator[int]:
        """Yield conservative candidates from cells within a radius square.

        The reach uses ``ceil(radius / cell_size)`` so a query larger than one
        cell (for example SPH_H) still visits every potentially intersecting
        cell. Callers perform the exact Euclidean distance test.
        """
        query_radius = self.cell_size if radius is None else float(radius)
        if not math.isfinite(query_radius) or query_radius < 0.0:
            raise ValueError(f"radius must be finite and non-negative, got {query_radius}")
        reach = math.ceil(query_radius / self.cell_size)
        center_x = min(
            max(math.floor(float(x) / self.cell_size) + _MARGIN_CELLS, 0),
            self._table_w - 1,
        )
        center_y = min(
            max(math.floor(float(y) / self.cell_size) + _MARGIN_CELLS, 0),
            self._table_h - 1,
        )
        x0, x1 = max(0, center_x - reach), min(self._table_w, center_x + reach + 1)
        y0, y1 = max(0, center_y - reach), min(self._table_h, center_y + reach + 1)
        for cell_y in range(y0, y1):
            for cell_x in range(x0, x1):
                slot = int(self._table[cell_y, cell_x])
                if slot >= 0:
                    start = int(self.starts[slot])
                    end = start + int(self.counts[slot])
                    yield from self.order[start:end]

    def neighbors_of(self, x: float, y: float) -> NDArray[np.int64]:
        """Return candidates in the same/adjacent cells around a point."""
        return np.fromiter(
            self.query_nearby(x, y, self.cell_size), dtype=np.int64
        )

    def occupied_cells(self) -> tuple[NDArray[np.int64], NDArray[np.int64], NDArray[np.int64]]:
        """Bhare hue khane - ``(cells_x, cells_y, counts)``."""
        return self.cells_x, self.cells_y, self.counts

    def iter_occupied_cells(self) -> Iterator[tuple[tuple[int, int], int]]:
        """Yield occupied world-cell coordinates and population."""
        for x, y, count in zip(self.cells_x, self.cells_y, self.counts):
            yield (int(x), int(y)), int(count)

    def particles_in_cell(self, cell: tuple[int, int]) -> tuple[int, ...]:
        """Return a read-only snapshot of particle IDs in a world cell."""
        x = min(max(int(cell[0]) + _MARGIN_CELLS, 0), self._table_w - 1)
        y = min(max(int(cell[1]) + _MARGIN_CELLS, 0), self._table_h - 1)
        slot = int(self._table[y, x])
        if slot < 0:
            return ()
        start = int(self.starts[slot])
        end = start + int(self.counts[slot])
        return tuple(int(index) for index in self.order[start:end])

    def __repr__(self) -> str:
        return (
            f"SpatialHash(cell_size={self.cell_size:.1f}, count={self.count}, "
            f"cells={self.keys.size}, pairs={self.candidate_count})"
        )