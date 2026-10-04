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
PARTICLE_COLOR = (120, 220, 255)    # chaand

# ---------------------------------------------------------------------------
# Particles - chhoti yaadein
# ---------------------------------------------------------------------------
MAX_PARTICLES = 10_000
PARTICLE_RADIUS = 3

# ---------------------------------------------------------------------------
# Physics - jo neeche kheenchta hai
# ---------------------------------------------------------------------------
# y neeche jaata hai, isliye positive = giri. Sikka bhi girta hai.
GRAVITY = 1000.0

# Ek second / 120 qadam. Fixed rehta hai, FPS se nahi badalta.
PHYSICS_DT = 1.0 / 120.0