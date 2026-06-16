# MarkovLens

## What This Is

MarkovLens is a multi-domain Markov chain forecasting workbench built as a BA/BI portfolio piece. It applies three Markov model formulations (m1 homogeneous, m2 time-varying, m3 extended) to two real business problems — brand market share forecasting and customer churn state modelling — backed by Monte Carlo simulation with empirical longshot-bias calibration.

The primary audience is BA/BI recruiters evaluating code quality, quantitative thinking, and engineering architecture. The secondary audience is the developer themselves, who needs it to be a genuinely useful analytical tool for real datasets.

## Core Value

A GitHub repo that convinces a senior BA/BI recruiter that the developer can think quantitatively AND ship a production-quality Python data product — two live domains, correct Markov math, clean 3-layer architecture.

## Requirements

### Validated

- ✓ 3-layer clean architecture (core → domains → app, enforced dependency direction) — existing
- ✓ DuckDB schema: 6 tables (datasets, transitions, transition_matrices, simulation_runs, forecasts, scenarios) — existing
- ✓ Type system: ForecastResult, SimulationResult dataclasses — existing
- ✓ Exception hierarchy: InvalidTransitionMatrixError + domain exceptions — existing
- ✓ Config management: pydantic-settings + .env template — existing
- ✓ Shared UI components: kpi_card, empty_state, section_header stubs — existing
- ✓ LONGSHOT_CALIBRATION table from Becker (2026) hardcoded in core/simulation.py — existing
- ✓ Constants and type aliases: DEFAULT_N_SIMULATIONS=10_000, TransitionMatrix, StateVector — existing
- ✓ Test infrastructure: conftest.py with matrix fixtures, integration markers — existing

### Validated — Phase 01 (Markov Engine, complete 2026-05-29)

**Markov Engine (core/)**
- ✓ ENG-01: validate_transition_matrix() — square, non-negative, rows sum to 1.0 within 1e-9
- ✓ ENG-02: M1Homogeneous.forecast() — constant P, Y_{t+1} = Y_t · P
- ✓ ENG-03: M2TimeVarying.forecast() — time-varying P_t per period
- ✓ ENG-04: M3Extended.forecast() — P_t with growth multiplier G (market size changes)
- ✓ ENG-05: monte_carlo_simulate() — 10,000 paths, reproducible seed, np.random.default_rng
- ✓ ENG-06: calibrate_probability() — apply LONGSHOT_CALIBRATION table interpolation
- ✓ ENG-07: compute_quantile_bands() — 10th/50th/90th percentile paths
- ✓ ENG-08: Sparsity detection — warn on cells with < 20 observations
- ✓ ENG-09: walk_forward_backtest() — no future data leakage
- ✓ ENG-10: Metrics: MAPE, Brier score, log-loss (core/metrics.py)

**Data Layer**
- ✓ DATA-01: core/io/loaders.py — CSV/Parquet → validated DataFrame with sparsity check
- ✓ DATA-02: scripts/seed_data.py — download Kaggle CSVs → process → populate DuckDB
- ✓ DATA-03: build_transition_matrix() — DuckDB GROUP BY → normalized NumPy matrix

### Validated — Phase 02 (Design System + Brand Share, complete 2026-05-30)

**Design System**
- ✓ UI-01: app/styles/plotly_theme.py — `register_theme()` + `app/styles/theme.css` full CSS design-token port (sequential heatmap ramp, categorical palette, churn state colors, utility classes)
- ✓ UI-02: Component library — `transition_heatmap` (BS-02), `monte_carlo_fan` (BS-03), `kpi_card` + `empty_state` with custom-HTML (D-06/D-07)
- ✓ BS-05: `compute_stationary()` in core/models.py — dominant left eigenvector via `scipy.linalg.eig(P.T)` with power-iteration fallback

**Brand Share Domain**
- ✓ BS-01: `domains/brand_share/service.py` — NumPy-only `BrandShareForecastResult` (14 fields), `run_forecast()` full m1/m2/m3 pipeline, `list_datasets()` brand_share-filtered
- ✓ BS-02: `transition_heatmap` component — annotated cells, fixed [0,1] colorscale, `⚠` sparsity markers at < 20 observations
- ✓ BS-03: `monte_carlo_fan` component — P10/P50/P90 bands (tonexty fill), `add_vline` historical/forecast separator, named legend
- ✓ BS-04: Model comparison — MAPE/Brier/log-loss for m1/m2/m3, `best_model` derived from measured accuracy (never hardcoded), interpretation paragraph
- ✓ BS-06: `app/pages/1_Brand_Share.py` — 4-tab forecaster (Overview, Transition Matrix, Monte Carlo, Model Comparison), control strip, KPI strip, loading/empty/error states; `@st.cache_data` gated

### Validated — Phase 03 (Churn Domain, complete 2026-05-31)

**Churn Domain**
- ✓ CH-01: `domains/churn/service.py` — NumPy-only `ChurnAnalysisResult`, full m1 absorbing-chain pipeline
- ✓ CH-02: Temporal Sankey state-flow diagram (SVG bezier paths) with period scrubber
- ✓ CH-03: What-if simulator — accordion sliders per from-state, live before/after stacked-area, impact narrative
- ✓ CH-04: `app/pages/2_Churn.py` — 2-tab page (Overview + What-If), KPI strip, loading/empty/error states

