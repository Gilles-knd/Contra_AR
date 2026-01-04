# Repository Guidelines

## Project Structure & Module Organization
- Core loop and CLI entrypoints live in `main.py` (training/play modes). Shared constants and hyperparameters are centralized in `constants.py`.
- Game entities are in `entities/` (`player.py`, `enemy.py`, `bullet.py`), level layout helpers in `level/` (`static_level.py`, `obstacles.py`), and camera logic in `rendering/camera.py`.
- Checkpoints and telemetry: `agent.pkl` stores trained weights; `training_stats.json`, `training.png`, and `training_metrics.png` capture recent runs. Keep generated artifacts out of version control unless intentionally updating them.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` — create and enter a virtual environment.
- `pip install -r requirements.txt` — install runtime deps (`pygame`, `numpy`, `matplotlib`).
- `python main.py train 500 50` — train for 500 episodes, rendering every 50 (set render_every to 0 for faster headless runs).
- `python main.py play` — run a demo using `agent.pkl` if present; falls back to an untrained agent.
- `python main.py` — prints usage help; use this to confirm the CLI arguments.

## Coding Style & Naming Conventions
- Python 3; use 4-space indentation and keep line lengths readable (~100 cols).
- Prefer descriptive names matching domain terms (e.g., `reward_progress`, `player_bullets_shot`); keep constants in `constants.py`.
- Maintain modular separation: environment logic in `Environment`, entity-specific behavior within respective classes. Add brief, high-signal comments only where logic is non-obvious.
- When adding data files, use lowercase-with-underscores and keep them in the nearest relevant folder.

## Testing Guidelines
- No automated test suite yet; sanity-check changes with quick training runs (short episode counts) and a `play` pass to verify rendering, collisions, and reward signals.
- When adding tests, prefer `pytest`, name files `test_*.py`, and isolate heavy assets. Use small deterministic seeds for reproducible runs.
- If you change reward tuning or physics, update or regenerate `training_stats.json` and linked plots to reflect the new behavior.

## Commit & Pull Request Guidelines
- Commit messages should be imperative and scoped (e.g., `tune reward scaling`, `fix enemy spawn bounds`); keep bodies concise and explain rationale for tuning.
- Pull requests: describe intent, list behavioral changes, and call out impacts on training stability or performance. Include reproduction commands (`train`/`play` args) and note any updated artifacts.
- Link issues when relevant and add before/after screenshots or metric snippets if visuals or reward curves change.
