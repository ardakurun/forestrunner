"""
save_data.py - loading and saving the high score (data/highscore.json).

The file is only read once when the game starts and only written when a run
ends with a new record, never during gameplay.
"""
import json
import os

from settings import HIGHSCORE_FILE


def load_high_score(path=HIGHSCORE_FILE):
    """Return the saved high score, or 0 if the file is missing or broken."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return max(0, int(data.get("high_score", 0)))
    except (OSError, ValueError, TypeError, AttributeError):
        # Missing file, invalid JSON, wrong data type... just start from zero.
        return 0


def save_high_score(score, path=HIGHSCORE_FILE):
    """Write the high score to disk. Returns True if it worked."""
    data = {"high_score": int(score)}
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Write to a temporary file first and then swap it in, so a crash
        # in the middle of saving can never leave a half-written file.
        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
        os.replace(temp_path, path)
        return True
    except OSError:
        pass

    # Some synced folders (OneDrive, Dropbox) can briefly block the swap.
    # Fall back to writing the file directly.
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
        return True
    except OSError as error:
        print(f"[save_data] Could not save the high score: {error}")
        return False
