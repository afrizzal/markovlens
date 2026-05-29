# Requirements: MarkovLens

**Defined:** 2026-05-29
**Core Value:** A GitHub repo that convinces a senior BA/BI recruiter that the developer can think quantitatively AND ship a production-quality Python data product — two live domains, correct Markov math, clean 3-layer architecture.

## v1 Requirements

### Core Engine

- [x] **ENG-01**: `validate_transition_matrix()` raises `InvalidTransitionMatrixError` for non-square, negative, or row-sum≠1 matrices; enforces `dtype=np.float64`
- [x] **ENG-02**: `M1Homogeneous.forecast()` implements Y_{t+1} = Y_t · P (constant P), verified against Chan (2015) Table 3 regression test
- [x] **ENG-03**: `M2TimeVarying.forecast()` implements Y_{t+1} = Y_t · P_t (P changes per period), per Chan (2015)
- [x] **ENG-04**: `M3Extended.forecast()` implements Q_{t+1} = G ⊙ Q_t · P_t with growth multiplier G, accepting absolute counts not normalized shares
- [x] **ENG-05**: `monte_carlo_simulate()` runs 10,000 vectorized paths using `np.random.default_rng(seed)` + cumsum inverse-CDF; reproducible with same seed
- [x] **ENG-06**: `calibrate_probability()` applies LONGSHOT_CALIBRATION table interpolation, returns both raw and calibrated probabilities
- [x] **ENG-07**: `compute_quantile_bands()` returns 10th/50th/90th percentile paths with `target_extractor` callable guard (not raw state-index percentiles)
- [x] **ENG-08**: Sparsity detection warns on transition cells with < `MIN_OBSERVATIONS_PER_CELL` (20) observations; flag surfaced to UI layer
- [x] **ENG-09**: `walk_forward_backtest()` re-fits matrix at each step using only past data; no future data leakage
- [x] **ENG-10**: `core/metrics.py` implements MAPE, Brier score, log-loss for forecast accuracy reporting

### Data Layer

- [x] **DATA-01**: `core/io/loaders.py` loads CSV/Parquet → validated DataFrame with required columns (`entity_id`, `period`, `from_state`, `to_state`), `dtype=float64` for numeric columns
- [x] **DATA-02**: `scripts/seed_data.py` downloads Kaggle telco churn dataset + brand share dataset (synthetic DGP with documented parameters if no clean Kaggle source), populates DuckDB `transitions` table, and pre-populates 3-5 reference forecast runs into `forecasts` table to avoid empty KPIs on cold start
- [x] **DATA-03**: `build_transition_matrix()` in `core/db/queries.py` uses DuckDB GROUP BY → normalized NumPy matrix with row-stochastic normalization (`df.div(df.sum(axis=1), axis=0)`); returns matrix + observation counts per cell

### Design System

- [ ] **UI-01**: `app/styles/theme.css` complete + `app/styles/plotly_theme.py` Plotly 6.x template (`pio.templates.default = "streamlit+markovlens"`); smoke-tested before any chart code is written
- [ ] **UI-02**: Reusable component library — `kpi_card.py` (value + delta + sparkline), `transition_heatmap.py` (annotated, fixed [0,1] scale, sparsity flags), `monte_carlo_fan.py` (10th/50th/90th bands + separator), `empty_state.py` (icon + title + description + optional CTA)

### Brand Share

- [ ] **BS-01**: `domains/brand_share/service.py` orchestrates m1/m2/m3 forecast pipeline; returns `BrandShareForecastResult` with structured NumPy arrays (no Plotly coupling in domain layer)
- [ ] **BS-02**: Transition matrix heatmap via `transition_heatmap` component — annotated cells, fixed [0,1] color scale, sparse cell warning flags
- [ ] **BS-03**: Monte Carlo fan chart via `monte_carlo_fan` component — 10th/50th/90th bands, historical/forecast separator line, explicit legend
- [ ] **BS-04**: Model comparison view — metrics table (bold winning value per column, not per row) + overlaid forecast lines; plain-language interpretation block below table
- [ ] **BS-05**: Stationary distribution panel — dominant eigenvector of P^T as bar chart, labeled "Long-run equilibrium (if these rates persist…)"
- [ ] **BS-06**: `app/pages/1_Brand_Share.py` — full page with designed loading, empty, and error states; all computation gated behind `st.button()` or `@st.cache_data`

### Churn

- [ ] **CH-01**: `domains/churn/service.py` orchestrates Markov churn pipeline; returns `ChurnAnalysisResult` with structured NumPy arrays (no Plotly coupling in domain layer)
- [ ] **CH-02**: Sankey state flow diagram — link width proportional to raw counts (not probabilities), colored by from-state, absorbing "Churned" node at bottom in red
- [ ] **CH-03**: What-if state simulator — slider to edit one row of P, live forecast update showing before/after comparison; row re-normalized on adjustment
- [ ] **CH-04**: `app/pages/2_Churn.py` — full page with designed loading, empty, and error states

