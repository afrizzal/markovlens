---
phase: 02-design-system-brand-share
plan: "03"
subsystem: domain-service
tags: [markov, numpy, duckdb, brand-share, m1, m2, m3, monte-carlo, backtest]

# Dependency graph
requires:
  - phase: 01-markov-engine
    provides: "M1Homogeneous, M2TimeVarying, M3Extended, monte_carlo_simulate, compute_quantile_bands, walk_forward_backtest, mape, brier_score, log_loss, build_transition_matrix"
  - phase: 02-design-system-brand-share (02-01)
    provides: "compute_stationary in core/models.py (BS-05)"
provides:
  - "BrandShareForecastResult: NumPy-only frozen dataclass (14 fields) — no Plotly coupling (D-18)"
  - "list_datasets(conn) — brand_share-filtered via BRAND_SHARE_DOMAIN constant"
  - "run_forecast(conn, dataset_id, model_type, horizon) — full m1/m2/m3 pipeline"
  - "Per-model accuracy metrics: mape/brier/log_loss for m1/m2/m3"
  - "best_model derived from computed metrics, never hardcoded"
  - "Monte Carlo confidence bands (P10/P50/P90) for selected model"
  - "Walk-forward backtest results"
  - "Historical shares matrix (n_periods, n_states)"
  - "Integration tests: 5 tests covering BS-01, BS-03, BS-04, BS-05"
affects:
  - "02-04 (Brand Share page) depends on BrandShareForecastResult contract"
  - "03 (Churn domain) — can follow same service pattern"
  - "04 (Home, Export) — uses list_datasets and run_forecast"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Domain service accepts conn as parameter — stays pure and testable (no singleton)"
    - "state_labels = sorted(set(from_state)|set(to_state)) must match queries.py internals"
    - "M3 receives absolute Q_1 counts, not normalized shares (markov-patterns forbidden #5)"
    - "Per-period matrix embedding guard for union-state consistency"
    - "2-D lambda extractor for compute_quantile_bands: (p == b).astype(float)"
    - "One-step in-sample accuracy comparison against last-period actual"

key-files:
  created:
    - "tests/integration/test_brand_share_service.py"
  modified:
    - "domains/brand_share/service.py"
    - "core/models.py"
    - "pyproject.toml"

key-decisions:
  - "conn accepted as parameter (not singleton) — service stays pure and testable with temp DB"
  - "state_labels derived via sorted(set(df[from_state])|set(df[to_state])) to match queries.py internal sort"
  - "M3 Q_1 = absolute to_state counts from last period, G = np.ones (neutral growth — no size data)"
  - "Per-model accuracy via one-step-ahead in-sample comparison (prev period -> last period)"
  - "compute_stationary added to core/models.py in worktree (Rule 3 — was missing from this branch)"
  - "numpy.int32 period values cast to Python int before DuckDB query params (Rule 1 fix)"
  - "N803/N806/E731 suppressed for service.py in pyproject.toml — Chan 2015 math vars"

requirements-completed: [BS-01, BS-04]

# Metrics
duration: 24min
completed: "2026-05-30"
---

# Phase 02 Plan 03: Brand Share Service Summary

**NumPy-only BrandShareForecastResult with full m1/m2/m3 pipeline, per-model MAPE/Brier/log-loss, computed best_model, and Monte Carlo P10/P50/P90 bands — domain layer stays Streamlit-free**

## Performance

- **Duration:** 24 min
- **Started:** 2026-05-30T07:38:31Z
- **Completed:** 2026-05-30T08:02:31Z
- **Tasks:** 2 (TDD — each has test + impl commits)
- **Files modified:** 4

## Accomplishments

- Rewrote `BrandShareForecastResult` as a 14-field NumPy-only frozen dataclass (no `forecast_chart_json`, no `kpis` dict, no Plotly coupling per D-18)
- Implemented full `run_forecast()` orchestration: data loading → state_labels derivation → m1 constant matrix → per-period P_t sequence (with union-state embedding guard) → M1/M2/M3 forecasts → Monte Carlo bands → backtest → per-model accuracy metrics → computed winner
- Established state_labels gap workaround: `sorted(set(from_state)|set(to_state))` exactly matches `build_transition_matrix` internal sort so indices stay aligned
- All 5 integration tests pass; full 45-test suite clean; ruff + mypy clean

## Task Commits

1. **Task 1: Redefine BrandShareForecastResult + implement list_datasets + run_forecast skeleton** - `a4ad35c` (feat)
2. **Task 2: Complete run_forecast pipeline + per-model accuracy comparison** - `7c783d3` (feat)

## Files Created/Modified

