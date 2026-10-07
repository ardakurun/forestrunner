"""
player.py - the runner: movement physics, controls and animation state.

The player never moves left or right; the world scrolls past instead. The
player only moves up and down (jumping and falling) and can slide.

Keyboard handling lives in the game states. They talk to the player through
press_jump(), release_jump(), press_slide() and the slide_held flag passed
to update().

The player does not play sounds or spawn particles itself. Instead it lists
what happened this frame in self.events ("jump", "double_jump", "land",
"slide"), and the game reacts to those. That keeps this file about movement.
"""
import pygame

from animation import Animation
from assets import load_frames
from placeholder_art import make_player_frames
from settings import (COYOTE_TIME, DOUBLE_JUMP_VELOCITY, FAST_FALL_ENABLED,
                      FAST_FALL_GRAVITY_MULTIPLIER, FAST_FALL_MIN_SPEED,
                      FALL_GRAVITY_MULTIPLIER, GRAVITY, GROUND_Y,
                      HURT_BOUNCE_VELOCITY, HURT_KNOCKBACK_SPEED,
                      JUMP_BUFFER_TIME, JUMP_CUT_MIN_TIME, JUMP_CUT_MULTIPLIER,
                      JUMP_VELOCITY, MAX_FALL_SPEED, MAX_JUMPS,
                      PLAYER_ANIMATIONS, PLAYER_ASSETS_DIR, PLAYER_FRAME_SIZE,
                      PLAYER_HITBOX_SLIDE, PLAYER_HITBOX_STAND, PLAYER_X,
                      SLIDE_DURATION, SQUASH_RECOVERY_SPEED, SQUASH_STRETCH,
                      START_SPEED, VARIABLE_JUMP_HEIGHT)

_frames = {}  # loaded once, shared by every Player


def load_player_frames():
    """
    Frames for every player animation. For each animation name (see
    PLAYER_ANIMATIONS) the game first looks in assets/player for
    <name>.png (a horizontal strip) or a <name>/ folder of frames, and uses
    the placeholder art for anything that is missing.
    """
    if not _frames:
        placeholders = None
        for name in PLAYER_ANIMATIONS:
            frames = load_frames(PLAYER_ASSETS_DIR, name, PLAYER_FRAME_SIZE[0])
            if frames is None:
                if placeholders is None:
                    placeholders = make_player_frames()
                frames = placeholders[name]
            _frames[name] = frames
    return _frames


