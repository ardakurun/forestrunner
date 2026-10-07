# Forest Runner

A 2D pixel-art endless runner made with Python and Pygame. Run through the
forest, jump over rocks and stumps, slide under birds, and beat your best score.

## Running the game

```
pip install -r requirements.txt
python main.py
```

Requires Python 3.9+ and Pygame 2.

## Controls

| Key              | Action                                         |
|------------------|------------------------------------------------|
| SPACE (or UP, W) | Jump. Hold for a higher jump, tap for a hop    |
| SPACE in the air | Double jump                                    |
| DOWN or S        | Slide (hold to keep sliding)                   |
| DOWN in the air  | Drop down fast, then slide on landing          |
| ESC (or P)       | Pause / back                                   |
| F1               | Show collision boxes (handy when tuning)       |

## Project layout

| File                 | What it does                                                  |
|----------------------|---------------------------------------------------------------|
| `main.py`            | Starts the game                                               |
| `settings.py`        | **Every tunable number**: physics, speeds, obstacles, colors  |
| `game.py`            | Window, main loop, switching between screens                  |
| `states.py`          | The screens: menu, how to play, playing, paused, game over    |
| `player.py`          | Player movement, controls and animation states                |
| `animation.py`       | A simple frame animation class                                |
| `obstacle.py`        | Obstacles and the spawner that places them fairly             |
| `world.py`           | Parallax forest background and falling leaves                 |
| `effects.py`         | Particles, screen shake and screen flash                      |
| `ui.py`              | HUD, menus and wooden sign panels                             |
| `pixel_font.py`      | A built-in 5x7 pixel font (no font files needed)              |
| `audio.py`           | Sound effects and music (all optional)                        |
| `assets.py`          | Loads images and sprite strips, with caching                  |
| `save_data.py`       | Loads/saves the high score in `data/highscore.json`           |
| `placeholder_art.py` | Draws the temporary pixel art until real art is added         |

## Adding real art and sound

The game works without any asset files: missing images are drawn by
`placeholder_art.py` and missing sounds become small generated beeps. Drop
files into the `assets/` folders to replace them one at a time. Each folder
has a `README.txt` with the exact file names and sizes. For example:

- `assets/player/run.png`: a strip of 32 x 32 frames for the run animation
- `assets/obstacles/bird.png`: a strip of 20 px wide bird frames
- `assets/background/far_forest.png`: one parallax layer (480 x 270)
- `assets/sounds/jump.wav`, `assets/music/forest_theme.ogg`

## Tuning tips (all in `settings.py`)

- Bigger window: `WINDOW_SCALE = 3`
- Jump feel: `GRAVITY`, `JUMP_VELOCITY`, `DOUBLE_JUMP_VELOCITY`,
  `COYOTE_TIME`, `JUMP_BUFFER_TIME`, `SLIDE_DURATION`
- Difficulty: `START_SPEED`, `MAX_SPEED`, `DIFFICULTY_TIME_CONSTANT`
- New obstacle combinations: add an entry to `OBSTACLE_PATTERNS`. Spacing is
  in seconds, so a pattern that works at one speed works at every speed.
