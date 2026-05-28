# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Planning & Documentation

**Always read these files before starting any project work:**

1. [docs/planning/master-plan.md](docs/planning/master-plan.md) — vision, architecture, agreed-upon patterns
2. [docs/planning/task-progress.md](docs/planning/task-progress.md) — current task status (Done/Pending/Blocked)
3. [docs/planning/decisions.md](docs/planning/decisions.md) — technical decisions log (ADR-style)
4. [.claude/memory/MEMORY.md](.claude/memory/MEMORY.md) — cross-session knowledge index

**After coding, always update:**
- `docs/planning/task-progress.md` — move tasks to Done, record commit hash
- `docs/planning/decisions.md` — if any new technical decision was made
- `CLAUDE.md` — if a new feature or page was added (App Pages table below)
- `README.md` — if a user-visible change was shipped
- `manual-book.md` — if user workflow changed

**Planning folder rules:**
- `.planning/` is owned by the GSD workflow system — do NOT manually edit `STATE.md`, `PROJECT.md`, `ROADMAP.md`, or `phases/**`
- All new planning notes belong in `docs/planning/`
- If unsure: drop into `docs/planning/archive/temp-review/`

---

## What This Is

**MarkovLens** — A multi-domain forecasting workbench that applies Markov chain models (m1 homogeneous, m2 time-varying, m3 extended time-varying) to two real business problems: **brand market share forecasting** and **customer churn state modelling**.

Built as a portfolio piece demonstrating applied probability + Python data product engineering for a BA/BI role.

## How to Run

```bash
# Install dependencies (first time only)
uv sync

# Run Streamlit app
uv run streamlit run app/Home.py
# Opens http://localhost:8501

# Run tests
uv run pytest

# Lint + format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy core/ domains/
```

Required environment variables (copy `.env.example` to `.env`):
- `DUCKDB_PATH` — path to DuckDB file (default: `data/markovlens.duckdb`)
- `APP_ENV` — `development` | `production`
- `DEFAULT_RANDOM_SEED` — for reproducible Monte Carlo (default: `42`)

---

## Tech Stack

- **Python 3.12** (managed via `uv`)
- **Streamlit** + `streamlit-shadcn-ui` + `streamlit-extras` — Web UI
- **NumPy + Pandas + SciPy + scikit-learn** — Numerical computing
- **DuckDB** — Embedded analytical database (file-based, no server)
- **Plotly** — Interactive visualizations (transition matrix heatmaps, Monte Carlo fan charts, Sankey)
- **ReportLab** — PDF report generation
- **pytest** — Testing
- **ruff + mypy** — Linting + type checking

---

## Data Layer

All persistent data lives in **DuckDB** (`data/markovlens.duckdb`). See [docs/DATABASE.md](docs/DATABASE.md) for full schema.

**Core tables:**
- `datasets` — registered datasets (domain, source, metadata)
- `transitions` — raw transition observations (long format)
- `transition_matrices` — computed + cached matrices per (dataset, model_type, period)
- `simulation_runs` — Monte Carlo result cache
- `forecasts` — forecast outputs with accuracy metrics
- `scenarios` — saved what-if scenarios

**Rules:**
- All DB access via `core/db/connection.py` (singleton)
- No raw SQL strings scattered in app code — wrap in `core/db/queries.py`
- Use DuckDB's native Parquet/CSV reading for raw data ingestion
- Migrations: simple `if not exists` in `core/db/schema.sql` (no Alembic — overkill)

---

## App Pages

| Page | Path | Description |
|---|---|---|
| Home | `/` | Dashboard with KPIs, recent forecasts, quick actions |
| Brand Share | `/Brand_Share` | Market share forecasting (3 models) + transition matrix explorer + Monte Carlo |
| Customer Churn | `/Churn` | State-based churn modelling (Sankey flow + what-if simulator) |
| Reports | `/Reports` | Report builder + PDF/CSV/notebook export |
| Settings | `/Settings` | Dataset management, theme, preferences |

