"""
placeholder_art.py - procedural pixel-art placeholders.

Everything here is drawn with simple shapes when the game starts, so the game
looks decent before any real art exists. As soon as a matching PNG is put in
the assets folder, the game uses that instead (see player.py, obstacle.py and
world.py). Nothing else in the game depends on how these images are made.
"""
import math
import random

import pygame

from settings import GAME_HEIGHT, GAME_WIDTH, GROUND_Y, PLAYER_FRAME_SIZE

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
OUTLINE = (32, 24, 38)
SKIN = (248, 208, 165)
HOOD = (206, 66, 58)
HOOD_LIGHT = (238, 112, 86)
HOOD_DARK = (150, 42, 46)
TUNIC = (240, 178, 72)
TUNIC_DARK = (196, 132, 48)
BELT = (96, 58, 36)
PANTS = (78, 70, 110)
PANTS_DARK = (54, 48, 80)
BOOTS = (104, 64, 42)
BOOTS_DARK = (72, 44, 32)
EYE = (30, 24, 36)

ROCK = (128, 128, 142)
ROCK_LIGHT = (172, 172, 186)
ROCK_DARK = (94, 94, 112)
MOSS = (92, 150, 72)
MOSS_LIGHT = (128, 182, 88)
BARK = (122, 80, 50)
BARK_DARK = (90, 58, 38)
BARK_LIGHT = (150, 102, 64)
WOOD = (214, 170, 110)
WOOD_RING = (178, 132, 84)
MUSHROOM = (232, 128, 60)
MUSHROOM_LIGHT = (250, 176, 96)
BIRD = (52, 48, 72)
BIRD_LIGHT = (84, 80, 112)
BEAK = (240, 170, 60)

COLORKEY = (255, 0, 255)  # "transparent" color for the big background layers


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def new_sprite(width, height):
    """A fully transparent surface to draw a sprite on."""
    return pygame.Surface((width, height), pygame.SRCALPHA)


def add_outline(surface, color=OUTLINE):
    """Return a copy of a sprite with a 1-pixel outline around its shape."""
    mask = pygame.mask.from_surface(surface)
    silhouette = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
    result = new_sprite(*surface.get_size())
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        result.blit(silhouette, (dx, dy))
    result.blit(surface, (0, 0))
    return result


def _point(origin, angle, length):
    """Point `length` away from origin. angle 0 = straight down, positive = forward."""
    return (origin[0] + math.sin(angle) * length, origin[1] + math.cos(angle) * length)


def _rounded(point):
    return (round(point[0]), round(point[1]))


def _thick_line(surface, color, points, width):
    """A chain of thick lines with square joints - looks like a pixel-art limb."""
    points = [_rounded(p) for p in points]
    for start, end in zip(points, points[1:]):
        pygame.draw.line(surface, color, start, end, width)
    half = width // 2
    for x, y in points:
        surface.fill(color, (x - half, y - half, width, width))


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
THIGH, SHIN, UPPER_ARM, FOREARM, TORSO = 5, 5, 4, 4, 8


