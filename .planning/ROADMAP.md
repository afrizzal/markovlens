# Roadmap: MarkovLens

**Milestone:** v1.0 — Portfolio-ready Markov chain forecasting workbench
**Phases:** 5
**Requirements:** 33 v1 requirements fully mapped

---

## Phases

- [x] **Phase 01: Markov Engine** — Implement and validate the complete core engine: all three model classes, Monte Carlo simulation, calibration, metrics, and data layer
- [ ] **Phase 02: Design System + Brand Share** — Establish the Plotly/CSS design system and deliver the fully wired Brand Share domain page
- [ ] **Phase 03: Churn Domain** — Deliver the fully wired Customer Churn domain page reusing Phase 02 design system
- [ ] **Phase 04: Home, Export & Settings** — Wire the Home dashboard to real data, add CSV export, and complete the Settings page
- [ ] **Phase 05: Quality Assurance & Deployment** — Achieve test coverage targets and deploy a verified, cold-start-clean app to Streamlit Cloud

---

## Phase Details

### Phase 01: Markov Engine
**Goal**: The complete `core/` engine is implemented, validated against Chan (2015), and tested — every downstream phase can call it without encountering NotImplementedError
**Depends on**: Nothing (first phase)
**Requirements**: ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06, ENG-07, ENG-08, ENG-09, ENG-10, DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. A Python REPL session can import `core.models`, instantiate `M1Homogeneous`, call `.forecast()` with a valid matrix, and get a state-vector result that matches Chan (2015) Table 3 reference values
  2. `monte_carlo_simulate()` called twice with the same seed returns bit-identical output; called with different seeds returns different output
  3. `validate_transition_matrix()` raises `InvalidTransitionMatrixError` for a row that sums to 1.1, a matrix with a negative cell, and a non-square input — and passes silently on a valid 3x3 stochastic matrix
  4. Running `uv run pytest tests/unit/ -m "not slow"` reports > 80% coverage for `core/` with all ENG-01..ENG-10 regression tests green
  5. `scripts/seed_data.py` runs to completion and populates the `transitions` and `forecasts` DuckDB tables with at least 5 reference forecast rows visible via a `SELECT COUNT(*)` query
**Plans**: 6 plans
- [x] 01-01-PLAN.md — Scaffold Wave 0 test stubs across all phase modules
- [x] 01-02-PLAN.md — validate_transition_matrix + M1/M2/M3 (Chan 2015 regression)
- [x] 01-03-PLAN.md — monte_carlo_simulate + calibrate + quantile_bands + walk_forward + metrics
- [x] 01-04-PLAN.md — serialization helpers + build_transition_matrix + validate_transitions_df
- [x] 01-05-PLAN.md — IBM Telco CSV + synthetic FMCG DGP + reference forecasts (idempotent)
- [x] 01-06-PLAN.md — >=80% core/ coverage + ruff + mypy clean

### Phase 02: Design System + Brand Share
**Goal**: The Brand Share page is fully functional end-to-end — a recruiter can open it, select a dataset, run m1/m2/m3 forecasts, inspect the transition matrix heatmap, view the Monte Carlo fan chart, and compare model accuracy
**Depends on**: Phase 01
**Requirements**: UI-01, UI-02, BS-01, BS-02, BS-03, BS-04, BS-05, BS-06
**Success Criteria** (what must be TRUE):
  1. `python -c "import plotly.io as pio; from app.styles.plotly_theme import register_theme; register_theme(); assert 'markovlens' in pio.templates"` exits with code 0 — the Plotly theme is registered before any chart is rendered
  2. Navigating to `/Brand_Share` in a running Streamlit app shows a non-empty transition matrix heatmap with color-coded cells and a sparsity warning badge on any cell with < 20 observations
  3. Clicking "Run Forecast" produces a Monte Carlo fan chart with three visible bands (10th/50th/90th percentile), a vertical separator between historical and forecast periods, and an explicit chart legend
  4. The model comparison table shows MAPE, Brier score, and log-loss for m1, m2, and m3 side-by-side, with the best value per metric bolded, followed by a plain-language interpretation paragraph
  5. The stationary distribution panel shows a bar chart labeled "Long-run equilibrium (if these rates persist…)" with values that sum to 1.0
**Plans**: TBD
**UI hint**: yes

### Phase 03: Churn Domain
**Goal**: The Customer Churn page is fully functional — a recruiter can open it, view the Sankey state flow diagram, adjust a transition row via slider, and see before/after forecast comparison
**Depends on**: Phase 02
**Requirements**: CH-01, CH-02, CH-03, CH-04
**Success Criteria** (what must be TRUE):
  1. Navigating to `/Churn` shows a Sankey diagram where link widths are proportional to raw transition counts (not probabilities), node colors match from-state, and the absorbing "Churned" node is rendered in red at the bottom
  2. The what-if simulator renders a slider for a selected transition row; adjusting the slider re-normalizes the row to sum to 1.0 and immediately updates a side-by-side before/after forecast comparison without reloading the page
  3. `domains/churn/service.py` can be imported and called from a plain Python script (no Streamlit import); `ChurnAnalysisResult` contains structured NumPy arrays, not serialized Plotly JSON
