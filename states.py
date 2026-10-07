"""
states.py - the screens of the game: main menu, how to play, playing,
paused and game over.

Every state has the same four methods, and the Game only talks to the
current state through them:
    enter(**options)    - called when the game switches to this state
    handle_event(event) - called for every keyboard / window event
    update(dt)          - called every frame (dt = seconds since last frame)
    draw(surface)       - called every frame to draw onto the canvas
"""
import math

import pygame

from effects import Effects
from obstacle import ObstacleSpawner
from player import Player
from settings import (BACK_KEYS, CONFIRM_KEYS, DIFFICULTY_TIME_CONSTANT,
                      GAME_HEIGHT, GAME_OVER_INPUT_DELAY, GAME_OVER_PANEL_DELAY,
                      GAME_WIDTH, HINT_DURATION, JUMP_KEYS, MAX_SPEED,
                      MENU_DOWN_KEYS, MENU_UP_KEYS, MILESTONE_FLASH_TIME,
                      PAUSE_KEYS, RUN_DUST_INTERVAL, SCORE_MILESTONE,
                      SCORE_PER_PIXEL, SLIDE_DUST_INTERVAL, SLIDE_KEYS,
                      START_ACCELERATION, START_SPEED, UI_DANGER, UI_HIGHLIGHT,
                      UI_MUTED, UI_SHADOW, UI_TEXT)
from ui import format_score

CENTER_X = GAME_WIDTH // 2


class State:
    """Base class: a state that does nothing. Real states override what they need."""

    def __init__(self, game):
        self.game = game

    def enter(self, **options):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class MenuSelection:
    """Keyboard navigation for a vertical list of options (shared by menus)."""

    def __init__(self, options):
        self.options = options
        self.index = 0

    def handle_key(self, key, audio):
        """Move the selection. Returns the chosen option when confirmed, else None."""
        if key in MENU_UP_KEYS:
            self.index = (self.index - 1) % len(self.options)
            audio.play("menu_move")
        elif key in MENU_DOWN_KEYS:
            self.index = (self.index + 1) % len(self.options)
            audio.play("menu_move")
        elif key in CONFIRM_KEYS:
            audio.play("menu_select")
            return self.options[self.index]
        return None


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.menu = MenuSelection(("PLAY", "HOW TO PLAY", "QUIT"))
        self.player = Player()  # stands idle in the menu
        self.time = 0.0

    def enter(self, **options):
        self.player.reset()
        self.game.audio.play_music("menu")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.menu.index = len(self.menu.options) - 1  # jump to QUIT
            return
        choice = self.menu.handle_key(event.key, self.game.audio)
        if choice == "PLAY":
            self.game.change_state("playing")
        elif choice == "HOW TO PLAY":
            self.game.change_state("how_to_play")
        elif choice == "QUIT":
            self.game.quit()

    def update(self, dt):
        self.time += dt
        self.game.world.update(dt, 0)
        self.player.update(dt)

    def draw(self, surface):
        world, ui = self.game.world, self.game.ui
        world.draw_back(surface)
        self.player.draw_shadow(surface)
        self.player.draw(surface)
        world.draw_front(surface)

        ui.title(surface, 30, self.time)
        ui.font.draw(surface, "HOW FAR CAN YOU RUN?", (CENTER_X, 70), UI_TEXT, 1, "center", outline=UI_SHADOW)
        ui.panel(surface, (CENTER_X - 100, 92, 200, 86))
        ui.menu_options(surface, self.menu.options, self.menu.index, 135, self.time)
        ui.text(surface, "BEST: " + format_score(self.game.high_score), (CENTER_X, GAME_HEIGHT - 36),
                UI_HIGHLIGHT)
        ui.text(surface, "UP/DOWN: CHOOSE    SPACE/ENTER: SELECT", (CENTER_X, GAME_HEIGHT - 20), UI_MUTED)