---

## Markov Engine

The core engine in `core/` is **domain-agnostic** and implements the four model formulations from Chan (2015):

| Model | Formula | Use case |
|---|---|---|
| **m1** | `Y_{t+1} = Y_t · P` (constant P) | Stable markets |
| **m2** | `Y_{t+1} = Y_t · P_t` (time-varying P) | Dynamic / growing markets |
| **m3** | `Q_{t+1} = G ⊙ Q_t · P_t` (with growth multiplier) | Markets with size changes |
| **m4** | Non-Markov, category-based | Future (deferred to v0.2) |

Plus Monte Carlo simulation with longshot-bias calibration (per Becker 2026).

See [docs/MARKOV-MODELS.md](docs/MARKOV-MODELS.md) for formulas and worked examples.

---

## Conventions

### Coding Style

- **Type hints everywhere** — `from typing import` for complex types
- **Pure functions in `core/`** — no side effects beyond DB writes
- **Side-effectful code in `app/`** — Streamlit components, st.session_state
- **Docstrings on public functions** — NumPy style (Parameters/Returns/Examples)
- **No magic numbers** — extract to module constants or config

### Naming

| Item | Convention | Example |
|---|---|---|
| Files | snake_case | `transition_matrix.py` |
| Classes | PascalCase | `MarkovModel`, `MonteCarloRunner` |
| Functions | snake_case | `build_transition_matrix`, `run_simulation` |
| Constants | UPPER_SNAKE | `DEFAULT_N_SIMULATIONS = 10_000` |
| DB tables | snake_case | `transition_matrices`, `simulation_runs` |
| Streamlit pages | `N_Title_Case.py` | `1_Brand_Share.py`, `2_Churn.py` |

### UI Language

- **App UI strings**: English (recruiter-facing portfolio piece)
- **User-facing form copy** (if any): Indonesian (target market is also ID)
- **Code comments & docs**: English

### Commits

- Conventional commits style: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Atomic — one logical change per commit
- Use `rtk git commit` for token-optimized output

---

## GSD Workflow Enforcement

Before using Edit/Write/etc. on substantive code changes, start through a GSD command so planning artifacts and execution context stay in sync.

Entry points:
- `/gsd:quick <desc>` — small fixes, docs updates, 1-3 file changes
- `/gsd:debug` — bug investigation with scientific method
- `/gsd:plan-phase N` — plan a new phase
- `/gsd:execute-phase N` — execute all plans in a phase
- `/gsd:progress` — check status + route to next action

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass.

---

## Token Optimization

This project leverages several token-saving tools:

1. **rtk** (Rust Token Killer) — prefix all bash commands with `rtk` for 60-90% token savings. See user's global CLAUDE.md.
2. **context7 MCP** — fetch up-to-date library docs (Streamlit, NumPy, Plotly, DuckDB, etc.) via `mcp__context7__*` tools. Always prefer over WebSearch for library questions.
3. **Custom Skills** — invoke skills for repeated patterns (see `.claude/skills/`).
4. **Modular rules** — each `.claude/rules/*.md` file is loaded on-demand to avoid context bloat.

---

## Rules Files

Detailed conventions are split across `.claude/rules/`:

| File | Scope |
|---|---|
| [python-conventions.md](.claude/rules/python-conventions.md) | Python style, type hints, error handling |
| [markov-patterns.md](.claude/rules/markov-patterns.md) | Markov chain implementation rules + validation checklist |
| [streamlit-conventions.md](.claude/rules/streamlit-conventions.md) | Streamlit page structure, components, theming |
| [data-storage.md](.claude/rules/data-storage.md) | DuckDB usage, schema, query patterns |
| [coding-style.md](.claude/rules/coding-style.md) | General style (naming, file size, comments) |
| [context7.md](.claude/rules/context7.md) | When and how to use context7 MCP |
| [workflow.md](.claude/rules/workflow.md) | Pre-coding + post-coding checklist |
| [project-rules.md](.claude/rules/project-rules.md) | Project-specific rules (planning folders, security) |

