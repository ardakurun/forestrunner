"""
game.py - the Game class: creates the window, runs the main loop and
switches between the states (menu, playing, paused, ...).

Everything is drawn on a small canvas (GAME_WIDTH x GAME_HEIGHT) that is
scaled up to the window at the end of each frame. That gives sharp, chunky
pixels and keeps drawing fast, even on slow computers.
"""
import os

import pygame

from audio import AudioManager
from player import load_player_frames
from save_data import load_high_score, save_high_score
from settings import FADE_TIME, FPS, GAME_HEIGHT, GAME_WIDTH, MAX_DT, TITLE, WINDOW_SCALE
from states import GameOverState, HowToPlayState, MenuState, PausedState, PlayingState
from ui import UI
from world import World


def pick_window_scale():
    """WINDOW_SCALE from settings, or (if it is 0) the biggest whole-number scale that fits the screen."""
    if WINDOW_SCALE > 0:
        return WINDOW_SCALE
    desktops = pygame.display.get_desktop_sizes()
    if not desktops:
        return 2
    desktop_width, desktop_height = desktops[0]
    # Leave room for the taskbar and the window's title bar.
    return max(1, min(int(desktop_width * 0.9) // GAME_WIDTH, int(desktop_height * 0.85) // GAME_HEIGHT))


class Game:
    def __init__(self):
        # Without this, Windows display scaling (like 125%) stretches the window and blurs the pixels.
        os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")
        pygame.mixer.pre_init(44100, -16, 2, 512)  # small buffer: sounds play without delay
        pygame.init()
        scale = pick_window_scale()
        self.window = pygame.display.set_mode((GAME_WIDTH * scale, GAME_HEIGHT * scale))
        pygame.display.set_caption(TITLE)
        self.canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = False

        # Shared by all states. Images can only be loaded once the window exists.
        self.high_score = load_high_score()
        self.audio = AudioManager()
        self.ui = UI()
        self.world = World()
        pygame.display.set_icon(load_player_frames()["idle"][0])

        self.states = {
            "menu": MenuState(self),
            "how_to_play": HowToPlayState(self),
            "playing": PlayingState(self),
            "paused": PausedState(self),
            "game_over": GameOverState(self),
        }
        self.state = None
        self.fade_timer = 0.0
        self._fade_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.change_state("menu")

    # ------------------------------------------------------------------
    # States and score
    # ------------------------------------------------------------------
    def change_state(self, name, fade=False, **options):
        """Switch to another state. fade=True fades the new screen in from black."""
        self.state = self.states[name]
        self.state.enter(**options)
        if fade:
            self.fade_timer = FADE_TIME

    def submit_score(self, score):
        """Save the score if it beats the high score. Returns True for a new record."""
        if score <= self.high_score:
            return False
        self.high_score = score
        save_high_score(score)
        return True

    def quit(self):
        # Closing the game in the middle of a run still counts for the high score.
        if self.state in (self.states["playing"], self.states["paused"]):
            self.submit_score(self.states["playing"].score)
        self.running = False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        self.running = True
        while self.running:
            # Seconds since the last frame, capped so a hiccup can't break the physics.
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_DT)
            self.step(dt)
        pygame.quit()

    def step(self, dt):
        """One frame: handle input, update the current state, draw it."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            else:
                self.state.handle_event(event)

        self.state.update(dt)
        self.fade_timer = max(0.0, self.fade_timer - dt)

        self.state.draw(self.canvas)
        if self.fade_timer > 0:
            self._fade_surface.set_alpha(round(255 * self.fade_timer / FADE_TIME))
            self.canvas.blit(self._fade_surface, (0, 0))
        pygame.transform.scale(self.canvas, self.window.get_size(), self.window)
        pygame.display.flip()
