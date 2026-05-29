---
phase: 01-markov-engine
plan: 03
subsystem: core-engine
tags: [monte-carlo, calibration, quantile-bands, walk-forward, metrics, numpy, pandas]

requires:
  - phase: 01-02
    provides: validate_transition_matrix + M1Homogeneous (used by walk_forward)
provides:
  - monte_carlo_simulate (vectorized, reproducible, ~4ms/10k×12)
  - calibrate_probability (np.interp longshot-bias), compute_quantile_bands
  - walk_forward_backtest (no-leakage, vectorized groupby)
  - mape / brier_score / log_loss
affects: [01-04, 01-05, 02-brand-share, 03-churn]

tech-stack:
  added: []
  patterns:
    - "Cumsum inverse-CDF vectorized MC sampling; cum_matrix[:,-1]=1.0 boundary fix (D-12)"
    - "calibrate via np.interp over sorted anchors (clamps at boundaries, D-17)"
    - "compute_quantile_bands applies target_extractor BEFORE percentile; rejects 1-D output"
    - "walk-forward: train only on periods[:t_idx]; vectorized groupby, never iterrows"

key-files:
  created: []
  modified:
    - core/simulation.py
    - core/metrics.py
    - tests/unit/test_simulation.py
    - tests/unit/test_metrics.py

key-decisions:
  - "monte_carlo_simulate 10k×12 runs in ~4ms (target was ~50ms) — vectorized cumsum/argmax."
  - "Used unquoted pd.DataFrame annotations (file has from __future__ import annotations) to avoid UP037."

patterns-established:
  - "All per-window aggregation vectorized via groupby + fancy indexing (CLAUDE.md numerical rule)"

requirements-completed: [ENG-05, ENG-06, ENG-07, ENG-09, ENG-10]

duration: 8min
completed: 2026-05-29
---

# Phase 01 Plan 03: Simulation Engine + Metrics Summary

**Vectorized Monte Carlo (4ms/10k×12, seed-reproducible), longshot-bias calibration, quantile bands, no-leakage walk-forward backtest, and MAPE/Brier/log-loss — all 17 tests green, mypy clean.**

## Performance

- **Duration:** ~8 min
- **Completed:** 2026-05-29T08:45:51+07:00
- **Tasks:** 3 (TDD)
- **Files modified:** 4

## Accomplishments
- `monte_carlo_simulate`: cumsum inverse-CDF sampling, `default_rng`, int64 paths (n_sims, n_steps+1), D-12 boundary fix, int|ndarray start (D-13). **10k×12 = ~4ms** (target ~50ms).
- `calibrate_probability`: `np.interp` over sorted LONGSHOT_CALIBRATION anchors; clamps at boundaries (D-17).
- `compute_quantile_bands`: `Callable` type, extractor applied before percentile, raises on 1-D output (ENG-07).
- `walk_forward_backtest`: fits matrix on `periods[:t_idx]` only (no leakage); vectorized groupby helpers, zero `iterrows`; returns `list[dict]`.
- `mape` (zero-actual skip + warning), `brier_score`, `log_loss` (eps-clipped, finite).

## Task Commits

1. **Task 1: monte_carlo + calibrate + quantile_bands** - `985e972` (feat)
2. **Task 2: walk_forward_backtest** - `4fd9fef` (feat)
3. **Task 3: mape + brier_score + log_loss** - `e0cdde9` (feat)

## Files Created/Modified
- `core/simulation.py` - 3 stubs implemented + `walk_forward_backtest` & 2 helpers added; `pandas`, `Callable`, calibration arrays
- `core/metrics.py` - mape/brier/log_loss implemented
- `tests/unit/test_simulation.py` - 12 stubs un-skipped
- `tests/unit/test_metrics.py` - 5 stubs un-skipped

## Decisions Made
See key-decisions. Implementations match RESEARCH/CONTEXT decisions D-12..D-18.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_calibrate_interpolates wrong interval midpoint**
- **Found during:** Task 1. Test used `calibrate_probability(0.025)` expecting `(0.0043+0.0418)/2`, but `0.025` is fraction 0.375 of key interval `[0.01,0.05]`, not the midpoint (`0.03` is). `np.interp(0.025)` correctly returns ~0.01836.
- **Fix:** Changed input to `0.03` (true interval midpoint) → exactly `0.02305`. Implementation unchanged.
- **Committed in:** `985e972`

**2. [Rule 1 - Bug] iterrows mentioned in docstring tripped acceptance grep**
- **Found during:** Task 2. No actual `.iterrows()` calls, but the word appeared in the docstring; acceptance is `grep -c iterrows == 0`. Reworded docstring to "row-by-row Python iteration."
- **Committed in:** `4fd9fef`

---

**Total deviations:** 2 auto-fixed (1 test-scaffold math bug, 1 docstring wording). **Impact:** Implementations correct; no scope creep.

## Issues Encountered
- **ruff (deferred to 01-06):** simulation.py/metrics.py carry the same project-wide math-notation N803/N806 debt (`P`, `Y_prev`, `Q_t`, etc.) plus UP040 type-alias style. **mypy clean.** Resolving "ruff clean" is Plan 01-06's deliverable.

## User Setup Required
None.

## Next Phase Readiness
- **Ready for Plan 01-04 (Wave 3, data layer):** serialization helpers, `build_transition_matrix`, `validate_transitions_df`. `walk_forward_backtest` already consumes long-format transitions, aligning with the DuckDB `transitions` schema.
- No blockers.

---
*Phase: 01-markov-engine*
*Completed: 2026-05-29*