def _draw_runner(surface, pose):
    """
    Draw the runner from a pose description:
      hip   : (x, y) position of the hips
      lean  : torso angle (0 = upright, positive = leaning forward)
      legs  : ((angle, knee_bend) back leg, (angle, knee_bend) front leg)
      arms  : ((angle, elbow_bend) back arm, (angle, elbow_bend) front arm)
      scarf : (flow, phase) flow 0 = hanging down, 1 = streaming behind
    """
    hip = pose["hip"]
    lean = pose["lean"]
    shoulder = _point(hip, math.pi - lean, TORSO - pose.get("breath", 0))
    neck = _point(shoulder, math.pi - lean, 2)
    head = _rounded(_point(shoulder, math.pi - lean, 5))

    def leg(angle, bend, color, boot_color):
        knee = _point(hip, angle, THIGH)
        ankle = _point(knee, angle - bend, SHIN)
        _thick_line(surface, color, [hip, knee, ankle], 3)
        ax, ay = _rounded(ankle)
        surface.fill(boot_color, (ax - 1, ay - 1, 4, 3))

    def arm(angle, bend, color):
        elbow = _point(shoulder, angle, UPPER_ARM)
        hand = _point(elbow, angle + bend, FOREARM)
        _thick_line(surface, color, [shoulder, elbow, hand], 2)
        hx, hy = _rounded(hand)
        surface.fill(SKIN, (hx - 1, hy - 1, 2, 2))

    # Scarf: a short wavy ribbon trailing from the neck.
    flow, phase = pose.get("scarf", (1.0, 0.0))
    points = [neck]
    for i in range(1, 4):
        last = points[-1]
        wave = math.sin(phase + i * 1.3) * (1.0 + 0.6 * i) * flow
        dx = -3.5 * flow - 0.4             # streams backwards when flow is high
        dy = 3.0 * (1 - flow) + 0.6 + wave  # hangs down when flow is low
        points.append((last[0] + dx, last[1] + dy))
    _thick_line(surface, HOOD_DARK, points, 2)

    (back_leg, front_leg), (back_arm, front_arm) = pose["legs"], pose["arms"]
    arm(*back_arm, HOOD_DARK)
    leg(*back_leg, PANTS_DARK, BOOTS_DARK)
    _thick_line(surface, TUNIC, [hip, shoulder], 6)
    tunic_shade = _point(hip, math.pi - lean, 2)
    _thick_line(surface, TUNIC_DARK, [hip, tunic_shade], 6)
    belt = _rounded(_point(hip, math.pi - lean, 2))
    surface.fill(BELT, (belt[0] - 3, belt[1], 6, 1))
    leg(*front_leg, PANTS, BOOTS)

    # Head: red hood with the face showing on the front side.
    pygame.draw.circle(surface, HOOD, head, 4)
    pygame.draw.circle(surface, SKIN, (head[0] + 1, head[1] + 1), 3)
    surface.fill(HOOD, (head[0] - 3, head[1] - 4, 7, 2))
    surface.fill(HOOD_LIGHT, (head[0] - 2, head[1] - 3, 3, 1))
    surface.fill(EYE, (head[0] + 2, head[1], 1, 2))

    arm(*front_arm, HOOD)


def _runner_frame(pose):
    surface = new_sprite(*PLAYER_FRAME_SIZE)
    _draw_runner(surface, pose)
    return add_outline(surface)


def _run_pose(phase):
    def leg_pose(p):
        angle = 0.85 * math.sin(p)
        bend = 0.25 + 1.3 * max(0.0, math.cos(p))
        return angle, bend

    bob = round(abs(math.sin(phase)))
    return {
        "hip": (16, 19 - bob),
        "lean": 0.22,
        "legs": (leg_pose(phase + math.pi), leg_pose(phase)),
        "arms": ((0.9 * math.sin(phase), 1.4), (-0.9 * math.sin(phase), 1.4)),
        "scarf": (1.0, phase),
    }


