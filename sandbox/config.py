"""Central configuration constants for Singularity Sandbox.

Every tunable value lives here so behaviour can be changed in one place
instead of being scattered through the code as literals.
"""

# ---------------------------------------------------------------------------
# Window
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
# Colors (R, G, B)
# ---------------------------------------------------------------------------
BACKGROUND_COLOR = (8, 10, 18)
PARTICLE_COLOR = (120, 220, 255)

# ---------------------------------------------------------------------------
# Particles
# ---------------------------------------------------------------------------
MAX_PARTICLES = 10_000
PARTICLE_RADIUS = 3