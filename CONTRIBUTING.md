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
uv sync           # Creates .venv and installs all deps (including dev)
```

### Verify

```bash
uv run pytest                          # All tests should pass
uv run streamlit run app/Home.py       # App opens on :8501
```

## Daily Workflow

```bash
# Start app in dev mode (auto-reload)
uv run streamlit run app/Home.py

# Run a specific test
uv run pytest tests/unit/test_models.py::test_transition_matrix_sums_to_one

# Lint + format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy core/ domains/

# Run notebook
uv run jupyter lab notebooks/
```

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

# Just unit tests (fast)
uv run pytest tests/unit/

# Just integration tests (requires DuckDB)
uv run pytest tests/integration/ -m integration

# With coverage
uv run pytest --cov=core --cov=domains --cov-report=html
```

Aim for >80% coverage on `core/`. UI code (`app/`) is hard to unit test — manual QA via the app is fine.

## Questions?

Open an issue on GitHub.