- `domains/brand_share/service.py` — Complete rewrite: NumPy-only result dataclass, list_datasets, run_forecast full pipeline
- `tests/integration/test_brand_share_service.py` — 5 integration tests covering BS-01/BS-03/BS-04/BS-05
- `core/models.py` — Added `compute_stationary()` function (eigenvector + power-iteration fallback), `scipy.linalg` import, and related constants
- `pyproject.toml` — Added N803/N806/E731 per-file suppression for `domains/brand_share/service.py`

## Decisions Made

- **conn as parameter, not singleton:** Service functions accept `conn: duckdb.DuckDBPyConnection` directly so they stay testable with temp DuckDB and work with `@st.cache_resource` at the page layer.
- **state_labels derivation must mirror queries.py:** `sorted(set(df["from_state"]) | set(df["to_state"]))` is the exact expression used inside `build_transition_matrix` — documented as RESEARCH Pitfall 2 workaround.
- **M3 absolute counts:** `Q_1` is derived from raw `weight.sum()` per to_state in the last period (not normalized), per markov-patterns forbidden #5 and RESEARCH Pitfall 5.
- **Growth multiplier G=ones:** No market size growth data is available in the brand_share domain's transition format; `G = np.ones(n)` is correct neutral placeholder with a code comment.
- **One-step in-sample accuracy:** Per-model metrics compare each model's one-step forecast (from prev_period share) against the actual last_period share. This gives a cheap and interpretable in-sample accuracy signal for BS-04.
- **best_model computation:** `min(MODEL_KEYS, key=lambda m: accuracy_metrics[m]["mape"])` — computed from measured MAPE, never hardcoded (D-12).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added compute_stationary to core/models.py (worktree missing it)**
- **Found during:** Task 1 (service.py import stage)
- **Issue:** This worktree's branch was at a pre-02-01 state; `compute_stationary` was added in Plan 02-01 but not present in this worktree's `core/models.py`. Import failed with `ImportError: cannot import name 'compute_stationary'`.
- **Fix:** Added `compute_stationary()` (eigenvector via `scipy.linalg.eig(P.T)` + power-iteration fallback) and supporting constants to `core/models.py`.
- **Files modified:** `core/models.py`
- **Verification:** Import succeeds; `test_run_forecast_returns_numpy_only` passes.
- **Committed in:** `a4ad35c` (Task 1 commit)

**2. [Rule 1 - Bug] Cast numpy.int32 period values to Python int before DuckDB query**
- **Found during:** Task 1 (per-period matrix build loop)
- **Issue:** `df["period"].unique()` returns numpy integer values; DuckDB raises `NotImplementedException: Unable to transform python value of type '<class 'numpy.int32'>'` when used as query parameters.
- **Fix:** `periods = [int(p) for p in sorted(df["period"].unique())]` — explicit Python int cast.
- **Files modified:** `domains/brand_share/service.py`
- **Verification:** All per-period matrices build successfully; 5 integration tests pass.
- **Committed in:** `a4ad35c` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes were necessary for the service to function. No scope creep. The compute_stationary addition is the canonical BS-05 implementation that Plan 02-01 was supposed to deliver.

## Issues Encountered

- mypy `no-any-return` errors on numpy array division (`vec / total` and `Q_next / total`) — fixed by annotating intermediate variables as `np.ndarray` and calling `.astype(np.float64)`.
- Docstring mention of "import streamlit" triggered the grep-based acceptance check — renamed to "no Streamlit imports" phrasing in the module docstring.

## Known Stubs

None — all fields in `BrandShareForecastResult` are computed from real data. `G = np.ones(n)` is documented neutral assumption, not a stub (it is mathematically correct for a market with no size growth data).

## Next Phase Readiness

- `BrandShareForecastResult` contract is stable and ready for Plan 02-04 (Brand Share page)
- All component functions (transition_heatmap, monte_carlo_fan, kpi_card) from Plan 02-02 can now receive real data from `run_forecast`
- `list_datasets(conn)` returns live DuckDB datasets for the dataset selector widget

## Self-Check: PASSED

- `domains/brand_share/service.py` exists and contains no `forecast_chart_json` field
- `tests/integration/test_brand_share_service.py` exists with 5 tests
- `a4ad35c` exists in git log
- `7c783d3` exists in git log
- `uv run pytest tests/integration/test_brand_share_service.py -x -q` — 5 passed
- `uv run pytest -x -q` — 45 passed
- `uv run ruff check domains/` — clean
- `uv run mypy domains/` — clean

---
*Phase: 02-design-system-brand-share*
*Completed: 2026-05-30*
