---
phase: 03-churn-domain
plan: "02"
subsystem: domain
tags: [python, numpy, duckdb, markov, absorbing-chain, fundamental-matrix, churn]

requires:
  - phase: 03-churn-domain/03-01
    provides: Wave 0 test scaffold (12 importorskip-guarded tests) + seeded_churn_conn fixture
  - phase: 01-markov-engine
    provides: M1Homogeneous.forecast, validate_transition_matrix, build_transition_matrix, core exceptions
provides:
  - domains/churn/service.py: complete churn domain service (CH-01)
  - ChurnAnalysisResult: 9-field NumPy-only frozen dataclass
  - run_analysis(conn, dataset_id, horizon) -> ChurnAnalysisResult
  - simulate_scenario(conn, dataset_id, horizon, transition_overrides) -> np.ndarray
  - list_datasets(conn, *, domain="churn") -> list[Dataset]
  - compute_fundamental_matrix(P) -> (N | None, transient_idx)
  - compute_avg_lifetime(P, active_state_idx) -> float | None
  - _apply_overrides(P, overrides) -> np.ndarray (renormalized copy)
  - KPI_KEYS, DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER, ABSORBING_THRESHOLD module constants
affects:
  - 03-churn-domain/03-03 (Sankey component consumes state_distribution_over_time + transition_matrix)
  - 03-churn-domain/03-04 (Churn page calls run_analysis + simulate_scenario)

tech-stack:
  added: []
  patterns:
    - "Absorbing Markov chain fundamental matrix (I-Q)^{-1} with pinv fallback when cond > 1e10"
    - "ABSORBING_THRESHOLD=0.95 for near-absorbing state detection (real data never P[i,i]=1.0 exactly)"
    - "np.vstack([Y_1.reshape(1,-1), fc.forecast_array]) pattern to include period 0 in both distribution arrays"
    - "simulate_scenario accepts optional baseline_P to skip DB re-query on repeated calls (Pitfall 5)"

key-files:
  created: []
  modified:
    - domains/churn/service.py

key-decisions:
  - "Used ABSORBING_THRESHOLD=0.95 (not 1.0) — real churn data has near-absorbing Churned state (P[i,i]~0.98); strict 1.0 would treat it as transient and produce near-singular (I-Q)"
  - "state_distribution_over_time uses _state_distribution_over_time helper (iterative Y_t @ P) not M1Homogeneous.forecast — gives the historical-evolution array (n_periods+1 rows) for Sankey; baseline_forecast is the separate forward forecast"
  - "n_customers = df['entity_id'].nunique() — dataset.row_count is transitions count, not customer count (Open Question 2 resolved)"
  - "simulate_scenario returns np.ndarray (not ChurnAnalysisResult) — page stores baseline in @st.cache_data and only re-runs scenario overlay, keeping cold-start cost low"

patterns-established:
  - "Domain service pure (no streamlit, no plotly) — all imports verified clean"
  - "conn as first parameter pattern mirrors brand_share/service.py; @st.cache_resource for DB in page layer"
  - "state_labels = sorted(set(df['from_state']) | set(df['to_state'])) — MUST match queries.py internal sort for index alignment"

requirements-completed: [CH-01]

duration: 18min
completed: "2026-05-31"
---

# Phase 03 Plan 02: Churn Service Implementation Summary

**Absorbing Markov chain churn domain service with fundamental matrix KPIs, what-if scenario renormalization, and 11 Wave 0 tests turned green (72 total, 1 skip for CH-02 Sankey scope)**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-31T00:29:46Z
- **Completed:** 2026-05-31T00:47:46Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Rewrote domains/churn/service.py from obsolete 3-field stub (sankey_chart_json) to complete 510-line domain service implementing CH-01
- Implemented absorbing Markov chain fundamental matrix (I-Q)^{-1} with pinv fallback for compute_avg_lifetime KPI
- Turned 11 Wave 0 tests from SKIP to PASS: 5 unit + 6 integration (1 Sankey test stays skipped — CH-02 scope)

## Task Commits

Both tasks modified the same single file; implemented atomically in one write:

1. **Task 1: ChurnAnalysisResult + fundamental-matrix KPIs** - `90d5d3b` (feat)
2. **Task 2: run_analysis + simulate_scenario + list_datasets + _apply_overrides** - included in `90d5d3b` (same file, written together)

**Note:** TDD plan had Wave 0 tests from Plan 03-01 as RED phase. This plan implemented GREEN phase. Both tasks targeted a single file so a single commit captures the full implementation.

## Files Created/Modified

- `domains/churn/service.py` - Complete rewrite: ChurnAnalysisResult (9 NumPy fields), compute_fundamental_matrix, compute_avg_lifetime, _compute_kpis (4 KPIs), _compute_share_vector, _initial_distribution, _state_distribution_over_time, _apply_overrides, list_datasets, run_analysis, simulate_scenario

## Decisions Made

- ABSORBING_THRESHOLD=0.95 distinguishes near-absorbing "Churned" state (P[4,4]~0.98) from transient states without making (I-Q) near-singular
- state_distribution_over_time built via iterative Y_t @ P loop (not M1Homogeneous.forecast) to produce the historical-periods array (n_periods+1 rows) for the Sankey; baseline_forecast is the separate forward forecast from run_analysis
- n_customers = df["entity_id"].nunique() — the dataset.row_count field is transitions count, not customer count
- simulate_scenario returns np.ndarray (not ChurnAnalysisResult) to keep the page's what-if panel lightweight — only the scenario overlay is recomputed on slider change

## Deviations from Plan

None — plan executed exactly as written. All verbatim code patterns from RESEARCH.md were copied precisely (compute_fundamental_matrix, compute_avg_lifetime, _compute_kpis). The two-task structure was followed conceptually (Task 1 = dataclass/constants/KPI helpers, Task 2 = public API/orchestration), with both implemented in a single atomic write to avoid partial-state intermediate commits.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Known Stubs

None. All fields in ChurnAnalysisResult are computed from real DuckDB data. The KPI `avg_lifetime` returns `float("nan")` if the fundamental matrix cannot be computed (all states absorbing or matrix singular), which is a valid computed value documented in the dataclass docstring — not a stub.

## Next Phase Readiness

- Plan 03-03 (Sankey component) can now receive `state_distribution_over_time` and `transition_matrix` from `ChurnAnalysisResult`
- Plan 03-04 (Churn page) can call `run_analysis(conn, dataset_id, horizon)` and `simulate_scenario(...)` immediately
- `list_datasets(conn)` is ready for the cohort selector dropdown
- All Wave 0 churn tests green — phase gate ready for Plans 03-03 and 03-04

## Self-Check

- [x] `domains/churn/service.py` exists and has 510 lines
- [x] `grep "class ChurnAnalysisResult"` matches
- [x] `grep "sankey_chart_json"` returns nothing
- [x] `grep "import streamlit"` returns nothing
- [x] Commit 90d5d3b exists in git log
- [x] 72 passed, 1 skipped (all churn unit + integration tests green)
- [x] ruff clean, mypy clean, pure-import smoke passes

---
*Phase: 03-churn-domain*
*Completed: 2026-05-31*