### Export

- [ ] **RPT-01**: CSV export — download forecast results and transition matrix for current session via `st.download_button`

### Home Dashboard

- [ ] **HOME-01**: `app/Home.py` wired to real data — KPI strip showing dataset count, last forecast timestamp, total simulation runs, overall model accuracy (MAPE) from `forecasts` table

### Settings

- [ ] **SET-01**: `app/pages/4_Settings.py` — list registered datasets with row count, state count, domain, and last-seeded timestamp; allow re-running seed script

### Deployment

- [ ] **DEPLOY-01**: App deployed to Streamlit Cloud; cold start verified — seed script runs automatically if `forecasts` table is empty, all pages load without error
- [ ] **DEPLOY-02**: Production smoke check documented — checklist in `docs/DEPLOYMENT.md` confirming: app loads, both domain pages render, Home KPIs show real data, CSV export works

### Quality

- [ ] **QA-01**: Unit tests for `core/` — > 80% coverage; Chan (2015) Table 3/4 regression tests un-skipped and passing; all ENG-01..ENG-10 covered
- [ ] **QA-02**: Integration tests for `core/db/` — `queries.py` and data loading paths tested against real temp DuckDB (`tmp_path` fixture)
- [ ] **QA-03**: Domain layer tests for `domains/` — > 60% coverage; service orchestration paths covered

## v2 Requirements

### Export

- **RPT-02**: PDF report — formatted forecast output via ReportLab; full layout with charts and metrics table

### Data

- **DATA-04**: Dataset upload via Settings UI — user uploads CSV, app validates columns, registers as new dataset in DuckDB

### Churn

- **CH-05**: Churn stationary distribution panel — long-run state equilibrium for the churn model

### Quality

- **QA-04**: UI smoke tests — each Streamlit page renders without exception (headless Playwright or st.testing)

## Out of Scope

| Feature | Reason |
|---------|--------|
| m4 (non-Markov, category-based) | Additional complexity without commensurate portfolio payoff; deferred to v0.2 |
| Authentication / user accounts | Single-user portfolio demo; auth adds complexity with no demo value |
| Real-time data streaming | Static dataset analysis is the correct scope for Markov chain demonstration |
| Multi-user SaaS features | Wrong product type |
| External market data APIs | Kaggle datasets are sufficient for recruiter demo |
| Mobile-responsive UI | Streamlit desktop is the target; mobile layout adds complexity |
| `np.random.seed()` (legacy) | NEP 50 type promotion + reproducibility require `np.random.default_rng(seed)` exclusively |
| Raw SQL strings outside `queries.py` | SQL injection risk; all queries must go through `core/db/queries.py` |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENG-01 | Phase 01 | Complete |
| ENG-02 | Phase 01 | Complete |
| ENG-03 | Phase 01 | Complete |
| ENG-04 | Phase 01 | Complete |
| ENG-05 | Phase 01 | Complete |
| ENG-06 | Phase 01 | Complete |
| ENG-07 | Phase 01 | Complete |
| ENG-08 | Phase 01 | Complete |
| ENG-09 | Phase 01 | Complete |
| ENG-10 | Phase 01 | Complete |
| DATA-01 | Phase 01 | Complete |
| DATA-02 | Phase 01 | Complete |
| DATA-03 | Phase 01 | Complete |
| UI-01 | Phase 02 | Pending |
| UI-02 | Phase 02 | Pending |
| BS-01 | Phase 02 | Pending |
| BS-02 | Phase 02 | Pending |
| BS-03 | Phase 02 | Pending |
| BS-04 | Phase 02 | Pending |
| BS-05 | Phase 02 | Pending |
| BS-06 | Phase 02 | Pending |
| CH-01 | Phase 03 | Pending |
| CH-02 | Phase 03 | Pending |
| CH-03 | Phase 03 | Pending |
| CH-04 | Phase 03 | Pending |
| HOME-01 | Phase 04 | Pending |
| RPT-01 | Phase 04 | Pending |
| SET-01 | Phase 04 | Pending |
| QA-01 | Phase 05 | Pending |
| QA-02 | Phase 05 | Pending |
| QA-03 | Phase 05 | Pending |
| DEPLOY-01 | Phase 05 | Pending |
| DEPLOY-02 | Phase 05 | Pending |

**Coverage:**
- v1 requirements: 33 total
- Mapped to phases: 33
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-29*
*Last updated: 2026-05-29 after roadmap creation — traceability populated*
