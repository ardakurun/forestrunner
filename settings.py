"""
settings.py - every tunable value of Forest Runner lives here.

Units used throughout the game:
  * positions/sizes : "game pixels". The game is drawn on a small canvas
                      (GAME_WIDTH x GAME_HEIGHT) that is scaled up to the window,
                      which gives the crisp pixel-art look.
  * time            : seconds
  * speeds          : game pixels per second
  * accelerations   : game pixels per second squared
"""
import os

import pygame

# ---------------------------------------------------------------------------
# Paths (built from this file's folder, so the game works from any directory)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PLAYER_ASSETS_DIR = os.path.join(ASSETS_DIR, "player")
OBSTACLE_ASSETS_DIR = os.path.join(ASSETS_DIR, "obstacles")
BACKGROUND_ASSETS_DIR = os.path.join(ASSETS_DIR, "background")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
DATA_DIR = os.path.join(BASE_DIR, "data")
HIGHSCORE_FILE = os.path.join(DATA_DIR, "highscore.json")

# ---------------------------------------------------------------------------
# Window and rendering
# ---------------------------------------------------------------------------
TITLE = "Forest Runner"
GAME_WIDTH = 480            # internal canvas size (everything is drawn here)
GAME_HEIGHT = 270
WINDOW_SCALE = 0            # 0 = automatic: the biggest whole-number scale that fits your screen.
                            # Or pick one: 2 -> 960 x 540, 3 -> 1440 x 810, 4 -> 1920 x 1080.
FPS = 60
MAX_DT = 1 / 30             # clamp long frames so nothing can skip through obstacles

GROUND_Y = 222              # y position of the ground surface (the player's feet line)

# ---------------------------------------------------------------------------
# Controls (tuples, so several keys can do the same thing)
# ---------------------------------------------------------------------------
JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
SLIDE_KEYS = (pygame.K_DOWN, pygame.K_s)
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
BACK_KEYS = (pygame.K_ESCAPE, pygame.K_BACKSPACE)
MENU_UP_KEYS = (pygame.K_UP, pygame.K_w)
MENU_DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)

# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
PLAYER_X = 72                       # the player's fixed x position on screen (center)
PLAYER_FRAME_SIZE = (32, 32)        # size of one animation frame (also for sprite sheets)
PLAYER_HITBOX_STAND = (12, 24)      # collision box (width, height) while standing / jumping
PLAYER_HITBOX_SLIDE = (20, 11)      # collision box while sliding

GRAVITY = 1150
FALL_GRAVITY_MULTIPLIER = 1.35      # fall a bit faster than you rise -> snappier jumps
JUMP_VELOCITY = 340
DOUBLE_JUMP_VELOCITY = 300
MAX_JUMPS = 2                       # ground jump + one air jump
MAX_FALL_SPEED = 520

VARIABLE_JUMP_HEIGHT = True         # release SPACE early for a shorter hop
JUMP_CUT_MULTIPLIER = 0.5           # upward speed is multiplied by this on early release
JUMP_CUT_MIN_TIME = 0.08            # a jump always rises at least this long (taps stay useful)

COYOTE_TIME = 0.10                  # you can still ground-jump this long after leaving the ground
JUMP_BUFFER_TIME = 0.12             # a jump pressed this early before landing still happens

SLIDE_DURATION = 0.50               # a tap slides this long; holding the key keeps sliding
FAST_FALL_ENABLED = True            # pressing slide in the air drops you down quickly
FAST_FALL_GRAVITY_MULTIPLIER = 3.0
FAST_FALL_MIN_SPEED = 220

SQUASH_STRETCH = True               # stretch on jump, squash on landing
SQUASH_RECOVERY_SPEED = 12          # how quickly the squash/stretch returns to normal

HURT_BOUNCE_VELOCITY = 230          # little hop when the player gets hit
HURT_KNOCKBACK_SPEED = 55

