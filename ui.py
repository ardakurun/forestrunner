"""
ui.py - drawing helpers for text, panels, menus and the in-game HUD.

All UI is drawn on the same small canvas as the game, with the built-in
pixel font, so it matches the pixel-art style.
"""
import math

import pygame

from pixel_font import PixelFont
from settings import (GAME_HEIGHT, GAME_WIDTH, SCORE_DIGITS, UI_HIGHLIGHT,
                      UI_MUTED, UI_SHADOW, UI_TEXT, UI_TITLE, UI_TITLE_OUTLINE)

PANEL_BORDER = (44, 28, 22)
PANEL_WOOD = (104, 70, 44)
PANEL_WOOD_DARK = (88, 58, 36)
PANEL_WOOD_LIGHT = (142, 100, 62)
PANEL_NAIL = (206, 196, 172)


def format_score(score):
    return f"{int(score):0{SCORE_DIGITS}d}"


class UI:
    def __init__(self):
        self.font = PixelFont()
        self._panels = {}  # (width, height) -> pre-drawn panel image
        self._dim = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self._dim.fill((10, 16, 14))

    # ------------------------------------------------------------------
    # Basic building blocks
    # ------------------------------------------------------------------
    def text(self, surface, text, pos, color=UI_TEXT, scale=1, align="center", shadow=True):
        return self.font.draw(surface, text, pos, color, scale, align,
                              shadow=UI_SHADOW if shadow else None)

    def dim(self, surface, alpha=140):
        """Darken everything drawn so far (behind menus and panels)."""
        self._dim.set_alpha(alpha)
        surface.blit(self._dim, (0, 0))

    def panel(self, surface, rect):
        """A wooden sign. Pre-drawn once per size and then reused."""
        rect = pygame.Rect(rect)
        image = self._panels.get(rect.size)
        if image is None:
            image = self._make_panel(*rect.size)
            self._panels[rect.size] = image
        surface.blit(image, rect)

    @staticmethod
    def _make_panel(width, height):
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        # Dark frame with cut corners.
        image.fill(PANEL_BORDER, (1, 0, width - 2, height))
        image.fill(PANEL_BORDER, (0, 1, width, height - 2))
        image.fill(PANEL_WOOD, (2, 2, width - 4, height - 4))
        # Wooden planks.
        for y in range(14, height - 4, 14):
            image.fill(PANEL_WOOD_DARK, (2, y, width - 4, 1))
        image.fill(PANEL_WOOD_LIGHT, (2, 2, width - 4, 1))
        image.fill(PANEL_WOOD_DARK, (2, height - 3, width - 4, 1))
        # Nails in the corners.
        for x, y in ((4, 4), (width - 6, 4), (4, height - 6), (width - 6, height - 6)):
            image.fill(PANEL_NAIL, (x, y, 2, 2))
        return image

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------
    def title(self, surface, y, time):
        bob = round(math.sin(time * 2.0) * 2)
        self.font.draw(surface, "FOREST RUNNER", (GAME_WIDTH // 2, y + bob + 3), UI_SHADOW,
                       scale=4, align="center")
        self.font.draw(surface, "FOREST RUNNER", (GAME_WIDTH // 2, y + bob), UI_TITLE,
                       scale=4, align="center", outline=UI_TITLE_OUTLINE, outline_size=2)

    def menu_options(self, surface, options, selected, center_y, time, scale=2, spacing=22):
        """A vertical list of options; the selected one is highlighted with arrows."""
        top = center_y - (len(options) - 1) * spacing // 2
        for index, option in enumerate(options):
            y = top + index * spacing - self.font.height(scale) // 2
            if index == selected:
                rect = self.text(surface, option, (GAME_WIDTH // 2, y), UI_HIGHLIGHT, scale)
                wiggle = round(math.sin(time * 6) * 2)
                self.text(surface, ">", (rect.left - 10 - wiggle, y), UI_HIGHLIGHT, scale, "right")
                self.text(surface, "<", (rect.right + 10 + wiggle, y), UI_HIGHLIGHT, scale, "left")
            else:
                self.text(surface, option, (GAME_WIDTH // 2, y), UI_MUTED, scale)

    def blink(self, time, rate=2.0):
        """True for half of every blink cycle - handy for 'press a key' prompts."""
        return (time * rate) % 1.0 < 0.6

    # ------------------------------------------------------------------
    # In-game HUD
    # ------------------------------------------------------------------
    def hud(self, surface, score, best, flashing, time):
        score_color = UI_TEXT
        if flashing and int(time * 10) % 2 == 0:
            score_color = UI_HIGHLIGHT
        self.text(surface, "SCORE: " + format_score(score), (8, 6), score_color, 2, "left")

        if score > best:  # beating the record right now
            self.text(surface, "BEST: " + format_score(score), (GAME_WIDTH - 8, 8), UI_HIGHLIGHT, 1, "right")
        else:
            self.text(surface, "BEST: " + format_score(best), (GAME_WIDTH - 8, 8), UI_MUTED, 1, "right")
