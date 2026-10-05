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
# Spawn area ka radius (particle ke radius se alag baat hai).
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

# ---------------------------------------------------------------------------
# Tools - haath mein kya hai
# ---------------------------------------------------------------------------
# Brush se banate hain, attractor se kheenchte hain, explosion se udaate hain.

# ---------------------------------------------------------------------------
# Attractor - jo paas bulaata hai
# ---------------------------------------------------------------------------
# Kitni door tak haath pahunchta hai.
ATTRACTOR_RADIUS = 240.0
# Kheench (pixels per second squared): markaz par sabse tez, kinare par zero.
ATTRACTOR_STRENGTH = 2600.0
ATTRACTOR_PREVIEW_COLOR = (150, 120, 230)   # halka banafshi

# ---------------------------------------------------------------------------
# Explosion - ek dhamaka, ek hi baar
# ---------------------------------------------------------------------------
EXPLOSION_RADIUS = 280.0
# Dhakke ki raftaar (pixels per second): markaz par sabse tez, kinare par zero.
# Yeh taqat nahi, raftaar hai - chhota sa jhatka, isliye waqt se nahi badalta.
EXPLOSION_STRENGTH = 3200.0
EXPLOSION_PREVIEW_COLOR = (235, 140, 90)    # halka naarangi
# Flash kitni der zinda rahe - ek jhapki, bas.
EXPLOSION_FLASH_SECONDS = 0.22
EXPLOSION_FLASH_COLOR = (255, 225, 185)     # pal bhar ka ujala

# ---------------------------------------------------------------------------
# HUD ke aakhri do rang - tool ke naam ke liye
# ---------------------------------------------------------------------------
HUD_TOOL_COLOR = (215, 205, 245)          # halka neela-banafshi
HUD_HELP_COLOR = (95, 115, 140)           # dheema, bas ishara