---
phase: 02-design-system-brand-share
verified: 2026-05-30T00:00:00Z
status: passed
score: 8/8 must-haves verified
gaps:
  - truth: "REQUIREMENTS.md reflects BS-01 and BS-04 as Complete (not Pending)"
    status: partial
    reason: "The implementation is complete and all tests pass, but REQUIREMENTS.md still marks BS-01 and BS-04 as '[ ] Pending'. This is a documentation staleness gap, not a code gap."
    artifacts:
      - path: ".planning/REQUIREMENTS.md"
        issue: "Lines 34 and 37 show '- [ ] **BS-01**' and '- [ ] **BS-04**'; Traceability table lines 121/124 show 'Pending'. The code fully satisfies both requirements."
    missing:
      - "Update .planning/REQUIREMENTS.md: change BS-01 and BS-04 from '[ ]' to '[x]' and update Traceability table from 'Pending' to 'Complete'"
  - truth: "ruff check passes on all phase 02 files without errors"
    status: failed
    reason: "app/pages/1_Brand_Share.py has one fixable ruff I001 violation: import block lines 21-22 (monte_carlo_fan, transition_heatmap) are split from the remainder of the local import block by a blank line, placing them out of isort order. Auto-fixable with --fix."
    artifacts:
      - path: "app/pages/1_Brand_Share.py"
        issue: "I001 [*] Import block is un-sorted or un-formatted at line 21. The two component imports at lines 21-22 are intentionally separated (comment says 'imported after streamlit'), but ruff still flags them. Fix: merge the split block or add a per-file noqa directive for I001."
    missing:
      - "Run: uv run ruff check app/pages/1_Brand_Share.py --fix OR add # noqa: I001 to silence the intentional split"
human_verification:
  - test: "Open the Brand Share page in a browser with a seeded dataset"
    expected: "Control strip shows dataset name with '{n} transitions · {n} periods · {n} states' sub-caption; Run Forecast populates KPI strip and all four tabs; heatmap shows ⚠ on sparse cells; fan chart shows P10/P50/P90 bands with 'today' separator; Model Comparison shows the best-fit badge and bold-best-per-column metrics; Overview shows 'Long-run equilibrium' bar chart with the caveat sentence"
    why_human: "Streamlit rendering, chart visual accuracy, and end-to-end user interaction cannot be verified without a live browser session"
  - test: "Run forecast with a real seeded dataset and verify model comparison verdict paragraph"
    expected: "Verdict reads 'm1/m2/m3 gives the best overall fit (MAPE N.NN%).' followed by the correct reason sentence; the winning model badge matches best_model from the service"
    why_human: "Depends on which model actually wins for the seeded dataset; correctness of the plain-language sentence selection is content review"
---

# Phase 02: Design System + Brand Share — Verification Report

**Phase Goal:** The Brand Share page is fully functional end-to-end — a recruiter can open it, select a dataset, run m1/m2/m3 forecasts, inspect the transition matrix heatmap, view the Monte Carlo fan chart, and compare model accuracy.
**Verified:** 2026-05-30
**Status:** gaps_found (2 documentation/style gaps; no functional code gaps)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | register_theme() registers 'markovlens' template + sets 'streamlit+markovlens' default | VERIFIED | `uv run python` spot-check confirms; test_plotly_theme.py 3/3 green |
| 2 | theme.css is full markov.css port (light + dark tokens, no 'Phase 05' comment) | VERIFIED | `--chart-seq-5` present x2, `data-theme="dark"` present, grep for 'Phase 05' returns 0 |
| 3 | compute_stationary returns sum-to-1 vector for valid matrices; pure (no streamlit import) | VERIFIED | Spot-check `[0.5714, 0.4286]` correct; test_stationary.py 3/3 green; grep 'import streamlit' in core/models.py = 0 |
| 4 | transition_heatmap renders fixed [0,1] scale, per-cell % annotations, ⚠ markers on <20 obs cells | VERIFIED | zmin=0/zmax=1 found; SPARSE_OBS_THRESHOLD=20; ⚠ + #D97706 present; test_components.py 8/8 green |
| 5 | monte_carlo_fan renders P10/P50/P90 bands, 'today' separator, named legend | VERIFIED | add_vline present; 'Median (P50)', 'P10', 'P90' found; fill present; tests green |
| 6 | kpi_card uses custom HTML (no st.metric fallback, no Phase 05 TODO, accent-card class) | VERIFIED | st.metric count=0; accent-card present; delta_suffix param present |
| 7 | run_forecast returns NumPy-only BrandShareForecastResult (no Plotly coupling); domain stays streamlit-free; accuracy_metrics computed from real metrics; best_model derived (not hardcoded) | VERIFIED | forecast_chart_json absent; grep 'import streamlit' in service=0; _compute_accuracy_metrics calls mape/brier_score/log_loss from core.metrics; best_model = min(MODEL_KEYS, ...); integration tests 5/5 green |
| 8 | 1_Brand_Share.py runs without raising; control strip + KPI strip + 4 tabs; heatmap pre-forecast; caching gated; Overview stationary panel; Monte Carlo fan; Model Comparison verdict | VERIFIED | All 19 pattern assertions pass; test_page_import.py 2/2 green; full suite 61/61 green |
| 9 | REQUIREMENTS.md marks BS-01 and BS-04 as Complete | FAILED | File still shows '[ ] Pending' for both; implementations are real but docs not updated post-execution |
| 10 | ruff check passes on all phase 02 files without errors | FAILED | 1 fixable I001 violation in app/pages/1_Brand_Share.py (import block split, auto-fixable) |

