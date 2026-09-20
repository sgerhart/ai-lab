# Updating Python dependencies

**Prerequisites:** uv. Project directory with `pyproject.toml`.

**Effects:** Changes lockfile and venv.

**Steps:** `cd platform && uv lock && uv sync` (or mlx/training/evaluations). Commit `uv.lock` when it exists. Do not `pip install --user`.

**Verify:** `python3 -m unittest discover -s tests -v` from repo root.

**Rollback:** `git checkout -- uv.lock && uv sync --frozen`.
