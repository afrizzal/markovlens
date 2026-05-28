# Directory Structure

**Analysis Date:** 2026-05-29

## Top-Level Layout

```
markovlens/
├── app/                    # Streamlit UI (side effects only)
├── core/                   # Domain-agnostic Markov engine
├── domains/                # Domain-specific orchestration
├── data/                   # DuckDB + raw data (gitignored)
├── tests/                  # pytest suite
├── scripts/                # One-off data scripts
├── docs/                   # Reference documentation
├── notebooks/              # Jupyter exploration (gitignored from lint)
├── reports/                # Generated PDF/CSV output (gitignored from lint)
├── .claude/                # Claude Code config (rules, skills, memory)
├── .planning/              # GSD workflow artifacts (being created now)
├── .streamlit/             # Streamlit server config
├── .venv/                  # Python virtual environment (gitignored)
├── pyproject.toml          # Project metadata + all tool config
├── uv.lock                 # Locked dependency manifest
├── .env.example            # Environment variable template
├── CLAUDE.md               # Claude Code session instructions
└── README.md               # Project overview
```

## Source Code

### `app/`
```
app/
├── Home.py                 # Streamlit root — dashboard + KPIs
├── __init__.py
├── pages/                  # Multi-page app (numeric prefix = sidebar order)
│   ├── 1_Brand_Share.py    # (planned — not yet created)
│   ├── 2_Churn.py          # (planned)
│   ├── 3_Reports.py        # (planned)
│   └── 4_Settings.py       # (planned)
├── components/             # Reusable Streamlit components
│   ├── __init__.py
│   ├── kpi_card.py         # KPI metric card with sparkline
│   ├── empty_state.py      # Empty data fallback UI
│   └── section_header.py   # Page section header
└── styles/
    ├── __init__.py
    └── theme.css           # Custom CSS (injected via st.markdown)
                            # plotly_theme.py — planned, not yet created
```

### `core/`
```
core/
├── __init__.py
├── config.py               # Pydantic-Settings (reads .env)
├── exceptions.py           # InvalidTransitionMatrixError + domain exceptions
├── models.py               # M1Homogeneous, M2TimeVarying, M3Extended + validate_transition_matrix()
├── simulation.py           # monte_carlo_simulate(), calibrate_probability(), LONGSHOT_CALIBRATION
├── metrics.py              # MAPE, Brier, log-loss (stub — not yet implemented)
├── db/
│   ├── __init__.py
│   ├── connection.py       # DuckDB singleton (get_connection())
│   ├── schema.sql          # Idempotent CREATE TABLE IF NOT EXISTS (6 tables)
│   └── queries.py          # All SQL wrapped here
└── io/
    ├── __init__.py
    └── loaders.py          # CSV/Parquet → DataFrame loading
```

### `domains/`
```
domains/
├── __init__.py
├── brand_share/
│   ├── __init__.py
│   └── service.py          # Brand share orchestration (stub)
└── churn/
    ├── __init__.py
    └── service.py          # Churn modelling orchestration (stub)
```

### `tests/`
```
tests/
├── __init__.py
├── conftest.py             # Shared fixtures: sample_2x2_matrix, sample_4x4_chan_matrix, temp_duckdb_path
├── unit/
│   ├── __init__.py
│   └── test_models.py      # Unit tests for core/models.py (skipped — Phase 01 pending)
└── integration/
    └── __init__.py         # (empty — integration tests not yet written)
```

## Data Directory (gitignored)

```
data/
├── markovlens.duckdb       # Main DB (gitignored, regenerable)
├── markovlens.duckdb.wal   # Write-ahead log (gitignored)
├── raw/                    # Original Kaggle CSVs (gitignored)
│   ├── ecommerce_brand_share.csv
│   └── telco_churn.csv
├── processed/              # Cleaned Parquet (gitignored)
└── cache/                  # Computed matrix/simulation snapshots (gitignored)
```

## Configuration Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Dependencies, ruff, mypy, pytest, project metadata |
| `uv.lock` | Locked dependency versions (committed) |
| `.env.example` | Env var template (committed; `.env` is gitignored) |
| `.streamlit/config.toml` | Streamlit UI/server settings (primary color: #4338CA) |
| `.python-version` | `3.12` — pinned for uv |
| `.gitignore` | Excludes: `.venv/`, `data/`, `*.duckdb`, `__pycache__/` |

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Source files | `snake_case.py` | `transition_matrix.py` |
| Streamlit pages | `N_PascalCase.py` (numeric prefix) | `1_Brand_Share.py` |
| Test files | `test_<module>.py` | `test_models.py` |
| DB tables | `snake_case` plural | `transition_matrices` |
| CSS classes | `kebab-case` | `kpi-card` |

## Key Locations (Quick Reference)

| What | Where |
|---|---|
| App entry point | `app/Home.py` |
| DB schema | `core/db/schema.sql` |
| DB connection | `core/db/connection.py` |
| All SQL | `core/db/queries.py` |
| Markov models | `core/models.py` |
| Monte Carlo | `core/simulation.py` |
| Calibration table | `core/simulation.py:LONGSHOT_CALIBRATION` |
| Config/env vars | `core/config.py` |
| Domain exceptions | `core/exceptions.py` |
| Test fixtures | `tests/conftest.py` |
| Style variables | `app/styles/theme.css` |
| Project rules | `.claude/rules/` |
| Claude session docs | `CLAUDE.md` |
