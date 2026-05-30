# Phase 03: Churn Domain - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the fully-wired Customer Churn domain page reusing the Phase 02 design system:

- **CH-01** — `domains/churn/service.py` rewrite: `ChurnAnalysisResult` with NumPy arrays only (no Plotly coupling), full churn pipeline.
- **CH-02** — Temporal Sankey state flow diagram with time scrubber.
- **CH-03** — What-if simulator: all transition rows editable in accordion groups, row auto-renormalized, live before/after forecast comparison.
- **CH-04** — `app/pages/2_Churn.py` with designed loading, empty, and error states.

The Markov engine (Phase 01) and design system + component library (Phase 02) are complete and called — not modified. Home/Export/Settings (Phase 04) and QA/Deployment (Phase 05) are out of scope here.

</domain>

<decisions>
## Implementation Decisions

### Sankey Chart (CH-02)

- **D-01:** Use a **temporal multi-period Plotly Scatter** Sankey — ribbons spanning 8+ period columns, matching the design reference prototype (`docs/design-reference/js/charts.jsx` Sankey component). Each column = one period; ribbon width = proportional to raw transition counts (not probabilities). Node colors from churn state palette (`--state-active/atrisk/inactive/reactivated/churned`). Absorbing "Churned" node rendered at the bottom in `--state-churned` (red). Do NOT use Plotly `go.Sankey` (loses temporal dimension).
- **D-02:** Include a **time scrubber** below the Sankey: `st.slider` for period selection (0..N, default = last period) + a horizontal stacked distribution bar that updates to show state proportions at the selected period. `ChurnAnalysisResult` must store period-by-period state distribution array (`shape (n_periods+1, n_states)`) and per-period transition flow data for the ribbon chart.

### What-If Simulator (CH-03)

- **D-03:** Show **all transition rows** editable simultaneously — accordion groups by from-state (e.g. "From Active", "From At-Risk", "From Inactive"). Each group is collapsible. Within each group, sliders for every `→ To-State` transition. Any slider change **auto-renormalizes the entire row to sum to 1.0** before running the forecast. A "Reset all" ghost button appears when any value differs from baseline.
- **D-04:** Right panel = **impact summary card + stacked-area before/after chart**. Impact card: narrative prose driven by the largest delta (e.g. "Reducing Active → At-Risk by 3pp saves X customers"). Stacked area: baseline (translucent, opacity ≈ 0.18) vs. modified scenario (solid, opacity ≈ 0.8) for all states over the forecast horizon. Both update live as sliders change (via `st.session_state`; no button press required).

### KPI Strip (CH-04)

- **D-05:** Four KPIs matching the design reference:
  1. **Retention Rate** — share of customers in Active state at period N / initial Active count (or fraction still non-churned at horizon).
  2. **Avg Customer Lifetime** — expected periods until absorption into Churned state (computed from fundamental matrix `(I - Q)^{-1}` on the transient submatrix).
  3. **Expected Churn (30d / next period)** — count of Active customers × P(Active → Churned) in one step.
  4. **Revenue at Risk** — `expected_churn_count × DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER`. The constant (`DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER`) is a module-level constant in the service, annotated with a UI tooltip: *"Assumes Rp [value]/customer/month — adjust in Settings (v2)"*. Expose as a named constant so future Settings integration (v2) can wire it to a user-configurable value.

### Page Structure (CH-04)

- **D-06:** **2 tabs only** — "Overview" (Sankey + time scrubber + KPI strip) and "What-If Simulator" (accordion sliders + impact card + before/after chart). State Journey is deferred to v2 and must NOT appear as a visible empty tab.
- **D-07:** Same page structure pattern as `1_Brand_Share.py`: `set_page_config` → `register_theme()` → `inject_theme()` → module constants → `@st.cache_resource` DB → `@st.cache_data` for analysis results → control strip (cohort selector + horizon slider + "Run Analysis" button) → KPI strip → tabs.
- **D-08:** Session state keys namespaced `churn.*` (e.g. `churn.result`, `churn.scenario_matrix`). Scenario matrix (modified P) stored in session state so the what-if panel can re-run without re-fetching the original analysis.