def make_player_frames():
    """Return {animation name: [frames]} for every player animation."""
    frames = {}

    frames["idle"] = [
        _runner_frame({
            "hip": (16, 19), "lean": 0.0, "breath": breath,
            "legs": ((-0.12, 0.05), (0.12, 0.05)),
            "arms": ((-0.15, 0.3), (0.15, 0.3)),
            "scarf": (0.15, i * 1.6),
        })
        for i, breath in enumerate((0, 0, 1, 1))
    ]

    frames["run"] = [_runner_frame(_run_pose(i / 8 * math.tau)) for i in range(8)]

    frames["jump"] = [
        _runner_frame({"hip": (16, 17), "lean": 0.1,
                       "legs": ((-0.5, 0.3), (1.3, 1.9)),
                       "arms": ((-0.8, 0.4), (2.4, 0.2)), "scarf": (0.8, 0.0)}),
        _runner_frame({"hip": (16, 16), "lean": 0.15,
                       "legs": ((-0.2, 1.4), (1.1, 1.8)),
                       "arms": ((-1.0, 0.6), (2.6, 0.3)), "scarf": (0.9, 1.0)}),
    ]

    frames["fall"] = [
        _runner_frame({"hip": (16, 18), "lean": 0.05,
                       "legs": ((-0.3, 0.5), (0.4, 0.7)),
                       "arms": ((-2.0, -0.4), (2.0, 0.4)), "scarf": (0.6, 0.0)}),
        _runner_frame({"hip": (16, 18), "lean": 0.05,
                       "legs": ((-0.25, 0.6), (0.35, 0.8)),
                       "arms": ((-1.6, -0.4), (1.6, 0.4)), "scarf": (0.6, 2.0)}),
    ]

    # Double jump: a forward flip made by rotating a tucked pose in 90 degree steps.
    # The tucked body is centered in the frame, so it spins in place.
    tuck = _runner_frame({"hip": (13, 21), "lean": 0.5,
                          "legs": ((2.0, 2.6), (2.2, 2.7)),
                          "arms": ((1.6, 1.2), (1.9, 1.2)), "scarf": (0.7, 0.5)})
    frames["double_jump"] = [pygame.transform.rotate(tuck, -90 * i) for i in range(4)]

    frames["slide"] = [
        _runner_frame({"hip": (18, 26), "lean": -1.15,
                       "legs": ((1.0, 2.6), (1.25, 0.1)),
                       "arms": ((-0.6, 0.0), (1.8, 0.5)), "scarf": (1.0, phase)})
        for phase in (0.0, 1.6, 3.2)
    ]

    frames["hurt"] = [
        _runner_frame({"hip": (16, 18), "lean": -0.5,
                       "legs": ((0.5, 1.0), (0.9, 1.2)),
                       "arms": ((-2.6, 0.3), (2.6, -0.3)), "scarf": (0.5, 0.0)}),
        _runner_frame({"hip": (16, 19), "lean": -0.8,
                       "legs": ((0.7, 0.8), (1.1, 1.0)),
                       "arms": ((-2.2, 0.6), (2.9, -0.5)), "scarf": (0.4, 1.5)}),
    ]
    return frames


# ---------------------------------------------------------------------------
# Obstacles
# ---------------------------------------------------------------------------
def _make_rock():
    s = new_sprite(16, 12)
    pygame.draw.ellipse(s, ROCK_DARK, (1, 2, 14, 9))
    pygame.draw.ellipse(s, ROCK, (1, 1, 13, 8))
    s.fill(ROCK_LIGHT, (4, 2, 4, 1))
    s.fill(ROCK_LIGHT, (3, 3, 2, 1))
    s.fill(ROCK_DARK, (9, 5, 2, 1))
    s.fill(MOSS, (6, 1, 5, 1))
    s.fill(MOSS_LIGHT, (7, 1, 2, 1))
    return [add_outline(s)]


def _make_stump():
    s = new_sprite(18, 22)
    pygame.draw.polygon(s, BARK_DARK, [(1, 21), (4, 15), (5, 21)])     # left root
    pygame.draw.polygon(s, BARK_DARK, [(16, 21), (13, 15), (12, 21)])  # right root
    s.fill(BARK, (2, 4, 14, 17))
    s.fill(BARK_LIGHT, (3, 6, 2, 13))
    for x, top in ((7, 7), (10, 9), (13, 6)):
        s.fill(BARK_DARK, (x, top, 1, 10))
    pygame.draw.ellipse(s, WOOD, (2, 1, 14, 6))
    pygame.draw.ellipse(s, WOOD_RING, (5, 2, 8, 4), 1)
    s.fill(WOOD_RING, (8, 3, 2, 1))
    s.fill(MOSS, (2, 13, 2, 5))
    s.fill(MOSS_LIGHT, (2, 14, 1, 2))
    return [add_outline(s)]


