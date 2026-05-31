# Contributing to MarkovLens

Thanks for your interest. This project is primarily a portfolio piece, but contributions are welcome.

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Install uv (Windows PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install uv (macOS / Linux)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone and install

```bash
git clone https://github.com/afrizzal/markovlens.git
cd markovlens
uv sync                                # Creates .venv and installs all deps (including dev)
uv run python scripts/seed_data.py     # Populate DuckDB with reference data (idempotent)
```

### Verify

```bash
uv run pytest                          # All tests should pass (81 tests, ~15s)
uv run streamlit run app/Home.py       # App opens on http://localhost:8501
```

Navigate to **Brand Share** → click **Run Forecast**, then **Customer Churn** → click **Run Analysis**, to confirm both domains end-to-end.

### Required reading before significant changes

| File | Why |
|---|---|
| [docs/planning/master-plan.md](docs/planning/master-plan.md) | Vision, architecture, agreed-upon patterns |
| [docs/planning/decisions.md](docs/planning/decisions.md) | ADR log — explains non-obvious patterns (sys.path hack, ruff exemptions, schema choices). **Check here before "fixing" something that looks unusual.** |
| [docs/MARKOV-MODELS.md](docs/MARKOV-MODELS.md) | Mathematical foundation (Chan 2015 m1/m2/m3) |
| [.claude/rules/](.claude/rules/) | Detailed conventions split by concern (python, markov, streamlit, data, etc.) |

## Daily Workflow

```bash
# Start app in dev mode (auto-reload on file save)
uv run streamlit run app/Home.py

# Re-seed DB if you've changed seed_data.py or want a clean state (idempotent)
uv run python scripts/seed_data.py

# Run a specific test
uv run pytest tests/unit/test_models.py::test_m1_forecast_replicates_chan_2015_table3

# Lint + format
uv run ruff check .          # Catches style + naming + import-order issues
uv run ruff check . --fix    # Auto-fix what's fixable
uv run ruff format .

# Type check (strict on core/ and domains/)
uv run mypy core/ domains/

# Run notebook
uv run jupyter lab notebooks/
```

## Adding a New Streamlit Page

Streamlit auto-discovers pages from `app/pages/` with the filename pattern `N_Title_Case.py` (N controls sidebar order). When adding a new page, **the file MUST start with the sys.path prelude** documented in [docs/planning/decisions.md](docs/planning/decisions.md) `2026-05-31 — sys.path manipulation`:

```python
"""<Page Title> page for MarkovLens."""
from __future__ import annotations

# stdlib
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from app.X`, `from core.X`, `from domains.X` resolve.
# Streamlit adds the entry-script dir (app/) to sys.path, not the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# third-party
import numpy as np  # noqa: E402
import streamlit as st  # noqa: E402

st.set_page_config(
    page_title="<Title> — MarkovLens",
    page_icon="🔢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# local
from app.components.empty_state import empty_state  # noqa: E402
from app.styles import inject_theme, register_theme  # noqa: E402
```

Without this prelude, the page will crash with `ModuleNotFoundError: No module named 'app'` at runtime even though pytest passes (pytest uses project root as rootdir; Streamlit does not).

## Architectural Boundaries

The codebase uses a strict layered design enforced by code review and an importability test:

```
app/        # Streamlit UI only — no Markov math, no DB writes
  └─ calls →
domains/    # Orchestration — calls core/, returns NumPy-only dataclasses
  └─ calls →
core/       # Pure engine — no Streamlit, no Plotly imports
  └─ reads/writes →
data/markovlens.duckdb
```

**Enforcement check** (run before raising a PR that touches `core/` or `domains/`):

```bash
uv run python -c "from domains.brand_share.service import run_forecast; print('boundary ok')"
```

If this import fails because of an indirect `import streamlit` or `import plotly`, a layer has been violated. Move chart construction to `app/components/` and have the service return raw NumPy arrays + a typed dataclass instead.

## Frontend Work — Design Reference

UI changes consume `docs/design-reference/` as the visual contract:

- **`markov.css`** — design tokens (colors, typography scale, spacing). Port these into `app/styles/theme.css`, do not invent new tokens.
- **`components/*.jsx`** — component patterns from the Claude Design prototype. Translate to Streamlit-native equivalents in `app/components/`.
- **`screenshots/*.png`** — visual ground truth. New UI work should match these or document a justified deviation in `docs/planning/decisions.md`.

Do not start visual work by inventing colors or typography — extract them first.

## Project Structure

See [README.md](README.md#project-structure).

## Branching

- `master` — production-ready, deployable to Streamlit Cloud
- `feature/<short-name>` — new feature work
- `fix/<short-name>` — bug fixes
- `docs/<short-name>` — docs-only changes

## Commit Style

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add monte carlo confidence band calculation
fix: handle empty transition matrix in m2 model
docs: clarify calibration table source
refactor: extract simulation runner from m1 model
test: add walk-forward validation tests
chore: bump streamlit to 1.41
```

Atomic — one logical change per commit. Use `rtk git commit` for token-optimized output if working with Claude Code.

## Pull Request Process

1. Branch off `master`
2. Make changes — keep PR focused (one concern per PR)
3. Run full check before push:
   ```bash
   uv run ruff check . && uv run mypy core/ domains/ && uv run pytest
   ```
4. Update relevant docs:
   - `README.md` if user-visible feature
   - `manual-book.md` if workflow changed
   - `docs/planning/task-progress.md` if task completed
   - `docs/planning/decisions.md` if architecture decision made
5. Open PR with clear description (what + why)

## Code Style

See [.claude/rules/coding-style.md](.claude/rules/coding-style.md) and [.claude/rules/python-conventions.md](.claude/rules/python-conventions.md) for full conventions.

Key points:
- Type hints everywhere
- No magic numbers — module-level constants
- Pure functions in `core/`, side effects in `app/`
- Docstrings on public API (NumPy style)
- No comments explaining WHAT — code should be self-documenting

## Testing

```bash
# All tests
uv run pytest

# Just unit tests (fast, no DuckDB)
uv run pytest tests/unit/

# Just integration tests (real temp DuckDB via tmp_path fixture)
uv run pytest tests/integration/ -m integration

# With coverage — required gates: core/ ≥ 80%, domains/ ≥ 60%
uv run pytest --cov=core --cov=domains --cov-report=html
uv run pytest --cov=core --cov=domains --cov-fail-under=60

# Specific test (descriptive names — pick by intent, not file path)
uv run pytest -k "chan_2015" -v
uv run pytest -k "monte_carlo and reproducible" -v
```

### Coverage gates

| Layer | Floor | Current |
|---|---|---|
| `core/` | 80% | ~92% |
| `domains/brand_share/` | 60% | ~81% |
| `domains/churn/` | 60% | ~86% |
| `app/` | No floor — manually QA'd | — |

### Pytest temp directory

Pytest is configured (via `pyproject.toml` `addopts`) to use `.pytest_tmp/` at the project root instead of `%TEMP%`. This avoids Windows permission errors caused by antivirus or stale temp files. The directory is gitignored. **Do not change this without understanding the rationale** — see `docs/planning/decisions.md`.

## Questions?

Open an issue on GitHub.
