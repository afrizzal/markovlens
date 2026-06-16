---
phase: 05-quality-assurance-deployment
plan: 02
subsystem: deployment-seeding
tags: [cold-start, auto-seed, streamlit-cloud, deploy-01, db-init]
dependency_graph:
  requires: [core/db/connection.py, core/db/schema.sql, scripts/seed_data.py]
  provides: [core/db/init.ensure_seeded, app/db.get_db]
  affects: [app/Home.py, app/pages/1_Brand_Share.py, app/pages/2_Churn.py, app/pages/4_Settings.py, tests/unit/test_page_import.py]
tech_stack:
  added: []
  patterns: [forecasts-table sentinel, env-aware failure guard, deferred import for cold path, fetchone None-guard]
key_files:
  created:
    - core/db/init.py
    - app/db.py
    - tests/unit/test_db_init.py
  modified:
    - app/Home.py
    - app/pages/1_Brand_Share.py
    - app/pages/2_Churn.py
    - app/pages/4_Settings.py
    - tests/unit/test_page_import.py
    - scripts/seed_data.py
decisions:
  - "forecasts table used as seed sentinel (D-04): populated last by seed pipeline, non-zero count is reliable 'seed complete' signal"
  - "deferred import of numpy/scripts.seed_data inside ensure_seeded cold path: keeps core/db/init.py import-light on warm reruns"
  - "BLE001 and PLC0415 noqa directives removed: those rules are not in pyproject.toml ruff select list"
  - "scripts/seed_data.py fetchone None-guard added: surfaced by mypy when import chain via core/db/init.py pulled scripts/ into type check scope"
metrics:
  duration_min: 14
  completed_date: "2026-06-16"
  tasks_completed: 4
  files_changed: 8
requirements_satisfied: [DEPLOY-01]
---

# Phase 05 Plan 02: Cold-Start Auto-Seeding (DEPLOY-01) Summary

Implemented DEPLOY-01 cold-start auto-seeding so the Streamlit Cloud deployment populates demo data on first load via a forecasts-table sentinel pattern.

## What Was Built

### core/db/init.py — ensure_seeded() sentinel

`ensure_seeded(conn)` checks `SELECT COUNT(*) FROM forecasts`. If count > 0, returns immediately (fast path — warm rerun, no cost). If count = 0, defers import of `numpy` and `scripts.seed_data` and calls `_seed_brand_share` + `_seed_churn`. The deferred import pattern keeps `core/db/init.py` import-light — no NumPy/Pandas at module level on warm reruns. The `forecasts` table is the sentinel because the seed pipeline populates it LAST, making a non-zero count the most reliable "seed complete" signal (D-04).

### app/db.py — shared get_db() with spinner + env-aware guard

`@st.cache_resource(show_spinner="Preparing demo data…")` wraps `get_connection()` + `ensure_seeded(conn)`. The env-aware failure guard (D-08): if seed fails in `development`, surfaces `st.error + st.exception`; in `production`, shows `st.warning` and the page still renders. The `show_spinner` fires only on cache miss (cold start), silent on warm reruns (D-05/D-06).

### 5 pages wired to shared get_db()

All five entry points (Home + 4 pages) now import and call `get_db()` from `app/db.py`:

| File | Local _get_db removed | Import added | Call sites updated |
|------|----------------------|--------------|-------------------|
| app/Home.py | yes | from app.db import get_db | 2 |
| app/pages/1_Brand_Share.py | yes | from app.db import get_db | 5 |
| app/pages/2_Churn.py | yes | from app.db import get_db | 3 |
| app/pages/4_Settings.py | yes | from app.db import get_db | 1 |

The `st.cache_resource.clear()` in Settings Re-run seed button is preserved — it correctly clears the shared `get_db()` cache so the next call re-runs `ensure_seeded` after the manual reseed.

### tests/unit/test_db_init.py — 2 new unit tests

- `test_ensure_seeded_fast_path_when_forecasts_present`: inserts datasets + forecasts row, monkeypatches `_seed_brand_share`/`_seed_churn` — asserts neither is called (fast path).
- `test_ensure_seeded_runs_pipeline_when_empty` (`@pytest.mark.integration`): fresh DuckDB, assert pre-count=0, call `ensure_seeded`, assert post-count >= 5. Exercises the real seed pipeline against `data/seed/telco_churn.csv` (D-09). No network required.

### tests/unit/test_page_import.py — smoke test updates

- Added `patch("core.db.init.ensure_seeded", return_value=None)` to all 4 page loaders.
- Updated stale `hasattr(mod, "_get_db")` to `hasattr(mod, "get_db")` in Home and Settings assertions.

### D-15 mkdir guard confirmed

`core/db/connection.py` line 18: `settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)` — confirmed present before `duckdb.connect()`. No changes needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] FK constraint violation in fast-path test**
- **Found during:** Task 1 RED-GREEN cycle
- **Issue:** Test inserted a `forecasts` row without a parent `datasets` row — DuckDB FK constraint raised `ConstraintException`.
- **Fix:** Added `INSERT INTO datasets` before `INSERT INTO forecasts` in the test.
- **Files modified:** tests/unit/test_db_init.py
- **Commit:** e1f3951

**2. [Rule 1 - Bug] Unused noqa directives (BLE001, PLC0415)**
- **Found during:** Task 4 ruff check
- **Issue:** Plan template included noqa for rules not in pyproject.toml `select` list, causing `RUF100` errors.
- **Fix:** Removed both noqa directives; replaced with plain comments documenting the intent.
- **Files modified:** app/db.py, core/db/init.py
- **Commit:** 003f5dc, b6bd079

**3. [Rule 1 - Bug] mypy fetchone None-guard — core/db/init.py and scripts/seed_data.py**
- **Found during:** Task 4 mypy gate
- **Issue:** `fetchone()[0]` typed as `tuple | None` by mypy; indexing `None` is a type error. core/db/init.py was new code. scripts/seed_data.py errors were pre-existing but surfaced when `ensure_seeded`'s deferred import pulled `scripts/` into mypy's reachable-modules set.
- **Fix:** `core/db/init.py`: two-liner `row = fetchone(); count = row[0] if row is not None else 0`. `scripts/seed_data.py`: extracted `_count(table)` helper with same None-guard for 4 verify queries.
- **Files modified:** core/db/init.py, scripts/seed_data.py
- **Commit:** b6bd079

## Quality Gate Results

| Check | Result |
|-------|--------|
| D-15 mkdir guard | Confirmed at connection.py:18 |
| `grep -rn "import streamlit" core/` | No matches — core/ stays pure |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check` (plan files) | 8 files already formatted |
| `uv run mypy core/ domains/` | Success: no issues found in 18 source files |
| `uv run pytest -m "not slow"` | 103 passed, 0 failed |

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 | e1f3951 | feat(05-02): add ensure_seeded() cold-start sentinel + unit tests |
| Task 2 | 003f5dc | feat(05-02): create shared app/db.py get_db() and wire all 5 pages |
| Task 3 | 8cacab8 | fix(05-02): update page smoke tests for new app/db.py layer |
| Task 4 | b6bd079 | fix(05-02): mypy clean — fetchone None-guard in core/db/init.py + scripts/seed_data.py |

## Known Stubs

None — ensure_seeded calls the real seed pipeline; get_db() wires real connection; no placeholder data paths.

## Self-Check: PASSED

Files created confirmed present. All 4 commits confirmed in git log.