def _make_big_stump():
    s = new_sprite(26, 36)
    pygame.draw.polygon(s, BARK_DARK, [(1, 35), (5, 27), (7, 35)])
    pygame.draw.polygon(s, BARK_DARK, [(24, 35), (20, 27), (18, 35)])
    s.fill(BARK, (3, 6, 20, 30))
    s.fill(BARK_LIGHT, (4, 8, 3, 26))
    for x, top in ((9, 10), (13, 7), (17, 12), (20, 9)):
        s.fill(BARK_DARK, (x, top, 1, 20))
    # Broken, jagged top.
    top = [(3, 7), (5, 2), (8, 6), (11, 1), (14, 5), (17, 2), (20, 6), (23, 3), (23, 8), (3, 8)]
    pygame.draw.polygon(s, WOOD, top)
    pygame.draw.lines(s, WOOD_RING, False, [(5, 5), (8, 7), (11, 4), (14, 7), (17, 5), (20, 7)])
    # Shelf mushroom on the side.
    pygame.draw.ellipse(s, MUSHROOM, (17, 18, 8, 4))
    s.fill(MUSHROOM_LIGHT, (19, 18, 4, 1))
    pygame.draw.ellipse(s, MUSHROOM, (18, 24, 6, 3))
    s.fill(MOSS, (3, 26, 3, 7))
    s.fill(MOSS_LIGHT, (3, 27, 1, 3))
    return [add_outline(s)]


def _make_bird():
    """Three wing positions of a crow flying to the left."""
    wing_shapes = (
        [(8, 6), (11, 0), (14, 1), (13, 6)],   # wings up
        [(7, 6), (15, 4), (16, 6), (12, 8)],   # wings level
        [(8, 7), (11, 12), (14, 11), (13, 7)], # wings down
    )
    frames = []
    for wing in wing_shapes:
        s = new_sprite(20, 14)
        pygame.draw.polygon(s, BIRD, [(14, 6), (19, 4), (19, 9), (14, 9)])  # tail
        pygame.draw.ellipse(s, BIRD, (5, 5, 11, 5))                           # body
        pygame.draw.circle(s, BIRD, (6, 6), 3)                                # head
        pygame.draw.polygon(s, BEAK, [(3, 5), (0, 7), (3, 8)])                 # beak
        s.fill((255, 255, 255), (5, 5, 1, 1))                                 # eye
        pygame.draw.polygon(s, BIRD_LIGHT, wing)
        frames.append(add_outline(s))
    frames.append(frames[1])  # up, level, down, level -> smooth flapping loop
    return frames


_OBSTACLE_MAKERS = {
    "rock": _make_rock,
    "stump": _make_stump,
    "big_stump": _make_big_stump,
    "bird": _make_bird,
}


def make_obstacle_frames(art_name):
    """Return the list of frames for an obstacle's art name."""
    maker = _OBSTACLE_MAKERS.get(art_name)
    if maker is None:
        # Unknown art: a magenta box makes the missing art obvious but harmless.
        s = new_sprite(16, 16)
        s.fill((255, 0, 200))
        return [s]
    return maker()


# ---------------------------------------------------------------------------
# Background layers
# ---------------------------------------------------------------------------
SKY_TOP = (86, 166, 220)
SKY_BOTTOM = (206, 236, 222)
SUN = (255, 248, 206)
SUN_GLOW = ((176, 218, 232), (198, 230, 232), (222, 242, 230))
CLOUD = (250, 252, 255)
CLOUD_SHADE = (214, 230, 240)
FAR_FOREST = (124, 178, 166)
FAR_FOREST_LIGHT = (144, 194, 178)
MID_TREES = (76, 138, 116)
MID_TREES_LIGHT = (98, 160, 128)
MID_TRUNK = (64, 104, 96)
RAY = (255, 250, 214)
# Kept lighter and hazier than the obstacles, so dark obstacles stay readable in front.
TRUNK = (104, 96, 106)
TRUNK_LIGHT = (126, 118, 126)
TRUNK_DARK = (84, 76, 88)
NEAR_CANOPY = (42, 98, 74)
NEAR_CANOPY_LIGHT = (58, 120, 86)
BUSH = (40, 104, 64)
BUSH_LIGHT = (66, 140, 80)
BERRY = (214, 64, 72)
GRASS_TIP = (150, 206, 92)
GRASS = (98, 172, 66)
GRASS_DARK = (64, 130, 54)
DIRT = (120, 82, 52)
DIRT_DARK = (96, 64, 42)
DIRT_DEEP = (84, 56, 38)
PEBBLE = (156, 126, 94)
FERN = (24, 58, 42)
FERN_LIGHT = (36, 80, 54)
LEAF_DARK = (26, 66, 48)
LEAF = (38, 88, 60)
VINE = (44, 96, 58)