---

## Critical Instruction: Maintain This File

After any significant change, update:
1. **Tech Stack** section — if new tools added
2. **App Pages** table — if new page added
3. **Markov Engine** table — if new model implemented

Do NOT let this file drift from reality. It is loaded into every Claude Code session.

---

## Project Goal

**Ship a recruiter-ready portfolio piece in 4 weeks** that demonstrates BA/BI-grade thinking applied to Markov chain forecasting. The deliverable is a deployable Streamlit app with two distinct domain demonstrations, full documentation, and a story-driven README.

If the demo doesn't convince a senior recruiter that the developer can think quantitatively AND ship product, the project failed its purpose.

---

## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**MarkovLens**

MarkovLens is a multi-domain Markov chain forecasting workbench built as a BA/BI portfolio piece. It applies three Markov model formulations (m1 homogeneous, m2 time-varying, m3 extended) to two real business problems — brand market share forecasting and customer churn state modelling — backed by Monte Carlo simulation with empirical longshot-bias calibration.

The primary audience is BA/BI recruiters evaluating code quality, quantitative thinking, and engineering architecture. The secondary audience is the developer themselves, who needs it to be a genuinely useful analytical tool for real datasets.

**Core Value:** A GitHub repo that convinces a senior BA/BI recruiter that the developer can think quantitatively AND ship a production-quality Python data product — two live domains, correct Markov math, clean 3-layer architecture.

### Constraints

