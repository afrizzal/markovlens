---
phase: "04"
plan: "02"
subsystem: "app/Home.py"
tags: [home-dashboard, kpi-wiring, streamlit, duckdb, smoke-test]
dependency_graph:
  requires: [04-01-PLAN.md]
  provides: [wired-home-dashboard, home-smoke-test]
  affects: [app/Home.py, tests/unit/test_page_import.py]
tech_stack:
  added: []
  patterns: [importlib-mock-smoke-test, st.cache_resource, try-except-db-guard]
key_files:
  created: []
  modified:
    - app/Home.py
    - tests/unit/test_page_import.py
decisions:
  - "Home.py imports pandas inside the else-branch (only when recent forecasts exist) — no noqa needed since PLC0415 is not in ruff's enabled rule set"
  - "Smoke test mocks get_home_kpis at core.db.queries level (not app.Home) — matches the importlib exec_module load order"
  - "Merged master into worktree before Task 2 to bring in Plan 01 HomeKpis/RecentForecast (deviation Rule 3)"
metrics:
  duration: "9min"
  completed_date: "2026-06-01"
  tasks_completed: 2
  files_changed: 2
---

# Phase 04 Plan 02: Wire Home Dashboard Summary

Home.py rewritten to replace all hardcoded placeholders with real DuckDB data via the query helpers added in Plan 01. Smoke test added to verify the page loads without errors in a test environment.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rewrite app/Home.py with wired KPIs and Recent Forecasts | e1eaabd | app/Home.py |
| 2 | Add Home page smoke test to test_page_import.py | 885d325 | tests/unit/test_page_import.py |

## What Was Built

**Task 1 — app/Home.py rewrite:**
- KPI strip replaced: `st.metric()` placeholders → `kpi_card()` with real data from `get_home_kpis()`
- KPI 1 "Active Models" hardcoded to "3" (correct — always 3 model types)
- KPI 2 "Datasets Registered" → `_kpis.dataset_count`
- KPI 3 "Last Forecast (MAPE)" → `_kpis.avg_mape` formatted to 2dp, shows "—" if None
- KPI 4 "Simulations Run" → `_kpis.sim_run_count`
- Added `register_theme()` + `inject_theme()` calls (missing from scaffold)
- Removed conditional Churn page check — both pages are live, both `page_link()` calls unconditional
- Recent Forecasts: real `list_recent_forecasts(_db2, n=5)` call → `st.dataframe()` with icon/dataset/model/date/MAPE columns
- Empty state fallback via `empty_state()` component when no forecasts exist
- `try/except` guards around all DB calls — page never crashes on cold start without DB

**Task 2 — smoke test:**
- Added `HOME_PAGE_PATH`, `_load_home_page_module_importlib()`, and `test_home_page_imports_without_error()` to `tests/unit/test_page_import.py`
- Follows exact `importlib + mock.patch` pattern from Brand Share and Churn smoke tests
- Mocks: `core.db.connection.get_connection`, `core.db.queries.get_home_kpis`, `core.db.queries.list_recent_forecasts`
- Asserts `DOMAIN_ICON` and `_get_db` are present on the loaded module

## Verification

- `uv run ruff check app/Home.py` — all checks passed
- `uv run pytest tests/unit/test_page_import.py -q` — 4 passed (BS-06, overview sep, CH-04, HOME-01)
- `uv run pytest tests/ -q` — 95 passed (up from 94 before Plan 02)

## Deviations from Plan

**1. [Rule 3 - Blocking] Merged master into worktree to get Plan 01 code**
- **Found during:** Task 2 — `HomeKpis` and `RecentForecast` not importable in worktree
- **Issue:** This worktree was created before Plan 01 ran; `core/db/queries.py` lacked the query helpers
- **Fix:** `git merge master --no-commit` then committed, bringing in 13 Plan 01 files (queries.py, test files, planning docs)
- **Files modified:** core/db/queries.py, tests/integration/test_queries.py, tests/unit/test_home_queries.py, .planning/*
- **Commit:** 5d55bc5

## Known Stubs

None — all KPI values come from real DB queries. The empty-state fallback for Recent Forecasts is intentional behavior (not a stub), correctly triggered when the `forecasts` table is empty.

## Self-Check: PASSED

- `app/Home.py` exists and contains `get_home_kpis`, `list_recent_forecasts`, `register_theme`, `empty_state` imports
- Commit e1eaabd exists (Task 1)
- Commit 885d325 exists (Task 2)
- `grep "pages/2_Churn.py" app/Home.py` returns unconditional page_link at line 111
- `grep "if (_PAGES_DIR" app/Home.py` returns empty (conditional removed)
- 95 tests pass
