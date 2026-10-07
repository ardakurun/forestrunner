PLAYER ART
==========
Drop PNG files here to replace the placeholder runner. Anything missing
keeps using the placeholder, so you can replace one animation at a time.

Animation names: idle, run, jump, double_jump, fall, slide, hurt

Two layouts work for every animation:
  1. run.png        - a horizontal strip of frames, each 32 px wide
                      (frame size: PLAYER_FRAME_SIZE in settings.py)
  2. run/           - a folder with one PNG per frame
                      (run_0.png, run_1.png, ... sorted by name)

Frames are drawn with their bottom-center at the player's feet, so leave the
character's feet on the bottom row of each frame. The character faces right.
Speed and looping of each animation: PLAYER_ANIMATIONS in settings.py.
