---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 05
status: unknown
last_updated: "2026-06-16T03:09:45.586Z"
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 22
  completed_plans: 19
---

# GSD State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-29)

**Core value:** A GitHub repo that convinces a senior BA/BI recruiter that the developer can think quantitatively AND ship a production-quality Python data product — two live domains, correct Markov math, clean 3-layer architecture.
**Current phase:** 05

---

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 01 | Markov Engine | Complete |
| 02 | Design System + Brand Share | Complete (4/4 plans complete) |
| 03 | Churn Domain | Complete (4/4 plans complete) |
| 04 | Home, Export & Settings | Complete (4/4 plans complete) |
| 05 | Quality Assurance & Deployment | In Progress (1/4 plans complete) |

---

## Current Focus

Phase 05 in progress (1/4 plans complete). 05-01 complete: 17 targeted branch-coverage tests added; core/ 96%, domains/ ~83%, 118 tests green, integration gate 20 passed.

---

## Progress Bar

```
Phase 01 [##########] 100% (6/6 plans complete)
Phase 02 [##########] 100% (4/4 plans complete)
Phase 03 [##########] 100% (4/4 plans complete)
Phase 04 [##########] 100% (4/4 plans complete)
Phase 05 [█████░░░░░]  25% (1/4 plans complete)

Overall  [█████████░]  86% (19/22 plans complete) — Phase 05 in progress
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Requirements defined | 33 |
| Requirements complete | 13 |
| Phases complete | 1/5 |
| Plans created | 10 |
| Plans complete | 9 |

---

| Phase 01 P01 | 6min | 3 tasks | 6 files |
| Phase 01 P02 | 13min | 3 tasks | 2 files |
| Phase 01 P03 | 8min | 3 tasks | 4 files |
| Phase 01 P04 | 7min | 3 tasks | 6 files |
| Phase 01 P05 | 12min | 3 tasks | 8 files |
| Phase 01 P06 | 25min | 3 tasks | 17 files |
| Phase 02 P01 | 17min | 3 tasks | 6 files |
| Phase 02 P02 | 11min | 2 tasks | 6 files |
| Phase 02 P03 | 24min | 2 tasks | 4 files |
| Phase 02-design-system-brand-share P04 | 25 | 4 tasks | 2 files |
| Phase 03 P01 | 18min | 3 tasks | 3 files |
| Phase 03 P02 | 18 | 2 tasks | 1 files |
| Phase 03 P03 | 5 | 2 tasks | 4 files |
| Phase 04 P01 | 9 | 5 tasks | 3 files |
| Phase 04 P02 | 9min | 2 tasks | 2 files |
| Phase 04 P04 | 17 | 4 tasks | 4 files |
| Phase 05 P01 | 7 | 3 tasks | 2 files |
| Phase 05 P02 | 14 | 4 tasks | 8 files |

## Accumulated Context

### Key Decisions

- Phase 01 build order was strictly sequential: `validate_transition_matrix` → M1 → M2 → M3 → Monte Carlo → `calibrate_probability` → `compute_quantile_bands` → `build_transition_matrix()` → `core/io/loaders.py` → `core/metrics.py`
- `BrandShareForecastResult` and `ChurnAnalysisResult` must use structured NumPy arrays — no Plotly coupling in domain layer
- Phase 02 must open with a Plotly 6.x smoke test (template registration) before any chart code
- DATA-02 (seed script) must complete before HOME-01 and DEPLOY-01
- UI-01 and UI-02 (design system) are built once in Phase 02 and shared with Phase 03
- N803/N806 ruff rules suppressed for Chan 2015 math variable names (P, Y_1, Q_t, G) — intentional, not violations
- UP040 suppressed in core/ — TypeAlias explicit form retained over Python 3.12 type keyword for np.ndarray aliases
- Phase 01 quality gate confirmed: 90.76% coverage (>80%), 40/40 tests pass, ruff clean, mypy clean
- Phase 02 Plan 01: compute_stationary placed in core/models.py (pure, no streamlit import); register_theme() must run after import streamlit for Plotly template composition; dict literals over dict() calls per ruff C408
- Phase 02 Plan 01: 46/46 tests pass after foundation layer added (UI-01 + BS-05)
- Phase 02 Plan 02: _build_*_figure helpers for testable Plotly components; tonexty trace order for fan chart fill; SPARSE_OBS_THRESHOLD=20 constant avoids magic numbers
- Phase 02 Plan 02: 54/54 tests pass after component library added (UI-02, BS-02, BS-03, D-06/D-07)
- Phase 02 Plan 03: BrandShareForecastResult is NumPy-only (14 fields); conn accepted as parameter; state_labels derived via sorted(set) to match queries.py internal sort; M3 Q_1 = absolute counts; best_model computed from MAPE (not hardcoded); compute_stationary added to core/models.py; N803/N806/E731 suppressed for service.py
- BS-01, BS-04 requirements marked complete
- Phase 02 Plan 04: importlib fallback (not AppTest) for BS-06 smoke test — AppTest times out in test env without seeded DB; importlib + mock.patch avoids DB while exercising imports and _build_overview_figure
- Phase 02 Plan 04: _dataset_period_count helper needed because Dataset dataclass has no n_periods field; derived from load_transitions().nunique() cached per dataset_id
- Phase 02 Plan 04: 51/51 tests pass after Brand Share page + smoke test added (BS-06 complete)
- BS-06 requirement marked complete
- Phase 03 Plan 01: Wave 0 guard uses importorskip + hasattr + inspect.signature checks — old churn stub imports fine, signature conn-param check is the reliable discriminator; seeded_churn_conn yields conn only (not tuple); 61 passed, 12 skipped after scaffold added
- Phase 03 Plan 02: ABSORBING_THRESHOLD=0.95 for near-absorbing state detection (real Churned state P[i,i]~0.98, not 1.0 exactly); state_distribution_over_time uses iterative Y_t @ P loop (not M1 forecast); n_customers = df["entity_id"].nunique(); simulate_scenario returns np.ndarray not full ChurnAnalysisResult; 72 passed, 1 skipped after service rewrite
- Phase 03 Plan 03: SVG bezier path shapes used for temporal Sankey (not go.Sankey per D-01); N803/N806 suppressed for sankey_flow.py (W/H/PT/PB/sH/tH JSX-port layout vars); ASCII -> used in impact_narrative for Windows console encoding safety; stackgroup opacity via rgba alpha in fillcolor (not trace opacity); 76 passed after component added
- Phase 04 Plan 01: seeded_conn fixture defined in test_queries.py (not conftest.py) — integration-only scope; TRY_CAST for JSON mape extraction in get_home_kpis/list_recent_forecasts — NULL on malformed rows vs raise; Dataset.created_at added as last field (backward-compatible); 94 tests pass
- Phase 04 Plan 02: Home.py smoke test mocks get_home_kpis at core.db.queries level; importlib exec_module pattern consistent with BS-06 and CH-04; pandas import inside else-branch (no noqa needed — PLC0415 not in ruff's enabled rule set); 95 tests pass
- Phase 04 Plan 04: Settings page Re-run seed in st.expander(Advanced) prevents accidental clicks; subprocess.run(["uv","run","python",...]) avoids shell=True; importlib+mock.patch smoke test matches BS-06/CH-04/HOME-01 convention; merged master to bring in Plans 01-03 (worktree was branched before those commits); 101 tests pass
- Phase 05 Plan 01: PT011 requires match= on pytest.raises(ValueError) — use specific error message substring from actual raises; bare ValueError is too broad per ruff
- Phase 05 Plan 01: compute_stationary dual-fallback branches (L116-117, L132-134) left uncovered — triggering both scipy.linalg.eig AND power-iteration failure simultaneously is unreliable; 96% core/ exceeds 80% threshold by 16pp
- Phase 05 Plan 02: forecasts table COUNT sentinel for cold-start seeding (ensure_seeded fast-path on warm rerun); app/db.py get_db() consolidates 5 per-page _get_db functions into one shared cached accessor with env-aware seed failure guard (D-08); noqa BLE001/PLC0415 removed (rules not in ruff select list); fetchone None-guard added to core/db/init.py and scripts/seed_data.py (mypy compliance); 103 tests pass

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260531-ikw | Fix 4 visual issues from Phase 03 UI review | 2026-05-31 | e04277e | [260531-ikw-fix-4-visual-issues-from-phase-03-ui-rev](.planning/quick/260531-ikw-fix-4-visual-issues-from-phase-03-ui-rev/) |
| 260531-p03 | Churn polish — 6 prototype fidelity gaps (scrubber, slider %, KPI deltas+icons, bar labels) | 2026-05-31 | 5462f9b | [260531-p03-churn-polish-6-gaps](.planning/quick/260531-p03-churn-polish-6-gaps/) |
| 260531-knp | Stack What-If charts vertically + fix Scenario Impact / chart-title overlap | 2026-05-31 | 8f81ce7, 1d26846 | [260531-knp-stack-what-if-charts-vertically-and-fix-](.planning/quick/260531-knp-stack-what-if-charts-vertically-and-fix-/) |

### Active Blockers

None.

### Todos

- Start Phase 03: Churn Domain (2_Churn.py)

---

## Session Continuity

### Last Action

2026-06-16 — Phase 05 Plans 01+02+03 complete (parallel wave 1): 17 new tests (96% core coverage), cold-start ensure_seeded() + shared app/db.py (5 pages wired), .github/workflows/ci.yml with 4-gate CI. 118+ tests green. QA-01/02/03/DEPLOY-01 satisfied. Commits: e0ad660, bc1d5b2, e63f69d (05-01); e1f3951, 003f5dc, 8cacab8, b6bd079 (05-02); 0690d91, 07413c6 (05-03).

### Resume Point

Phase 05 Wave 1 complete (plans 01, 02, 03). Next: Phase 05 Plan 04 — deploy to Streamlit Cloud (human checkpoint required).

---
*State initialized: 2026-05-29*
*Last updated: 2026-06-16 - Completed Phase 05 Wave 1: QA tests, cold-start seeding, CI workflow*
