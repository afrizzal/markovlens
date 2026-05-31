---
phase: 03-churn-domain
plan: 01
subsystem: testing
tags: [pytest, churn, markov, duckdb, ruff, wave-0, test-scaffold]

# Dependency graph
requires:
  - phase: 02-design-system-brand-share
    provides: seeded_conn fixture pattern and integration test conventions (mirrored for churn)
  - phase: 01-markov-engine
    provides: core/db/queries.py (init_schema, register_dataset, bulk_insert_transitions)
provides:
  - Wave 0 unit test stubs for churn service (6 tests, importorskip-guarded)
  - Wave 0 integration test stubs with seeded_churn_conn fixture (6 tests, signature-guarded)
  - pyproject.toml ruff per-file-ignore for domains/churn/service.py
affects:
  - 03-02 (Plan 02 — service implementation must turn these stubs green)
  - 03-03 (Plan 03 — Sankey helper test activates on app/components/sankey_flow.py creation)
  - 03-04 (Plan 04 — page import smoke test is pre-wired)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Wave 0 test scaffold with importorskip + hasattr + inspect.signature guards for pre-implementation skipping
    - seeded_churn_conn fixture mirrors brand_share seeded_conn pattern with 3 churn states and domain="churn"
    - Signature-aware skip: detect old stub vs new API via inspect.signature(fn).parameters check

key-files:
  created:
    - tests/unit/test_churn_service.py
    - tests/integration/test_churn_service.py
  modified:
    - pyproject.toml

key-decisions:
  - "Wave 0 guard uses importorskip + hasattr + inspect.signature checks: old stub exists and imports fine, so importorskip alone is insufficient; attribute presence + signature conn-param check ensures clean skips before Plan 02 rewrites the service"
  - "seeded_churn_conn yields conn only (not tuple) unlike brand_share seeded_conn which yields (conn, dataset_id) — dataset_id is hardcoded ds_churn_test in all integration tests for simplicity"
  - "3 churn states for integration fixture: active/atrisk/churned (lowercase, case-insensitive lookup per RESEARCH Open Question 1); absorbing churned row enables compute_avg_lifetime transient-set check"

patterns-established:
  - "Signature guard pattern: inspect.signature(service.fn).parameters check detects old stub vs new API without relying on error trapping"
  - "5-state reference P matrix for unit tests: Active/At-Risk/Inactive/Reactivated/Churned with P[4,4]=0.98 near-absorbing, all rows sum to 1.0"

requirements-completed: [CH-01, CH-02, CH-03]

# Metrics
duration: 18min
completed: 2026-05-31
---

# Phase 03 Plan 01: Churn Domain Wave 0 Test Scaffold Summary

**Wave 0 test stubs for churn service — importorskip + signature guards, seeded_churn_conn fixture, ruff N803/N806/E731 suppressed for domains/churn/service.py**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-31T00:00:00Z
- **Completed:** 2026-05-31T00:18:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added ruff `["N803", "N806", "E731"]` per-file-ignore for `domains/churn/service.py` so Chan 2015 math variable names (P, Q, Y_1) and lambda helpers won't trigger ruff violations in Plan 02
- Created `tests/unit/test_churn_service.py` with 6 Wave 0 unit stubs covering compute_avg_lifetime (5-state reference P), all-absorbed None return, _apply_overrides renormalization, ChurnAnalysisResult fields, KPI_KEYS constant, and build_sankey_figure shape presence
- Created `tests/integration/test_churn_service.py` with 6 Wave 0 integration stubs and `seeded_churn_conn` fixture (3-state, 5-period, >=20 obs/cell, near-absorbing churned row)
- Full test suite: 61 passed, 12 skipped (Wave 0 guards working correctly)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ruff per-file-ignore for churn service** - `7b76a11` (chore)
2. **Task 2: Create unit test stubs for churn service + Sankey helper** - `58a5c68` (test)
3. **Task 3: Create integration test stubs + seeded_churn_conn fixture** - `fd11bce` (test)

## Files Created/Modified

- `pyproject.toml` — added `"domains/churn/service.py" = ["N803", "N806", "E731"]` immediately after brand_share entry
- `tests/unit/test_churn_service.py` — 6 unit test stubs with importorskip + hasattr guards
- `tests/integration/test_churn_service.py` — 6 integration test stubs + seeded_churn_conn fixture with signature-aware skip

## Decisions Made

- **Signature guard pattern adopted**: `inspect.signature(service.fn).parameters` check detects old stub vs new API. The old `domains/churn/service.py` stub imports cleanly (so `pytest.importorskip` doesn't skip), but has old signatures (`run_analysis(cohort_id, horizon)` instead of `run_analysis(conn, dataset_id, horizon)`). Adding a `"conn" not in parameters` guard keeps tests green until Plan 02 rewrites the service.
- **seeded_churn_conn yields `conn` only** (not a `(conn, dataset_id)` tuple like brand_share). All 6 integration tests hardcode `"ds_churn_test"` — simpler and avoids tuple destructuring errors.
- **3 states for integration fixture**: `active/atrisk/churned` (lowercase, matching RESEARCH Open Question 1 case-insensitive lookup). Absorbing churned row ensures `compute_avg_lifetime` has a valid transient submatrix to invert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added inspect.signature guard on top of importorskip + hasattr**
- **Found during:** Task 2 (unit tests) and Task 3 (integration tests)
- **Issue:** Old `domains/churn/service.py` stub imports successfully (importorskip doesn't fire) and has `run_analysis`/`simulate_scenario` attributes (hasattr passes) but with wrong signatures (`cohort_id` vs `conn`). Tests fail with `TypeError: multiple values for argument` or `TypeError: takes 2 positional arguments but 4 were given`.
- **Fix:** Added `import inspect; if "conn" not in inspect.signature(service.fn).parameters: pytest.skip(...)` after each hasattr guard. Unit tests use `hasattr` alone where sufficient (compute_avg_lifetime, _apply_overrides, KPI_KEYS don't exist in old stub at all).
- **Files modified:** `tests/unit/test_churn_service.py`, `tests/integration/test_churn_service.py`
- **Verification:** `uv run pytest tests/ -q` → 61 passed, 12 skipped
- **Committed in:** `58a5c68` (Task 2), `fd11bce` (Task 3)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug from pre-existing stub with wrong signatures)
**Impact on plan:** The guard pattern is stricter than plan specified but preserves the same Wave 0 behavior — tests skip until Plan 02 produces the correct service.

## Issues Encountered

The existing `domains/churn/service.py` stub has old-style signatures (`cohort_id` positional, `list_cohorts()` instead of `list_datasets()`). This caused test failures at the hasattr-pass level. Resolved by adding signature inspection guards. No plan change required.

## Known Stubs

None — this plan only creates test scaffolding; no application code was created.

## Next Phase Readiness

- Plan 02 (`03-02-PLAN.md`) can now be executed. When `domains/churn/service.py` is rewritten with correct API, all 12 Wave 0 tests will auto-activate and run for real.
- The `seeded_churn_conn` fixture is ready for Plan 02 integration tests.
- `build_sankey_figure` test (`test_build_sankey_figure`) will activate in Plan 03 when `app/components/sankey_flow.py` is created.

---
*Phase: 03-churn-domain*
*Completed: 2026-05-31*