### Validated — Phase 04 (Home, Export & Settings, complete 2026-06-01)

**Home Dashboard**
- ✓ HOME-01: `app/Home.py` wired to real DuckDB — KPI strip reads dataset_count, sim_run_count, avg_mape from `get_home_kpis()`; Recent Forecasts via `list_recent_forecasts()` with empty-state fallback

**Export**
- ✓ RPT-01: CSV export — `st.download_button` in Brand Share + Churn pages; two-section CSV (forecast + transition matrix); 5 unit tests verify format

**Settings**
- ✓ SET-01: `app/pages/4_Settings.py` — Datasets tab with real DuckDB list (name, domain, rows, states, created_at) + Re-run seed button in Advanced expander; Preferences/Appearance/About read-only tabs

**Query Layer**
- ✓ `HomeKpis` + `get_home_kpis()` — 4 aggregate KPIs from DB (count, sims, mape, last_forecast_at)
- ✓ `RecentForecast` + `list_recent_forecasts()` — last N forecasts with JOIN to datasets
- ✓ `Dataset.created_at` — added to existing dataclass + list_datasets/get_dataset queries

### Validated — Phase 05 (Quality Assurance & Deployment, complete 2026-06-16)

**Quality**
- ✓ QA-01: `.github/workflows/ci.yml` — 4-gate CI (ruff lint, ruff format, mypy, pytest) on push/PR to master; `astral-sh/setup-uv@v8.2.0`
- ✓ QA-02: 120 tests pass; core/ 96% coverage (>80% gate); domains/ ~83% coverage
- ✓ QA-03: Integration gate — 21 integration tests against temp DuckDB; all pass

**Deployment**
- ✓ DEPLOY-01: App deployed to https://markovlens.streamlit.app; cold start verified (Datasets=2 confirms `ensure_seeded()` ran on Streamlit Cloud's ephemeral filesystem)
- ✓ DEPLOY-02: Production smoke check documented in `docs/DEPLOYMENT.md` — 5 green items; `APP_ENV=production` secret configured

### Active

_(none — all v1.0 requirements complete)_

### Out of Scope

- m4 (non-Markov, category-based) — complexity without portfolio payoff; deferred to v0.2
- Authentication / user accounts — single-user portfolio demo, no auth needed
- Real-time data streaming — static dataset analysis is the correct scope
- Multi-user SaaS features — not the product type
- External API integrations (Bloomberg, market data) — Kaggle datasets are sufficient for demo
- Mobile-responsive UI — Streamlit desktop is the target

## Context

**Codebase state (as of Phase 02 completion, 2026-05-30):** Markov engine + design system + Brand Share domain complete. 61/61 tests pass. `app/pages/1_Brand_Share.py` is fully wired — 4-tab forecaster with Plotly theme, all 3 model types, Monte Carlo fan chart, transition heatmap, model comparison, stationary distribution panel. Domain service is NumPy-only (no Plotly coupling). Churn domain service is still a stub; `2_Churn.py` not yet created. The project is ~55% complete.

**Mathematical foundation:** Chan (2015) *Market Share Modelling and Forecasting Using Markov Chains and Alternative Models*, IJICIC Vol.11 No.4. All model implementations must cite specific equations.

**Calibration source:** Becker (2026) empirical analysis of 72.1M Polymarket trades for longshot-bias correction. Do not modify calibration table without rerunning backtests.

**Deployment target:** Streamlit Cloud (free tier) — 1GB RAM, 1 CPU, no persistent background processes.

**Data:** Kaggle public datasets (telco churn, e-commerce brand share). Must work with real business data too — entity_id must be anonymized at ingestion.

**Portfolio positioning:** The GitHub repo IS the artifact. Code quality, architectural clarity, and correct math signal BA/BI-grade quantitative + engineering thinking. UI must be professional, not a class project.

## Constraints

- **Timeline**: 4 weeks hard — actively job hunting; must ship a compelling demo
- **Tech stack**: Python 3.12 + Streamlit + DuckDB + NumPy/Plotly — locked in, no migrations
- **Math**: All Markov implementations must correctly follow Chan (2015) — wrong math invalidates the portfolio story
- **Performance**: Streamlit Cloud 1GB RAM — Monte Carlo must use @st.cache_data; no 10k-sim cold starts on every interaction
- **UI polish**: Streamlit must not look like a student project — design system via theme.css + Plotly template required

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| DuckDB over SQLite | Columnar store, 10-100x faster for aggregations, native Parquet/CSV reading | — Pending |
| 3-layer arch (core/domains/app) | Testable pure functions in core; Streamlit isolated to app layer | — Pending |
| No Alembic migrations | Schema is additive; CREATE TABLE IF NOT EXISTS + manual scripts is simpler for solo dev | — Pending |
| np.random.default_rng over np.random.seed | Modern NumPy 2.0 API; reproducible per-simulation without global state | — Pending |
| LONGSHOT_CALIBRATION hardcoded | Becker table is empirically derived; requires deliberate update + backtest rerun to change | — Pending |
| Code quality over UI as primary artifact | BA/BI recruiters evaluate GitHub; professional UI is supporting evidence, not the headline | — Pending |
| Both domains in v1 | Dual-domain demo shows generalization of the Markov engine; single-domain weakens portfolio story | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-16 after Phase 05 completion — all v1.0 milestone requirements validated*