# ---------------------------------------------------------------------------
# How to play
# ---------------------------------------------------------------------------
class HowToPlayState(State):
    CONTROLS = (("SPACE", "JUMP"), ("SPACE AGAIN", "DOUBLE JUMP"),
                ("DOWN / S", "SLIDE"), ("ESC", "MENU"))
    TIPS = ("HOLD SPACE TO JUMP HIGHER, TAP FOR A SMALL HOP",
            "PRESS DOWN IN THE AIR TO DROP FAST",
            "HOLD DOWN TO KEEP SLIDING",
            "JUMP OVER ROCKS AND STUMPS, SLIDE UNDER LOW BIRDS")

    def enter(self, **options):
        self.time = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and (event.key in BACK_KEYS or event.key in CONFIRM_KEYS):
            self.game.audio.play("menu_select")
            self.game.change_state("menu")

    def update(self, dt):
        self.time += dt
        self.game.world.update(dt, 0)

    def draw(self, surface):
        world, ui = self.game.world, self.game.ui
        world.draw_back(surface)
        world.draw_front(surface)
        ui.dim(surface, 90)
        ui.panel(surface, (CENTER_X - 165, 18, 330, 222))
        ui.text(surface, "HOW TO PLAY", (CENTER_X, 30), UI_HIGHLIGHT, 2)

        y = 60
        for key, action in self.CONTROLS:
            ui.text(surface, key, (CENTER_X - 14, y), UI_HIGHLIGHT, 2, "right")
            ui.text(surface, "=", (CENTER_X, y), UI_MUTED, 2)
            ui.text(surface, action, (CENTER_X + 14, y), UI_TEXT, 2, "left")
            y += 22

        y += 8
        for tip in self.TIPS:
            ui.text(surface, tip, (CENTER_X, y), UI_MUTED)
            y += 13

        if ui.blink(self.time):
            ui.text(surface, "PRESS ESC TO GO BACK", (CENTER_X, 220), UI_TEXT)


