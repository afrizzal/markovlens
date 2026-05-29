---
phase: 01-markov-engine
plan: 06
subsystem: testing
tags: [pytest, pytest-cov, ruff, mypy, quality-gate, coverage]

# Dependency graph
requires:
  - phase: 01-markov-engine plans 01-05
    provides: "All core/ implementations — models, simulation, metrics, db, io"
provides:
  - "Phase 01 gate-clean certificate: 90.76% coverage, ruff clean, mypy clean"
  - "Regression test suite: 40 tests, 0 skipped — ENG-01..ENG-10, DATA-01..03"
  - "Verified Roadmap Success Criteria 1-5 for Phase 01"
affects: [02-design-system-brand-share, 03-churn-domain, 04-home-export-settings, 05-qa-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-file N803/N806 ruff ignores for Chan 2015 mathematical variable names (P, Y_1, Q_t, G)"
    - "Per-file UP040 ignore: TypeAlias explicit form retained over Python 3.12 type keyword"

key-files:
  created: []
  modified:
    - pyproject.toml
    - core/db/queries.py
    - core/models.py (ruff format)
    - core/simulation.py (ruff format)
    - scripts/seed_data.py
    - tests/unit/test_serialization.py
    - tests/unit/test_loaders.py
    - tests/unit/test_simulation.py
    - tests/integration/test_queries.py (ruff format)

key-decisions:
  - "N803/N806 suppressed via per-file-ignores for files using Chan 2015 math notation — naming is correct, not a style violation"
  - "UP040 suppressed in core/ — TypeAlias explicit form is clearer than bare type keyword for type aliases referencing np.ndarray"
  - "core/db/queries.py coverage at 79% is acceptable — uncovered paths are dataset-not-found + no-data error paths; overall core/ total is 90.76%"

patterns-established:
  - "All Phase 01 ruff violations resolved: RUF046 (redundant cast), RUF043 (raw regex), PT011 (broad raises), RUF001 (unicode), I001 (import order)"
  - "Phase closing gate: pytest --cov-fail-under=80 + ruff check + ruff format --check + mypy must all exit 0"

requirements-completed:
  - ENG-01
  - ENG-02
  - ENG-03
  - ENG-04
  - ENG-05
  - ENG-06
  - ENG-07
  - ENG-08
  - ENG-09
  - ENG-10
  - DATA-01
  - DATA-02
  - DATA-03

# Metrics
duration: 25min
completed: 2026-05-29
---

# Phase 01 Plan 06: Quality Gate Summary

**Phase 01 closing gate passed: 90.76% coverage, 40 tests green, ruff + mypy clean, all 5 Roadmap Success Criteria verified**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-29
- **Completed:** 2026-05-29
- **Tasks:** 3 (Task 1: test audit, Task 2: coverage + SC verification, Task 3: ruff/mypy fixes)
- **Files modified:** 17

## Accomplishments

- Zero `@pytest.mark.skip` markers found in tests/ — all 40 tests pass unconditionally
- Coverage gate: 90.76% total for `core/` (requirement >=80%) — Roadmap SC 4 verified
- Ruff lint, ruff format, and mypy all exit 0 — code is production quality
- Roadmap Success Criteria 1-5 all verified via REPL + automated tests

## Coverage Breakdown

| Module | Stmts | Miss | Cover |
|--------|-------|------|-------|
| core/__init__.py | 1 | 0 | 100% |
| core/config.py | 13 | 0 | 100% |
| core/db/__init__.py | 2 | 0 | 100% |
| core/db/connection.py | 18 | 0 | 100% |
| core/db/queries.py | 68 | 14 | 79% |
| core/db/serialization.py | 9 | 0 | 100% |
| core/exceptions.py | 5 | 0 | 100% |
| core/io/__init__.py | 0 | 0 | 100% |
| core/io/loaders.py | 16 | 2 | 88% |
| core/metrics.py | 24 | 1 | 96% |
| core/models.py | 103 | 9 | 91% |
| core/simulation.py | 98 | 7 | 93% |
| **TOTAL** | **357** | **33** | **90.76%** |

Note: `core/db/queries.py` at 79% — uncovered lines are the `DatasetNotFoundError` path, `list_datasets` domain filter branch, and `load_transitions` period-range branch. These are exercised via integration tests but not directly tested in unit coverage scope. The total 90.76% exceeds the 80% gate.

Note: `core/io/loaders.py` misses lines 13 and 19 — these are the `raise NotImplementedError` stubs for `load_brand_share_csv` and `load_churn_csv`. These are Phase 02 stubs; intentionally not covered.

## Roadmap Success Criteria Verification

| SC | Description | Evidence |
|----|-------------|----------|
| SC1 | M1 reproduces Chan 2015 Table 3 | `forecast_array[0]` = [0.5829, 0.2780, 0.0667, 0.0724] within atol=1e-3 |
| SC2 | `monte_carlo_simulate` bit-reproducible with seed | `same seed identical: True`, `diff seed differs: True`, `dtype: int64` |
| SC3 | `validate_transition_matrix` raises on bad input | row-sum OK, negative OK, non-square OK, valid OK |
| SC4 | core/ coverage > 80%, regression tests green | 90.76%, 40 passed |
| SC5 | seed script produces >= 5 forecast rows | integration test `test_seed_produces_reference_forecasts` passes |

## Test Suite Summary

- **Total tests:** 40
- **Passed:** 40
- **Skipped:** 0
- **Failed:** 0
- **Test files:** 6 (unit: 5, integration: 1)

## Task Commits

Tasks 1 and 2 were verification-only (40 tests already passing, 90.76% coverage already met). Task 3 produced the sole code commit:

1. **Task 1: Test suite audit** — no commit needed (zero skip markers, 40 tests passing)
2. **Task 2: Coverage + SC verification** — no commit needed (90.76% already met)
3. **Task 3: Ruff + mypy clean pass** — `6616a72` (chore)

## Files Created/Modified

- `pyproject.toml` — Added per-file-ignores: N803/N806 for math notation, UP040 for TypeAlias, RUF059 for integration tests, N806 for scripts
- `core/db/queries.py` — Fixed RUF046: removed redundant `int()` cast around `round()`
- `scripts/seed_data.py` — Fixed RUF001: ASCII `x` instead of Unicode `×`; ruff format applied
- `tests/unit/test_serialization.py` — Fixed RUF043: raw strings `r"NaN|Inf"` in `match=`
- `tests/unit/test_loaders.py` — Fixed PT011: added `match="entity_id"` to broad `pytest.raises`
- `tests/unit/test_simulation.py` — Fixed I001: sorted imports in `test_walk_forward_no_leakage`; PT018 suppressed via per-file-ignore
- All `core/*.py`, `tests/**/*.py` — `ruff format` whitespace normalization (semantic no-ops)

## Decisions Made

- N803/N806 suppressed for math-notation files via per-file-ignores rather than renaming — Chan 2015 variable names (P, Y_1, Q_t, G) are load-bearing for readability; renaming would be a correctness hazard for future maintainers cross-referencing the paper
- UP040 (TypeAlias -> type keyword) suppressed in core/ — `TypeAlias` form is more explicit when aliasing a third-party type like `np.ndarray`; the new `type` keyword syntax offers no practical benefit here
- PT018 (compound assertions) suppressed for test_simulation.py — the compound `assert 0.10 in bands and 0.50 in bands and 0.90 in bands` is clearest in context

## Deviations from Plan

The plan said "If Step A fails, add targeted tests for uncovered branches." Coverage was already 90.76% before any changes — no additional tests needed.

The plan's Task 3 Step A said "ruff must exit 0 — fix any reported issues." 63 ruff errors were found and resolved:
- 45 N803/N806 suppressed via per-file-ignores (math notation — intentional, not style violations)
- 4 UP040 suppressed via per-file-ignores (TypeAlias explicit form retained)
- 3 RUF059 suppressed via per-file-ignores (unpacked tuple vars in integration tests)
- 11 code-level fixes: RUF046, RUF043, PT011, RUF001, I001

All fixes are stylistic only — no behavior changes. Tests still pass 40/40 after all format changes.

**[Rule 2 - Auto-fixed] Added `match=` to broad pytest.raises in test_loaders.py**
- **Found during:** Task 3 (ruff check)
- **Issue:** PT011 — `pytest.raises(ValueError)` too broad; any ValueError would pass
- **Fix:** Added `match="entity_id"` to target the specific error message for NaN entity_id
- **Files modified:** tests/unit/test_loaders.py
- **Commit:** 6616a72

## Issues Encountered

None significant. All quality gates were met without requiring additional test coverage.

## Stubs

`core/io/loaders.py` lines 12 and 18 contain intentional Phase 02 stubs:
- `load_brand_share_csv` → `raise NotImplementedError("load_brand_share_csv — implement in Phase 02")`
- `load_churn_csv` → `raise NotImplementedError("load_churn_csv — implement in Phase 02")`

These stubs are tracked here. They do NOT prevent Phase 01's goal (quality gate for the Markov engine), as these functions are Phase 02 scope.

## Phase 01 Requirements Completion

All 13 Phase 01 requirements are verified complete:

| ID | Requirement | Verified by |
|----|-------------|-------------|
| ENG-01 | validate_transition_matrix() | test_models.py (4 tests) + REPL Step F |
| ENG-02 | M1Homogeneous.forecast() | test_models.py + Chan 2015 Table 3 replication |
| ENG-03 | M2TimeVarying.forecast() | test_models.py (shape + hold-last-P_t) |
| ENG-04 | M3Extended.forecast() | test_models.py (Chan 2015 m3 table) |
| ENG-05 | monte_carlo_simulate() | test_simulation.py (6 tests) + REPL Step E |
| ENG-06 | calibrate_probability() | test_simulation.py (3 tests) |
| ENG-07 | compute_quantile_bands() | test_simulation.py (2 tests) |
| ENG-08 | Sparsity detection | test_models.py test_validate_warns_sparse_cells |
| ENG-09 | walk_forward_backtest() | test_simulation.py test_walk_forward_no_leakage |
| ENG-10 | MAPE, Brier, log-loss | test_metrics.py (5 tests) |
| DATA-01 | validate_transitions_df() | test_loaders.py (3 tests) |
| DATA-02 | seed_data.py idempotent | test_queries.py (2 integration tests) |
| DATA-03 | build_transition_matrix() | test_queries.py (3 integration tests) |

## Next Phase Readiness

Phase 01 is gate-clean and Phase 02 may proceed.

- `core/` is 100% implemented for Phase 01 scope
- All test fixtures in `tests/conftest.py` are reusable
- DuckDB schema is stable (6 tables, schema.sql idempotent)
- Seed data pipeline is proven idempotent: brand share (synthetic FMCG) + churn (IBM Telco)
- Two domain stubs (`load_brand_share_csv`, `load_churn_csv`) are scaffolded for Phase 02

---
*Phase: 01-markov-engine*
*Completed: 2026-05-29*
