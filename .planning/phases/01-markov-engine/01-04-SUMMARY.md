---
phase: 01-markov-engine
plan: 04
subsystem: database
tags: [duckdb, serialization, json, transition-matrix, sql, validation]

requires:
  - phase: 01-02
    provides: validate_transition_matrix (used to validate built matrices)
provides:
  - core/db/serialization.py (ndarray<->JSON with NaN/Inf rejection)
  - build_transition_matrix (parameterized GROUP BY -> validated stochastic matrix + counts)
  - validate_transitions_df (DATA-01 boundary validator)
affects: [01-05, 02-brand-share, 03-churn, 04-home]

tech-stack:
  added: []
  patterns:
    - "ndarray persisted as JSON nested list; NaN/Inf rejected at boundary (D-24)"
    - "build_transition_matrix uses ? parameter binding — never f-string SQL"
    - "Zero-observation rows become absorbing self-loops to keep matrix row-stochastic"

key-files:
  created:
    - core/db/serialization.py
  modified:
    - core/db/queries.py
    - core/io/loaders.py
    - tests/unit/test_serialization.py
    - tests/unit/test_loaders.py
    - tests/integration/test_queries.py

key-decisions:
  - "Zero-outgoing-transition states map to absorbing self-loop (P[i,i]=1.0) so build_transition_matrix output passes validate_transition_matrix — standard Markov convention; not in the plan's literal code."
  - "Omitted plan-requested `import numpy as np` in loaders.py: validate_transitions_df uses only pandas; adding it would be an unused import (ruff F401)."
  - "Used unquoted duckdb.DuckDBPyConnection annotation (file has from __future__ import annotations) — avoids UP037 and mypy resolves it."

patterns-established:
  - "All persistence SQL parameterized in core/db/queries.py; matrices validated before return"

requirements-completed: [DATA-01, DATA-03]

duration: 7min
completed: 2026-05-29
---

# Phase 01 Plan 04: Data Layer Summary

**DuckDB data layer: ndarray↔JSON serialization (NaN/Inf-guarded), `build_transition_matrix` (parameterized GROUP BY → validated row-stochastic matrix + counts), and `validate_transitions_df` — 10 covered tests green, mypy clean.**

## Performance

- **Duration:** ~7 min
- **Completed:** 2026-05-29T08:52:51+07:00
- **Tasks:** 3 (TDD)
- **Files modified:** 6 (1 created)

## Accomplishments
- `core/db/serialization.py`: `ndarray_to_json`/`json_to_ndarray`, round-trips 1D/2D/3D float64, rejects NaN/Inf at boundary (D-24)
- `validate_transitions_df` in loaders.py: required-column + NaN guard (DATA-01); Phase 02 stubs untouched
- `build_transition_matrix` in queries.py: parameterized GROUP BY filtered by dataset_id (+optional period), returns `(float64 matrix, int64 counts)`, validates result; zero-obs rows → self-loops
- e2e verified: rows sum `[1.0, 1.0]`, counts total `20`, JSON round-trip `True`

## Task Commits

1. **Task 1: serialization.py** - `6c49af6` (feat) — 4 tests
2. **Task 2: validate_transitions_df** - `2eb18b0` (feat) — 3 tests
3. **Task 3: build_transition_matrix** - `abb74af` (feat) — 3 integration tests

## Files Created/Modified
- `core/db/serialization.py` (new) - JSON serialization helpers
- `core/db/queries.py` - added build_transition_matrix + imports
- `core/io/loaders.py` - added validate_transitions_df + REQUIRED_TRANSITION_COLUMNS
- 3 test files - un-skipped (4 serialization, 3 loaders, 3 build_transition; 2 seed stay skipped for Plan 05)

## Decisions Made
See key-decisions frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] build_transition_matrix failed on states with no outgoing transitions**
- **Found during:** Task 3 (test_build_transition_matrix_filters_dataset). ds_a had only `A→` rows, so state B's row was all-zeros → failed `validate_transition_matrix` (row ≠ 1.0).
- **Fix:** Map zero-observation rows to absorbing self-loops (`matrix[i,i]=1.0`) before validation. Standard Markov convention; `counts` unaffected (filtering assertion `counts.sum()==2` still holds).
- **Committed in:** `abb74af`

**2. [Rule 1 - Bug] Plan-requested unused numpy import in loaders.py**
- **Found during:** Task 2. Plan said add `import numpy as np`, but validate_transitions_df uses only pandas → would be ruff F401.
- **Fix:** Omitted the unused import. pandas (already present) is sufficient.
- **Committed in:** `2eb18b0`

---

**Total deviations:** 2 auto-fixed. **Impact:** build_transition_matrix is now robust for sparse data; no scope creep.

## Issues Encountered
- **ruff (deferred to 01-06):** same project-wide math-notation/UP040 debt. **mypy clean on all 3 new/modified core files.**

## Next Phase Readiness
- **Ready for Plan 01-05 (Wave 4, seed script — CHECKPOINT):** serialization + build_transition_matrix + validate_transitions_df all available. `test_seed_idempotency` and `test_seed_produces_reference_forecasts` remain skipped, waiting for the seed script.
- Plan 01-05 is `autonomous: false` — it needs the IBM Telco CSV committed at `data/seed/telco_churn.csv` (human action).

---
*Phase: 01-markov-engine*
*Completed: 2026-05-29*