# ---------------------------------------------------------------------------
# Playing
# ---------------------------------------------------------------------------
class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        self.player = Player()
        self.spawner = ObstacleSpawner()
        self.effects = Effects()
        self.obstacles = []
        self.scene = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))  # the world is drawn here first
        self.held_jump_keys = set()
        self.held_slide_keys = set()
        self.show_hitboxes = False  # toggle with F1 - handy when tuning
        self.reset_run()

    def reset_run(self):
        self.player.reset()
        self.player.running = True
        self.spawner.reset()
        self.effects.reset()
        self.obstacles.clear()
        self.elapsed = 0.0          # seconds survived
        self.difficulty = 0.0       # 0 = easy start, approaches 1 over time
        self.speed = 0.0            # world speed in pixels/second
        self.run_distance = 0.0
        self.score = 0
        self.next_milestone = SCORE_MILESTONE
        self.milestone_timer = 0.0
        self.dust_timer = 0.0

    def enter(self, resume=False, **options):
        if not resume:
            self.reset_run()
        self._sync_held_keys()
        self.game.audio.play_music("game")
        self.game.audio.resume_music()

    def _sync_held_keys(self):
        """Read which keys are really held right now (keys may change while paused)."""
        pressed = pygame.key.get_pressed()
        self.held_jump_keys = {key for key in JUMP_KEYS if pressed[key]}
        self.held_slide_keys = {key for key in SLIDE_KEYS if pressed[key]}
        if not self.held_jump_keys:
            self.player.release_jump()

    # --- input ---------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in PAUSE_KEYS:
                self.game.change_state("paused")
            elif event.key in JUMP_KEYS:
                self.held_jump_keys.add(event.key)
                self.player.press_jump()
            elif event.key in SLIDE_KEYS:
                self.held_slide_keys.add(event.key)
                self.player.press_slide()
            elif event.key == pygame.K_F1:
                self.show_hitboxes = not self.show_hitboxes
        elif event.type == pygame.KEYUP:
            if event.key in JUMP_KEYS:
                self.held_jump_keys.discard(event.key)
                if not self.held_jump_keys:
                    self.player.release_jump()
            elif event.key in SLIDE_KEYS:
                self.held_slide_keys.discard(event.key)
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.game.change_state("paused")  # never lose a run because of alt-tab

    # --- update --------------------------------------------------------
    def update(self, dt):
        self.elapsed += dt
        # Smooth difficulty curve: rises quickly at first, then levels off.
        self.difficulty = 1.0 - math.exp(-self.elapsed / DIFFICULTY_TIME_CONSTANT)
        target_speed = START_SPEED + (MAX_SPEED - START_SPEED) * self.difficulty
        self.speed = min(target_speed, self.speed + START_ACCELERATION * dt)

        world = self.game.world
        world.update(dt, self.speed)
        self.spawner.update(dt, self.speed, self.difficulty, world.distance, self.obstacles)
        self._update_obstacles(dt)
        self.player.update(dt, self.speed, slide_held=bool(self.held_slide_keys))
        self._handle_player_events()
        self._emit_running_dust(dt)
        self.effects.update(dt)
        self._update_score(dt)
        self._check_collisions()

    def update_after_crash(self, dt):
        """Used by the game over screen: nothing scrolls, but the scene stays alive."""
        self.game.world.update(dt, 0)
        self._update_obstacles(dt)  # birds keep flying away
        self.player.update(dt)
        self._handle_player_events()
        self.effects.update(dt)

    def _update_obstacles(self, dt):
        distance = self.game.world.distance
        for obstacle in self.obstacles:
            obstacle.update(dt, distance)
        if any(obstacle.off_screen for obstacle in self.obstacles):
            self.obstacles = [obstacle for obstacle in self.obstacles if not obstacle.off_screen]

    def _handle_player_events(self):
        """Turn what the player did this frame into particles and sounds."""
        x, y = self.player.feet
        audio = self.game.audio
        for event in self.player.events:
            if event == "jump":
                self.effects.jump_dust(x, y)
                audio.play("jump")
            elif event == "double_jump":
                self.effects.double_jump(x, y - 4)
                audio.play("double_jump")
            elif event == "land":
                self.effects.land_dust(x, y, self.player.landing_strength)
                audio.play("land")
            elif event == "slide":
                self.effects.slide_dust(x + 4, y)
                audio.play("slide")

    def _emit_running_dust(self, dt):
        player = self.player
        if not (player.alive and player.on_ground and self.speed > 0):
            return
        self.dust_timer -= dt
        if self.dust_timer > 0:
            return
        x, y = player.feet
        if player.sliding:
            self.dust_timer = SLIDE_DUST_INTERVAL
            self.effects.slide_dust(x + 6, y - 1)
        else:
            self.dust_timer = RUN_DUST_INTERVAL * START_SPEED / self.speed  # more dust when faster
            self.effects.run_dust(x - 3, y - 1)

    def _update_score(self, dt):
        self.run_distance += self.speed * dt
        self.score = int(self.run_distance * SCORE_PER_PIXEL)
        self.milestone_timer = max(0.0, self.milestone_timer - dt)
        if self.score >= self.next_milestone:
            self.next_milestone += SCORE_MILESTONE
            self.milestone_timer = MILESTONE_FLASH_TIME
            self.effects.milestone(60, 14)
            self.game.audio.play("milestone")

    def _check_collisions(self):
        hitbox = self.player.hitbox
        for obstacle in self.obstacles:
            if hitbox.colliderect(obstacle.hitbox):
                self._crash(obstacle)
                return

    def _crash(self, obstacle):
        (px, py), (ox, oy) = self.player.hitbox.center, obstacle.hitbox.center
        self.player.die()
        self.effects.hit((px + ox) // 2, (py + oy) // 2, obstacle.data["debris"])  # burst at the contact point
        self.game.audio.play("hit")
        self.speed = 0.0
        self.game.change_state("game_over")

    # --- drawing -------------------------------------------------------
    def draw_scene(self, surface):
        """Draw the world, obstacles, player and particles (with screen shake)."""
        scene = self.scene
        world = self.game.world
        world.draw_back(scene)
        self.player.draw_shadow(scene)
        for obstacle in self.obstacles:
            obstacle.draw(scene)
        self.player.draw(scene)
        self.effects.particles.draw(scene)
        world.draw_front(scene)
        if self.show_hitboxes:
            pygame.draw.rect(scene, (0, 255, 0), self.player.hitbox, 1)
            for obstacle in self.obstacles:
                pygame.draw.rect(scene, (255, 0, 0), obstacle.hitbox, 1)

        # Screen shake: the finished scene is drawn slightly offset.
        offset = self.effects.shake.offset
        if offset != (0, 0):
            surface.fill(UI_SHADOW)
        surface.blit(scene, offset)
        self.effects.flash.draw(surface)

    def draw(self, surface):
        self.draw_scene(surface)
        ui = self.game.ui
        ui.hud(surface, self.score, self.game.high_score, self.milestone_timer > 0, self.elapsed)
        if self.elapsed < HINT_DURATION and (self.elapsed < HINT_DURATION - 1 or ui.blink(self.elapsed, 4)):
            ui.text(surface, "SPACE: JUMP    DOWN: SLIDE    ESC: PAUSE", (CENTER_X, GAME_HEIGHT - 22), UI_TEXT)


# ---------------------------------------------------------------------------
# Paused
# ---------------------------------------------------------------------------
class PausedState(State):
    def __init__(self, game):
        super().__init__(game)
        self.menu = MenuSelection(("RESUME", "RESTART", "MAIN MENU"))

    def enter(self, **options):
        self.menu.index = 0
        self.time = 0.0
        self.game.audio.pause_music()
        self.game.audio.play("pause")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in PAUSE_KEYS:
            self.game.change_state("playing", resume=True)
            return
        choice = self.menu.handle_key(event.key, self.game.audio)
        if choice == "RESUME":
            self.game.change_state("playing", resume=True)
        elif choice == "RESTART":
            self.game.submit_score(self.game.states["playing"].score)
            self.game.change_state("playing", fade=True)
        elif choice == "MAIN MENU":
            self.game.submit_score(self.game.states["playing"].score)
            self.game.change_state("menu", fade=True)

    def update(self, dt):
        self.time += dt  # the game itself is frozen while paused

    def draw(self, surface):
        ui = self.game.ui
        self.game.states["playing"].draw(surface)
        ui.dim(surface, 130)
        ui.panel(surface, (CENTER_X - 90, 62, 180, 140))
        ui.font.draw(surface, "PAUSED", (CENTER_X, 76), UI_HIGHLIGHT, 3, "center", outline=UI_SHADOW)
        ui.menu_options(surface, self.menu.options, self.menu.index, 138, self.time)
        ui.text(surface, "ESC: RESUME", (CENTER_X, 214), UI_MUTED)


# ---------------------------------------------------------------------------
# Game over
# ---------------------------------------------------------------------------
class GameOverState(State):
    def enter(self, **options):
        self.time = 0.0
        self.jingle_played = False
        self.score = self.game.states["playing"].score
        self.new_best = self.game.submit_score(self.score)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.time < GAME_OVER_INPUT_DELAY:
            return  # short delay so mashing SPACE while crashing doesn't skip this screen
        if event.key in CONFIRM_KEYS or event.key in JUMP_KEYS:
            self.game.audio.play("menu_select")
            self.game.change_state("playing", fade=True)
        elif event.key in BACK_KEYS:
            self.game.audio.play("menu_select")
            self.game.change_state("menu", fade=True)

    def update(self, dt):
        self.time += dt
        self.game.states["playing"].update_after_crash(dt)
        if not self.jingle_played and self.time >= GAME_OVER_PANEL_DELAY:
            self.jingle_played = True
            self.game.audio.play("game_over")

    def draw(self, surface):
        ui = self.game.ui
        playing = self.game.states["playing"]
        playing.draw_scene(surface)
        if self.time < GAME_OVER_PANEL_DELAY:
            ui.hud(surface, self.score, self.game.high_score, False, 0)
            return

        # The panel drops in from above.
        appear = min(1.0, (self.time - GAME_OVER_PANEL_DELAY) / 0.25)
        top = 46 - round((1.0 - appear) ** 2 * 40)
        ui.dim(surface, round(120 * appear))
        ui.panel(surface, (CENTER_X - 120, top, 240, 170))
        ui.font.draw(surface, "GAME OVER", (CENTER_X, top + 14), UI_DANGER, 3, "center", outline=UI_SHADOW)
        ui.text(surface, "SCORE: " + format_score(self.score), (CENTER_X, top + 48), UI_TEXT, 2)
        best_color = UI_HIGHLIGHT if self.new_best else UI_MUTED
        ui.text(surface, "BEST: " + format_score(self.game.high_score), (CENTER_X, top + 70), best_color, 2)
        if self.new_best and ui.blink(self.time, 3):
            ui.text(surface, "NEW BEST!", (CENTER_X, top + 92), UI_HIGHLIGHT)
        if self.time >= GAME_OVER_INPUT_DELAY:
            ui.text(surface, "PRESS SPACE TO RESTART", (CENTER_X, top + 120), UI_TEXT)
            ui.text(surface, "PRESS ESC FOR MENU", (CENTER_X, top + 140), UI_MUTED)
