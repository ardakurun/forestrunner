"""
obstacle.py - obstacles and the spawner that places them fairly.

Positions: an obstacle stores its position in the *world* (world_x). The
camera has scrolled world.distance pixels, so its position on screen is
world_x - distance. Ground obstacles never move in the world, which keeps
them perfectly in step with the scrolling ground.

Fairness: the spawner only uses hand-made patterns from settings.py whose
spacing is measured in seconds, and it always leaves enough recovery time
between patterns for the player to land and react, at any speed.
"""
import math
import random

import pygame

from animation import Animation
from assets import load_frames
from placeholder_art import make_obstacle_frames
from settings import (EXTRA_GAP_EASY, EXTRA_GAP_HARD, FIRST_SPAWN_DELAY,
                      GROUND_Y, HARD_PATTERN_BIAS, MAX_OBSTACLES,
                      OBSTACLE_ASSETS_DIR, OBSTACLE_PATTERNS, OBSTACLE_TYPES,
                      PATTERN_REPEAT_LIMIT, PLAYER_X, REACTION_TIME_EASY,
                      REACTION_TIME_HARD, SPAWN_X)

BOB_SPEED = 6.0  # wobble speed of flying obstacles (radians per second)

_frames = {}  # art name -> frames, loaded once


def load_obstacle_frames(art_name, frame_width):
    """assets/obstacles/<art_name>.png (or a folder of frames), else placeholder art."""
    if art_name not in _frames:
        frames = load_frames(OBSTACLE_ASSETS_DIR, art_name, frame_width)
        _frames[art_name] = frames or make_obstacle_frames(art_name)
    return _frames[art_name]


class Obstacle:
    def __init__(self, kind, world_x):
        self.kind = kind
        self.data = OBSTACLE_TYPES[kind]
        frames = load_obstacle_frames(self.data["art"], self.data["size"][0])
        self.animation = Animation(frames, fps=self.data["anim_fps"] or 1)
        self.world_x = float(world_x)
        self.extra_speed = self.data["extra_speed"]
        self.bob_amount = self.data["bob"]
        self.bob_time = random.uniform(0, math.tau)
        self.base_bottom = GROUND_Y - self.data["altitude"]
        self.hitbox = pygame.Rect(0, 0, *self.data["hitbox"])

    def update(self, dt, distance):
        """distance = how far the world has scrolled (the camera position)."""
        self.world_x -= self.extra_speed * dt  # flying things move on their own too
        self.animation.update(dt)
        bob = 0.0
        if self.bob_amount:
            self.bob_time += dt
            bob = math.sin(self.bob_time * BOB_SPEED) * self.bob_amount
        self.hitbox.centerx = round(self.world_x - distance)
        self.hitbox.bottom = round(self.base_bottom + bob)

    @property
    def off_screen(self):
        return self.hitbox.right < -40

    def draw(self, surface):
        image = self.animation.image
        surface.blit(image, image.get_rect(center=self.hitbox.center))


class ObstacleSpawner:
    def __init__(self):
        self.reset()

    def reset(self):
        self.timer = FIRST_SPAWN_DELAY  # seconds until the next pattern appears
        self.history = []               # names of the most recent patterns

    def update(self, dt, speed, difficulty, distance, obstacles):
        if speed <= 0:
            return
        self.timer -= dt
        if self.timer > 0 or len(obstacles) >= MAX_OBSTACLES:
            return
        pattern = self._choose_pattern(difficulty)
        self._spawn(pattern, speed, distance, obstacles)
        self.timer = self._time_until_next(pattern, difficulty)

    def _choose_pattern(self, difficulty):
        options, weights = [], []
        for pattern in OBSTACLE_PATTERNS:
            if pattern["min_difficulty"] > difficulty or self._repeated_too_often(pattern["name"]):
                continue
            # Harder patterns slowly become more common as difficulty rises.
            bias = 1 + HARD_PATTERN_BIAS * pattern["min_difficulty"] * difficulty
            options.append(pattern)
            weights.append(pattern["weight"] * bias)
        if not options:
            options, weights = OBSTACLE_PATTERNS[:1], [1]
        pattern = random.choices(options, weights)[0]
        self.history.append(pattern["name"])
        del self.history[:-PATTERN_REPEAT_LIMIT]
        return pattern

    def _repeated_too_often(self, name):
        recent = self.history[-PATTERN_REPEAT_LIMIT:]
        return len(recent) == PATTERN_REPEAT_LIMIT and all(n == name for n in recent)

    @staticmethod
    def _spawn(pattern, speed, distance, obstacles):
        # Time for something at SPAWN_X, moving with the ground, to reach the player.
        lead_time = (SPAWN_X - PLAYER_X) / speed
        for kind, delay in pattern["items"]:
            own_speed = speed + OBSTACLE_TYPES[kind]["extra_speed"]
            # Place it so it reaches the player exactly `delay` seconds after the
            # first obstacle, even if it flies faster than the ground scrolls.
            screen_x = PLAYER_X + own_speed * (lead_time + delay)
            obstacles.append(Obstacle(kind, round(screen_x + distance)))

    @staticmethod
    def _time_until_next(pattern, difficulty):
        items = pattern["items"]
        last_delay = max(delay for _, delay in items)
        recover = max(OBSTACLE_TYPES[kind]["recover_time"]
                      for kind, delay in items if delay == last_delay)
        reaction = REACTION_TIME_EASY + (REACTION_TIME_HARD - REACTION_TIME_EASY) * difficulty
        extra_max = EXTRA_GAP_EASY + (EXTRA_GAP_HARD - EXTRA_GAP_EASY) * difficulty
        return last_delay + recover + reaction + random.uniform(0, extra_max)
