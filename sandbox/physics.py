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
    COLLISION_CONTACT_MARGIN,
    COLLISION_DEGENERATE_DISTANCE,
    COLLISION_ITERATIONS,
    COLLISION_PREVIOUS_SHARE,
    COLLISION_SLOP,
    EXPLOSION_RADIUS,
    EXPLOSION_STRENGTH,
    GRAVITATIONAL_CONSTANT,
    GRAVITY,
    PARTICLE_RADIUS,
    PHYSICS_DT,
    WELL_SOFTENING,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from sandbox.gravity import GravityWells
from sandbox.particles import ParticleSystem
from sandbox.spatial import SpatialHash

def _fallback_angle(first: NDArray[np.int64], second: NDArray[np.int64]) -> NDArray[np.float64]:
    """Ek hi jagah phanse jore ki simt - indices se banti hai.

    Deterministic hai (wahi indices, wahi simt) aur alag alag jore alag
    taraf khinche jaate hain - warna poora dher ek hi lakeer ban jata.
    """
    mixed = first.astype(np.int64) * 2654435761 + second.astype(np.int64) * 40503
    return (mixed % 6283) * 1e-3

class PhysicsSystem:
    """Ek chhoti dhadkan - sab ko aage badha dena.

    Attributes:
        gravity: neeche ki kheench, pixels per second squared.
        bounce: har takraav par kitni raftaar wapas, 0.0 se 1.0 tak.
        floor, ceiling, left_wall, right_wall: kinare, radius ke hisaab se.
        attractor_radius, attractor_strength: kheench ka daayra aur zor.
        explosion_radius, explosion_strength: dhamake ka daayra aur zor.
        gravitational_constant, softening: kuon ka zor aur narm markaz.
        collision_iterations: takraav ke kitne pass har qadam.
        candidates, overlaps: pichhle qadam ka hisaab - kitne jore mumkin
            the, aur kitne waqai takraye.
        world_gravity, boundaries, collisions: teen switch.

    Poore jama ka hisaab ek hi jagah hota hai:

        duniya ki kheench + bahar ki taqatain + kuon ka field

    Gravity hamesha rehti hai; bahar ki taqatain har qadam par taza di
    jaati hain (``attract`` / ``clear_forces``); aur kuan duniya mein tike
    rehte hain - har qadam apna hissa khud dete hain.
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
        gravitational_constant: float = GRAVITATIONAL_CONSTANT,
        softening: float = WELL_SOFTENING,
        wells: GravityWells | None = None,
        spatial: SpatialHash | None = None,
        collision_iterations: int = COLLISION_ITERATIONS,
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
        # Kuon ka field - softening ke saath, warna markaz par qayamat.
        self.gravitational_constant = float(gravitational_constant)
        self.softening = float(softening)
        self._wells = wells
        # Padosiyon ka naqsha - takraav isi se dhoonde jaate hain.
        self._spatial = spatial if spatial is not None else SpatialHash()
        self.collision_iterations = int(collision_iterations)
        self.previous_share = float(COLLISION_PREVIOUS_SHARE)
        self.candidates = 0
        self.overlaps = 0
        # Teen switch: duniya ki kheench, deewarein, aur takraav.
        self.world_gravity = True
        self.boundaries = True
        self.collisions = True
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

    def toggle_world_gravity(self) -> bool:
        """Duniya ki kheench on/off - naya haal lautaata hai.

        Band karne se sirf yeh switch badalta hai; gravity khud jaisi thi
        waisi hi rehti hai - wapas on karte hi utni hi zor se kheenchti hai.
        """
        self.world_gravity = not self.world_gravity
        return self.world_gravity

    def toggle_boundaries(self) -> bool:
        """Deewarein on/off - naya haal lautaata hai.

        Band hone par koi takraav nahi - particle khuli fiza mein nikal jata
        hai. Wapas on karte hi bahar wale bhi seedhe ho jaate hain.
        """
        self.boundaries = not self.boundaries
        return self.boundaries

    def toggle_collisions(self) -> bool:
        """Takraav on/off - naya haal lautaata hai.

        Band hone par particles bhoot ban jaate hain: ek doosre ke aar paar
        nikal jaate hain. Kuch tajrube isi liye chhue hue chaahiye hote hain.
        """
        self.collisions = not self.collisions
        return self.collisions

    def bind_wells(self, wells: GravityWells | None) -> None:
        """Kuan ka state yahan aata hai - hisaab phir bhi physics ka."""
        self._wells = wells

    def bind_spatial(self, spatial: SpatialHash | None) -> None:
        """Naqsha yahan aata hai - lekin hisaab phir bhi physics ka."""
        self._spatial = spatial if spatial is not None else SpatialHash()

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

        1. Pehle farq (current - previous) scratch mein - yani raftaar.
        2. Phir acceleration purani jagah par naapo. Yeh qadam se pehle
           zaroori hai: kuan ka field jagah ke saath badalta hai, aur Verlet
           ko wohi force chahiye jo purani jagah par tha. Baad mein naapa
           to har orbit dheere dheere apni energy kho deti hai.
        3. Phir history likho, current ko aage badhao, aur deewaron se takrao.

        Acceleration teen jagah se aati hai, aur teenon ek hi jama mein:

            duniya ki kheench + bahar ki taqatain + kuon ka field

        Duniya ki kheench switch se band ho sakti hai; bahar ki taqatain sirf
        tab ginti hain jab koi chal rahi ho; aur kuan hamesha. ``count`` se
        aage wale khane kabhi chhue nahi jaate.
        """
        count = particles.count
        if count == 0:
            return

        current = particles.active_positions
        previous = particles.active_previous_positions

        displacement = self._displacement_scratch(particles.capacity)[:count]
        np.subtract(current, previous, out=displacement)

        wells = self._wells
        has_wells = wells is not None and wells.count > 0
        acceleration = None
        if self.world_gravity or self._forces or has_wells:
            acceleration = self._external_acceleration(count)
            if has_wells:
                self._add_well_acceleration(current, acceleration, count)
            if self.world_gravity:
                np.add(acceleration, self._acceleration, out=acceleration)

        # History: qadam se pehle kahan tha.
        np.copyto(previous, current)

        current += displacement
        if acceleration is not None:
            np.multiply(acceleration, dt * dt, out=acceleration)
            current += acceleration

        if self.collisions:
            self._resolve_collisions(current, previous)

        # Deewarein sabse aakhir mein. Takraav ki correction kisi ko deewar se
        # bahar chhod sakti hai, aur aakhri lafz deewar ka hi hota hai.
        if self.boundaries:
            self._apply_boundaries(current, previous)

    # ------------------------------------------------------------------
    # Takraav
    # ------------------------------------------------------------------
    def _resolve_collisions(
        self,
        current: NDArray[np.float32],
        previous: NDArray[np.float32],
    ) -> None:
        """Takarao - jore NumPy ke saath, particles par koi loop nahi.

        Naqsha har qadam dobara banta hai, kyunki jagah badalti rehti hai.
        Phir wohi jore ``collision_iterations`` baar chhaane jaate hain:
        pehle pass ke baad nayi takraav khul jati hai, doosra usay bhi
        sehta hai.

        Sudhaar ka bara hissa ``current`` par, aur ``COLLISION_PREVIOUS_SHARE``
        jitna ``previous`` par bhi. Poora hissa dene se jore ki raftaar
        badalti hi nahi aur dher mein hamesha ke liye halchal reh jati hai;
        kuch hissa dene se takraav khud raftaar kha jati hai - dher bas jata
        hai. Uchhal ka koi model nahi: sirf jagah ka sudhaar.
        """
        hasher = self._spatial
        hasher.rebuild(current)
        pairs_i, pairs_j = hasher.candidate_pairs()
        self.candidates = int(pairs_i.size)
        self.overlaps = 0
        if pairs_i.size == 0:
            return

        minimum = 2.0 * PARTICLE_RADIUS
        # Itni chhoti kami ko chhod diya jata hai - warna solver hamesha
        # "kuch bacha hai" kehta rehta aur har pass poora chalta rehta.
        touch_sq = (minimum - COLLISION_SLOP) ** 2
        # Agle pass ke liye itne paas wale jore hi rakhe jaate hain.
        near_sq = (minimum + COLLISION_CONTACT_MARGIN) ** 2
        size = int(current.shape[0])
        x = current[:, 0]
        y = current[:, 1]

        for iteration in range(self.collision_iterations):
            dx = x[pairs_j] - x[pairs_i]
            dy = y[pairs_j] - y[pairs_i]
            dist_sq = dx * dx + dy * dy

            hit = dist_sq < touch_sq
            count = int(hit.sum())
            if iteration == 0:
                # Pehla pass hi asli takraav hai; baad ke pass usi bhid ko
                # suljhate hain, isliye unhe ginti mein nahi jodte.
                self.overlaps = count
            if count == 0:
                break

            ii = pairs_i[hit]
            jj = pairs_j[hit]
            delta_x = dx[hit]
            delta_y = dy[hit]
            dist = np.sqrt(dist_sq[hit])
            penetration = minimum - dist

            # Ek hi jagah baithe do particles: delta zero hai, isliye simt
            # indices se banti hai - deterministic, aur zero se taqseem
            # ka sawal hi paida nahi hota.
            same_spot = dist < COLLISION_DEGENERATE_DISTANCE
            if same_spot.any():
                angle = _fallback_angle(ii, jj)
                delta_x = np.where(same_spot, np.cos(angle), delta_x)
                delta_y = np.where(same_spot, np.sin(angle), delta_y)
                dist = np.where(same_spot, 1.0, dist)
                penetration = np.where(same_spot, minimum, penetration)

            # Har particle ko aadha dhakka - barabar wazn, barabar hissa.
            factor = penetration / (2.0 * dist)

            # ``previous`` ko bhi itna hi hissa milta hai, magar poora nahi -
            # bacha hua hissa raftaar mein badal jata hai. Isi se dher apni
            # falls ki raftaar kholta hai aur tham jata hai. Poora hissa
            # (share 1.0) dene par kuch bhi thamta nahi, aur zero par jore
            # uchhalne lagte hain - dono naapon se dekhe gaye.
            share = self.previous_share
            push_x = delta_x * factor
            push_y = delta_y * factor
            keep_x = delta_x * factor * share
            keep_y = delta_y * factor * share

            # Ek particle ke kai jore ho sakte hain - bincount sab jama kar
            # leta hai (unbuffered add ki tarah, magar tez). Dono taraf ka
            # hisaab ek hi call mein: indices jod kar, dhakka ulta karke.
            both = np.concatenate((ii, jj))
            fix_x = np.bincount(both, weights=np.concatenate((-push_x, push_x)), minlength=size)
            fix_y = np.bincount(both, weights=np.concatenate((-push_y, push_y)), minlength=size)

            x += fix_x
            y += fix_y
            previous[:, 0] += np.bincount(both, weights=np.concatenate((-keep_x, keep_x)), minlength=size)
            previous[:, 1] += np.bincount(both, weights=np.concatenate((-keep_y, keep_y)), minlength=size)

            if iteration + 1 < self.collision_iterations:
                # Jore jo ab bahut door hain, agle pass mein bhi nahi mil
                # sakte - unhe fehrist se hata do. Sirf do index wali arrays
                # saaf hoti hain, aur doori agle pass mein phir naapi jaati
                # hai. Yeh saaf-safai pass ke aakhir mein hoti hai, warna
                # usi pass ke mask purani lambai ke reh jaate hain.
                keep = dist_sq < near_sq
                if not keep.all():
                    pairs_i = pairs_i[keep]
                    pairs_j = pairs_j[keep]
                    if pairs_i.size == 0:
                        break

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

    def _add_well_acceleration(
        self,
        current: NDArray[np.float32],
        acceleration: NDArray[np.float32],
        count: int,
    ) -> None:
        """Har kuan apna hissa isi buffer mein jama karta hai.

        Loop kuon par hai - chand hi hote hain. Particles par loop bilkul
        nahi: har kuan ke liye poora dhunda ek hi NumPy amal mein hilta hai.

        Kheench ulti-square hai, magar softening ke saath:

            a = G * M * delta / (delta^2 + s^2)^(3/2)

        Markaz par ``delta`` khud zero ho jaata hai, aur denominator kabhi
        zero nahi hota - isliye na NaN, na bekaar ki raftaar.
        """
        wells = self._wells
        if wells is None or wells.count == 0:
            return

        delta = self._scratch("_delta", (count, 2))
        dist_sq = self._scratch("_dist_sq", (count,))
        soft_sq = self.softening * self.softening
        positions = wells.active_positions
        masses = wells.active_masses

        for i in range(wells.count):
            # delta = kuan - particle, yani kheench ki simt seedhi.
            np.subtract((float(positions[i, 0]), float(positions[i, 1])), current, out=delta)
            np.einsum("ij,ij->i", delta, delta, out=dist_sq)
            dist_sq += soft_sq
            # (r^2)^-1.5 = 1/r^3 - isliye delta/r^3 poori kheench ban jaati hai.
            # Base kabhi zero nahi (softening > 0), isliye koi NaN nahi.
            np.power(dist_sq, -1.5, out=dist_sq)
            np.multiply(dist_sq, self.gravitational_constant * float(masses[i]), out=dist_sq)
            np.multiply(delta, dist_sq[:, None], out=delta)
            np.add(acceleration, delta, out=acceleration)

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