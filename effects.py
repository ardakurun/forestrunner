"""
effects.py - particles, screen shake and screen flash.

Particles come from a fixed-size pool: they are created once and then reused,
so no new objects are made during gameplay. To add a new kind of effect, add
a recipe to PARTICLE_PRESETS in settings.py (and a small method below if you
want a nice name for it).
"""
import math
import random

import pygame

from settings import (GAME_HEIGHT, GAME_WIDTH, HIT_FLASH_TIME, MAX_PARTICLES,
                      PARTICLE_PRESETS, SHAKE_DECAY, SHAKE_MAX_OFFSET,
                      SHAKE_ON_HARD_LANDING, SHAKE_ON_HIT)


class Particle:
    # __slots__ makes these small objects lighter and faster.
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color", "gravity", "drag")

    def __init__(self):
        self.x = self.y = self.vx = self.vy = 0.0
        self.life = self.max_life = 1.0
        self.size = 1.0
        self.color = (255, 255, 255)
        self.gravity = self.drag = 0.0


class ParticleSystem:
    def __init__(self, capacity=MAX_PARTICLES):
        self._free = [Particle() for _ in range(capacity)]
        self.active = []

    def emit(self, preset_name, x, y, colors=None, count=None):
        """Spawn a burst of particles using a recipe from PARTICLE_PRESETS."""
        preset = PARTICLE_PRESETS[preset_name]
        count = preset["count"] if count is None else count
        colors = colors or preset["colors"]
        for i in range(count):
            if not self._free:
                return  # pool is empty: skip the rest instead of creating more
            p = self._free.pop()
            if preset.get("ring"):
                angle = i / count * math.tau + random.uniform(-0.15, 0.15)
                speed = random.uniform(*preset["vx"])
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed * 0.6  # a slightly flattened ring
            else:
                p.vx = random.uniform(*preset["vx"])
                p.vy = random.uniform(*preset["vy"])
            p.x, p.y = x, y
            p.life = p.max_life = random.uniform(*preset["life"])
            p.size = random.uniform(*preset["size"])
            p.color = random.choice(colors)
            p.gravity = preset["gravity"]
            p.drag = preset["drag"]
            self.active.append(p)

    def update(self, dt):
        # Move living particles and return dead ones to the pool, without
        # building a new list every frame.
        alive = 0
        for p in self.active:
            p.life -= dt
            if p.life <= 0:
                self._free.append(p)
                continue
            friction = max(0.0, 1.0 - p.drag * dt)
            p.vx *= friction
            p.vy = p.vy * friction + p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            self.active[alive] = p
            alive += 1
        del self.active[alive:]

    def draw(self, surface):
        for p in self.active:
            # Shrink with age: pixel-art friendly, no transparency needed.
            size = max(1, round(p.size * math.sqrt(p.life / p.max_life)))
            surface.fill(p.color, (round(p.x) - size // 2, round(p.y) - size // 2, size, size))

    def clear(self):
        self._free.extend(self.active)
        self.active.clear()


class ScreenShake:
    """Trauma-based shake: hits add trauma, which fades out over time."""

    def __init__(self):
        self.trauma = 0.0
        self.offset = (0, 0)

    def add(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - SHAKE_DECAY * dt)
        if self.trauma > 0:
            # Squaring makes small shakes subtle and big ones punchy.
            strength = SHAKE_MAX_OFFSET * self.trauma * self.trauma
            self.offset = (round(random.uniform(-strength, strength)),
                           round(random.uniform(-strength, strength)))
        else:
            self.offset = (0, 0)

    def reset(self):
        self.trauma = 0.0
        self.offset = (0, 0)


class ScreenFlash:
    """A full-screen color flash that fades out quickly."""

    def __init__(self):
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.duration = self.timer = 0.0

    def start(self, duration, color=(255, 255, 255)):
        self.surface.fill(color)
        self.duration = self.timer = duration

    def update(self, dt):
        self.timer = max(0.0, self.timer - dt)

    def draw(self, surface):
        if self.timer > 0:
            self.surface.set_alpha(round(190 * self.timer / self.duration))
            surface.blit(self.surface, (0, 0))


class Effects:
    """All visual feedback in one place. Gameplay code calls e.g. effects.jump_dust(x, y)."""

    def __init__(self):
        self.particles = ParticleSystem()
        self.shake = ScreenShake()
        self.flash = ScreenFlash()

    def update(self, dt):
        self.particles.update(dt)
        self.shake.update(dt)
        self.flash.update(dt)

    def reset(self):
        self.particles.clear()
        self.shake.reset()
        self.flash.timer = 0.0

    # --- named effects -----------------------------------------------------
    def jump_dust(self, x, y):
        self.particles.emit("jump_dust", x, y)

    def land_dust(self, x, y, strength):
        """strength 0..1: how hard the landing was."""
        self.particles.emit("land_dust", x, y, count=4 + round(8 * strength))
        if strength > 0.8:
            self.shake.add(SHAKE_ON_HARD_LANDING)

    def run_dust(self, x, y):
        self.particles.emit("run_dust", x, y)

    def slide_dust(self, x, y):
        self.particles.emit("slide_dust", x, y)

    def double_jump(self, x, y):
        self.particles.emit("double_jump", x, y)

    def hit(self, x, y, debris_colors):
        self.particles.emit("hit", x, y)
        self.particles.emit("hit", x, y, colors=debris_colors)
        self.shake.add(SHAKE_ON_HIT)
        self.flash.start(HIT_FLASH_TIME)

    def milestone(self, x, y):
        self.particles.emit("milestone", x, y)