class Player:
    _shadow_cache = {}

    def __init__(self):
        frames = load_player_frames()
        self.animations = {
            name: Animation(frames[name], fps, loop)
            for name, (fps, loop) in PLAYER_ANIMATIONS.items()
        }
        self.hitbox = pygame.Rect(0, 0, *PLAYER_HITBOX_STAND)
        self.reset()

    def reset(self):
        self.x = float(PLAYER_X)
        self.y = float(GROUND_Y)       # position of the feet
        self.ground_y = GROUND_Y       # could change later for platforms
        self.vy = 0.0                  # vertical speed (negative = up)
        self.on_ground = True
        self.jumps_used = 0
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.jump_time = 0.0           # how long the current jump has been rising
        self.jump_cut_ready = False    # True while releasing SPACE would shorten the jump
        self.jump_held = False
        self.slide_held = False
        self.sliding = False
        self.slide_timer = 0.0
        self.fast_falling = False
        self.running = False           # False = standing idle (menu)
        self.alive = True
        self.landing_strength = 0.0    # 0..1, set when a "land" event happens
        self.scale_x = self.scale_y = 1.0
        self.events = []
        self.state = None
        self.set_state("idle")
        self._update_hitbox()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def press_jump(self):
        self.jump_held = True
        if self.alive:
            # Remember the press for a short time (jump buffering).
            self.jump_buffer_timer = JUMP_BUFFER_TIME

    def release_jump(self):
        self.jump_held = False

    def press_slide(self):
        if not self.alive:
            return
        if self.on_ground:
            self._start_slide()
        elif FAST_FALL_ENABLED and not self.fast_falling:
            # In the air: drop down fast, then slide on landing.
            self.fast_falling = True
            self.jump_cut_ready = False
            self.vy = max(self.vy, FAST_FALL_MIN_SPEED)

    def die(self):
        if not self.alive:
            return
        self.alive = False
        self.sliding = False
        self.fast_falling = False
        self.jump_cut_ready = False
        self.on_ground = False
        self.vy = -HURT_BOUNCE_VELOCITY

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt, speed=0.0, slide_held=False):
        self.events.clear()  # last frame's events have been handled already
        self.slide_held = slide_held
        if self.alive:
            self._update_controls(dt)
        elif not self.on_ground:
            self.x -= HURT_KNOCKBACK_SPEED * dt  # knocked back after a crash
        self._apply_physics(dt)
        self._update_squash(dt)
        self._update_animation(dt, speed)
        self._update_hitbox()

    def _update_controls(self, dt):
        self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        if self.jump_buffer_timer > 0 and self._try_jump():
            self.jump_buffer_timer = 0.0

        # Variable jump height: letting go of SPACE early cuts the jump short.
        if (self.jump_cut_ready and not self.jump_held and self.vy < 0
                and self.jump_time >= JUMP_CUT_MIN_TIME):
            self.vy *= JUMP_CUT_MULTIPLIER
            self.jump_cut_ready = False

        if self.sliding:
            self.slide_timer -= dt
            if self.slide_timer <= 0 and not self.slide_held:
                self.sliding = False

    def _try_jump(self):
        # Coyote time: a jump just after leaving the ground still counts as a ground jump.
        if self.on_ground or self.coyote_timer > 0:
            self.jumps_used = 1
            self._jump(JUMP_VELOCITY, "jump")
            return True
        if self.jumps_used < MAX_JUMPS:
            self.jumps_used += 1
            self._jump(DOUBLE_JUMP_VELOCITY, "double_jump")
            return True
        return False

    def _jump(self, velocity, event):
        self.vy = -velocity
        self.on_ground = False
        self.coyote_timer = 0.0
        self.sliding = False
        self.fast_falling = False
        self.jump_time = 0.0
        self.jump_cut_ready = VARIABLE_JUMP_HEIGHT
        self.events.append(event)
        if SQUASH_STRETCH:
            self.scale_x, self.scale_y = 0.8, 1.2
        if event == "double_jump":
            self.state = None  # restart the flip animation even if it was playing
            self.set_state("double_jump")

    def _apply_physics(self, dt):
        if not self.on_ground:
            gravity = GRAVITY
            if self.vy > 0:
                gravity *= FALL_GRAVITY_MULTIPLIER
            if self.fast_falling:
                gravity *= FAST_FALL_GRAVITY_MULTIPLIER
            # This formula is exact for constant gravity, so jumps reach the
            # same height no matter what the frame rate is.
            self.y += self.vy * dt + 0.5 * gravity * dt * dt
            self.vy = min(self.vy + gravity * dt, MAX_FALL_SPEED)
            if self.vy < 0:
                self.jump_time += dt
            if self.coyote_timer > 0:
                self.coyote_timer = max(0.0, self.coyote_timer - dt)
                if self.coyote_timer == 0 and self.jumps_used == 0:
                    self.jumps_used = 1  # too late for a ground jump; the air jump is left

        if self.y >= self.ground_y:
            if not self.on_ground:
                self._land()
            self.y = float(self.ground_y)
        elif self.on_ground:
            # Ran off an edge without jumping: start coyote time.
            self.on_ground = False
            self.coyote_timer = COYOTE_TIME

    def _land(self):
        self.landing_strength = min(1.0, max(0.0, self.vy) / MAX_FALL_SPEED)
        self.on_ground = True
        self.vy = 0.0
        self.jumps_used = 0
        self.coyote_timer = 0.0
        self.jump_cut_ready = False
        self.events.append("land")
        if SQUASH_STRETCH:
            squash = 0.12 + 0.2 * self.landing_strength
            self.scale_x, self.scale_y = 1 + squash, 1 - squash
        if self.alive and (self.fast_falling or self.slide_held):
            self._start_slide()  # dropped down with DOWN held: go straight into a slide
        self.fast_falling = False

    def _start_slide(self):
        if not self.sliding:
            self.events.append("slide")
        self.sliding = True
        self.slide_timer = SLIDE_DURATION

    def _update_squash(self, dt):
        blend = min(1.0, SQUASH_RECOVERY_SPEED * dt)
        self.scale_x += (1.0 - self.scale_x) * blend
        self.scale_y += (1.0 - self.scale_y) * blend

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------
    def set_state(self, name):
        if name != self.state:
            self.state = name
            self.animation = self.animations[name]
            self.animation.reset()

    def _choose_state(self):
        if not self.alive:
            return "hurt"
        if self.on_ground:
            if self.sliding:
                return "slide"
            return "run" if self.running else "idle"
        if self.state == "double_jump" and not self.animation.finished:
            return "double_jump"  # let the flip finish
        return "jump" if self.vy < 0 else "fall"

    def _update_animation(self, dt, speed):
        self.set_state(self._choose_state())
        playback = 1.0
        if self.state == "run":
            playback = max(0.6, speed / START_SPEED)  # legs move faster as the world speeds up
        self.animation.update(dt, playback)

    def _update_hitbox(self):
        self.hitbox.size = PLAYER_HITBOX_SLIDE if self.sliding else PLAYER_HITBOX_STAND
        self.hitbox.midbottom = (round(self.x), round(self.y))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    @property
    def feet(self):
        return round(self.x), round(self.y)

    def draw_shadow(self, surface):
        """A soft shadow on the ground. It shrinks while jumping, which helps timing."""
        height = self.ground_y - self.y
        width = max(6, round(16 - height * 0.12))
        shadow = self._shadow_cache.get(width)
        if shadow is None:
            shadow = pygame.Surface((width, 4), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
            self._shadow_cache[width] = shadow
        surface.blit(shadow, shadow.get_rect(center=(round(self.x), self.ground_y)))

    def draw(self, surface):
        image = self.animation.image
        if abs(self.scale_x - 1) > 0.03 or abs(self.scale_y - 1) > 0.03:
            width, height = image.get_size()
            image = pygame.transform.scale(
                image, (round(width * self.scale_x), round(height * self.scale_y)))
        surface.blit(image, image.get_rect(midbottom=self.feet))