**Score:** 8/10 truths verified (8 functional truths all pass; 2 housekeeping truths fail — docs staleness + style lint)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/styles/plotly_theme.py` | register_theme() Plotly 6.x template | VERIFIED | def register_theme( present; CATEGORICAL_COLORWAY correct; pio.templates.default set |
| `app/styles/theme.css` | Full design-token CSS port of markov.css | VERIFIED | --chart-seq-5 x2; [data-theme="dark"] x1; Phase 05 x0 |
| `app/styles/__init__.py` | inject_theme + register_theme re-exports | VERIFIED | Both exported |
| `core/models.py` | compute_stationary() helper, pure | VERIFIED | def compute_stationary( x1; import streamlit x0; scipy x1 |
| `tests/unit/test_plotly_theme.py` | UI-01 smoke test | VERIFIED | 3 tests, all green |
| `tests/unit/test_stationary.py` | BS-05 stationary distribution test | VERIFIED | 3 tests, all green |
| `app/components/transition_heatmap.py` | Annotated heatmap with fixed [0,1] + sparsity markers | VERIFIED | All patterns present; SPARSE_OBS_THRESHOLD=20 |
| `app/components/monte_carlo_fan.py` | Fan chart P10/P50/P90 + separator + legend | VERIFIED | All patterns present |
| `app/components/kpi_card.py` | Custom-HTML KPI card | VERIFIED | No st.metric; accent-card present |
| `app/components/empty_state.py` | Empty state with action_label/action_callback | VERIFIED | New signature present |
| `app/components/__init__.py` | Exports all 5 components | VERIFIED | __all__ = ["empty_state","kpi_card","monte_carlo_fan","section_header","transition_heatmap"] |
| `tests/unit/test_components.py` | UI-02/BS-02/BS-03 structural tests | VERIFIED | 8 tests, all green |
| `domains/brand_share/service.py` | BrandShareForecastResult (NumPy-only) + pipeline | VERIFIED | No forecast_chart_json; no import streamlit; sorted(set( present; DEFAULT_N_SIMULATIONS; best_model=min(; walk_forward_backtest + compute_quantile_bands called |
| `tests/integration/test_brand_share_service.py` | BS-01/BS-04 integration tests | VERIFIED | 5 tests, all green |
| `app/pages/1_Brand_Share.py` | Fully-wired Brand Share page (BS-06) | VERIFIED | All 19 structural assertions pass; test_page_import.py green |
| `tests/unit/test_page_import.py` | BS-06 import smoke test + Overview structural check | VERIFIED | 2 tests, all green |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| app/styles/plotly_theme.py | plotly.io.templates | pio.templates['markovlens'] = Template(…); default = 'streamlit+markovlens' | WIRED | Confirmed by spot-check; test_plotly_theme green |
| core/models.py compute_stationary | scipy.linalg.eig(P.T) | left eigenvector with power-iteration fallback | WIRED | scipy import present; implementation produces [4/7, 3/7] |
| app/components/transition_heatmap.py | go.Heatmap zmin=0 zmax=1 | fixed color axis + add_annotation per cell + sparsity marker | WIRED | zmin=0 / zmax=1 / SPARSE_OBS_THRESHOLD found |
| app/components/monte_carlo_fan.py | go.Scatter fill bands + add_vline | P90/P10/P50/historical trace order + today separator | WIRED | fill present; add_vline present; legend names present |
| domains/brand_share/service.py run_forecast | core.db.queries.build_transition_matrix + M1/M2/M3 + monte_carlo_simulate + compute_quantile_bands + compute_stationary | orchestration pipeline | WIRED | All imports and calls verified at lines 17-21, 158-268 |
| domains/brand_share/service.py | state_labels = sorted(set(from)|set(to)) | label derivation matching queries.py internal sort | WIRED | sorted(set( found at line 162 |
| app/pages/1_Brand_Share.py | domains.brand_share.service.run_forecast | via @st.cache_data _cached_forecast keyed on (dataset_id, model, horizon, n_simulations, seed) | WIRED | @st.cache_data + service.run_forecast + 4-arg key confirmed |
| app/pages/1_Brand_Share.py | app.components (transition_heatmap / monte_carlo_fan / kpi_card / empty_state) | tab rendering | WIRED | All 4 component call-sites found |
| app/pages/1_Brand_Share.py | app.styles register_theme / inject_theme | called at top of page before any chart | WIRED | register_theme() at line 33, inject_theme() at line 34 |
| app/pages/1_Brand_Share.py (Overview tab) | _build_overview_figure + add_vline 'today' separator | historical + forecast traces with vertical separator | WIRED | def _build_overview_figure( + add_vline + 'Market share forecast' found |
| app/pages/1_Brand_Share.py (Overview tab) | result.stationary_distribution | stationary panel consumed in if/go.Bar branch (D-13/D-14) | WIRED | stationary_distribution referenced at lines 435-445 inside Overview tab |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| app/pages/1_Brand_Share.py | result (BrandShareForecastResult) | _cached_forecast → service.run_forecast → core engine DB queries | Yes — load_transitions → build_transition_matrix → M1/M2/M3.forecast → monte_carlo_simulate → compute_quantile_bands; all backed by DuckDB queries | FLOWING |
| app/components/transition_heatmap.py | matrix, obs_counts | Caller passes numpy arrays from build_transition_matrix | Yes — function requires real ndarray inputs | FLOWING |
| app/components/monte_carlo_fan.py | p10, p50, p90 | result.confidence_bands[0.10/0.50/0.90] from service | Yes — compute_quantile_bands produces real paths | FLOWING |
| app/components/kpi_card.py | value, delta | Caller computes from result.forecasts and historical_shares | Yes — KPI strip only populated when result is not None | FLOWING |
| core/models.py compute_stationary | P (transition_matrix) | Caller passes validated np.ndarray | Yes — scipy.linalg.eig on real matrix | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| register_theme() registers template and sets composed default | uv run python -c "import streamlit; import plotly.io as pio; from app.styles.plotly_theme import register_theme; register_theme(); assert 'markovlens' in pio.templates and pio.templates.default == 'streamlit+markovlens'; print('OK')" | OK; colorway[0]='#4338CA' | PASS |
| compute_stationary returns [4/7, 3/7] for [[0.7,0.3],[0.4,0.6]] | uv run python -c "…compute_stationary…assert np.allclose(s,[4/7,3/7],atol=1e-4); print('OK')" | OK; sum=1.0 | PASS |
| page file parses and all structural patterns present | uv run python -c "import ast; …assert all patterns…; print('All page assertions: OK')" | All 19 assertions: OK | PASS |
| Full test suite (61 tests) | uv run pytest -x -q | 61 passed in 8.74s | PASS |
| ruff on page file | uv run ruff check app/pages/1_Brand_Share.py | 1 I001 error (import sort) | FAIL |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| UI-01 | 02-01 | theme.css + plotly_theme.py + smoke test | SATISFIED | theme.css has full token set; register_theme works; test_plotly_theme 3/3 green |
| BS-05 | 02-01 | compute_stationary helper in core/models.py | SATISFIED | Function exists, pure, correct output; test_stationary 3/3 green |
| UI-02 | 02-02 | Reusable component library (4 components) | SATISFIED | All 4 components exist with correct signatures; test_components 8/8 green |
| BS-02 | 02-02 | transition_heatmap with fixed [0,1] scale + sparsity flags | SATISFIED | zmin/zmax/SPARSE_OBS_THRESHOLD/⚠/#D97706 all present |
| BS-03 | 02-02 | monte_carlo_fan with P10/P50/P90 + separator + legend | SATISFIED | fill/add_vline/legend names present |
| BS-01 | 02-03 | BrandShareForecastResult NumPy-only; run_forecast orchestration | SATISFIED (code) / STALE (docs) | Implementation complete; integration tests 5/5 green; REQUIREMENTS.md still shows [ ] |
| BS-04 | 02-03 | Per-model accuracy metrics; best_model computed (not hardcoded) | SATISFIED (code) / STALE (docs) | _compute_accuracy_metrics calls mape/brier/log_loss; best_model=min(MODEL_KEYS,...); REQUIREMENTS.md still shows [ ] |
| BS-06 | 02-04 | 1_Brand_Share.py — full page, all tabs, gated caching | SATISFIED | All 19 structural assertions pass; test_page_import 2/2 green |

**Orphaned requirements check:** REQUIREMENTS.md maps exactly UI-01, UI-02, BS-01, BS-02, BS-03, BS-04, BS-05, BS-06 to Phase 02 — all 8 are covered by plans 02-01 through 02-04. No orphaned requirements.

**REQUIREMENTS.md staleness note:** The file marks BS-01 and BS-04 as `[ ] Pending` in both the checklist (lines 34, 37) and the Traceability table (lines 121, 124). The code fully satisfies both requirements as verified above. This is a post-execution documentation update that was not applied.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| app/pages/1_Brand_Share.py | 21-30 | I001: import block is un-sorted (monte_carlo_fan/transition_heatmap imports split from rest of local block) | Warning | ruff fails; fixable with --fix; no runtime impact |
| .planning/REQUIREMENTS.md | 34, 37, 121, 124 | BS-01 and BS-04 marked Pending despite complete implementation | Warning | Documentation drift; would mislead anyone reading REQUIREMENTS.md |

No blocker anti-patterns found. No TODO/FIXME/placeholder comments in any of the implementation files. No NotImplementedError stubs. No hardcoded empty returns.

---

## Human Verification Required

### 1. End-to-end page walkthrough

**Test:** Start `uv run streamlit run app/Home.py`, navigate to Brand Share page. Select a seeded dataset, observe control-strip sub-caption shows "{n} transitions · {n} periods · {n} states". Click Run Forecast. Check that all four tabs populate.
**Expected:** KPI strip shows leader/gainer/loser cards; Transition Matrix tab shows annotated heatmap with ⚠ on sparse cells; Monte Carlo tab shows fan chart with P10/P50/P90 bands and a "today" vertical separator; Model Comparison shows cards with "Best fit" badge and bold-best-per-column metrics table.
**Why human:** Streamlit rendering, visual design correctness (colors, layout, badge positioning), and interactive state transitions cannot be verified programmatically.

### 2. Overview tab stationary panel

**Test:** After running a forecast, inspect the Overview tab right column.
**Expected:** Title reads exactly "Long-run equilibrium" (separate from the caveat); caveat reads "Assumes today's transition rates hold indefinitely — a what-if, not a prediction." A horizontal bar chart shows per-state equilibrium probabilities summing to 100%.
**Why human:** The exact rendering of the two-part title+caveat split (not a combined string) and bar chart visual accuracy require visual inspection.

### 3. Model Comparison verdict paragraph

**Test:** Note which model has the lowest MAPE in the metrics table. Verify the verdict paragraph names that model and displays the correct reason sentence.
**Expected:** e.g. "**m1** gives the best overall fit (MAPE 3.42%). A constant-matrix model works well here — brand-switching rates appear stable over the observed periods."
**Why human:** Requires knowing which model wins for the actual seeded dataset and reading the paragraph text for correctness.

---

## Gaps Summary

Two gaps block a clean "passed" verdict, both non-functional:

1. **REQUIREMENTS.md staleness** (BS-01, BS-04): The implementations are complete and all tests pass. The REQUIREMENTS.md file was not updated post-execution to change `[ ]` to `[x]` for BS-01 and BS-04. Fix: update lines 34, 37, 121, 124 of `.planning/REQUIREMENTS.md`.

2. **ruff I001 in 1_Brand_Share.py**: The page imports are split into two local-import blocks separated by a blank line. ruff isort flags this as unsorted. The split is intentional (imports after `set_page_config` to guarantee Streamlit initialises its template first), but the `# noqa: E402` comments on the affected lines do not suppress I001. Fix: add `# noqa: I001` to the split import block, or run `uv run ruff check --fix` (which may re-merge the blocks in a way that preserves the ordering constraint).

No functional gaps exist. All 61 tests pass. The phase goal — a recruiter can open the Brand Share page, select a dataset, run m1/m2/m3 forecasts, inspect the transition matrix heatmap, view the Monte Carlo fan chart, and compare model accuracy — is fully achieved in the codebase.

---

_Verified: 2026-05-30_
_Verifier: Claude (gsd-verifier)_
