---
name: decision-uv
description: uv chosen over poetry/pip as Python package manager. 10-100x faster, simpler syntax, Rust-based.
metadata:
  type: project
---

**Decision:** Use `uv` (from Astral) as the Python package manager.

**Why:**
- 10-100x faster than pip/poetry (Rust-based)
- Single tool for venv + dependency resolution + install + Python version management
- Simpler syntax: `uv add`, `uv run`, `uv sync` — no `poetry install --no-dev` ceremony
- No need to manually activate venv (`uv run` auto-activates)
- Becoming Python community standard 2025+
- User new to Python — fewer concepts to learn

**How to apply:**
- All Python commands prefixed with `uv run` in CI/scripts
- `pyproject.toml` declares deps under `[project]` and `[dependency-groups]`
- `.python-version` pins Python 3.12
- Never `pip install` directly — always `uv add <pkg>` then `uv sync`

**User's first uv exposure:** scaffolded by Claude in initial setup. Manual step required: install uv via PowerShell (`irm https://astral.sh/uv/install.ps1 | iex`).