# state name: (frames per second, loops?)
PLAYER_ANIMATIONS = {
    "idle": (5, True),
    "run": (14, True),
    "jump": (10, False),
    "double_jump": (20, False),
    "fall": (8, True),
    "slide": (12, True),
    "hurt": (8, False),
}

# ---------------------------------------------------------------------------
# World speed and difficulty
# ---------------------------------------------------------------------------
START_SPEED = 210
MAX_SPEED = 520
START_ACCELERATION = 600            # used to get from standing still to START_SPEED
DIFFICULTY_TIME_CONSTANT = 100      # difficulty = 1 - e^(-seconds / this): smooth, never sudden

# ---------------------------------------------------------------------------
# Obstacles
# ---------------------------------------------------------------------------
# Every obstacle type. "art" picks the images (assets/obstacles/<art>.png, or a
# placeholder). The hitbox is centered on the sprite and is a little smaller
# than the drawing so near misses feel fair.
#   altitude     : height of the hitbox bottom above the ground (0 = on the ground)
#   extra_speed  : moves this much faster than the ground (flying things)
#   bob          : vertical wobble in pixels (flying things)
#   recover_time : seconds the player needs after this obstacle before the next one
#   debris       : particle colors used when the player crashes into it
OBSTACLE_TYPES = {
    "rock": {
        "art": "rock", "size": (16, 12), "hitbox": (12, 9),
        "altitude": 0, "extra_speed": 0, "bob": 0, "anim_fps": 0,
        "recover_time": 0.60,
        "debris": ((128, 128, 140), (172, 172, 184), (92, 150, 72)),
    },
    "stump": {
        "art": "stump", "size": (18, 22), "hitbox": (14, 19),
        "altitude": 0, "extra_speed": 0, "bob": 0, "anim_fps": 0,
        "recover_time": 0.62,
        "debris": ((122, 80, 50), (214, 170, 110), (92, 150, 72)),
    },
    "big_stump": {
        "art": "big_stump", "size": (26, 36), "hitbox": (22, 32),
        "altitude": 0, "extra_speed": 0, "bob": 0, "anim_fps": 0,
        "recover_time": 0.85,
        "debris": ((110, 72, 46), (214, 170, 110), (232, 128, 60)),
    },
    "bird_low": {
        "art": "bird", "size": (20, 14), "hitbox": (14, 8),
        "altitude": 16, "extra_speed": 40, "bob": 1.5, "anim_fps": 10,
        "recover_time": 0.42,
        "debris": ((52, 48, 72), (90, 86, 116), (240, 170, 60)),
    },
    "bird_high": {
        "art": "bird", "size": (20, 14), "hitbox": (14, 8),
        "altitude": 31, "extra_speed": 55, "bob": 1.5, "anim_fps": 10,
        "recover_time": 0.40,
        "debris": ((52, 48, 72), (90, 86, 116), (240, 170, 60)),
    },
}

