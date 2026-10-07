"""
animation.py - a simple frame-based animation.

An Animation is a list of images (frames) plus a playback speed. It does not
care where the frames came from, so placeholder art and real PNG sprite
sheets work exactly the same way.
"""


class Animation:
    def __init__(self, frames, fps=10, loop=True):
        if not frames:
            raise ValueError("An animation needs at least one frame")
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.time = 0.0

    def reset(self):
        self.time = 0.0

    def update(self, dt, speed=1.0):
        """Advance the animation. speed > 1 plays it faster."""
        self.time += dt * speed

    @property
    def frame_index(self):
        index = int(self.time * self.fps)
        if self.loop:
            return index % len(self.frames)
        return min(index, len(self.frames) - 1)

    @property
    def finished(self):
        """True once a non-looping animation has played all of its frames."""
        return not self.loop and self.time * self.fps >= len(self.frames)

    @property
    def image(self):
        return self.frames[self.frame_index]
