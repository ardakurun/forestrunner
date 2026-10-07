"""
audio.py - sound effects and music.

Audio files are optional:
  * Sound effects: the game looks for assets/sounds/<name>.ogg / .wav / .mp3
    for every name in SOUND_NAMES. Missing ones are replaced by small
    generated retro beeps (turn this off with USE_PLACEHOLDER_SOUNDS).
  * Music: assets/music/<file>.ogg / .wav / .mp3, see MUSIC_TRACKS in
    settings.py. Without a file there is simply no music.
If the computer has no audio device, the game runs silently.
"""
import array
import os
import random

import pygame

from settings import (AUDIO_EXTENSIONS, MUSIC_DIR, MUSIC_TRACKS, MUSIC_VOLUME,
                      SFX_VOLUME, SOUNDS_DIR, USE_PLACEHOLDER_SOUNDS)

SOUND_NAMES = ("jump", "double_jump", "slide", "land", "hit", "game_over",
               "menu_move", "menu_select", "milestone", "pause")

# Placeholder sound recipes: segments played one after another.
# (waveform, start pitch Hz, end pitch Hz, seconds, volume 0..1)
PLACEHOLDER_RECIPES = {
    "jump": [("square", 300, 620, 0.10, 0.25)],
    "double_jump": [("square", 520, 980, 0.06, 0.22), ("square", 700, 1300, 0.08, 0.2)],
    "slide": [("noise", 0, 0, 0.16, 0.22)],
    "land": [("triangle", 170, 60, 0.07, 0.6)],
    "hit": [("noise", 0, 0, 0.10, 0.45), ("square", 220, 55, 0.24, 0.3)],
    "game_over": [("triangle", 392, 392, 0.13, 0.45), ("triangle", 330, 330, 0.13, 0.45),
                  ("triangle", 262, 196, 0.35, 0.45)],
    "menu_move": [("square", 660, 660, 0.035, 0.15)],
    "menu_select": [("square", 660, 660, 0.05, 0.18), ("square", 990, 990, 0.09, 0.18)],
    "milestone": [("square", 523, 523, 0.05, 0.16), ("square", 659, 659, 0.05, 0.16),
                  ("square", 784, 784, 0.05, 0.16), ("square", 1046, 1046, 0.1, 0.16)],
    "pause": [("square", 880, 440, 0.06, 0.14)],
}


def _find_file(folder, name):
    for extension in AUDIO_EXTENSIONS:
        path = os.path.join(folder, name + extension)
        if os.path.isfile(path):
            return path
    return None


def _synthesize(recipe, rate):
    """Turn a recipe into a list of 16-bit samples."""
    rng = random.Random(1)
    samples = []
    for wave, start_hz, end_hz, seconds, volume in recipe:
        count = max(1, int(seconds * rate))
        attack = max(1, int(0.003 * rate))  # a tiny fade-in avoids clicks
        phase = 0.0
        noise = 0.0
        for i in range(count):
            t = i / count
            phase += (start_hz + (end_hz - start_hz) * t) / rate
            if wave == "square":
                value = 1.0 if phase % 1.0 < 0.5 else -1.0
            elif wave == "triangle":
                value = 4.0 * abs(phase % 1.0 - 0.5) - 1.0
            else:  # softened noise
                noise = noise * 0.55 + rng.uniform(-1.0, 1.0) * 0.45
                value = noise * 1.8
            envelope = min(1.0, i / attack) * (1.0 - t) ** 1.5
            samples.append(int(max(-1.0, min(1.0, value * envelope * volume)) * 32767))
    return samples


def _make_placeholder_sound(name):
    recipe = PLACEHOLDER_RECIPES.get(name)
    mixer_info = pygame.mixer.get_init()
    if recipe is None or mixer_info is None:
        return None
    rate, sample_format, channels = mixer_info
    if sample_format != -16:  # only signed 16-bit output is supported here
        return None
    samples = _synthesize(recipe, rate)
    if channels > 1:  # duplicate every sample for each speaker
        samples = [s for s in samples for _ in range(channels)]
    return pygame.mixer.Sound(buffer=array.array("h", samples).tobytes())


class AudioManager:
    def __init__(self):
        self.enabled = pygame.mixer.get_init() is not None
        self.sounds = {}
        self.current_music = None
        if not self.enabled:
            print("[audio] No audio device available - the game will be silent.")
            return
        for name in SOUND_NAMES:
            sound = self._load_sound(name)
            if sound is not None:
                sound.set_volume(SFX_VOLUME)
                self.sounds[name] = sound

    @staticmethod
    def _load_sound(name):
        path = _find_file(SOUNDS_DIR, name)
        if path is not None:
            try:
                return pygame.mixer.Sound(path)
            except pygame.error as error:
                print(f"[audio] Could not load {path}: {error}")
        if USE_PLACEHOLDER_SOUNDS:
            return _make_placeholder_sound(name)
        return None

    def play(self, name):
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def play_music(self, track):
        """Loop a music track from MUSIC_TRACKS. Silently does nothing if the file is missing."""
        if not self.enabled or track == self.current_music:
            return
        self.current_music = track
        path = _find_file(MUSIC_DIR, MUSIC_TRACKS.get(track, track))
        if path is None:
            pygame.mixer.music.fadeout(400)
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1, fade_ms=800)
        except pygame.error as error:
            print(f"[audio] Could not play {path}: {error}")

    def pause_music(self):
        if self.enabled:
            pygame.mixer.music.pause()

    def resume_music(self):
        if self.enabled:
            pygame.mixer.music.unpause()
