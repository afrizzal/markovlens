---
phase: 04-home-export-settings
plan: 01
subsystem: database
tags: [duckdb, queries, dataclass, testing, home-kpi]

# Dependency graph
requires:
  - phase: 01-markov-engine
    provides: DuckDB schema (6 tables), core/db/queries.py Dataset dataclass and query helpers
provides:
  - HomeKpis dataclass with dataset_count, sim_run_count, last_forecast_at, avg_mape
  - get_home_kpis() query function for Home dashboard KPI strip
  - RecentForecast dataclass with forecast_id, dataset_name, domain, model_type, created_at, mape
  - list_recent_forecasts() query function returning newest N forecasts with dataset JOIN
  - Dataset.created_at field (datetime | None) in existing Dataset dataclass
  - 5 unit tests in tests/unit/test_home_queries.py
  - 3 integration tests + seeded_conn fixture in tests/integration/test_queries.py
affects:
  - 04-02 (Home KPI wiring — consumes get_home_kpis + list_recent_forecasts)
  - 04-04 (Settings page — consumes list_datasets which now returns created_at)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "avg_mape via TRY_CAST(json_extract_string(..., '$.mape') AS DOUBLE) — DuckDB JSONPath on accuracy_metrics_json"
    - "seeded_conn pytest fixture pattern for integration tests requiring a pre-populated DuckDB"

key-files:
  created:
    - tests/unit/test_home_queries.py
  modified:
    - core/db/queries.py

key-decisions:
  - "seeded_conn fixture defined in test_queries.py (not conftest.py) — scope is integration-only, no cross-suite sharing needed"
  - "Dataset.created_at added as last field to avoid breaking positional construction (all callers use keyword args in queries.py)"
  - "TRY_CAST used for JSON mape extraction — guards against malformed rows without raising"

patterns-established:
  - "HomeKpis/RecentForecast follow @dataclass(frozen=True) value-object pattern consistent with SimulationResult"
  - "Integration tests that need DB state use a local fixture (not the global singleton) per connection hygiene rule"

requirements-completed: [HOME-01, RPT-01, SET-01]

# Metrics
duration: 9min
completed: 2026-06-01
---

# Phase 04 Plan 01: Query Helpers + Wave 0 Tests Summary

**Extended core/db/queries.py with HomeKpis/RecentForecast dataclasses + get_home_kpis/list_recent_forecasts functions, added Dataset.created_at, and wrote 8 new tests (5 unit + 3 integration) covering the new query layer**

## Performance

- **Duration:** 9 min
- **Started:** 2026-06-01T19:10:19Z
- **Completed:** 2026-06-01T19:19:00Z
- **Tasks:** 5 (+ 1 auto-fix)
- **Files modified:** 3

## Accomplishments

- Added `HomeKpis` dataclass (4 fields) and `get_home_kpis()` query using DuckDB JSONPath to parse avg MAPE from `accuracy_metrics_json`
- Added `RecentForecast` dataclass (6 fields) and `list_recent_forecasts()` with LEFT JOIN to datasets, ordered by `created_at DESC`
- Extended `Dataset` dataclass with `created_at: datetime | None` and updated both `list_datasets()` and `get_dataset()` queries
- 5 unit tests pass (dataclass field contracts + empty-DB behavior)
- 3 integration tests pass including a full INSERT + query round-trip verifying mape precision

## Task Commits

Each task was committed atomically:

1. **Task 1: Dataset.created_at + list_datasets/get_dataset** - `2481e9a` (feat)
2. **Task 2: HomeKpis + get_home_kpis()** - `6ac57ef` (feat)
3. **Task 3: RecentForecast + list_recent_forecasts()** - `b15748d` (feat)
4. **Task 4: Unit test stubs** - `915be67` (test)
5. **Task 5: Integration tests + seeded_conn fixture** - `120b490` (test)
6. **Auto-fix: Remove unused pytest import** - `03175d0` (fix)

## Files Created/Modified

- `core/db/queries.py` - Added `datetime` import, `Dataset.created_at` field, updated `list_datasets`/`get_dataset` SELECTs, appended `HomeKpis`/`get_home_kpis`/`RecentForecast`/`list_recent_forecasts`
- `tests/unit/test_home_queries.py` - New: 5 unit tests covering dataclass field contracts and empty-DB behavior
- `tests/integration/test_queries.py` - Appended: `seeded_conn` fixture + 3 integration tests for new query functions

## Decisions Made

- `seeded_conn` fixture placed in `test_queries.py` rather than `conftest.py` — it is only needed by integration tests in this file; global conftest would expose it to all test files unnecessarily
- `TRY_CAST` over plain `CAST` for JSON mape extraction — real data may have malformed or missing mape keys; `TRY_CAST` returns NULL rather than raising, keeping `avg_mape` nullable
- `Dataset.created_at` added as the last field to preserve any future positional construction (safe — no callers use positional args outside queries.py)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused `pytest` import from test_home_queries.py**
- **Found during:** Final ruff check after Task 4
- **Issue:** `import pytest` was included in the test file but never used — ruff F401 violation
- **Fix:** Removed the unused import line
- **Files modified:** `tests/unit/test_home_queries.py`
- **Verification:** `uv run ruff check tests/unit/test_home_queries.py` passes clean
- **Committed in:** `03175d0`

**2. [Rule 2 - Missing Critical] Added seeded_conn fixture to test_queries.py**
- **Found during:** Task 5 implementation
- **Issue:** Plan's integration tests reference `seeded_conn` fixture but it doesn't exist anywhere in the test suite
- **Fix:** Added `seeded_conn` pytest fixture that creates a temp DuckDB, runs `init_schema()`, and inserts one dataset row — placed directly in `test_queries.py` above the Phase 04 tests
- **Files modified:** `tests/integration/test_queries.py`
- **Verification:** All 3 integration tests pass; the fixture is scoped to the file correctly
- **Committed in:** `120b490` (Task 5 commit)

---

**Total deviations:** 2 auto-fixed (1 linting fix, 1 missing fixture)
**Impact on plan:** Both fixes essential for test correctness. No scope creep.

## Issues Encountered

None — all queries executed cleanly; DuckDB JSONPath syntax `$.mape` with `json_extract_string` + `TRY_CAST` worked correctly on first attempt.

## Known Stubs

None — this plan adds only data-access layer code. No UI rendering or page wiring performed here. Stubs exist in `app/Home.py` (KPI wiring pending Plan 02), but those are not part of this plan's scope.

## Next Phase Readiness

- `get_home_kpis()` and `list_recent_forecasts()` are ready for Plan 02 to wire into `app/Home.py`
- `Dataset.created_at` is available for Plan 04 (Settings page) to display dataset age
- Full test suite at 94/94 pass (previously 76/76 — added 18 net tests including prior integration suite)

## Self-Check: PASSED

- FOUND: core/db/queries.py
- FOUND: tests/unit/test_home_queries.py
- FOUND: tests/integration/test_queries.py
- FOUND: .planning/phases/04-home-export-settings/04-01-SUMMARY.md
- FOUND: commit 2481e9a (Task 1)
- FOUND: commit 6ac57ef (Task 2)
- FOUND: commit b15748d (Task 3)
- FOUND: commit 915be67 (Task 4)
- FOUND: commit 120b490 (Task 5)
- FOUND: commit 03175d0 (auto-fix)
- FOUND: commit 89e744f (metadata)

---
*Phase: 04-home-export-settings*
*Completed: 2026-06-01*