def _new_layer(width, height):
    """An opaque surface filled with the colorkey (it becomes transparent when finished)."""
    surface = pygame.Surface((width, height))
    surface.fill(COLORKEY)
    return surface


def _finish_layer(surface, alpha=None):
    """Make the colorkey transparent. RLEACCEL makes big layers very fast to draw."""
    surface = surface.convert()
    surface.set_colorkey(COLORKEY, pygame.RLEACCEL)
    if alpha is not None:
        surface.set_alpha(alpha)
    return surface


def _wrapped(width, x, draw):
    """Draw at x and one layer-width left and right, so the layer tiles seamlessly."""
    for offset in (-width, 0, width):
        draw(x + offset)


def _blend(color_a, color_b, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(color_a, color_b))


def _pine(surface, x, base_y, height, half_width, color, light=None):
    """A layered pine tree silhouette, optionally with a lighter left edge."""
    for i in range(4):
        top = base_y - height + i * height * 0.2
        bottom = top + height * 0.38
        hw = half_width * (0.45 + 0.55 * (i + 1) / 4)
        pygame.draw.polygon(surface, color, [(x, top), (x - hw, bottom), (x + hw, bottom)])
        if light is not None:
            pygame.draw.polygon(surface, light, [(x, top), (x - hw, bottom), (x - hw * 0.5, bottom)])


def _make_sky():
    height = GROUND_Y + 4
    surface = pygame.Surface((GAME_WIDTH, height))
    bands = 14
    band_height = height / bands
    for band in range(bands):
        color = _blend(SKY_TOP, SKY_BOTTOM, band / (bands - 1))
        top = round(band * band_height)
        surface.fill(color, (0, top, GAME_WIDTH, round((band + 1) * band_height) - top))
        if band > 0:  # a dithered row softens the step between two bands
            previous = _blend(SKY_TOP, SKY_BOTTOM, (band - 1) / (bands - 1))
            for x in range(band % 2, GAME_WIDTH, 2):
                surface.set_at((x, top), previous)
    sun = (392, 44)
    for radius, color in zip((30, 22, 16), SUN_GLOW):
        pygame.draw.circle(surface, color, sun, radius)
    pygame.draw.circle(surface, SUN, sun, 11)
    return surface.convert(), 0


def _make_clouds():
    width, height = GAME_WIDTH * 2, 70
    surface = _new_layer(width, height)
    rng = random.Random(7)
    x = 30
    while x < width - 40:
        size = rng.uniform(0.7, 1.4)
        y = rng.randint(14, 46)
        puffs = [(rng.uniform(-18, 18) * size, rng.uniform(-6, 2) * size, rng.uniform(6, 11) * size)
                 for _ in range(5)]

        def cloud(cx, puffs=puffs, y=y, size=size):
            for dx, dy, r in puffs:
                pygame.draw.circle(surface, CLOUD, (round(cx + dx), round(y + dy)), round(r))
            left, right = round(cx - 24 * size), round(cx + 24 * size)
            surface.fill(CLOUD, (left, y, right - left, round(5 * size)))
            surface.fill(CLOUD_SHADE, (left + 2, y + round(5 * size) - 1, right - left - 4, 2))

        _wrapped(width, x, cloud)
        x += rng.randint(130, 220)
    return _finish_layer(surface), 6


def _make_far_forest():
    top, width = 92, GAME_WIDTH
    height = GROUND_Y + 4 - top
    surface = _new_layer(width, height)
    rng = random.Random(11)
    base = height - 30
    x = 0
    while x < width:
        h, hw = rng.randint(46, 96), rng.randint(9, 15)

        def tree(px, h=h, hw=hw):
            _pine(surface, px, base, h, hw, FAR_FOREST, FAR_FOREST_LIGHT)

        _wrapped(width, x, tree)
        x += rng.randint(9, 17)
    surface.fill(FAR_FOREST, (0, base - 4, width, height - base + 4))
    return _finish_layer(surface), top