# Hand-made obstacle patterns. The spawner picks one at a time.
#   min_difficulty : pattern is only used once difficulty (0..1) reaches this
#   weight         : how often it is picked compared to the others
#   items          : (obstacle type, delay) - delay is in SECONDS after the
#                    first obstacle reaches the player. Using time instead of
#                    pixels keeps every pattern fair at any speed.
OBSTACLE_PATTERNS = [
    {"name": "rock", "min_difficulty": 0.00, "weight": 4, "items": [("rock", 0.0)]},
    {"name": "stump", "min_difficulty": 0.00, "weight": 4, "items": [("stump", 0.0)]},
    {"name": "big stump", "min_difficulty": 0.06, "weight": 3, "items": [("big_stump", 0.0)]},
    {"name": "low bird", "min_difficulty": 0.10, "weight": 3, "items": [("bird_low", 0.0)]},
    {"name": "high bird", "min_difficulty": 0.18, "weight": 2, "items": [("bird_high", 0.0)]},
    {"name": "rock pair", "min_difficulty": 0.20, "weight": 2,
     "items": [("rock", 0.0), ("rock", 0.08)]},
    {"name": "stump and rock", "min_difficulty": 0.28, "weight": 2,
     "items": [("stump", 0.0), ("rock", 0.09)]},
    {"name": "two stumps", "min_difficulty": 0.32, "weight": 2,
     "items": [("stump", 0.0), ("stump", 0.70)]},
    {"name": "slide then jump", "min_difficulty": 0.40, "weight": 2,
     "items": [("bird_low", 0.0), ("stump", 0.55)]},
    {"name": "jump then slide", "min_difficulty": 0.45, "weight": 2,
     "items": [("rock", 0.0), ("bird_low", 0.60)]},
    {"name": "bird tunnel", "min_difficulty": 0.50, "weight": 2,
     "items": [("bird_low", 0.0), ("bird_low", 0.28)]},
    {"name": "wait for it", "min_difficulty": 0.55, "weight": 2,
     "items": [("bird_high", 0.0), ("stump", 0.40)]},
    {"name": "rock rhythm", "min_difficulty": 0.60, "weight": 2,
     "items": [("rock", 0.0), ("rock", 0.62), ("rock", 1.24)]},
    {"name": "big stump and stump", "min_difficulty": 0.70, "weight": 1,
     "items": [("big_stump", 0.0), ("stump", 0.85)]},
]

SPAWN_X = GAME_WIDTH + 24           # new obstacles appear just past the right edge
FIRST_SPAWN_DELAY = 1.4             # seconds of calm at the start of every run
MAX_OBSTACLES = 12                  # safety cap
REACTION_TIME_EASY = 0.55           # extra breathing room between patterns at difficulty 0...
REACTION_TIME_HARD = 0.22           # ...and at difficulty 1
EXTRA_GAP_EASY = 1.00               # random extra gap (0..this) at difficulty 0...
EXTRA_GAP_HARD = 0.35               # ...and at difficulty 1
HARD_PATTERN_BIAS = 1.5             # how strongly harder patterns are favored later on
PATTERN_REPEAT_LIMIT = 2            # never pick the same pattern more than this many times in a row

# ---------------------------------------------------------------------------
# Score
# ---------------------------------------------------------------------------
SCORE_PER_PIXEL = 0.1               # 10 game pixels travelled = 1 point
SCORE_DIGITS = 6
SCORE_MILESTONE = 1000              # the score flashes (and a sound plays) every N points
MILESTONE_FLASH_TIME = 1.0

# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------
MAX_PARTICLES = 300
SHAKE_MAX_OFFSET = 6                # pixels at full shake
SHAKE_DECAY = 1.6                   # shake "trauma" lost per second
SHAKE_ON_HIT = 0.75
SHAKE_ON_HARD_LANDING = 0.18
HIT_FLASH_TIME = 0.12
RUN_DUST_INTERVAL = 0.10            # seconds between dust puffs at START_SPEED (faster when faster)
SLIDE_DUST_INTERVAL = 0.04

DUST_COLORS = ((196, 170, 128), (168, 140, 100), (222, 204, 166))
SPARKLE_COLORS = ((255, 255, 255), (200, 240, 255), (255, 244, 180))