### Domain Service (CH-01)

- **D-09:** Rewrite `ChurnAnalysisResult` with NumPy-only fields — NO Plotly coupling in domain layer. Minimum fields: `transition_matrix` (shape `(n_states, n_states)`), `state_distribution_over_time` (shape `(n_periods+1, n_states)`), `baseline_forecast` (shape `(horizon+1, n_states)`), `kpis` (dict of computed KPI values), `state_labels` (list), `dataset_name` (str), `n_customers` (int), `observation_counts` (shape `(n_states, n_states)`). All Plotly construction happens in the page or a new `app/components/sankey_flow.py` component.
- **D-10:** Rename `list_cohorts()` → `list_datasets(domain="churn")` to match the shared DuckDB `datasets` table API (consistent with `brand_share.service.list_datasets()`). Keep "Cohort" terminology in the UI selector label only.
- **D-11:** `run_analysis(conn, dataset_id, horizon)` orchestrates: `build_transition_matrix` → `M1Homogeneous.forecast` (churn uses m1 by default — only one model type surfaced, unlike brand share) → compute KPIs. `simulate_scenario(conn, dataset_id, horizon, transition_overrides)` accepts a partial dict of `{(from_i, to_j): new_prob}` row overrides, renormalizes, and returns a second `state_distribution_over_time` for comparison.

### Claude's Discretion

- Exact Plotly trace parameters for ribbon path construction (bezier control points, opacity levels).
- Whether `sankey_flow` component lives in `app/components/sankey_flow.py` or inline in the page.
- How `(I - Q)^{-1}` fundamental matrix computation handles near-singular cases (e.g., all customers absorbed).
- Whether the what-if right panel re-runs on each slider tick or debounces via a "Calculate" button (lean toward live since Streamlit re-runs are fast for small matrices; gate with `@st.cache_data` keyed on the scenario matrix hash).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Reference (visual ground truth — same source as Phase 02)
- `docs/design-reference/js/pages3.jsx` — Churn page IA: PageChurnLanding (Overview), PageWhatIf (What-If Simulator), WhatIfChart, ChurnTabs
- `docs/design-reference/js/charts.jsx` — Sankey component (temporal ribbon SVG logic to port to Plotly Scatter)
- `docs/design-reference/js/data.jsx` — CHURN_STATES, CHURN (5-state P matrix + dist over 12 periods), COHORT_KPIS
- `docs/design-reference/markov.css` — churn state color tokens: `--state-active`, `--state-atrisk`, `--state-inactive`, `--state-reactivated`, `--state-churned`
- `docs/design-reference/shots/churn.png` — rendered screenshot (visual ground truth for the churn page)

### Prior Phase Context
- `.planning/phases/02-design-system-brand-share/02-CONTEXT.md` — design system decisions (D-01..D-21), component contracts, caching pattern, 3-layer architecture decisions

### Markov Math
- `docs/MARKOV-MODELS.md` — Chan (2015) m1/m2/m3 equations
- `docs/MONTE-CARLO.md` — Monte Carlo simulation, calibration, quantile bands

### Core API
- `core/db/queries.py` — `Dataset`, `list_datasets`, `get_dataset`, `load_transitions`, `build_transition_matrix`
- `core/models.py` — `M1Homogeneous`, `validate_transition_matrix`, `compute_stationary`
- `core/simulation.py` — `monte_carlo_simulate`, `calibrate_probability`, `compute_quantile_bands`
- `core/exceptions.py` — `DatasetTooSparseError`, `DatasetNotFoundError`, `InvalidTransitionMatrixError`
- `docs/DATABASE.md` — schema reference; `docs/DATASETS.md` — seeded datasets (Telco churn dataset structure)

### Existing Page (pattern reference)
- `app/pages/1_Brand_Share.py` — complete page implementation; follow exact same structural pattern for `2_Churn.py`
- `domains/brand_share/service.py` — BrandShareForecastResult shape + run_forecast pattern; mirror for ChurnAnalysisResult

