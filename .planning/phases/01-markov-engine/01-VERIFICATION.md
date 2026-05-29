---
phase: 01-markov-engine
verified: 2026-05-29T10:30:00+07:00
status: passed
score: 5/5 must-haves verified
re_verification: false
gaps: []
human_verification: []
---

# Phase 01: Markov Engine Verification Report

**Phase Goal:** Build the domain-agnostic Markov engine — validate, forecast, simulate, calibrate, and persist.
**Verified:** 2026-05-29T10:30:00+07:00
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | M1 reproduces Chan 2015 Table 3 within atol=1e-3 | VERIFIED | `test_m1_forecast_replicates_chan_2015_table3` passes; REPL confirms `forecast_array[0]=[0.5829,0.2780,0.0667,0.0724]` |
| SC2 | `monte_carlo_simulate` bit-reproducible with same seed; different with different seed | VERIFIED | `test_monte_carlo_same_seed_reproducible` and `test_monte_carlo_different_seeds_differ` both pass; REPL confirms `same_seed_identical=True`, `diff_seed_differs=True`, `dtype=int64` |
| SC3 | `validate_transition_matrix` raises `InvalidTransitionMatrixError` on row-sum>1, negative cell, non-square; passes silently on valid 3x3 | VERIFIED | 3 raise tests + 1 accept test in `test_models.py`; REPL manual check confirmed all 4 cases |
| SC4 | `uv run pytest tests/unit/ -m "not slow"` reports >80% coverage for `core/`, all regression tests green | VERIFIED | `uv run pytest --cov=core --cov-fail-under=80 -q` exits 0; **40 passed, 0 skipped, 90.76% coverage** |
| SC5 | `scripts/seed_data.py` populates `transitions` and `forecasts` tables with >=5 forecast rows | VERIFIED | Integration tests `test_seed_idempotency` + `test_seed_produces_reference_forecasts` pass; live DB query shows `forecasts=7` |

**Score: 5/5 truths verified**

---

### Required Artifacts

| Artifact | Description | Exists | Substantive | Wired | Status |
|----------|-------------|--------|-------------|-------|--------|
| `core/models.py` | M1/M2/M3 model classes + `validate_transition_matrix` | Yes | 216 lines, full implementation | Imported by `core/db/queries.py`, `scripts/seed_data.py`, tests | VERIFIED |
| `core/simulation.py` | `monte_carlo_simulate`, `calibrate_probability`, `compute_quantile_bands`, `walk_forward_backtest` | Yes | 293 lines, full implementation | Imported by tests; `walk_forward_backtest` imports `core.metrics` | VERIFIED |
| `core/metrics.py` | `mape`, `brier_score`, `log_loss` | Yes | 99 lines, 3 functions implemented | Imported by `core/simulation.py` (walk_forward) and tests | VERIFIED |
| `core/db/queries.py` | `build_transition_matrix`, `register_dataset`, `list_datasets`, `bulk_insert_transitions`, `load_transitions` | Yes | 315 lines, all 5 query functions implemented | Used by `scripts/seed_data.py`; covered by integration tests | VERIFIED |
| `core/db/serialization.py` | `ndarray_to_json`, `json_to_ndarray` with NaN/Inf guard | Yes | 67 lines, both functions implemented | Imported by `scripts/seed_data.py`; covered by unit tests | VERIFIED |
| `core/io/loaders.py` | `validate_transitions_df` (Phase 01 scope); Phase 02 stubs present | Yes | 65 lines; Phase 01 function implemented; 2 Phase 02 stubs are intentional `NotImplementedError` | `validate_transitions_df` called in `core/db/queries.py` (`bulk_insert_transitions`) | VERIFIED (Phase 01 scope) |
| `core/exceptions.py` | `InvalidTransitionMatrixError`, `DatasetNotFoundError`, etc. | Yes | 5 custom exception classes | Imported by `core/models.py`, `core/db/queries.py` | VERIFIED |
| `scripts/seed_data.py` | Idempotent seed with synthetic FMCG + IBM Telco; >=5 forecasts | Yes | 368 lines, full implementation with idempotency via `_delete_dataset_rows` | Calls `core/db/queries.py`, `core/models.py`, `core/db/serialization.py` | VERIFIED |
| `data/seed/telco_churn.csv` | IBM Telco churn CSV committed to repo | Yes | 7044 lines (header + 7043 rows) | Read by `scripts/seed_data.py`._load_telco_transitions() | VERIFIED |
| `tests/unit/test_models.py` | ENG-01..04, ENG-08 regression tests | Yes | 11 tests, 0 skips | Covers all model classes and validator | VERIFIED |
| `tests/unit/test_simulation.py` | ENG-05..07, ENG-09 tests | Yes | 12 tests, 0 skips | Covers MC, calibration, quantile bands, walk-forward | VERIFIED |
| `tests/unit/test_metrics.py` | ENG-10 tests | Yes | 5 tests, 0 skips | Covers MAPE, Brier, log-loss | VERIFIED |
| `tests/integration/test_queries.py` | DATA-02, DATA-03 integration tests | Yes | 5 tests, 0 skips, marked `@pytest.mark.integration` | Tests against real temp DuckDB via `tmp_path` fixture | VERIFIED |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `core/models.py:validate_transition_matrix` | `InvalidTransitionMatrixError` | `from core.exceptions import InvalidTransitionMatrixError` | WIRED | Raises on 4 distinct invalid conditions |
| `core/db/queries.py:build_transition_matrix` | `core/models.py:validate_transition_matrix` | `from core.models import validate_transition_matrix` | WIRED | Called after matrix computation; catches zero-obs rows |
| `core/db/queries.py:bulk_insert_transitions` | `core/io/loaders.py:validate_transitions_df` | `from core.io.loaders import validate_transitions_df` | WIRED | Guards all bulk inserts at the DB boundary |
| `core/simulation.py:walk_forward_backtest` | `core/metrics.py:mape` | `from core.metrics import mape as mape_fn` (deferred import) | WIRED | Called per backtest window; result captured in `mape_val` |
| `scripts/seed_data.py:main` | `core/db/queries.py:build_transition_matrix` | `from core.db.queries import build_transition_matrix` | WIRED | Called for m1 (all-period) and m2 (per-period) matrices |
| `scripts/seed_data.py:_seed_churn/_seed_brand_share` | `core/models.py:M1Homogeneous/M2TimeVarying` | `from core.models import M1Homogeneous, M2TimeVarying` | WIRED | Models instantiated and `.forecast()` called to generate reference rows |
| `scripts/seed_data.py:_store_forecast` | `core/db/serialization.py:ndarray_to_json` | `from core.db.serialization import ndarray_to_json` | WIRED | Serializes `forecast_array` before INSERT |