**Plans**: TBD
**UI hint**: yes

### Phase 04: Home, Export & Settings
**Goal**: The app is a coherent product — the Home dashboard shows live KPIs from real forecast data, CSV export works from the Brand Share page, and the Settings page lists datasets with their metadata
**Depends on**: Phase 03
**Requirements**: HOME-01, RPT-01, SET-01
**Success Criteria** (what must be TRUE):
  1. Opening the Home page shows a KPI strip with four non-zero values: dataset count, last forecast timestamp, total simulation runs, and overall MAPE — all sourced from the `forecasts` and `simulation_runs` DuckDB tables (not hardcoded)
  2. Clicking the CSV export button on the Brand Share page triggers a browser download of a `.csv` file containing the forecast results and transition matrix for the current session
  3. The Settings page lists at least 2 registered datasets, each showing domain, row count, state count, and last-seeded timestamp; a "Re-run seed script" button exists and completes without error
**Plans**: TBD
**UI hint**: yes

### Phase 05: Quality Assurance & Deployment
**Goal**: The app is deployed, publicly accessible, and verifiably correct — all test suites pass, and a documented smoke check confirms the live Streamlit Cloud deployment loads cleanly from a cold start
**Depends on**: Phase 04
**Requirements**: QA-01, QA-02, QA-03, DEPLOY-01, DEPLOY-02
**Success Criteria** (what must be TRUE):
  1. `uv run pytest` with no flags exits green; `core/` coverage >= 80%, `domains/` coverage >= 60%; no tests skipped except those marked `@pytest.mark.slow`
  2. The integration test suite (`pytest -m integration`) passes against a fresh temporary DuckDB file — `build_transition_matrix()`, `core/io/loaders.py`, and all `queries.py` paths covered
  3. The Streamlit Cloud URL loads the Home page within 60 seconds on a cold start (empty cache), displaying real KPI values — confirming the seed script auto-ran and the `forecasts` table is not empty
  4. `docs/DEPLOYMENT.md` contains a completed smoke-check checklist with green status for: app loads, Brand Share page renders, Churn page renders, Home KPIs show real data, CSV export works
**Plans**: TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 01. Markov Engine | 6/6 | Complete | 2026-05-29 |
| 02. Design System + Brand Share | 0/TBD | Not started | - |
| 03. Churn Domain | 0/TBD | Not started | - |
| 04. Home, Export & Settings | 0/TBD | Not started | - |
| 05. Quality Assurance & Deployment | 0/TBD | Not started | - |

---

## Requirement Coverage

| REQ-ID | Phase | Category |
|--------|-------|----------|
| ENG-01 | Phase 01 | Core Engine |
| ENG-02 | Phase 01 | Core Engine |
| ENG-03 | Phase 01 | Core Engine |
| ENG-04 | Phase 01 | Core Engine |
| ENG-05 | Phase 01 | Core Engine |
| ENG-06 | Phase 01 | Core Engine |
| ENG-07 | Phase 01 | Core Engine |
| ENG-08 | Phase 01 | Core Engine |
| ENG-09 | Phase 01 | Core Engine |
| ENG-10 | Phase 01 | Core Engine |
| DATA-01 | Phase 01 | Data Layer |
| DATA-02 | Phase 01 | Data Layer |
| DATA-03 | Phase 01 | Data Layer |
| UI-01 | Phase 02 | Design System |
| UI-02 | Phase 02 | Design System |
| BS-01 | Phase 02 | Brand Share |
| BS-02 | Phase 02 | Brand Share |
| BS-03 | Phase 02 | Brand Share |
| BS-04 | Phase 02 | Brand Share |
| BS-05 | Phase 02 | Brand Share |
| BS-06 | Phase 02 | Brand Share |
| CH-01 | Phase 03 | Churn |
| CH-02 | Phase 03 | Churn |
| CH-03 | Phase 03 | Churn |
| CH-04 | Phase 03 | Churn |
| HOME-01 | Phase 04 | Home Dashboard |
| RPT-01 | Phase 04 | Export |
| SET-01 | Phase 04 | Settings |
| QA-01 | Phase 05 | Quality |
| QA-02 | Phase 05 | Quality |
| QA-03 | Phase 05 | Quality |
| DEPLOY-01 | Phase 05 | Deployment |
| DEPLOY-02 | Phase 05 | Deployment |

**Coverage: 33/33 ✓**

---
*Roadmap created: 2026-05-29*
*Last updated: 2026-05-29 after initial creation*
