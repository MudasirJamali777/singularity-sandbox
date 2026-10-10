"""Singularity Sandbox - chhoti shuruaat."""

import pygame

from sandbox.config import (
    BACKGROUND_COLOR,
    FPS,
    MATTER,
    WATER,
    MAX_FRAME_SECONDS,
    MAX_STEPS_PER_FRAME,
    PARTICLES_PER_STROKE,
    PHYSICS_DT,
    WELL_PREVIEW_RADIUS,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from sandbox.gravity import GravityWells
from sandbox.input import Brush, Tool, ToolState
from sandbox.particles import ParticleSystem
from sandbox.physics import PhysicsSystem
from sandbox.renderer import Renderer
from sandbox.spatial import SpatialHash

# Keyboard ka kaam - 1, 2, 3, 4. Baaki saara tool ka hisaab input.py mein.
TOOL_KEYS: dict[int, Tool] = {
    pygame.K_1: Tool.BRUSH,
    pygame.K_2: Tool.ATTRACTOR,
    pygame.K_3: Tool.EXPLOSION,
    pygame.K_4: Tool.WELL,
}


def main() -> None:
    """Pygame jagaao, khirki kholo, loop chalao."""
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # Chhe saathi - yaadein, kuan, roshni, kheench, brush, aur naqsha.
    particles = ParticleSystem()
    wells = GravityWells()
    renderer = Renderer()
    # Ek hi naqsha - physics isse takraav dhoondhti hai, aur F1 wala debug
    # overlay usi ko dikhata hai. Do naqshe rakhna do jagah sach rakhta.
    spatial = SpatialHash()
    physics = PhysicsSystem(wells=wells, spatial=spatial)
    brush = Brush()
    tools = ToolState(Tool.BRUSH, brush)
    # F1: spatial grid; F2: WATER density colors.
    debug_grid = False
    density_debug = False

    # Bacha hua waqt - jab tak ek qadam ka na ho jaye.
    accumulator = 0.0
    # Guzra hua waqt - dhamake ki jhalak isi se ginti hai.
    elapsed = 0.0
    paused = False
    # Mouse daba hua ho to yahan uska pata, warna kuch nahi.
    attractor: tuple[float, float] | None = None

    def paint(centers: list[tuple[float, float]] | None) -> None:
        """Har nishaan par brush bhar do - particles ka kaam ParticleSystem ka."""
        if not centers:
            return
        for cx, cy in centers:
            particles.spawn_disk(
                cx,
                cy,
                brush.radius,
                PARTICLES_PER_STROKE,
                material=brush.material,
            )

    def preview_radius() -> float:
        """Chune hue auzaar ka hala - asar kahan tak pahunchega."""
        if tools.selected is Tool.BRUSH:
            return float(brush.radius)
        if tools.selected is Tool.ATTRACTOR:
            return physics.attractor_radius
        if tools.selected is Tool.WELL:
            return WELL_PREVIEW_RADIUS
        return physics.explosion_radius

    running = True
    while running:
        # Pehle waqt naapo: tick() frame ko seemit karta hai. Ek frame ka
        # waqt hadd se zyada nahi gina jata - window hilane ya system ke
        # rukne ke baad ek jhatke mein hazaar qadam nahi chalne chahiye.
        dt = min(clock.tick(FPS) / 1000.0, MAX_FRAME_SECONDS)
        elapsed += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # Samaan wahi rahe - bas waqt ruk jaye. Toggle par bacha hua
                # waqt bhi saaf, warna unpause par chhota sa jhatka aata.
                paused = not paused
                accumulator = 0.0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # Sab kuch gayab - particles, kuan, jhalak, aur waqt ka hisaab.
                particles.clear()
                wells.clear()
                physics.reset_collision_stats()
                physics.sph_system.reset_diagnostics()
                spatial.clear()
                accumulator = 0.0
                brush.lift()
                renderer.clear_flashes()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                # Duniya ki kheench on/off - off par sirf kuan bache.
                physics.toggle_world_gravity()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                # Deewarein on/off - off par khuli fiza, koi takraav nahi.
                physics.toggle_boundaries()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                # Takraav on/off - off par particles bhoot ban jate hain aur
                # ek doosre ke aar paar nikal jate hain.
                physics.toggle_collisions()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                # Debug grid: sirf nazar ka kaam, hisaab par koi asar nahi.
                debug_grid = not debug_grid
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                density_debug = not density_debug
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_5:
                # WATER brush, while retaining attractor/explosion/well tools.
                tools.select(Tool.BRUSH, brush)
                brush.select_material(WATER)
                attractor = None
            elif event.type == pygame.KEYDOWN and event.key in TOOL_KEYS:
                # Auzaar badla to purana haath khol do - kheench turant ruk jaye.
                if tools.select(TOOL_KEYS[event.key], brush):
                    attractor = None
                if event.key == pygame.K_1:
                    brush.select_material(MATTER)
            elif event.type == pygame.MOUSEWHEEL:
                # Sirf brush mode mein asar - baaki auzaaron mein nav band hai.
                brush.resize(event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if tools.selected is Tool.BRUSH:
                    # Nayi lakeer - purane nishaan se rishta nahi.
                    brush.lift()
                    paint(brush.centers_to(event.pos))
                elif tools.selected is Tool.ATTRACTOR:
                    attractor = event.pos
                elif tools.selected is Tool.EXPLOSION:
                    # Ek click = ek dhamaka. Dabaye rakhne se bar bar nahi.
                    physics.explode(particles, event.pos)
                    renderer.add_flash(event.pos, elapsed)
                elif tools.selected is Tool.WELL:
                    # Ek click = ek kuan, jo wahin tika rehta hai.
                    wells.add(event.pos[0], event.pos[1])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Haath chhod diya - lakeer tamam, kheench khatam.
                brush.lift()
                attractor = None
            elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                if tools.selected is Tool.BRUSH:
                    # Drag = yaadon ki lakeer (beech ke nishaan bhi).
                    paint(brush.centers_to(event.pos))
                elif tools.selected is Tool.ATTRACTOR:
                    attractor = event.pos

        # Kheench: sirf jab mouse daba ho. Ruke waqt mein kuch nahi khinchta.
        if attractor is not None and not paused:
            physics.attract(particles, attractor)
        else:
            physics.clear_forces()

        # Jo waqt aaya, jama karo - phir barabar hisson mein kharch.
        # Ruke hue waqt mein kuch jama nahi hota, warna chhutte par toofan aata.
        if not paused:
            accumulator += dt
            steps = 0
            while accumulator >= PHYSICS_DT and steps < MAX_STEPS_PER_FRAME:
                physics.step(particles, PHYSICS_DT)
                accumulator -= PHYSICS_DT
                steps += 1
            if steps == MAX_STEPS_PER_FRAME:
                # Physics waqt ke saath nahi chal sakti - bacha hua waqt
                # chhod do. Sim dheemi chalegi, magar frame atkega nahi.
                accumulator = 0.0

        # Pehle saaf, phir naqsha, phir particles, phir kuan, phir jhalak,
        # phir nishaan, phir khabar. Kuan particles ke upar - gehre markaz
        # doob na jayein.
        screen.fill(BACKGROUND_COLOR)
        # SPH/collision passes may leave a material subset in the shared hash;
        # the debug overlay always shows every active particle.
        if debug_grid:
            spatial.rebuild(particles.active_positions)
        renderer.draw_particles(
            screen,
            particles,
            density=physics.sph_system.density,
            density_debug=density_debug,
        )
        if debug_grid:
            # Khane particles ke upar - patla kinara bhi, warna dhera khud
            # unhe dhaanp deta hai.
            renderer.draw_debug_grid(screen, spatial)
        renderer.draw_wells(screen, wells)
        renderer.draw_flashes(screen, elapsed, physics.explosion_radius)

        mouse = pygame.mouse.get_pos()
        if pygame.mouse.get_focused() and 0 <= mouse[0] < WINDOW_WIDTH and 0 <= mouse[1] < WINDOW_HEIGHT:
            renderer.draw_preview(screen, tools.selected, preview_radius(), mouse)

        tool_label = tools.label
        if tools.selected is Tool.BRUSH:
            tool_label = "WATER BRUSH" if brush.material == WATER else "MATTER BRUSH"
        renderer.draw_hud(
            screen,
            clock.get_fps(),
            particles.count,
            particles.capacity,
            tool_label,
            paused,
            wells.count,
            wells.capacity,
            physics.world_gravity,
            physics.boundaries,
            physics.collisions,
            debug_grid,
            water_count=physics.sph_system.water_count,
            average_water_density=physics.sph_system.average_density,
            sph_density_debug=density_debug,
        )
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()