# Particle recipes. Add a new entry here to create a new effect.
#   count    : particles per burst
#   vx, vy   : random velocity range (pixels/second)
#   ring     : True -> particles fly out evenly in a circle at speed vx (min, max)
#   life     : random lifetime range (seconds)
#   size     : random start size range (pixels). Particles shrink as they age.
#   gravity  : downward acceleration
#   drag     : how quickly they slow down (0 = never)
PARTICLE_PRESETS = {
    "jump_dust": {"count": 6, "vx": (-60, 10), "vy": (-30, -5), "life": (0.25, 0.45),
                  "size": (2, 3), "gravity": 60, "drag": 3.0, "colors": DUST_COLORS},
    "land_dust": {"count": 10, "vx": (-80, 80), "vy": (-40, -5), "life": (0.25, 0.5),
                  "size": (2, 3), "gravity": 80, "drag": 3.5, "colors": DUST_COLORS},
    "run_dust": {"count": 1, "vx": (-70, -25), "vy": (-22, -4), "life": (0.18, 0.35),
                 "size": (1, 2), "gravity": 40, "drag": 2.0, "colors": DUST_COLORS},
    "slide_dust": {"count": 2, "vx": (-110, -40), "vy": (-35, -8), "life": (0.2, 0.4),
                   "size": (1, 3), "gravity": 70, "drag": 2.5, "colors": DUST_COLORS},
    "double_jump": {"count": 12, "ring": True, "vx": (55, 75), "vy": (0, 0), "life": (0.2, 0.32),
                    "size": (1, 2), "gravity": 0, "drag": 4.0, "colors": SPARKLE_COLORS},
    "hit": {"count": 24, "vx": (-150, 150), "vy": (-190, -30), "life": (0.45, 0.9),
            "size": (2, 4), "gravity": 420, "drag": 0.8, "colors": SPARKLE_COLORS},
    "milestone": {"count": 14, "vx": (-50, 50), "vy": (-60, -10), "life": (0.4, 0.7),
                  "size": (1, 2), "gravity": 30, "drag": 1.0,
                  "colors": ((255, 230, 120), (255, 255, 255), (250, 190, 80))},
}

# ---------------------------------------------------------------------------
# Background / atmosphere
# ---------------------------------------------------------------------------
# Drawn back to front. "factor" = scroll speed relative to the ground
# (0 = static, 1 = moves with the ground). "drift" = extra pixels/second
# (clouds keep drifting even in the menu). "front" layers are drawn in
# front of the player and obstacles. A PNG named assets/background/<name>.png
# replaces the placeholder for that layer.
BACKGROUND_LAYERS = [
    {"name": "sky", "factor": 0.0, "drift": 0, "front": False},
    {"name": "clouds", "factor": 0.03, "drift": 5, "front": False},
    {"name": "far_forest", "factor": 0.10, "drift": 0, "front": False},
    {"name": "mid_trees", "factor": 0.25, "drift": 0, "front": False},
    {"name": "light_rays", "factor": 0.0, "drift": 0, "front": False},
    {"name": "near_trees", "factor": 0.50, "drift": 0, "front": False},
    {"name": "bushes", "factor": 0.75, "drift": 0, "front": False},
    {"name": "ground", "factor": 1.0, "drift": 0, "front": False},
    {"name": "foreground_plants", "factor": 1.25, "drift": 0, "front": True},
    {"name": "canopy", "factor": 1.10, "drift": 0, "front": True},
]
LEAF_COUNT = 14                     # falling leaves floating through the scene

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
UI_TEXT = (244, 240, 224)
UI_SHADOW = (20, 26, 22)
UI_HIGHLIGHT = (255, 214, 102)
UI_MUTED = (170, 186, 160)
UI_DANGER = (236, 96, 72)
UI_TITLE = (214, 240, 128)
UI_TITLE_OUTLINE = (22, 52, 34)

FADE_TIME = 0.30                    # fade-in when switching between some screens
GAME_OVER_PANEL_DELAY = 0.55        # crash animation plays this long before the panel appears
GAME_OVER_INPUT_DELAY = 0.85        # ignore keys this long (so mashing SPACE doesn't skip it)
HINT_DURATION = 4.0                 # how long the controls hint shows at the start of a run

# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
SFX_VOLUME = 0.5
MUSIC_VOLUME = 0.45
USE_PLACEHOLDER_SOUNDS = True       # simple generated beeps until real sound files are added
AUDIO_EXTENSIONS = (".ogg", ".wav", ".mp3")
# The game looks for assets/music/<name>.ogg/.wav/.mp3 for these tracks.
MUSIC_TRACKS = {"menu": "menu", "game": "forest_theme"}