### Rules
- `.claude/rules/streamlit-conventions.md` — page structure, caching, loading/empty/error states
- `.claude/rules/markov-patterns.md` — validation, MIN_OBSERVATIONS_PER_CELL=20, forbidden practices
- `.claude/rules/python-conventions.md` — type hints, NumPy style, @dataclass(frozen=True)
- `.claude/rules/data-storage.md` — DuckDB patterns, parameterized queries

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/components/kpi_card.py` — ready; use `label, value, unit, delta, delta_suffix, accent, icon, tooltip`
- `app/components/empty_state.py` — ready; use for pre-analysis state on both tabs
- `app/components/section_header.py` — ready; use for tab section headers
- `app/styles/__init__.py` — `inject_theme()` + `register_theme()`; call at page top
- `core/models.py` — `compute_stationary()` (eigenvector + power-iteration fallback); reuse for avg lifetime computation (fundamental matrix)
- `core/db/queries.py` — `build_transition_matrix(conn, dataset_id)` returns `(matrix, obs_counts)`; `load_transitions()` returns DataFrame

### Established Patterns
- 3-layer: `app/pages/2_Churn.py` → `domains/churn/service.py` → `core/`; no `import streamlit` in domain layer
- `@st.cache_resource` for DuckDB connection; `@st.cache_data` for `run_analysis()` keyed on `(dataset_id, horizon)`
- `@dataclass(frozen=True)` for `ChurnAnalysisResult`
- Session state prefix: `churn.*`
- Accordion pattern: use `st.expander` per from-state group in What-If panel
- `N803/N806` ruff suppression for matrix variable names (P, Q, Y) — already established in Phase 01/02

### Integration Points
- `domains/churn/service.py` — rewrite (stub has wrong result type and TODOs referencing wrong phase)
- `app/pages/2_Churn.py` — new page (CH-04); auto-discovered by Streamlit at `/Churn`
- `app/components/` — new `sankey_flow.py` component for the temporal Plotly Scatter Sankey (or inline, per Claude's discretion)
- `app/styles/theme.css` — churn state colors already present; no changes needed

</code_context>

<specifics>
## Specific Ideas

- Design reference uses 5 churn states: Active, At-Risk, Inactive, Reactivated, Churned — with "Churned" as near-absorbing (P[churned, churned] = 0.98). The Telco dataset may have different state labels; `state_labels` in the result drives all chart labeling dynamically.
- The prototype accordion groups sliders by from-state label (e.g. "From Active"). Ghost marker on each slider = baseline value (per prototype copy: "ghost marker = baseline value").
- Revenue at Risk constant: `DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER = 50_000` (Rp). Shown in UI tooltip. Named so future Settings v2 can expose it as a user-configurable field.
- Impact card narrative driven by the single largest delta transition (not a generic message). Follow prototype: "Reducing [From] → [To] by Xpp saves N customers."
- The `simulate_scenario` function in the service returns a new `state_distribution_over_time` array only — not a full `ChurnAnalysisResult`. The page stores the baseline result in `@st.cache_data` and only re-runs the scenario overlay, keeping cold-start cost low.

</specifics>

<deferred>
## Deferred Ideas

- **State Journey tab** — individual customer-path visualization (sequence plots, path frequency heatmap). Prototype shows it in the ChurnTabs header but provides no implementation. Deferred to v2.
- **Saved scenarios drawer** — the prototype's slide-out drawer for saving/loading named what-if scenarios (maps to `scenarios` DuckDB table). Deferred to v2; table exists in schema, UI deferred.
- **Save scenario modal** — name + save a specific transition override configuration. Deferred with saved scenarios drawer.
- **Stationary distribution panel for churn** — analogous to Brand Share BS-05. Deferred to v2 as CH-05 in REQUIREMENTS.md.
- **Dataset upload from Settings page** — DATA-04 (v2 scope).

*Reviewed todos (not folded): none — no pending todos matched Phase 03 scope.*

</deferred>

---

*Phase: 03-churn-domain*
*Context gathered: 2026-05-31*