---

### Data-Flow Trace (Level 4)

Only `scripts/seed_data.py` renders dynamic data to DuckDB; all other artifacts are pure computation libraries. Data flows verified:

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `scripts/seed_data.py:_seed_brand_share` | `m1_result.forecast_array` | `M1Homogeneous(m1_matrix).forecast(Y_1, 12)` where `m1_matrix` comes from `build_transition_matrix(conn, BRAND_SHARE_DATASET_ID)` — a real GROUP BY SQL query | Yes — queries `transitions` table populated from synthetic DGP | FLOWING |
| `scripts/seed_data.py:_seed_churn` | `result.forecast_array` (5 horizons) | `M1Homogeneous(m1_matrix).forecast(Y_1, horizon)` where `m1_matrix` comes from `build_transition_matrix(conn, CHURN_DATASET_ID)` — real SQL query on IBM Telco data | Yes — queries `transitions` table populated from Telco CSV | FLOWING |
| `forecasts` table (DuckDB) | `forecast_json` column | `ndarray_to_json(forecast_array)` → SQL INSERT via `_store_forecast` | 7 rows confirmed in live DB | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| M1 forecast returns correct model type and shape | `python -c "from core.models import M1Homogeneous; ..."` | `model_type=m1`, array shape (12, 4) | PASS |
| Monte Carlo reproducible with same seed | `python -c "from core.simulation import monte_carlo_simulate; ..."` | `same_seed_identical=True`, `diff_seed_differs=True`, `dtype=int64` | PASS |
| `validate_transition_matrix` raises on all 3 bad inputs | `python -c "from core.models import validate_transition_matrix; ..."` | 3 raises caught correctly; valid 3x3 passes silently | PASS |
| 40 tests pass at 90.76% coverage | `uv run pytest --cov=core --cov-fail-under=80 -q` | 40 passed, 0 skipped, 90.76% (required >=80%) | PASS |
| Forecasts table has >=5 rows | `python -c "from core.db.connection import get_connection..."` | `forecasts_count=7`, SC5 passed | PASS |
| ruff clean | `uv run ruff check core/ scripts/ tests/` | `All checks passed!` | PASS |
| mypy clean | `uv run mypy core/` | `Success: no issues found in 12 source files` | PASS |