- **Timeline**: 4 weeks hard — actively job hunting; must ship a compelling demo
- **Tech stack**: Python 3.12 + Streamlit + DuckDB + NumPy/Plotly — locked in, no migrations
- **Math**: All Markov implementations must correctly follow Chan (2015) — wrong math invalidates the portfolio story
- **Performance**: Streamlit Cloud 1GB RAM — Monte Carlo must use @st.cache_data; no 10k-sim cold starts on every interaction
- **UI polish**: Streamlit must not look like a student project — design system via theme.css + Plotly template required
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.12+ - Core application language (required by `pyproject.toml`)
- SQL (DuckDB dialect) - Data persistence and querying via `core/db/schema.sql`
- YAML - Streamlit configuration
- CSS - Custom theming via `app/styles/theme.css`
## Runtime
- Python 3.12+ (enforced via `requires-python = ">=3.12"` in `pyproject.toml`)
- `uv` (Astral) - Modern Python package/virtual environment manager
- Lockfile: `uv.lock` (present)
- No pip used directly; all dependencies managed through `pyproject.toml`
## Frameworks
- Streamlit 1.40.0+ - Web application framework (multi-page app via `app/Home.py` and `app/pages/`)
- streamlit-shadcn-ui 0.1.18+ - UI component library with modern design system
- streamlit-extras 0.5.0+ - Additional Streamlit utilities and helpers
- NumPy 2.0.0+ - Vectorized numerical computations for Markov chains
- Pandas 2.2.0+ - DataFrames for data manipulation and transitions
- SciPy 1.14.0+ - Scientific functions (linear algebra, statistics)
- scikit-learn 1.5.0+ - Machine learning utilities and preprocessing
- Plotly 5.24.0+ - Interactive charts (heatmaps, fan charts, Sankey diagrams)
- pytest 8.3.0+ - Test runner with markers (`slow`, `integration`)
- pytest-cov 6.0.0+ - Code coverage reporting
- pytest-mock 3.14.0+ - Mocking and fixture support
- ruff 0.7.0+ - Unified linting and code formatting
- mypy 1.13.0+ - Type checking (strict mode for `core/` and `domains/`)
- ipykernel 6.29.0+ - Jupyter kernel for notebook development
- jupyter 1.1.0+ - Notebook environment
- nbformat 5.10.0+ - Notebook format support
## Key Dependencies
- duckdb 1.1.0+ - Embedded analytical database (file-based, no server required)
- pyarrow 18.0.0+ - Apache Arrow for efficient data serialization
- python-dotenv 1.0.0+ - Environment variable loading from `.env`
- pydantic 2.9.0+ - Data validation and modeling
- pydantic-settings 2.6.0+ - Configuration management via Pydantic (used in `core/config.py`)
- reportlab 4.2.0+ - PDF report generation (deferred to Phase 04)
## Configuration
- Configuration source: `core/config.py` (Pydantic-Settings)
- Settings loaded from `.env` file (template: `.env.example`)
- Key env vars:
- `pyproject.toml` - Primary configuration (dependencies, tool settings, metadata)
- `.streamlit/config.toml` - Streamlit UI configuration
- ruff: 100 character line length, targets Python 3.12
- Excludes: `notebooks/`, `data/`, `reports/`
- Selected rules: E, F, I, N, W, UP, B, SIM, RUF, C4, PT
- Per-file ignores: `tests/*` ignores S101 (assert_used)
- mypy: Python 3.12, `warn_return_any=true`, `warn_unused_configs=true`
- Non-strict mode globally; enforcement expected via IDE integration
- pytest: testpaths = `tests/`, strict markers enabled
- Markers: `slow` (deselectable), `integration` (DuckDB-based tests)
- Run: `uv run pytest`
## Platform Requirements
- Python 3.12+
- 500MB+ free disk (DuckDB file + venv)
- Terminal/shell for `uv` commands
- Deployment target: Streamlit Cloud (free tier)
- Resource constraints: ~1GB RAM, 1 CPU
- DuckDB file size limit: < 500MB (gitignored)
- No long-running background processes
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Language & Tooling
- **Python 3.12+** — modern syntax features used throughout
- **ruff** — linting + formatting (replaces black/isort/flake8); 100-char line length
- **mypy** — strict type checking enforced on `core/` and `domains/`
- **uv** — dependency management (never `pip install` directly)
## Type Hints
- Type hints on all public functions — non-negotiable
- Type aliases defined at module level: `TransitionMatrix: TypeAlias = np.ndarray`
- Pydantic `BaseModel` / `BaseSettings` for config and structured return types
- `@dataclass(frozen=True)` for immutable value objects (e.g. `SimulationResult`)
## Naming
| Item | Convention | Example |
|---|---|---|
| Modules/files | `snake_case` | `transition_matrix.py` |
| Classes | `PascalCase` | `MarkovModel`, `SimulationRunner` |
| Functions | `snake_case` | `build_transition_matrix` |
| Constants | `UPPER_SNAKE` | `DEFAULT_N_SIMULATIONS` |
| Private helpers | leading `_` | `_compute_quantile_bands` |
| DB tables | `snake_case` plural | `transition_matrices` |
| Streamlit pages | `N_PascalCase.py` | `1_Brand_Share.py` |
## Error Handling
- Validate at boundaries only (user input, file I/O, DB queries)
- Trust internal contracts — no defensive null-checks within `core/`
- Raise specific exceptions: `ValueError`, `KeyError`, custom domain exceptions from `core/exceptions.py`
- Silent `except Exception: pass` is forbidden
- User-facing error messages are actionable (tell user what to do, not internal jargon)
## Layer Separation
- `core/` and `domains/` are **pure** — no `import streamlit` allowed
- All SQL wrapped in `core/db/queries.py` — never inline SQL strings in `app/`
- Pages call domain services; services call core (no layer skipping)
## Numerical Code
- Vectorized NumPy operations — never loop over arrays in pure Python
- `np.float64` for probabilities (avoid float32 accumulation errors)
- `np.random.default_rng(seed)` — never legacy `np.random.seed()`
- Validate matrix invariants: rows sum to 1.0, no negatives
## Constants
- No magic numbers — extract to module-level `UPPER_SNAKE` constants
- Reference: `core/simulation.py` holds `LONGSHOT_CALIBRATION`, `DEFAULT_N_SIMULATIONS`, etc.
## Comments
- Default: **no comments** — naming self-documents
- Comment only for: paper references (`# Chan 2015 Eq.(3)`), workarounds, non-obvious invariants
- Never restate what the code does
## Imports
## Docstrings
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern
```
```
- `core/` and `domains/` must not import `streamlit`
- Pages call services; services call core — no layer skipping
- All SQL wrapped in `core/db/queries.py`
## Layers
### 1. Core Layer (`core/`)
- `core/models.py` — M1Homogeneous, M2TimeVarying, M3Extended + `validate_transition_matrix()`
- `core/simulation.py` — `monte_carlo_simulate()`, `calibrate_probability()`, `compute_quantile_bands()`; holds `LONGSHOT_CALIBRATION` table
- `core/metrics.py` — MAPE, Brier score, log-loss (not yet implemented)
- `core/config.py` — Pydantic-Settings reading from `.env`
- `core/exceptions.py` — `InvalidTransitionMatrixError` and other domain exceptions
- `core/db/connection.py` — DuckDB singleton connection
- `core/db/schema.sql` — Idempotent `CREATE TABLE IF NOT EXISTS` schema (6 tables)
- `core/db/queries.py` — All SQL wrapped here (no raw SQL elsewhere)
- `core/io/loaders.py` — Dataset loading (CSV/Parquet → DataFrame)
### 2. Domain Layer (`domains/`)
- `domains/brand_share/service.py` — Market share forecasting (m1/m2/m3)
- `domains/churn/service.py` — Customer state churn modelling
### 3. App Layer (`app/`)
- `app/pages/1_Brand_Share.py` — Brand share forecaster
- `app/pages/2_Churn.py` — Churn state modelling
- `app/pages/3_Reports.py` — PDF/CSV export
- `app/pages/4_Settings.py` — Dataset management
- `kpi_card.py` — KPI metric card
- `empty_state.py` — Empty data fallback UI
- `section_header.py` — Page section header
## Data Flow
```
```
- Streamlit: `@st.cache_resource` for DuckDB connection, `@st.cache_data` for forecast results
- DuckDB: `transition_matrices` and `simulation_runs` tables cache computed results by `(dataset_id, model_type, period)` key
## Entry Points
| Entry point | Purpose |
|---|---|
| `app/Home.py` | Streamlit app root |
| `scripts/seed_data.py` | Regenerate DuckDB from raw CSVs |
| `uv run pytest` | Run test suite |
| `uv run ruff check .` | Lint |
| `uv run mypy core/ domains/` | Type check |
## Database Schema
| Table | Purpose |
|---|---|
| `datasets` | Registered datasets with metadata |
| `transitions` | Raw transition observations (entity_id, period, from_state, to_state) |
| `transition_matrices` | Computed + cached matrices per (dataset, model_type, period) |
| `simulation_runs` | Monte Carlo result cache (distributions, quantile paths, calibrated probability) |
| `forecasts` | Forecast outputs with accuracy metrics |
| `scenarios` | Saved what-if scenario configurations |
## Current Implementation State
- All `core/models.py` model methods raise `NotImplementedError` (Phase 01 TODO)
- `core/simulation.py` functions raise `NotImplementedError` (Phase 01 TODO)
- `core/metrics.py` — not yet created
- `app/pages/` — pages not yet created (only `app/Home.py` exists)
- `domains/brand_share/service.py` and `domains/churn/service.py` — stubs
- DuckDB schema (`core/db/schema.sql`)
- Data classes / return types (`ForecastResult`, `SimulationResult`)
- `LONGSHOT_CALIBRATION` table in `core/simulation.py`
- Type aliases and constants
- Project config (`core/config.py`)
- Exception hierarchy (`core/exceptions.py`)
- Shared UI components (`app/components/`)
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
