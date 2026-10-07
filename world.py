"""
world.py - the scrolling forest: parallax layers and falling leaves.

world.distance is how far the camera has travelled. Each layer scrolls by
distance * factor, so far layers (small factor) move slowly and near layers
move fast. That difference in speed is what creates the feeling of depth.

Real art: put assets/background/<layer name>.png next to the game (names are
listed in BACKGROUND_LAYERS in settings.py). A PNG layer is drawn at the top
of the screen and repeated sideways, so make it GAME_HEIGHT pixels tall
with transparent areas where the layers behind it should show through.
"""
import math
import os
import random

from assets import load_image
from placeholder_art import make_background_layer
from settings import (BACKGROUND_ASSETS_DIR, BACKGROUND_LAYERS, GAME_WIDTH,
                      GROUND_Y, LEAF_COUNT)

LEAF_COLORS = ((214, 150, 60), (190, 110, 50), (150, 190, 80), (236, 196, 90))


class ParallaxLayer:
    def __init__(self, image, y, factor, drift, front):
        self.image = image
        self.y = y
        self.factor = factor    # 0 = static, 1 = moves exactly with the ground
        self.drift = drift      # extra sideways motion in pixels/second (clouds)
        self.front = front      # drawn in front of the player?
        self.drift_offset = 0.0

    def update(self, dt):
        self.drift_offset += self.drift * dt

    def draw(self, surface, distance):
        width = self.image.get_width()
        offset = (distance * self.factor + self.drift_offset) % width
        x = -round(offset)
        while x < GAME_WIDTH:  # repeat the image to fill the screen
            surface.blit(self.image, (x, self.y))
            x += width


class Leaf:
    __slots__ = ("x", "y", "fall_speed", "depth", "phase", "sway_speed", "color")


class World:
    def __init__(self):
        self.distance = 0.0
        self.layers = [self._load_layer(spec) for spec in BACKGROUND_LAYERS]
        self.back_layers = [layer for layer in self.layers if not layer.front]
        self.front_layers = [layer for layer in self.layers if layer.front]
        self.leaves = [Leaf() for _ in range(LEAF_COUNT)]
        for leaf in self.leaves:
            self._place_leaf(leaf, x=random.uniform(0, GAME_WIDTH), y=random.uniform(0, GROUND_Y))

    @staticmethod
    def _load_layer(spec):
        image = load_image(os.path.join(BACKGROUND_ASSETS_DIR, spec["name"] + ".png"))
        if image is not None:
            y = 0
        else:
            image, y = make_background_layer(spec["name"])
        return ParallaxLayer(image, y, spec["factor"], spec["drift"], spec["front"])

    @staticmethod
    def _place_leaf(leaf, x, y):
        leaf.x, leaf.y = x, y
        leaf.fall_speed = random.uniform(14, 30)
        leaf.depth = random.uniform(0.45, 0.9)  # how strongly it scrolls with the world
        leaf.phase = random.uniform(0, math.tau)
        leaf.sway_speed = random.uniform(2.0, 4.0)
        leaf.color = random.choice(LEAF_COLORS)

    def update(self, dt, speed):
        """speed = how fast the ground is scrolling (pixels/second)."""
        self.distance += speed * dt
        for layer in self.layers:
            layer.update(dt)
        for leaf in self.leaves:
            leaf.phase += leaf.sway_speed * dt
            leaf.x += (math.sin(leaf.phase) * 16 - 8 - speed * leaf.depth) * dt
            leaf.y += leaf.fall_speed * dt
            if leaf.x < -6:
                # Blown off the left side: come back from beyond the right edge.
                self._place_leaf(leaf, GAME_WIDTH + random.uniform(4, 80),
                                 random.uniform(0, GROUND_Y - 30))
            elif leaf.y > GROUND_Y:
                # Reached the ground: start again from the top.
                self._place_leaf(leaf, random.uniform(0, GAME_WIDTH + 60), -4)

    def draw_back(self, surface):
        """Everything behind the player: sky, trees, ground and leaves."""
        for layer in self.back_layers:
            layer.draw(surface, self.distance)
        for leaf in self.leaves:
            width = 2 if math.sin(leaf.phase * 2) > 0 else 1  # flutter
            surface.fill(leaf.color, (round(leaf.x), round(leaf.y), width, 2))

    def draw_front(self, surface):
        """Layers drawn in front of the player (plants at the bottom, leaves at the top)."""
        for layer in self.front_layers:
            layer.draw(surface, self.distance)
