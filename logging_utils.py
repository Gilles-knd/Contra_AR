"""Logging utilities for training statistics."""

import json
import os


def append_training_log(entry, path="training_stats.json"):
    """Append a training summary entry to JSON log."""
    data = []
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        except Exception:
            data = []

    data.append(entry)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
