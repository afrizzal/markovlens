---
phase: 01-markov-engine
plan: 01
subsystem: testing
tags: [pytest, test-scaffolding, tdd, wave-0]

requires: []
provides:
  - Skip-annotated test stubs for every Phase 01 requirement (ENG-01..10, DATA-01..03)
  - 4 un-skipped model tests now blocked only by NotImplementedError (RED state ready for Plan 02)
  - Named, importable test targets so Waves 2-5 just remove the skip decorator after implementing
affects: [01-02, 01-03, 01-04, 01-05, 01-06]

tech-stack:
  added: []
  patterns:
    - "Wave 0 stub pattern: @pytest.mark.skip(reason=\"Wave 0 stub — implementation in later wave\")"
    - "Deferred imports inside test bodies so collection passes before modules/functions exist"

key-files:
  created:
    - tests/unit/test_simulation.py
    - tests/unit/test_metrics.py
    - tests/unit/test_loaders.py
    - tests/unit/test_serialization.py
    - tests/integration/test_queries.py
  modified:
    - tests/unit/test_models.py

key-decisions:
  - "Scaffolding plan marks ZERO requirements complete — stubs are not implementations. Each requirement is marked complete by its implementing plan (02-05); 01-06 re-affirms all 13."
  - "Followed PLAN skip reason 'Wave 0 stub — implementation in later wave' (not VALIDATION.md's 'Wave 0 — not yet implemented') because the PLAN acceptance_criteria grep for that exact prefix."

patterns-established:
  - "Wave 0 stub: every downstream-required test exists up front, skip-annotated, with deferred imports"

requirements-completed: []

duration: 6min
completed: 2026-05-29
---

# Phase 01 Plan 01: Test Infrastructure Summary

**Scaffolded 40 pytest test targets (4 un-skipped model RED tests + 36 skip-annotated stubs) covering every Phase 01 requirement, so Waves 2-5 implement against a waiting test instead of a scavenger hunt.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-05-29T08:16:00+07:00
- **Completed:** 2026-05-29T08:22:13+07:00
- **Tasks:** 3
- **Files modified:** 6 (5 created, 1 modified)

## Accomplishments
- Removed `TODO Phase 01` skip from the 4 existing `test_models.py` tests — they now fail with `NotImplementedError` (correct RED state for Plan 02)
- Added 7 skip-annotated model stubs (validate negative/dtype/sparse, m1/m2/m3 forecast shapes) — `test_models.py` collects 11 tests
- Created 4 unit stub files (24 stubs) for Monte Carlo, calibration, quantile bands, walk-forward, MAPE/Brier/log-loss, loaders, serialization
- Created `tests/integration/test_queries.py` (5 stubs) for `build_transition_matrix` + seed idempotency/reference-forecast paths
- Verified all stub SQL against `core/db/schema.sql` and `init_schema`/`close_connection` against `core/db/connection.py` — no contract drift

## Task Commits

1. **Task 1: Unskip + extend test_models.py** - `4f5f20a` (test)
2. **Task 2: Create simulation/metrics/loaders/serialization stubs** - `6f50704` (test)
3. **Task 3: Create integration test_queries.py** - `21a8c24` (test)

## Files Created/Modified
- `tests/unit/test_models.py` - 4 tests un-skipped + 7 new stubs (11 total)
- `tests/unit/test_simulation.py` - 12 stubs (ENG-05/06/07/09)
- `tests/unit/test_metrics.py` - 5 stubs (ENG-10)
- `tests/unit/test_loaders.py` - 3 stubs (DATA-01)
- `tests/unit/test_serialization.py` - 4 stubs (DATA-03 serialize)
- `tests/integration/test_queries.py` - 5 integration stubs (DATA-02/03)

## Decisions Made
- **Requirements-completed left empty.** A scaffolding plan creates test targets, not implementations. Verified that plans 02-05 collectively claim all 13 requirements, so marking none here orphans nothing and keeps REQUIREMENTS.md traceability honest.
- **Skip-reason string** follows the PLAN (`Wave 0 stub — implementation in later wave`) over VALIDATION.md, because the PLAN's acceptance_criteria assert that exact prefix.

## Deviations from Plan

None - plan executed exactly as written. (Task 3's pyproject `integration` marker check found the marker already declared, so no edit was needed — this is the plan's own conditional, not a deviation.)

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- **Verification state:** `uv run pytest tests/ --collect-only` exits 0 (40 collected). `uv run pytest tests/ -m "not slow"` → 4 failed (NotImplementedError, by design), 36 skipped.
- **Ready for Plan 02 (Wave 2):** implement `validate_transition_matrix` + M1/M2/M3 in `core/models.py`, then un-skip the matching `test_models.py` stubs.
- No blockers.

---
*Phase: 01-markov-engine*
*Completed: 2026-05-29*
