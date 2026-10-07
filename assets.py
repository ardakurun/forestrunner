"""
assets.py - loading images from the assets folder.

Every function returns None when a file is missing, so the rest of the game
can fall back to placeholder art instead of crashing. Loaded images are
cached: asking for the same file twice never reads it from disk twice.

Note: images can only be loaded after the game window exists, because
convert_alpha() needs to know the screen's pixel format.
"""
import os
import re

import pygame

_image_cache = {}


def load_image(path):
    """Load a PNG with transparency. Returns None if it is missing or broken."""
    if path in _image_cache:
        return _image_cache[path]

    image = None
    if os.path.isfile(path):
        try:
            image = pygame.image.load(path).convert_alpha()
        except pygame.error as error:
            print(f"[assets] Could not load {path}: {error}")

    _image_cache[path] = image
    return image


def slice_strip(sheet, frame_width):
    """Cut a horizontal sprite strip into frames that are frame_width wide."""
    frame_height = sheet.get_height()
    count = max(1, sheet.get_width() // frame_width)
    return [
        sheet.subsurface((index * frame_width, 0, frame_width, frame_height)).copy()
        for index in range(count)
    ]


def _natural_key(text):
    """Sort 'run_2.png' before 'run_10.png'."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def load_frames(folder, name, frame_width):
    """
    Load the animation frames called `name` from `folder`.

    Two layouts are supported:
      1. folder/name.png    - a horizontal strip with frames frame_width wide
      2. folder/name/*.png  - one PNG per frame, sorted by file name
    Returns a list of Surfaces, or None if neither exists.
    """
    strip = load_image(os.path.join(folder, name + ".png"))
    if strip is not None:
        return slice_strip(strip, frame_width)

    frame_dir = os.path.join(folder, name)
    if os.path.isdir(frame_dir):
        files = sorted(
            (f for f in os.listdir(frame_dir) if f.lower().endswith(".png")),
            key=_natural_key,
        )
        frames = [load_image(os.path.join(frame_dir, f)) for f in files]
        frames = [frame for frame in frames if frame is not None]
        if frames:
            return frames

    return None
