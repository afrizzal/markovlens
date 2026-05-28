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
