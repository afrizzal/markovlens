---
phase: 05-quality-assurance-deployment
plan: 01
subsystem: testing
tags: [pytest, coverage, markov, unit-tests, branch-coverage]

# Dependency graph
requires:
  - phase: 01-markov-engine
    provides: core/models.py, core/simulation.py (ENG-01..ENG-10)
provides:
  - Targeted branch-coverage tests closing D-02 gaps in core/models.py and core/simulation.py
  - 17 new test functions across test_models.py and test_simulation.py
  - Full suite green at 118 tests, 0 failures
  - Integration gate (pytest -m integration) passing at 20 tests
  - core/ coverage 96%, domains/ coverage ~83%
affects: [05-02, 05-03, 05-04, deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pytest.raises(ValueError, match=...) — always supply match= to satisfy PT011"
    - "Import ordering in tests: stdlib (unittest.mock) before third-party (pandas)"

key-files:
  created: []
  modified:
    - tests/unit/test_models.py
    - tests/unit/test_simulation.py

key-decisions:
  - "PT011 requires match= in pytest.raises(ValueError) — added specific substrings from actual error messages"
  - "Import ordering: unittest.mock is stdlib, must come before pandas (third-party) — ruff I001"
  - "compute_stationary exception branches (L116-117, L132-134) left uncovered — triggering both-fail path is unreliable; 96% core/ coverage exceeds 80% threshold"

patterns-established:
  - "Branch-coverage tests: import-inside-test style, AAA, match= on ValueError raises"

requirements-completed: [QA-01, QA-02, QA-03]

# Metrics
duration: 7min
completed: 2026-06-16
---

# Phase 05 Plan 01: Test Suite Quality Gate Summary

**17 targeted branch-coverage tests added closing D-02 gaps; core/ 96%, domains/ ~83%, full suite 118/118 green, integration gate 20/20**

## Performance

- **Duration:** 7 min
- **Started:** 2026-06-16T06:51:22Z
- **Completed:** 2026-06-16T06:58:00Z
- **Tasks:** 3 (2 TDD + 1 verification gate)
- **Files modified:** 2

## Accomplishments

- 11 new tests in test_models.py covering: ndim/NaN validate_transition_matrix branches, compute_stationary success + trivial paths, M2/M3 constructor validation, M3 2-D G else-branch (L260)
- 6 new tests in test_simulation.py covering: 1-D extractor ValueError guard (L165), empty-df returns in _counts_from_long_df (L185) and _state_distribution_from_long_df (L205), no-weight-column branch (L247), too-few-periods early return (L255), mape exception to None (L279)
- Full suite green: 118 passed, 0 failed, 0 unexpected skips
- QA-02 integration gate explicit: pytest -m integration 20 passed
- Coverage: core/ 96%, domains/ ~83% (both above QA-01/QA-03 thresholds)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add targeted tests for core/models.py** - `e0ad660` (test)
2. **Task 2: Add targeted tests for core/simulation.py** - `bc1d5b2` (test)
3. **Ruff fix: PT011 + I001 cleanup** - `e63f69d` (fix — deviation auto-fix)

## Coverage Numbers (Observed)

| Module | Coverage |
|--------|----------|
| core/models.py | 96% |
| core/simulation.py | 100% |
| core/metrics.py | 96% |
| core/db/queries.py | 96% |
| core/io/loaders.py | 88% |
| **core/ total** | **96%** |
| domains/brand_share/service.py | 81% |
| domains/churn/service.py | 86% |
| **domains/ total** | **~83%** |

## Integration Gate (QA-02)

```
pytest -m integration
20 passed, 98 deselected in 9.10s
```

Tests: tests/integration/test_queries.py (8), tests/integration/test_brand_share_service.py (5), tests/integration/test_churn_service.py (7).

Note: 05-02's marked integration test is not yet present. The existing 20 integration tests satisfy QA-02 as confirmed by D-03.

## Files Created/Modified

- `tests/unit/test_models.py` — 11 new tests appended
- `tests/unit/test_simulation.py` — 6 new tests appended

## Decisions Made

- PT011 requires match= on pytest.raises(ValueError) — added specific substrings from actual error messages.
- Import ordering: unittest.mock is stdlib and must precede third-party pandas imports — ruff I001 enforced.
- The compute_stationary dual-fallback branches (L116-117, L132-134) remain at 0% coverage because triggering both scipy.linalg.eig AND power-iteration to fail simultaneously on a plausible matrix is unreliable. Core coverage is 96% which exceeds the 80% threshold.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PT011 ruff violations on pytest.raises(ValueError)**
- **Found during:** Task 3 (ruff check gate)
- **Issue:** Plan code examples used bare pytest.raises(ValueError) without match= parameter, which triggers ruff PT011
- **Fix:** Added match= with specific substrings from actual error messages (e.g., match="must be 3D", match="G must be 1D", match="must return a 2-D")
- **Files modified:** tests/unit/test_models.py, tests/unit/test_simulation.py
- **Verification:** ruff check exits 0 on both files
- **Committed in:** e63f69d

**2. [Rule 1 - Bug] I001 import ordering in test_walk_forward_mape_exception_sets_none**
- **Found during:** Task 3 (ruff check gate)
- **Issue:** import pandas as pd before from unittest.mock import patch — stdlib must come first
- **Fix:** Reordered to stdlib (unittest.mock) then third-party (pandas) then local
- **Files modified:** tests/unit/test_simulation.py
- **Verification:** ruff check exits 0
- **Committed in:** e63f69d

---

**Total deviations:** 2 auto-fixed (both Rule 1 — ruff lint violations from plan code samples)
**Impact on plan:** Both fixes required for ruff clean. No logic change, no scope creep.

## Issues Encountered

None — all tests passed on first run after ruff fixes.

## Known Stubs

None — this plan adds test code only; no production code was created or modified.

## Next Phase Readiness

- QA-01 satisfied: core/ coverage 96% (>80%)
- QA-02 satisfied: pytest -m integration 20 passed
- QA-03 satisfied: domains/ coverage ~83% (>60%)
- Phase 05 Plan 02 can proceed independently

## Self-Check: PASSED

Commits verified: e0ad660, bc1d5b2, e63f69d all present in git log.
Files verified: tests/unit/test_models.py and tests/unit/test_simulation.py confirmed modified.

---
*Phase: 05-quality-assurance-deployment*
*Completed: 2026-06-16*