def _make_mid_trees():
    top, width = 60, GAME_WIDTH
    height = GROUND_Y + 4 - top
    surface = _new_layer(width, height)
    rng = random.Random(23)
    base = height - 12
    x = 10
    while x < width:
        h, hw = rng.randint(84, 140), rng.randint(15, 23)

        def tree(px, h=h, hw=hw):
            surface.fill(MID_TRUNK, (round(px) - 2, base - 16, 4, 16))
            _pine(surface, px, base - 10, h, hw, MID_TREES, MID_TREES_LIGHT)

        _wrapped(width, x, tree)
        x += rng.randint(24, 44)
    surface.fill(MID_TREES, (0, base - 2, width, height - base + 2))
    return _finish_layer(surface), top


def _make_light_rays():
    height = GROUND_Y
    surface = _new_layer(GAME_WIDTH, height)
    slant = 150
    for x, top_width, bottom_width in ((300, 16, 40), (350, 10, 26), (410, 22, 52), (250, 8, 20)):
        pygame.draw.polygon(surface, RAY, [(x, 0), (x + top_width, 0),
                                           (x - slant + bottom_width, height),
                                           (x - slant, height)])
    return _finish_layer(surface, alpha=34), 0


def _make_near_trees():
    width, height = 640, GROUND_Y + 6
    surface = _new_layer(width, height)
    rng = random.Random(5)
    for x in (70, 240, 410, 560):
        x += rng.randint(-20, 20)
        trunk_w = rng.randint(14, 22)

        def trunk(px, trunk_w=trunk_w):
            px = round(px)
            # Roots flaring out at the bottom.
            pygame.draw.polygon(surface, TRUNK_DARK, [(px - 8, height), (px + 2, height - 22),
                                                      (px + trunk_w - 2, height - 22),
                                                      (px + trunk_w + 8, height)])
            surface.fill(TRUNK, (px, 0, trunk_w, height))
            surface.fill(TRUNK_LIGHT, (px + 1, 0, 2, height))
            surface.fill(TRUNK_DARK, (px + trunk_w - 3, 0, 3, height))
            for y in range(20, height - 30, 26):  # bark marks
                surface.fill(TRUNK_DARK, (px + trunk_w // 2 - 1, y, 2, 7))
            # Leafy crown at the top of the screen.
            for dx, dy, r in ((-14, 6, 16), (trunk_w + 12, 4, 15), (trunk_w // 2, -4, 18),
                              (-30, -2, 12), (trunk_w + 28, -2, 12)):
                pygame.draw.circle(surface, NEAR_CANOPY, (px + dx, dy), r)
                pygame.draw.circle(surface, NEAR_CANOPY_LIGHT, (px + dx - 3, dy - 4), r // 2)

        _wrapped(width, x, trunk)
    return _finish_layer(surface), 0


def _make_bushes():
    width, height = GAME_WIDTH, 30
    surface = _new_layer(width, height)
    rng = random.Random(31)
    x = 20
    while x < width:
        puffs = [(rng.randint(-14, 14), rng.randint(7, 12)) for _ in range(rng.randint(3, 5))]
        berries = rng.random() < 0.35

        def bush(px, puffs=puffs, berries=berries):
            for dx, r in puffs:
                pygame.draw.circle(surface, BUSH, (round(px + dx), height - r // 2), r)
            for dx, r in puffs:
                pygame.draw.circle(surface, BUSH_LIGHT, (round(px + dx - 2), height - r), r // 3)
            if berries:
                for dx in (-6, 1, 7):
                    surface.fill(BERRY, (round(px + dx), height - 9 - abs(dx) // 2, 2, 2))

        _wrapped(width, x, bush)
        x += rng.randint(50, 110)
    return _finish_layer(surface), GROUND_Y - height + 4


def _make_ground():
    width = GAME_WIDTH
    blade_room = 3  # grass blades may poke this far above the ground line
    height = GAME_HEIGHT - GROUND_Y + blade_room
    surface = _new_layer(width, height)
    rng = random.Random(3)
    top = blade_room  # this row is GROUND_Y on screen

    surface.fill(DIRT, (0, top + 8, width, height))
    surface.fill(DIRT_DEEP, (0, top + 30, width, height))
    for x in range(width):
        # Wavy grass edge with a darker shadow line under it.
        edge = top + 6 + (1 if (x // 5) % 3 == 0 else 0)
        surface.fill(GRASS, (x, top, 1, edge - top))
        surface.fill(GRASS_DARK, (x, edge, 1, 2))
        # Grass blades poking up above the ground line.
        blade = rng.choice((0, 0, 1, 1, 2, 3))
        if blade:
            surface.fill(GRASS, (x, top - blade, 1, blade))
            surface.set_at((x, top - blade), GRASS_TIP)
    for _ in range(90):  # dirt specks and pebbles
        x, y = rng.randrange(width - 3), rng.randint(top + 11, height - 3)
        if rng.random() < 0.25:
            surface.fill(PEBBLE, (x, y, 2, 2))
            surface.set_at((x + 1, y + 1), DIRT_DARK)
        else:
            surface.fill(DIRT_DARK, (x, y, rng.randint(1, 3), 1))
    for _ in range(40):  # light specks in the grass
        surface.set_at((rng.randrange(width), rng.randint(top + 1, top + 4)), GRASS_TIP)
    return _finish_layer(surface), GROUND_Y - blade_room


def _make_foreground_plants():
    width, height = 520, 30
    surface = _new_layer(width, height)
    rng = random.Random(17)
    x = 40
    while x < width:
        blades = [(rng.uniform(-10, 10), rng.randint(10, 27), rng.uniform(-6, 6))
                  for _ in range(rng.randint(5, 9))]

        def tuft(px, blades=blades):
            for i, (dx, h, lean) in enumerate(blades):
                color = FERN_LIGHT if i % 3 == 0 else FERN
                start = (round(px + dx), height)
                end = (round(px + dx + lean), height - h)
                pygame.draw.line(surface, color, start, end, 2)

        _wrapped(width, x, tuft)
        x += rng.randint(90, 170)
    return _finish_layer(surface), GAME_HEIGHT - height


def _make_canopy():
    width, height = 560, 46
    surface = _new_layer(width, height)
    rng = random.Random(41)
    x = 0
    while x < width:
        leaves = [(rng.randint(-22, 22), rng.randint(-6, 12), rng.randint(6, 13)) for _ in range(6)]
        vines = [(rng.randint(-16, 16), rng.randint(18, 42)) for _ in range(rng.randint(1, 2))]

        def cluster(px, leaves=leaves, vines=vines):
            for dx, length in vines:
                vx = round(px + dx)
                pygame.draw.line(surface, VINE, (vx, 0), (vx, length), 1)
                for y in range(6, length, 7):
                    surface.fill(LEAF, (vx - 2 if (y // 7) % 2 else vx + 1, y, 2, 2))
            for dx, dy, r in leaves:
                pygame.draw.circle(surface, LEAF_DARK, (round(px + dx), dy), r)
            for dx, dy, r in leaves[:3]:
                pygame.draw.circle(surface, LEAF, (round(px + dx - 2), dy - 2), r // 2)

        _wrapped(width, x, cluster)
        x += rng.randint(110, 190)
    return _finish_layer(surface), 0


_LAYER_MAKERS = {
    "sky": _make_sky,
    "clouds": _make_clouds,
    "far_forest": _make_far_forest,
    "mid_trees": _make_mid_trees,
    "light_rays": _make_light_rays,
    "near_trees": _make_near_trees,
    "bushes": _make_bushes,
    "ground": _make_ground,
    "foreground_plants": _make_foreground_plants,
    "canopy": _make_canopy,
}


def make_background_layer(name):
    """Return (image, y position) for a background layer, or None if the name is unknown."""
    maker = _LAYER_MAKERS.get(name)
    return maker() if maker else None
