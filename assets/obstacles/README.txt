OBSTACLE ART
============
Drop PNG files here to replace the placeholder obstacles:

  rock.png, stump.png, big_stump.png, bird.png

A file can be a single image or a horizontal strip of animation frames.
The frame width is the "size" width of that obstacle in OBSTACLE_TYPES
(settings.py), e.g. bird.png with 4 frames of 20 px = an 80 px wide strip.
A folder (bird/ with bird_0.png, bird_1.png, ...) works too.

The image is centered on the obstacle's collision box. If you change how
big an obstacle looks, also adjust its "hitbox" in settings.py
(press F1 while playing to see the collision boxes).
