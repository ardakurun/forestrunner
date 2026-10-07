BACKGROUND ART
==============
Each parallax layer can be replaced by a PNG with the layer's name:

  sky.png, clouds.png, far_forest.png, mid_trees.png, light_rays.png,
  near_trees.png, bushes.png, ground.png, foreground_plants.png, canopy.png

A PNG layer is drawn at the top of the screen and repeated sideways, so
make it 270 px tall (the game's canvas height, GAME_HEIGHT) and at least
480 px wide, with transparency where the layers behind should show.
The left and right edges should line up so the image tiles seamlessly.

Scroll speed and drawing order: BACKGROUND_LAYERS in settings.py.
