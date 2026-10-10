"""Dil ki saari settings - ek jagah, saaf saaf."""

# ---------------------------------------------------------------------------
# Window - jahan khwab khulega
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Singularity Sandbox"
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------
FPS = 60

# ---------------------------------------------------------------------------
# Colors - dil ke rang
# ---------------------------------------------------------------------------
BACKGROUND_COLOR = (8, 10, 18)      # raat
PARTICLE_COLOR = (120, 220, 255)    # matter - chaand
WATER_COLOR = (35, 125, 235)        # paani - gehra neela

# ---------------------------------------------------------------------------
# Particles - chhoti yaadein
# ---------------------------------------------------------------------------
MAX_PARTICLES = 10_000
PARTICLE_RADIUS = 3
MATTER = 0
WATER = 1

# ---------------------------------------------------------------------------
# Neighbor search and particle collisions
# ---------------------------------------------------------------------------
# A diameter-sized cell means ordinary collisions need only a 3x3 neighborhood.
CELL_SIZE = PARTICLE_RADIUS * 2
COLLISION_ITERATIONS = 3
# Preserve the legacy Matter collision default; press C to toggle it in-app.
COLLISIONS_ENABLED = True
COLLISION_DISTANCE_EPSILON_SQUARED = 1e-12

# ---------------------------------------------------------------------------
# SPH water prototype (2D, screen pixels)
# ---------------------------------------------------------------------------
SPH_H = 18.0
SPH_MASS = 1.0
# Approximate number density of a settled 5 px-spaced 2D particle layer.
SPH_REST_DENSITY = 0.04
SPH_GAS_CONSTANT = 50_000.0
SPH_VISCOSITY = 3_000.0
SPH_DENSITY_EPSILON = 1e-6
# Water should settle against walls rather than bounce like separate marbles.
SPH_WALL_BOUNCE = 0.0

# ---------------------------------------------------------------------------
# Legacy sandbox tools, world controls, and UI
# ---------------------------------------------------------------------------
MAX_FRAME_SECONDS = 0.25
MAX_STEPS_PER_FRAME = 8
MAX_WELLS = 32
MAX_CANDIDATE_PAIRS_PER_CELL = 100_000

ATTRACTOR_RADIUS = 180.0
ATTRACTOR_STRENGTH = 1_500.0
EXPLOSION_RADIUS = 130.0
EXPLOSION_STRENGTH = 8_000.0
GRAVITATIONAL_CONSTANT = 50.0
WELL_MASS = 1_000.0
WELL_SOFTENING = 20.0

COLLISION_SLOP = 0.02
COLLISION_CONTACT_MARGIN = 2.0
COLLISION_DEGENERATE_DISTANCE = 1e-6
COLLISION_PREVIOUS_SHARE = 0.75

ATTRACTOR_PREVIEW_COLOR = (80, 180, 255)
EXPLOSION_PREVIEW_COLOR = (255, 100, 75)
WELL_PREVIEW_COLOR = (205, 100, 255)
WELL_PREVIEW_RADIUS = 24.0
EXPLOSION_FLASH_COLOR = (255, 150, 60)
EXPLOSION_FLASH_SECONDS = 0.32

DEBUG_CELL_COLORS = (
    (50, 90, 150),
    (55, 150, 200),
    (230, 180, 60),
    (245, 75, 60),
)
DEBUG_CELL_ALPHA = (28, 40, 55, 75)
HUD_OFF_COLOR = (105, 115, 130)
HUD_HELP_COLOR = (110, 135, 160)
HUD_TOOL_COLOR = (140, 210, 160)

WELL_CORE_COLOR = (9, 8, 18)
WELL_CORE_RADIUS = 8
WELL_DOT_COLOR = (255, 225, 255)
WELL_DOT_RADIUS = 2
WELL_FIELD_COLOR = (140, 70, 190)
WELL_FIELD_SCALE = 2.2
WELL_RING_COLOR = (205, 105, 245)
WELL_VISUAL_RADIUS = 12

# ---------------------------------------------------------------------------
# Physics - jo neeche kheenchta hai
# ---------------------------------------------------------------------------
# y neeche jaata hai, isliye positive = giri. Sikka bhi girta hai.
GRAVITY = 1000.0

# Farsh se takra kar kitni raftaar wapas - 0.0 kuch nahi, 1.0 poori.
BOUNCE = 0.7

# Ek second / 120 qadam. Fixed rehta hai, FPS se nahi badalta.
PHYSICS_DT = 1.0 / 120.0

# ---------------------------------------------------------------------------
# HUD - chhoti si khabar, screen ke kone mein
# ---------------------------------------------------------------------------
HUD_COLOR = (150, 175, 200)         # halka sa neela-grey
HUD_PAUSED_COLOR = (255, 190, 120)  # thama hua waqt - garam rang
HUD_ACTIVE_COLOR = (140, 210, 160)  # chalte hue waqt - halka sabz
HUD_FONT_SIZE = 18
HUD_MARGIN = 10
HUD_LINE_GAP = 4

# ---------------------------------------------------------------------------
# Brush - haath se banayi hui yaadein
# ---------------------------------------------------------------------------
# Spawn area ka radius (particle ke radius se alag baat).
BRUSH_RADIUS = 18
BRUSH_MIN_RADIUS = 1
BRUSH_MAX_RADIUS = 100
# Wheel ke ek dhakke par kitne pixels.
BRUSH_WHEEL_STEP = 2
# Har brush center par kitni yaadein.
PARTICLES_PER_STROKE = 6
# Centers ki doori = radius * yeh. Aadha radius = thehra hua, bhara hua rang.
BRUSH_SPACING = 0.5
# Ek event par centers ki hadd - tez jhatke par particle ki barish na ho.
BRUSH_MAX_SAMPLES = 64
BRUSH_PREVIEW_COLOR = (90, 135, 180)    # halka neela outline