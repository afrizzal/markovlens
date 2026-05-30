---
phase: 02-design-system-brand-share
plan: 04
subsystem: ui
tags: [streamlit, plotly, brand-share, markov, monte-carlo, kpi-cards, tabs]

# Dependency graph
requires:
  - phase: 02-01
    provides: design system foundation (theme.css, plotly_theme.py, register_theme, inject_theme)
  - phase: 02-02
    provides: component library (transition_heatmap, monte_carlo_fan, kpi_card, empty_state)
  - phase: 02-03
    provides: BrandShareForecastResult, run_forecast, list_datasets, service pipeline

provides:
  - "app/pages/1_Brand_Share.py: fully-wired 4-tab Brand Share forecaster (BS-06)"
  - "tests/unit/test_page_import.py: BS-06 smoke test + Overview structural assertion"

affects:
  - phase-03-churn (same page assembly pattern)
  - phase-04-home (Home.py references Brand Share page link)
  - phase-05-deploy (page tested as part of full-app smoke check)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Page assembly: set_page_config first, register_theme() + inject_theme() immediately after, all logic in main()"
    - "E402 noqa on local imports that must follow set_page_config (Streamlit constraint)"
    - "Session state namespaced with PAGE_NS prefix (brand_share.*) to avoid cross-page collisions"
    - "_cached_forecast keyed on (dataset_id, model_type, horizon, n_simulations, seed) for @st.cache_data"
    - "Dataset period count derived via _dataset_period_count @st.cache_data helper (Dataset has no n_periods)"
    - "segmented_control with AttributeError fallback to radio for Streamlit version compatibility"
    - "AppTest times out without seeded DB — importlib + patch approach used for BS-06 smoke test"
    - "Test module loaded via importlib.util.spec_from_file_location due to digit prefix in filename"

key-files:
  created:
    - app/pages/1_Brand_Share.py
    - tests/unit/test_page_import.py
  modified: []

key-decisions:
  - "importlib fallback (not AppTest) for BS-06 smoke test: AppTest times out in test env without seeded DB; importlib + patch avoids DB entirely while still exercising import-time setup and _build_overview_figure helper"
  - "APP_PAGES: 1_Brand_Share.py wraps all rendering in main() so AppTest and importlib both run it predictably"
  - "_dataset_period_count separate @st.cache_data helper: Dataset dataclass has no n_periods field, so period count derived from load_transitions().nunique() cached per dataset_id"
  - "stationary_distribution consumed inside Overview render block (not at top-level) to satisfy SC-5"

patterns-established:
  - "Brand Share page: control strip in st.container(border=True), KPI strip with 3 kpi_card columns, 4 st.tabs"
  - "empty_state shown when result is None, full content when result is populated"
  - "Model verdict paragraph auto-selects reason sentence by best_model key, never hardcoded"

requirements-completed: [BS-06]

# Metrics
duration: 25min
completed: 2026-05-30
---

# Phase 02 Plan 04: Brand Share Page Summary

**Fully-wired 4-tab Brand Share forecaster assembling design system + components + service into recruiter-facing demo with stacked-area forecast, stationary distribution panel, Monte Carlo fan chart, and bold-best-per-column model comparison**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-30T08:28:37Z
- **Completed:** 2026-05-30T08:53:37Z
- **Tasks:** 4 (Tasks 1, 2a, 2b, 2c)
- **Files modified:** 2

## Accomplishments

- Created `app/pages/1_Brand_Share.py` (782 lines) — complete Brand Share forecaster with set_page_config, register_theme, control strip (dataset/model/horizon/run), KPI strip (leader/gainer/loser), 4 tabs, all tab content wired
- Overview tab: `_build_overview_figure` helper produces stacked-area historical + forecast with "today" separator via `add_vline`; stationary distribution panel with split title/caveat (SC-5)
- Monte Carlo tab: secondary controls (start brand, horizon, n_simulations, seed, Randomize, Run Simulation), fan chart via component, final-state histogram
- Model Comparison tab: 3-column model cards with "Best fit" badge on winner, bold-best-per-column metrics table, walk-forward backtest table, verdict paragraph auto-generated from `result.best_model`
- Created `tests/unit/test_page_import.py`: BS-06 smoke test (importlib + patch) + `test_overview_figure_has_separator` structural check; 51/51 tests pass

## Task Commits

1. **Task 1: Brand Share page shell** — `e158730` (feat)
2. **Tasks 2a/2b/2c: All tab content** — included in same commit as shell (page fully wired in one write)
3. **Test file: BS-06 smoke test** — `a1eaee5` (test)

## Files Created/Modified

- `app/pages/1_Brand_Share.py` — Fully-wired 4-tab Brand Share forecaster (BS-06)
- `tests/unit/test_page_import.py` — Import smoke test + Overview structural assertion

## Decisions Made

- **importlib fallback for smoke test**: AppTest.from_file times out after 3s in CI/test environments without a seeded DuckDB file. Switched to importlib + mock.patch for DB/service calls. Documented in test docstring.
- **All tab content in one commit**: Tasks 2a/2b/2c all modify the same file; writing the complete page in Task 1 and committing once was cleaner than three partial overwrites.
- **_dataset_period_count helper**: `Dataset` dataclass has no `n_periods` field. Created a `@st.cache_data` helper keyed on `dataset_id` that calls `load_transitions().nunique()` — cheap and cached, matching the interfaces note in the plan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Merged master into worktree to get component files**
- **Found during:** Task 2c (running tests)
- **Issue:** The worktree was spawned from a commit before Plans 02-01/02-02/02-03 were merged to master, so `app/components/monte_carlo_fan.py` and `transition_heatmap.py` were missing. AppTest failed with ModuleNotFoundError.
- **Fix:** `git merge master --no-edit` — brought in all Phase 02 Plan 01-03 commits.
- **Files modified:** all component, domain, and planning files from prior plans
- **Verification:** 51/51 tests pass after merge
- **Committed in:** merge commit (auto-generated by git)

---

**Total deviations:** 1 auto-fixed (blocking: missing component files in worktree)
**Impact on plan:** Required for functionality — no scope change.

## Issues Encountered

- AppTest timeouts in test environment without seeded DuckDB: `AppTest.from_file` hangs at `@st.cache_resource` DB connection call. Switched to importlib + patch approach as described in plan spec's fallback.
- Worktree was behind master (missing 02-01/02-02/02-03 commits): fixed via `git merge master`.

## Known Stubs

None — all data flows are wired to real service calls via `_cached_forecast`. KPI strip and tab content show `empty_state` pre-forecast (intentional gating behavior, not stubs). The `gainer_label` and `loser_label` default to "no gainer"/"no loser" when there are no positive/negative share changes — this is correct behavior, not a stub.

## Next Phase Readiness

- BS-06 complete; Brand Share page fully functional pending a seeded DuckDB (`scripts/seed_data.py`)
- Phase 02 all 4 plans complete — ready for Phase 03 (Churn domain)
- `1_Brand_Share.py` pattern is the template for `2_Churn.py` in Phase 03

## Self-Check

Files:
- [x] `app/pages/1_Brand_Share.py` — exists (confirmed via tests)
- [x] `tests/unit/test_page_import.py` — exists (51/51 pass)

Commits:
- [x] `e158730` — feat(02-04): Brand Share page
- [x] `a1eaee5` — test(02-04): smoke test + structural check

---
*Phase: 02-design-system-brand-share*
*Completed: 2026-05-30*
