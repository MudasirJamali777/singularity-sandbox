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
# Gravity wells - duniya mein tike hue kuan
# ---------------------------------------------------------------------------
# G * M. Bara = gehri kheench. (pixels^3 per second^2)
# r = 250 par saikron pixels/s^2 - yani duniya ki gravity jitna hi mehsoos ho.
GRAVITATIONAL_CONSTANT = 2.0e6
# Har kuan ka apna wazan - default itna.
WELL_MASS = 40.0
# Zyada nahi - gehre hi. 32 kuon tak sab theek chalta hai.
MAX_WELLS = 32
# Softening: r^2 + s^2. Yeh hi markaz ko dhamake se bachata hai.
# 24 px naap kar chuna gaya: 16 par core se guzarte hue particle har qadam
# mein ~35% extra raftaar bator leta hai (dt = 1/120 par core theek se
# resolve nahi hota), aur 24 par wohi guzarna 3% ke andar rehta hai -
# particle markaz se seedha nikal kar wapas aata hai, phans jata nahi.
# Door ka field itna hi rehta hai: a(r=250) sirf 0.4% badalta hai.
WELL_SOFTENING = 24.0

# Nazar ka libaas: andar kala dil, bahar banafshi ring, aur dheemi field.
WELL_VISUAL_RADIUS = 16
WELL_CORE_RADIUS = 9
WELL_DOT_RADIUS = 3
WELL_FIELD_SCALE = 2.4
# Tool chuna hua ho to cursor ke gird itna bara nishaan.
WELL_PREVIEW_RADIUS = 48.0
WELL_CORE_COLOR = (16, 10, 30)          # kala dil
WELL_RING_COLOR = (168, 112, 240)       # banafshi ring
WELL_FIELD_COLOR = (86, 58, 128)        # dheemi field
WELL_DOT_COLOR = (226, 206, 255)        # chamakta markaz
WELL_PREVIEW_COLOR = (228, 120, 210)    # halka gulabi-banafshi

# ---------------------------------------------------------------------------
# HUD ke aakhri rang
# ---------------------------------------------------------------------------
HUD_TOOL_COLOR = (215, 205, 245)          # halka neela-banafshi
HUD_HELP_COLOR = (95, 115, 140)           # dheema, bas ishara
HUD_OFF_COLOR = (232, 128, 128)           # kuch band hai - narm sa lal

# ---------------------------------------------------------------------------
# Loop ki hadd - qadam kabhi na barhe
# ---------------------------------------------------------------------------
# Ek frame mein itne se zyada qadam nahi. Agar physics waqt se peeche reh
# jaye (jaise 10,000 particles ka dher), to bacha hua waqt phenk diya jata
# hai - warna har frame ka waqt barhta hai, us se qadam aur barhte hain, aur
# frame pehle se dheema hota hai. Yeh death spiral asli mein naapa gaya:
# 30 ms/qadam par frame ka waqt har frame taqreeban 3.6 guna barh raha tha.
# Simulation dheemi chalti hai - rukti nahi. Qadam khud wahi fixed rehta hai.
MAX_STEPS_PER_FRAME = 8
# Ek frame ka waqt itna hi gina jata hai. Window hilane ya laptop band karne
# ke baad ek jhatke mein hazaar qadam nahi chalne chahiye.
MAX_FRAME_SECONDS = 0.25

# ---------------------------------------------------------------------------
# Spatial hash - padosiyon ka naqsha
# ---------------------------------------------------------------------------
# Khane ka naap = takraav ka diameter (2 * radius). Itna chhota khana: har
# khane mein ek do particle, aur padosi sirf ek khana door hota hai.
CELL_SIZE = 2.0 * PARTICLE_RADIUS

# Ek khane ke jore ki hadd. Sirf patle haadsay ke liye: agar kisi ne ek hi
# jagah hazaron particles jama kar diye to unke saare jore memory kha jate.
MAX_CANDIDATE_PAIRS_PER_CELL = 128

# ---------------------------------------------------------------------------
# Takraav - particles jo ek doosre ko dhakelte hain
# ---------------------------------------------------------------------------
# Kitne pass. Ek pass se poora bhid nahi khulta - ek jore ko hilane se
# doosra overlap paida ho jata hai. Naapon ke mutabiq: 2 se 4 tak har pass
# gehra paithan kam karta hai (2000 particles par 3 pass = 0.68 px, 4 pass
# = 0.62 px, 6 pass = 0.51 px), aur 4 ke baad fayda dheema ho jata hai.
COLLISION_ITERATIONS = 4
# Itni chhoti doori ko "ek hi jagah" maana jata hai (brush se aaye jore).
# Aise jore ki simt index se banti hai, delta se nahi - warna zero se taqseem.
COLLISION_DEGENERATE_DISTANCE = 1e-4
# Itni chhoti kami (pixels) chhod di jaati hai - solver kabhi "ho gaya"
# nahi kehta tha, aur har pass poora chalta rehta tha.
COLLISION_SLOP = 0.05
# Agle pass ke liye sirf itne paas wale jore rakhe jaate hain (pixels).
# Isse doosre aur teesre pass ka kaam aadha reh jata hai.
COLLISION_CONTACT_MARGIN = 2.0
# Sudhaar ka kitna hissa ``previous`` par bhi lagta hai (1.0 = poora).
#
# Yeh is batch ka sabse nazuk number hai, aur isay naap kar chuna gaya:
#
#   1.0  : correction current aur previous dono par barabar lagti hai, isliye
#          jore ki raftaar mein koi tabdeeli nahi hoti. Grid ke hisaab se
#          bilkul theek, magar falls ki raftaar kabhi khatam nahi hoti - 2000
#          particles ka dher ganton tak ubalta rehta hai aur particles ek
#          doosre mein dhas jate hain (nearest doori 3.95 px, diameter 6 px).
#   0.75 : 25% hissa raftaar ban jata hai - dher tham jata hai (v 29 px/s).
#   0.70 : 30% hissa - sabsay thehra aur sabse saaf dher (nn 5.2 px, v 21).
#   0.65 : is se neeche bhi thehra hai magar fayda chhota, aur jore ki raftaar
#          zyada badalti hai - "ridiculous artificial velocity" ka dar.
#
# Isliye 0.70: har takraav apni 30% raftaar kho deti hai, aur dher tham jata
# hai - kisi ko uchhalna nahi parta.
COLLISION_PREVIOUS_SHARE = 0.70

# ---------------------------------------------------------------------------
# Debug grid - F1 wala naqsha
# ---------------------------------------------------------------------------
# Bhare khane ka rang: khaali (nazar nahi aata), halka neela, gehra neela,
# peela, naarangi, lal. Jitne zyada particles, utna garam rang.
DEBUG_CELL_COLORS = ((40, 56, 82), (70, 120, 190), (200, 180, 70), (235, 130, 60), (240, 70, 60))
DEBUG_CELL_ALPHA = (60, 110, 150, 190, 230)