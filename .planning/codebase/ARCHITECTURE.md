# Architecture

**Analysis Date:** 2026-05-29

## Pattern

Three-layer clean architecture with strict dependency direction:

```
app/          ← Streamlit UI (side-effectful, no domain logic)
  ↓ calls
domains/      ← Orchestration + domain services (business logic)
  ↓ calls
core/         ← Domain-agnostic Markov engine (pure functions + DB writes)
  ↓ writes
data/         ← DuckDB file + raw data
```

Rules enforced:
- `core/` and `domains/` must not import `streamlit`
- Pages call services; services call core — no layer skipping
- All SQL wrapped in `core/db/queries.py`

## Layers

### 1. Core Layer (`core/`)

Domain-agnostic Markov engine implementing Chan (2015). All public functions are pure; side effects limited to DuckDB writes via `core/db/`.

**Key modules:**
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

Orchestrates core functions for specific business problems. Each domain has a `service.py` that is the single entry point called by `app/`.

**Domains:**
- `domains/brand_share/service.py` — Market share forecasting (m1/m2/m3)
- `domains/churn/service.py` — Customer state churn modelling

### 3. App Layer (`app/`)

Streamlit UI only. No domain logic, no direct DB access. All computation delegated to `domains/*/service.py`.

**Entry point:** `app/Home.py` (run via `uv run streamlit run app/Home.py`)

**Pages (planned):**
- `app/pages/1_Brand_Share.py` — Brand share forecaster
- `app/pages/2_Churn.py` — Churn state modelling
- `app/pages/3_Reports.py` — PDF/CSV export
- `app/pages/4_Settings.py` — Dataset management

**Shared components (`app/components/`):**
- `kpi_card.py` — KPI metric card
- `empty_state.py` — Empty data fallback UI
- `section_header.py` — Page section header

**Theming:** `app/styles/theme.css` injected via `st.markdown`; Plotly theme in `app/styles/plotly_theme.py` (planned)

## Data Flow

```
User action (Streamlit widget)
  → app/pages/*.py collects input
  → domains/*/service.py orchestrates
  → core/models.py or core/simulation.py computes
  → core/db/queries.py caches result in DuckDB
  → result returned up the chain
  → app/components/* renders charts/cards
```

**Caching strategy:**
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

6 tables in `data/markovlens.duckdb` (defined in `core/db/schema.sql`):

| Table | Purpose |
|---|---|
| `datasets` | Registered datasets with metadata |
| `transitions` | Raw transition observations (entity_id, period, from_state, to_state) |
| `transition_matrices` | Computed + cached matrices per (dataset, model_type, period) |
| `simulation_runs` | Monte Carlo result cache (distributions, quantile paths, calibrated probability) |
| `forecasts` | Forecast outputs with accuracy metrics |
| `scenarios` | Saved what-if scenario configurations |

## Current Implementation State

**Scaffolded, not implemented:**
- All `core/models.py` model methods raise `NotImplementedError` (Phase 01 TODO)
- `core/simulation.py` functions raise `NotImplementedError` (Phase 01 TODO)
- `core/metrics.py` — not yet created
- `app/pages/` — pages not yet created (only `app/Home.py` exists)
- `domains/brand_share/service.py` and `domains/churn/service.py` — stubs

**Implemented:**
- DuckDB schema (`core/db/schema.sql`)
- Data classes / return types (`ForecastResult`, `SimulationResult`)
- `LONGSHOT_CALIBRATION` table in `core/simulation.py`
- Type aliases and constants
- Project config (`core/config.py`)
- Exception hierarchy (`core/exceptions.py`)
- Shared UI components (`app/components/`)
