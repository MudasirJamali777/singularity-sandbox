"""Verlet - raftaar store kiye baghair.

    next = current + (current - previous) + acceleration * dt**2

Farq hi chalna hai. Gravity sirf y par; Pygame mein y neeche jaata hai.
Chaaron kinare aa gaye - har takraav par thoda sa uchhaal (BOUNCE).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from sandbox.config import (
    ATTRACTOR_RADIUS,
    ATTRACTOR_STRENGTH,
    BOUNCE,
    EXPLOSION_RADIUS,
    EXPLOSION_STRENGTH,
    GRAVITY,
    PARTICLE_RADIUS,
    PHYSICS_DT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from sandbox.particles import ParticleSystem

class PhysicsSystem:
    """Ek chhoti dhadkan - sab ko aage badha dena.

    Attributes:
        gravity: neeche ki kheench, pixels per second squared.
        bounce: har takraav par kitni raftaar wapas, 0.0 se 1.0 tak.
        floor, ceiling, left_wall, right_wall: kinare, radius ke hisaab se.
        attractor_radius, attractor_strength: kheench ka daayra aur zor.
        explosion_radius, explosion_strength: dhamake ka daayra aur zor.

    Gravity hamesha rehti hai; bahar ki taqatain har qadam par taza di
    jaati hain (``attract`` / ``clear_forces``) - isliye poore jama ka hisaab
    ek hi jagah, ek hi qadam mein hota hai.
    """

    def __init__(
        self,
        gravity: float = GRAVITY,
        bounce: float = BOUNCE,
        floor: float = WINDOW_HEIGHT - PARTICLE_RADIUS,
        ceiling: float = PARTICLE_RADIUS,
        left_wall: float = PARTICLE_RADIUS,
        right_wall: float = WINDOW_WIDTH - PARTICLE_RADIUS,
        attractor_radius: float = ATTRACTOR_RADIUS,
        attractor_strength: float = ATTRACTOR_STRENGTH,
        explosion_radius: float = EXPLOSION_RADIUS,
        explosion_strength: float = EXPLOSION_STRENGTH,
    ) -> None:
        self.gravity = float(gravity)
        self.bounce = float(bounce)
        # Radius ke hisaab se - warna aadhe particle bahar jhaankte hain.
        self.floor = float(floor)
        self.ceiling = float(ceiling)
        self.left_wall = float(left_wall)
        self.right_wall = float(right_wall)
        # Bahar ki taqatain - attractor kheenchti hai, explosion udaata hai.
        self.attractor_radius = float(attractor_radius)
        self.attractor_strength = float(attractor_strength)
        self.explosion_radius = float(explosion_radius)
        self.explosion_strength = float(explosion_strength)
        # Sirf y ki taraf kheench.
        self._acceleration: NDArray[np.float32] = np.array(
            (0.0, self.gravity), dtype=np.float32
        )
        # Scratch: ek baar bane, phir usi mein likhe.
        self._displacement: NDArray[np.float32] | None = None
        # Bahar ki taqatain - har frame taza, aur kuch na ho to khaali.
        self._forces: tuple[tuple[NDArray[np.bool_], NDArray[np.float32], float], ...] = ()
        self._external: NDArray[np.float32] | None = None
        # Force ke hisaab ke do khali bartan - dobara istemal ke liye.
        self._delta: NDArray[np.float32] | None = None
        self._dist_sq: NDArray[np.float32] | None = None

    # ------------------------------------------------------------------
    # Bahar ki taqatain
    # ------------------------------------------------------------------
    def set_forces(
        self,
        *forces: tuple[NDArray[np.bool_], NDArray[np.float32], float],
    ) -> None:
        """Agle qadam ke liye taqatain: har ek ``(mask, directions, strength)``.

        - ``mask``: kaun jal raha hai, shape ``(count,)``.
        - ``directions``: kis taraf, shape ``(count, 2)`` - unit vectors.
        - ``strength``: kitne zor se, pixels per second squared.

        Yeh khali list bhi ho sakti hai (sirf gravity). Har qadam par taaza
        di jaati hai, isliye mask khud compute nahi hota - jisne mask banaya
        wohi jaanta hai ke andar kaun tha.
        """
        for mask, directions, _ in forces:
            if mask.shape[0] != directions.shape[0]:
                raise ValueError("mask aur directions ka size ek hona chahiye")
        self._forces = forces

    def clear_forces(self) -> None:
        """Bahar ki taqatain khatam - sirf gravity bachi."""
        self._forces = ()

    def attract(self, particles: ParticleSystem, center: tuple[float, float]) -> None:
        """``center`` ki taraf narm kheench - agle qadam ke liye.

        Radius ke andar wale hi khinchte hain; bahar wale azad. Zor markaz
        par sabse zyada aur radius par bilkul khatam - seedhi lakeer, koi
        ulta-square gravity nahi. Yeh teleport nahi, asli acceleration hai.
        """
        current = particles.active_positions
        if particles.count == 0:
            self.clear_forces()
            return

        offsets, inside = self._radial_offsets(current, center, self.attractor_radius)
        # Kheench andar ki taraf - isliye offsets ka ulta.
        self.set_forces((inside, -offsets, self.attractor_strength))

    def explode(self, particles: ParticleSystem, center: tuple[float, float]) -> int:
        """Ek dhamaka - abhi, bas ek hi baar. Lautata hai kitne uday.

        Raftaar kahin store nahi, magar ``current - previous`` mein chhupi
        hoti hai. Isliye dhakka ``previous`` mein likha jaata hai: agle qadam
        par Verlet khud usay bahar ki raftaar samajhta hai. ``current`` ko
        chhua nahi jaata - teleport bilkul nahi.
        """
        if particles.count == 0:
            return 0

        previous = particles.active_previous_positions
        offsets, inside = self._radial_offsets(
            particles.active_positions, center, self.explosion_radius
        )
        if not inside.any():
            return 0

        # Dhakka = raftaar ka badlaav (px/s) * ek chhota qadam (s).
        # Isse unit ka matlab waqt se nahi badalta: sirf raftaar.
        previous[inside] -= offsets[inside] * (self.explosion_strength * PHYSICS_DT)
        return int(inside.sum())

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def step(self, particles: ParticleSystem, dt: float) -> None:
        """Har zinda particle ko ``dt`` second aage badhao, phir kinare sambhalo.

        Tarteeb hi asal baat hai - dono views seedha storage mein jhankti hain:

        1. Pehle farq (current - previous) scratch mein.
        2. Phir current ko history mein likho. Yeh pehle kiya to wahi farq
           mit jaata - aur raftaar chupchaap kho jaati.
        3. Aakhir mein current aage badhao, phir deewaron se takrao.

        Gravity ke upar bahar ki taqatain bhi isi qadam mein jama hoti hain -
        magar sirf tab, jab koi chal rahi ho. ``count`` se aage wale khane
        kabhi chhue nahi jaate.
        """
        count = particles.count
        if count == 0:
            return

        current = particles.active_positions
        previous = particles.active_previous_positions

        displacement = self._displacement_scratch(particles.capacity)[:count]
        np.subtract(current, previous, out=displacement)

        # History: qadam se pehle kahan tha.
        np.copyto(previous, current)

        current += displacement
        current += self._acceleration * (dt * dt)

        # Gravity ke upar bahar ki taqatain - agar is waqt koi jal rahi hai.
        if self._forces:
            current += self._external_acceleration(count) * (dt * dt)

        self._apply_boundaries(current, previous)

    # ------------------------------------------------------------------
    # Kinare
    # ------------------------------------------------------------------
    def _apply_boundaries(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
    ) -> None:
        """Chaaron kinare - dono axis, apne apne mask ke saath.

        Har kinara alag mask hai (hit_left / hit_right / hit_top /
        hit_bottom), isliye sirf takraane wale particles chhue jaate hain;
        hawa mein udte hue bilkul azad rehte hain.
        """
        # Y: ceiling (chhoti value) aur floor (bari value).
        self._bounce_axis(current, previous, 1, self.ceiling, self.floor)
        # X: left wall (chhoti value) aur right wall (bari value).
        self._bounce_axis(current, previous, 0, self.left_wall, self.right_wall)

    def _bounce_axis(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
        axis: int,
        low: float,
        high: float,
    ) -> None:
        """Ek axis ke dono kinare.

        Qaida har kinare par ek hi hai:

            purana displacement : d = current - previous
            naya  displacement : -BOUNCE * d

        Verlet mein displacement ``current - previous`` chhipa hua hai, isliye
        naya displacement ``previous`` ke zariye likha jaata hai:

            previous = current - naya_displacement

        ``current`` pehle kinare par clamp ho jata hai, to yeh yun banta hai:

            previous = kinara + BOUNCE * d

        BOUNCE = 0 par ``previous`` kinare par hi ruk jata hai (purana
        behaviour); BOUNCE = 1 par poori raftaar wapas. Dono current aur
        previous barabar kar dena ghalat hai - woh particle ko rook deta hai,
        uchhaal nahi.
        """
        positions = current[:, axis]
        previous_axis = previous[:, axis]
        # Purana displacement pehle pakdo, warna clamp karne par mit jayega.
        step_d = positions - previous_axis

        hit_low = positions < low
        if hit_low.any():
            positions[hit_low] = low
            outgoing = -self.bounce * step_d[hit_low]
            previous_axis[hit_low] = low - outgoing

        hit_high = positions > high
        if hit_high.any():
            positions[hit_high] = high
            outgoing = -self.bounce * step_d[hit_high]
            previous_axis[hit_high] = high - outgoing

    # ------------------------------------------------------------------
    # Andar
    # ------------------------------------------------------------------
    def _radial_offsets(
        self,
        current: NDArray[np.float32],
        center: tuple[float, float],
        radius: float,
    ) -> tuple[NDArray[np.float32], NDArray[np.bool_]]:
        """Markaz se har particle tak ka vector - ``(offsets, inside)``.

        ``offsets[i]`` ki lambai hi falloff hai: markaz par sabse tez, radius
        par khatam. Simt (direction) bahar ki taraf - jo andar kheenchta hai
        woh isay ulta kar leta hai.

        Bilkul markaz par delta khud zero hota hai, aur ``maximum`` chhote
        se bacha kar rakhta hai - isliye na zero se taqseem, na NaN.
        """
        count = current.shape[0]
        delta = self._scratch("_delta", (count, 2))
        np.subtract(current, center, out=delta)

        dist_sq = self._scratch("_dist_sq", (count,))
        np.einsum("ij,ij->i", delta, delta, out=dist_sq)

        inside = dist_sq < radius * radius
        offsets = np.zeros_like(delta)
        if inside.any():
            dist = np.sqrt(dist_sq[inside])
            falloff = 1.0 - dist / radius
            np.maximum(falloff, 0.0, out=falloff)
            safe = np.maximum(dist, 1e-6)
            offsets[inside] = (delta[inside] / safe[:, None]) * falloff[:, None]
        return offsets, inside

    def _scratch(self, name: str, shape: tuple[int, ...]) -> NDArray[np.float32]:
        """Naam wala ek hi buffer - jagah barhne par naya, warna wahi purana."""
        buf = getattr(self, name)
        if buf is None or buf.shape[0] < shape[0]:
            buf = np.empty(shape, dtype=np.float32)
            setattr(self, name, buf)
        return buf[: shape[0]]

    def _external_acceleration(self, count: int) -> NDArray[np.float32]:
        """Sab zinda forces ka jama hua acceleration - shape ``(count, 2)``.

        Pehle buffer saaf, phir sirf un rows par likha jaata hai jahan mask
        ``True`` hai. Buffer dobara istemal hota hai - har qadam naya array
        banane ki zaroorat nahi.
        """
        acc = self._external
        if acc is None or acc.shape[0] != count:
            acc = np.zeros((count, 2), dtype=np.float32)
            self._external = acc
        else:
            acc.fill(0.0)

        for mask, directions, strength in self._forces:
            # Purane qadam ka force ho sakta hai - ab lena dena nahi.
            if mask.shape[0] != count:
                continue
            np.add(acc, directions * strength, out=acc, where=mask[:, None])
        return acc

    def _displacement_scratch(self, capacity: int) -> NDArray[np.float32]:
        """``capacity`` rows ka float32 buffer.

        Jagah capacity se li jaati hai, count se nahi - warna painting
        har frame resize karti.
        """
        scratch = self._displacement
        if scratch is None or scratch.shape[0] < capacity:
            scratch = np.empty((capacity, 2), dtype=np.float32)
            self._displacement = scratch
        return scratch

    def __repr__(self) -> str:
        return (
            f"PhysicsSystem(gravity={self.gravity}, bounce={self.bounce}, "
            f"bounds=({self.left_wall}, {self.ceiling}, "
            f"{self.right_wall}, {self.floor}))"
        )