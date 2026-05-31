---
phase: 04-home-export-settings
plan: "03"
subsystem: app/pages
tags: [csv-export, rpt-01, download-button, unit-tests]
dependency_graph:
  requires: [04-01-PLAN.md]
  provides: [RPT-01 CSV download in Brand Share and Churn pages]
  affects: [app/pages/1_Brand_Share.py, app/pages/2_Churn.py, tests/unit/test_csv_export.py]
tech_stack:
  added: []
  patterns: [csv.writer + io.StringIO for stdlib-only CSV bytes, st.download_button for in-page export]
key_files:
  created: [tests/unit/test_csv_export.py]
  modified: [app/pages/1_Brand_Share.py, app/pages/2_Churn.py]
decisions:
  - "CSV bytes built via io.StringIO + csv.writer (stdlib only, D-08)"
  - "Filename pattern: markovlens_{domain}_forecast_{timestamp}.csv (D-09)"
  - "Download button visible only when result in session state, placed after KPI strip (D-10)"
  - "BrandShareForecastResult uses forecasts dict not m1_forecast fields — adapted CSV helper accordingly"
  - "Removed emoji from download button label (project-rules.md rule 17)"
metrics:
  duration_seconds: 438
  tasks_completed: 3
  files_modified: 2
  files_created: 1
  completed_date: "2026-06-01"
---

# Phase 04 Plan 03: CSV Export (RPT-01) Summary

CSV download buttons added to both domain pages: Brand Share and Churn. Each generates a two-section CSV (Forecast rows + Transition Matrix) via stdlib `csv.writer`, with 5 unit tests verifying format invariants.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add _brand_share_csv_bytes helper + download button to Brand Share | f44a1d1 | app/pages/1_Brand_Share.py |
| 2 | Add _churn_csv_bytes helper + download button to Churn | aba5b71 | app/pages/2_Churn.py |
| 3 | Create unit tests for CSV helper logic | 9b1d6ed | tests/unit/test_csv_export.py |

## What Was Built

**Brand Share page (1_Brand_Share.py):**
- Added `csv`, `io`, `datetime` stdlib imports
- Added `_brand_share_csv_bytes(result)` helper: uses `result.forecasts[result.best_model]` for the forecast section, then `result.transition_matrix` for the matrix section
- Added `st.download_button` after KPI strip; visible only when `brand_share.result` in session state

**Churn page (2_Churn.py):**
- Added `csv`, `io`, `datetime` stdlib imports
- Added `_churn_csv_bytes(result)` helper: uses `result.baseline_forecast` for forecast section, then `result.transition_matrix` for matrix section
- Added `st.download_button` after KPI strip; visible only when `churn.result` in session state

**CSV format (both domains):**
```
# Forecast,model=m1
period,State1,State2,...
0,0.450000,...
...
(empty row)
# Transition Matrix
from_state,State1,State2,...
State1,0.900000,...
```

**Unit tests (tests/unit/test_csv_export.py):**
- `test_brand_share_csv_has_forecast_section` — both section headers present
- `test_csv_forecast_rows_count` — one data row per forecast period
- `test_csv_column_headers_match_state_labels` — state labels in header
- `test_csv_transition_matrix_rows_sum_to_one` — matrix probabilities sum to 1.0
- `test_csv_bytes_is_utf8_encoded` — returns bytes, decodable as UTF-8

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] BrandShareForecastResult interface mismatch**
- **Found during:** Task 1
- **Issue:** Plan specified `m1_forecast`, `m2_forecast`, `m3_forecast` as separate fields, but the actual `BrandShareForecastResult` uses `forecasts: dict[str, np.ndarray]` keyed by model id. The plan's `<interfaces>` block was describing a hypothetical structure.
- **Fix:** Used `result.forecasts.get(result.best_model) or result.forecasts["m1"]` instead
- **Files modified:** app/pages/1_Brand_Share.py
- **Commit:** f44a1d1

**2. [Rule 2 - Convention] Removed emoji from button label**
- **Found during:** Tasks 1 and 2
- **Issue:** Plan used "⬇ Download forecast CSV" with emoji; project-rules.md Rule 17 forbids emojis as functional icons
- **Fix:** Label changed to "Download forecast CSV" / "Download churn CSV"
- **Files modified:** app/pages/1_Brand_Share.py, app/pages/2_Churn.py
- **Commit:** f44a1d1, aba5b71

**3. [Rule 1 - Lint] RUF005 and UP037 fixes**
- **Found during:** Task 1
- **Issue:** Initial implementation used `["period"] + labels` (RUF005) and quoted type annotation `"service.BrandShareForecastResult"` (UP037)
- **Fix:** Changed to `["period", *labels]` spread syntax and unquoted type annotation
- **Files modified:** app/pages/1_Brand_Share.py
- **Commit:** f44a1d1

**4. [Adaptation] Test file uses inline reimplementation**
- Plan specified inline reimplementation in the test file for Streamlit-import isolation — followed as specified. Tests do not import app pages.

## Verification Results

- `uv run ruff check app/pages/1_Brand_Share.py app/pages/2_Churn.py tests/unit/test_csv_export.py` — all clean
- `uv run pytest tests/unit/test_csv_export.py -q` — 5/5 passed
- `uv run pytest tests/ --ignore=tests/integration -q` — 74/74 passed (no regressions)
- Both pages have `st.download_button` and CSV helper functions confirmed via grep

## Known Stubs

None. The download buttons are wired to live session state data; they only appear when a real forecast result exists.

## Self-Check: PASSED

- app/pages/1_Brand_Share.py — modified, syntax OK, ruff clean
- app/pages/2_Churn.py — modified, syntax OK, ruff clean
- tests/unit/test_csv_export.py — created, 5 tests pass
- Commits f44a1d1, aba5b71, 9b1d6ed — verified in git log