---

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| ENG-01 | `validate_transition_matrix()` raises `InvalidTransitionMatrixError` for non-square, negative, row-sum≠1; enforces `dtype=np.float64` | SATISFIED | 4 tests in `test_models.py` covering all error conditions + dtype check; REPL verified |
| ENG-02 | `M1Homogeneous.forecast()` implements Y_{t+1} = Y_t · P; Chan 2015 Table 3 regression | SATISFIED | `test_m1_forecast_replicates_chan_2015_table3` passes within atol=1e-3 |
| ENG-03 | `M2TimeVarying.forecast()` implements Y_{t+1} = Y_t · P_t per period; hold-last-P_t | SATISFIED | `test_m2_forecast_shape` + `test_m2_holds_last_pt_at_horizon` pass |
| ENG-04 | `M3Extended.forecast()` implements Q_{t+1} = G ⊙ Q_t · P_t; absolute counts | SATISFIED | `test_m3_forecast_replicates_chan_2015` passes (normalized shares within 1e-2 of Chan table) |
| ENG-05 | `monte_carlo_simulate()` 10k vectorized paths; `default_rng(seed)`; reproducible with same seed | SATISFIED | 6 tests in `test_simulation.py`; `dtype=int64`, shape `(n_sims, n_steps+1)` verified |
| ENG-06 | `calibrate_probability()` applies LONGSHOT_CALIBRATION interpolation; returns calibrated probability | SATISFIED | 3 tests in `test_simulation.py` checking anchor points, interpolation, and clamping |
| ENG-07 | `compute_quantile_bands()` 10th/50th/90th percentile paths; `target_extractor` callable guard | SATISFIED | `test_quantile_bands_shape` + `test_quantile_bands_target_extractor_applied` pass |
| ENG-08 | Sparsity detection warns on cells with < `MIN_OBSERVATIONS_PER_CELL` (20) observations | SATISFIED | `test_validate_warns_sparse_cells` (caplog fixture) passes — WARNING logged for sparse cells |
| ENG-09 | `walk_forward_backtest()` re-fits matrix at each step; no future data leakage | SATISFIED | `test_walk_forward_no_leakage` passes; implementation uses `periods[:t_idx]` (train only) |
| ENG-10 | `core/metrics.py` implements MAPE, Brier score, log-loss | SATISFIED | 5 tests in `test_metrics.py` covering all 3 functions; 96% branch coverage |
| DATA-01 | `core/io/loaders.py` validates DataFrame: required columns, NaN guard | SATISFIED | 3 tests in `test_loaders.py`; `validate_transitions_df` gates `bulk_insert_transitions` |
| DATA-02 | `scripts/seed_data.py` populates `transitions` + `forecasts` (>=5 rows); idempotent | SATISFIED | `test_seed_idempotency` + `test_seed_produces_reference_forecasts` pass; live DB has 7 forecast rows; D-23 idempotency via DELETE-before-INSERT verified |
| DATA-03 | `build_transition_matrix()` GROUP BY → row-stochastic matrix + observation counts | SATISFIED | 3 integration tests in `test_queries.py`: normalization, counts, dataset isolation; parameterized SQL (no SQL injection) |

**All 13 Phase 01 requirements: SATISFIED**

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `core/io/loaders.py` | 13, 19 | `raise NotImplementedError(...)` for `load_brand_share_csv` / `load_churn_csv` | INFO | Intentional Phase 02 stubs. These are **not** Phase 01 scope. Documented in `01-06-SUMMARY.md` under "Stubs". Not called anywhere in Phase 01 code paths. |

No blocker or warning anti-patterns found. The two `NotImplementedError` stubs are intentional, clearly labeled with TODO comments pointing to Phase 02, and are excluded from test coverage (the 2 uncovered lines in `core/io/loaders.py` at 88% coverage). No other `raise NotImplementedError` exists in `core/`.

Zero `@pytest.mark.skip` decorators in all test files.

Zero `import streamlit` in `core/` or `domains/`.

---

### Human Verification Required

None. All Phase 01 success criteria are programmatically verifiable and have been verified.

---

### Gaps Summary

No gaps. All 5 roadmap success criteria are verified. All 13 Phase 01 requirement IDs (ENG-01 through ENG-10, DATA-01 through DATA-03) are implemented, tested, and confirmed.

**Phase 01 is gate-clean. Phase 02 may proceed.**

---

## Summary Table

| Check | Result |
|-------|--------|
| Tests | 40 passed, 0 failed, 0 skipped |
| Coverage | 90.76% (required >=80%) |
| ruff lint | Clean (0 violations) |
| mypy type check | Clean (0 issues in 12 files) |
| `raise NotImplementedError` in Phase 01 scope | 0 (2 allowed Phase 02 stubs in loaders.py) |
| `@pytest.mark.skip` | 0 |
| `import streamlit` in core/ or domains/ | 0 |
| Chan 2015 regression (SC1) | Pass (atol=1e-3) |
| Monte Carlo reproducibility (SC2) | Pass (bit-identical same seed) |
| Matrix validation (SC3) | Pass (3 raises + 1 accept) |
| Forecasts in DB (SC5) | 7 rows (required >=5) |
| Requirements covered | 13/13 |

---

_Verified: 2026-05-29T10:30:00+07:00_
_Verifier: Claude (gsd-verifier)_
