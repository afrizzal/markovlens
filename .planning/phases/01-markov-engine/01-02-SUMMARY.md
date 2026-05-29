---
phase: 01-markov-engine
plan: 02
subsystem: core-engine
tags: [markov, chan-2015, numpy, validation, m1, m2, m3]

requires:
  - phase: 01-01
    provides: skip-annotated model test stubs (un-skipped here)
provides:
  - validate_transition_matrix() with collect-all-errors + sparsity WARNING
  - M1Homogeneous / M2TimeVarying / M3Extended forecast implementations (Chan 2015)
  - Chan 2015 Table 3 (m1) and m3-share regressions green
affects: [01-03, 01-04, 01-05, 02-brand-share, 03-churn]

tech-stack:
  added: []
  patterns:
    - "forecast_array EXCLUDES initial vector: [0]=Y_2 (one matmul), [h-1]=Y_{h+1} (RESEARCH Pitfall 2)"
    - "M2/M3 P_t_sequence is np.ndarray (n_periods,n,n) not list[ndarray] (D-08)"
    - "Hold-last: P_t[-1] (and G[-1] if 2D) reused when horizon > n_periods (D-06/D-07)"
    - "m3 returns ABSOLUTE counts (sum grows with G); normalize for share comparison"

key-files:
  created: []
  modified:
    - core/models.py
    - tests/unit/test_models.py

key-decisions:
  - "M1 Chan regression test had off-by-one index (asserted forecast_array[1], but Chan t=2=Y_2 is at [0]). Fixed test index; implementation correct per RESEARCH Pitfall 2."
  - "M3 Chan regression compared raw absolute output to normalized shares. Fixed test to normalize before compare; m3 MUST return absolute counts per docs/MARKOV-MODELS.md + CLAUDE.md forbidden #5."
  - "Placed `import logging` in stdlib import group (plan said 'after numpy', but isort/ruff requires stdlib-first)."

patterns-established:
  - "Markov forecast convention: forecast_array[0] is the first projected step, not the initial state"

requirements-completed: [ENG-01, ENG-02, ENG-03, ENG-04, ENG-08]

duration: 13min
completed: 2026-05-29
---

# Phase 01 Plan 02: Matrix Validation + M1/M2/M3 Models Summary

**`validate_transition_matrix` (collect-all-errors + sparsity warning) and all three Chan (2015) Markov models implemented — m1 Table 3 regression green to 1e-3, m3 share regression green to 1e-2.**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-05-29T08:24:00+07:00
- **Completed:** 2026-05-29T08:37:31+07:00
- **Tasks:** 3 (TDD)
- **Files modified:** 2

## Accomplishments
- `validate_transition_matrix()`: validates ndim/square/float64/finite/sign/row-sum, collects ALL failures into one `InvalidTransitionMatrixError`; logs (never raises) sparsity when `transition_counts < MIN_OBSERVATIONS_PER_CELL`
- `M1Homogeneous.forecast()`: iterative `Y_t @ P` per Chan Eq.(1); reproduces Chan 2015 Table 3 (t=2 = `[0.5829, 0.2780, 0.0667, 0.0724]`) within atol=1e-3
- `M2TimeVarying`: ndarray constructor (D-08), hold-last-P_t (D-06)
- `M3Extended`: ndarray constructor + G shape validation (D-09/D-10), `(G ⊙ Q_t) @ P_t` (D-07); absolute-count output, normalized shares match Chan m3 table within 1e-2
- All 11 `tests/unit/test_models.py` tests pass; 0 skips, 0 `NotImplementedError` in models.py

## Task Commits

1. **Task 1: validate_transition_matrix** - `243934c` (feat) — 6 validation tests green
2. **Task 2: M1Homogeneous.forecast** - `cd32e78` (feat) — Chan Table 3 regression green
3. **Task 3: M2TimeVarying + M3Extended** - `06aeb63` (feat) — all 11 tests green

**Chan 2015 m1 regression (REPL):** `forecast_array[0]` = `[0.5829 0.278 0.0667 0.0724]` == Chan Table 3 t=2 ✓

## Files Created/Modified
- `core/models.py` - all 4 `NotImplementedError` stubs replaced; M2/M3 constructors changed list→ndarray
- `tests/unit/test_models.py` - 6 stubs un-skipped; 2 regression-test index/normalization fixes

## Decisions Made
See key-decisions frontmatter. Two test-scaffold bugs fixed (implementations were correct):
1. M1 off-by-one index (`[1]`→`[0]`)
2. M3 absolute-vs-share unit mismatch (normalize before compare)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] M1 Chan regression off-by-one index**
- **Found during:** Task 2 (M1 forecast verification — test failed)
- **Issue:** Test asserted `forecast_array[1] == Chan-t=2`, but per RESEARCH Pitfall 2 `forecast_array[0]=Y_2` (array excludes initial Y_1). Off by exactly one matmul.
- **Fix:** Changed assertion index `[1]`→`[0]`. Expected values + atol unchanged.
- **Verification:** `test_m1_forecast_replicates_chan_2015_table3` green; matches Chan Table 3.
- **Committed in:** `cd32e78`

**2. [Rule 1 - Bug] M3 regression compared absolute counts to normalized shares**
- **Found during:** Task 3 (M3 forecast verification — test failed, actual sum=1.035 vs expected sum=1.0)
- **Issue:** m3 output is absolute (grows with G); Chan's m3 table reports normalized shares (separate Q_t total column = 2,904,830, ×1.035 growth confirmed).
- **Fix:** Normalize `forecast_array[0]` before comparing to share-expected values. Implementation unchanged (m3 must stay absolute per CLAUDE.md forbidden #5).
- **Verification:** normalized shares = `[0.5809, 0.2835, 0.0598, 0.0759]` ≈ Chan `[0.5799, 0.2847, 0.0603, 0.0751]` within 1e-2.
- **Committed in:** `06aeb63`

**3. [Rule 3 - Blocking] import logging placement**
- **Found during:** Task 1. Plan said "after numpy"; isort requires stdlib-first. Placed in stdlib group for ruff-cleanliness.
- **Committed in:** `243934c`

---

**Total deviations:** 3 auto-fixed (2 test-scaffold bugs, 1 import-order). **Impact:** Implementations match Chan (2015) exactly; only the Plan-01 test scaffolds (written during the frozen plan-phase) carried the two regression bugs. No scope creep.

## Issues Encountered
- **ruff not clean (deferred):** core/models.py + repo carry pre-existing project-wide ruff debt — 39 N803/N806 from MANDATED Chan math notation (`Y_1`, `P_t`, `Q_t`), plus UP040 (TypeAlias style) and 1 dubious SIM300. The original models.py already had 14 ruff errors before this plan. Resolving "ruff clean" is the explicit deliverable of **Plan 01-06**; not addressed here to avoid an unilateral project-wide ruff-config/notation decision mid-plan. **mypy is clean.**

## User Setup Required
None.

## Next Phase Readiness
- **Ready for Plan 01-03 (Wave 3):** `monte_carlo_simulate`, `calibrate_probability`, `compute_quantile_bands`, `walk_forward_backtest`, metrics — all have waiting stubs and a working `validate_transition_matrix` + models to build on.
- **For Plan 01-06:** must add ruff per-file-ignores for N803/N806 (math notation) or migrate, and decide UP040 (PEP 695 `type` aliases). Tracked.

---
*Phase: 01-markov-engine*
*Completed: 2026-05-29*
