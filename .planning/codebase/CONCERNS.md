# Concerns & Technical Debt

**Analysis Date:** 2026-05-29

## Critical Path Blockers

### All core functions are NotImplementedError stubs

Every meaningful function in `core/` raises `NotImplementedError` with a Phase 01 TODO comment. The app cannot function at all until Phase 01 is complete.

Affected:
- `core/models.py:validate_transition_matrix()` — line 45
- `core/models.py:M1Homogeneous.forecast()` — line 69
- `core/models.py:M2TimeVarying.forecast()` — line 83
- `core/models.py:M3Extended.forecast()` — line 100
- `core/simulation.py:monte_carlo_simulate()` — line 59
- `core/simulation.py:calibrate_probability()` — line 75
- `core/simulation.py:compute_quantile_bands()` — line 95

**Impact:** Phase 02 (Brand Share UI) and Phase 03 (Churn UI) are completely blocked on Phase 01.

### Streamlit pages do not exist yet

`app/pages/` directory is empty. Only `app/Home.py` exists. The four main application pages (Brand Share, Churn, Reports, Settings) are not created.

## Tech Debt

### Validation deferred

`validate_transition_matrix()` exists as a signature but raises `NotImplementedError`. M1/M2/M3 constructors call it, meaning model instantiation also fails.

### Sparsity warnings not implemented

`core/models.py:MIN_OBSERVATIONS_PER_CELL = 20` constant is defined but the sparsity check logic is not implemented. Risk: sparse matrices silently produce misleading forecasts.

### Calibration table lacks versioning

`LONGSHOT_CALIBRATION` in `core/simulation.py` is hardcoded from Becker (2026). No version field in DB or config to detect when calibration table changed and invalidate cached simulation results.

### `core/metrics.py` not created

The metrics module (`MAPE`, `Brier score`, `log-loss`) is referenced in `CLAUDE.md` and architecture docs but the file does not exist yet.

### `app/pages/` missing

`app/styles/plotly_theme.py` referenced in `CLAUDE.md` and `streamlit-conventions.md` does not exist.

### Domain services are stubs

`domains/brand_share/service.py` and `domains/churn/service.py` exist as files but contain no implemented methods.

### `core/io/loaders.py` is likely a stub

Data loading from CSV/Parquet has not been implemented per the overall Phase 01 state.

## Fragile Areas

### Implicit DuckDB singleton contract

`core/db/connection.py` uses a module-level global `_connection`. Tests that call `get_connection()` will share the same connection unless they explicitly use `temp_duckdb_path` fixture. Tests using a different DB path may accidentally pollute each other.

### Schema migration strategy is manual

`core/db/schema.sql` uses `CREATE TABLE IF NOT EXISTS` — safe for additive changes but any column rename or type change requires a manual migration script in `scripts/migrate_*.py`. No migration history tracking.

### JSON columns in DuckDB

`matrix_json`, `quantile_paths_json`, `result_json`, `modified_transitions_json` are stored as `JSON` columns. DuckDB 1.1+ JSON API must be used carefully; type coercion across versions can cause subtle bugs.

### `app/Home.py` is a placeholder

Current `app/Home.py` likely renders a welcome screen. When pages and real data are added, the home dashboard KPIs will need to query actual `forecasts` and `simulation_runs` tables — wiring not yet done.

## Missing Features

### Walk-forward validation not implemented

`core/models.py` has no `walk_forward_backtest()` function yet. Required for accuracy metrics and phase backtesting.

### No error boundaries in Streamlit pages

When pages are built, they must wrap domain service calls in `try/except` with `st.error()` fallback. This pattern is documented but not enforced at build time.

### Model comparison spec incomplete

`ForecastResult` has `accuracy_metrics: dict[str, float] | None = None` but no logic to populate it. Model comparison between m1/m2/m3 requires this.

## Security

### `.env` exposure risk

`DUCKDB_PATH`, `DEFAULT_RANDOM_SEED` etc. live in `.env`. File is gitignored but if accidentally committed would expose deployment configuration. `.env.example` is the committed template — must stay clean.

### Dataset anonymization deferred

No PII anonymization is implemented in `core/io/loaders.py`. When real customer churn datasets are loaded, SHA-256 hashing of `entity_id` must be applied at ingestion time (documented in `CLAUDE.md` but not enforced by code).

### SQL injection: parameterized queries enforced by convention only

The rule to use `conn.execute("...", [params])` is documented but not technically enforced. A future contributor could accidentally add f-string SQL in `core/db/queries.py`.

## Performance

### Monte Carlo scaling

`monte_carlo_simulate()` will run 10,000 simulations per call. On Streamlit Cloud (1 CPU, ~1GB RAM), large matrices (10+ states × 10,000 sims × 24 steps) may be slow. `@st.cache_data` on forecast results mitigates re-computation but cold-start will be noticeable.

### No matrix construction optimization

`build_transition_matrix()` (when implemented) will need to use DuckDB GROUP BY + NumPy efficiently. Naïve Python looping over observations will be too slow for large datasets.

## Test Coverage Gaps

### Phase 01 tests are skipped

`tests/unit/test_models.py` exists but all tests are marked skip until implementation is complete.

### No integration tests written

`tests/integration/` directory is empty. DuckDB integration tests (`@pytest.mark.integration`) need to be created for `core/db/queries.py` and data loading paths.

### No UI/smoke tests

No Streamlit page smoke tests. When pages are built, at minimum a "page renders without error" test should be added.

### `core/metrics.py` has no test file

Module doesn't exist yet; test file will need to be created alongside implementation.

## Dependency Risks

| Package | Risk |
|---|---|
| `streamlit-shadcn-ui 0.1.18+` | Beta library; API may break across minor versions |
| `pydantic-settings 2.6+` | Settings API changed in Pydantic v2; ensure `BaseSettings` import from `pydantic_settings` not `pydantic` |
| `duckdb 1.1+` | JSON API behavior varies; test against exact version in CI |
| `reportlab 4.2+` | Only needed for Phase 04 Reports; unused import risk if imported early |

## Scaling Limits

| Limit | Threshold | Note |
|---|---|---|
| DuckDB file size | < 500MB | Streamlit Cloud constraint; documented in CLAUDE.md |
| Streamlit Cloud RAM | ~1GB | Monte Carlo + Plotly rendering peak; monitor during Phase 02 |
| Plotly fan chart rendering | > 10,000 paths | May lag in browser; downsample `quantile_paths` for display |
| State count | 10 default | Higher state counts → n² matrix cells → sparsity issues |

## Phase Dependency Chain

```
Phase 01 (Core Engine) → Phase 02 (Brand Share UI) → Phase 04 (Reports)
                       ↘ Phase 03 (Churn UI)       ↗
```

Phase 01 is the critical dependency. Nothing downstream can be demoed until `validate_transition_matrix()`, all three model forecasters, and the Monte Carlo simulation are implemented and tested.
