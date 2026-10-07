"""
pixel_font.py - a tiny built-in 5x7 pixel font.

Every character is drawn from the little pictures below ('#' = filled pixel),
so the game needs no font files and text always matches the pixel-art style.
Glyph images are cached per (character, color, scale), so drawing text every
frame (like the score) does not create new images.
"""
import pygame

GLYPH_HEIGHT = 7

GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": ("...", "...", "...", "...", "...", "...", "..."),
    ".": (".", ".", ".", ".", ".", ".", "#"),
    ",": ("..", "..", "..", "..", "..", ".#", "#."),
    ":": (".", ".", "#", ".", ".", "#", "."),
    "!": ("#", "#", "#", "#", "#", ".", "#"),
    "'": ("#", "#", ".", ".", ".", ".", "."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": ("...", "...", "...", "###", "...", "...", "..."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "=": ("....", "....", "####", "....", "####", "....", "...."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("..#", ".#.", "#..", "#..", "#..", ".#.", "..#"),
    ")": ("#..", ".#.", "..#", "..#", "..#", ".#.", "#.."),
    "<": ("...#", "..#.", ".#..", "#...", ".#..", "..#.", "...#"),
    ">": ("#...", ".#..", "..#.", "...#", "..#.", ".#..", "#..."),
    "%": ("##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
}
UNKNOWN_GLYPH = GLYPHS["?"]


class PixelFont:
    def __init__(self):
        self._cache = {}

    def _glyph(self, char, color, scale):
        key = (char, color, scale)
        image = self._cache.get(key)
        if image is None:
            rows = GLYPHS.get(char, UNKNOWN_GLYPH)
            image = pygame.Surface((len(rows[0]) * scale, GLYPH_HEIGHT * scale), pygame.SRCALPHA)
            for y, row in enumerate(rows):
                for x, pixel in enumerate(row):
                    if pixel == "#":
                        image.fill(color, (x * scale, y * scale, scale, scale))
            self._cache[key] = image
        return image

    @staticmethod
    def height(scale=1):
        return GLYPH_HEIGHT * scale

    def width(self, text, scale=1):
        """Width in pixels of text drawn at this scale (1 pixel gap between letters)."""
        text = text.upper()
        if not text:
            return 0
        total = sum(len(GLYPHS.get(char, UNKNOWN_GLYPH)[0]) for char in text)
        return (total + len(text) - 1) * scale

    def _draw_plain(self, surface, text, x, y, color, scale):
        for char in text:
            glyph = self._glyph(char, color, scale)
            surface.blit(glyph, (x, y))
            x += glyph.get_width() + scale

    def draw(self, surface, text, pos, color, scale=1, align="left",
             shadow=None, outline=None, outline_size=1):
        """
        Draw text and return its rectangle.

        pos is (x, top). align decides what x means: "left", "center" or "right".
        shadow / outline are optional colors for readability on busy backgrounds.
        """
        text = text.upper()
        width = self.width(text, scale)
        x, y = pos
        if align == "center":
            x -= width // 2
        elif align == "right":
            x -= width

        if outline is not None:
            size = outline_size
            for dx in (-size, 0, size):
                for dy in (-size, 0, size):
                    if dx or dy:
                        self._draw_plain(surface, text, x + dx, y + dy, outline, scale)
        if shadow is not None:
            offset = max(1, scale // 2)
            self._draw_plain(surface, text, x + offset, y + offset, shadow, scale)
        self._draw_plain(surface, text, x, y, color, scale)
        return pygame.Rect(x, y, width, GLYPH_HEIGHT * scale)
