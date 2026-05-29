# Phase 02: Design System + Brand Share - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the MarkovLens design system and deliver the fully-wired Brand Share domain page:

- **UI-01** — `app/styles/plotly_theme.py` (Plotly 6.x template) + extended `app/styles/theme.css`, both ported from the imported design-reference tokens.
- **UI-02** — Reusable component library: `kpi_card` (extend), `transition_heatmap` (new), `monte_carlo_fan` (new), `empty_state` (extend).
- **BS-01** — `domains/brand_share/service.py` orchestration returning structured NumPy arrays (no Plotly coupling).
- **BS-02..BS-05** — Transition matrix heatmap, Monte Carlo fan chart, model comparison view, stationary distribution panel.
- **BS-06** — `app/pages/1_Brand_Share.py` with designed loading / empty / error states.

Built to the visual standard of the imported design prototype (`docs/design-reference/`). The Markov
engine and data layer (Phase 01) are complete and called, not modified. Churn (Phase 03), Home/Export/
Settings (Phase 04), and deployment/QA (Phase 05) are out of scope here, but the design system built
now is reused by all of them.

</domain>

<decisions>
## Implementation Decisions

### Design Reference (HARD PREREQUISITE)

- **D-01:** A complete React/Tailwind design prototype has been imported to `docs/design-reference/`
  (`markov.css` tokens, `js/*.jsx` component + page patterns, `shots/*.png`). This is the **visual
  ground truth**. `UI-SPEC.md` (produced by `/gsd:ui-phase 02`) **MUST be derived from these assets**,
  not generated from scratch via design questioning. The UI implementation ports these tokens/patterns
  into Streamlit.
- **D-02:** The prototype is React/Tailwind; the app is **Streamlit**. Translate tokens and visual
  patterns into Streamlit-achievable form (CSS injection + Plotly template + components). The bespoke
  shell (custom sidebar nav, top-bar search, ⌘K, dark-mode toggle, notifications, avatar) is a north
  star — approximate with Streamlit's native multipage sidebar; do **not** block on pixel-replicating it.
- **D-03:** `app/styles/theme.css` is replaced/extended to match `docs/design-reference/markov.css`
  (it "ports 1:1 to Streamlit CSS injection"). Adopt its token names and values verbatim where possible
  — it is a superset of the current `theme.css`. Includes light **and** dark token sets, the sequential
  heatmap ramp (`--chart-seq-1..5`: `#EEF2FF → #1E1B4B`), categorical palette (`--chart-1..6`), and
  churn state colors (used in Phase 03).

### Plotly Theme (UI-01)

- **D-04:** `app/styles/plotly_theme.py` registers a `markovlens` template and exposes `register_theme()`.
  Success criterion #1 checks `'markovlens' in pio.templates` after `register_theme()`. Per REQUIREMENTS
  UI-01, compose the default as `pio.templates.default = "streamlit+markovlens"` (layer over Streamlit's
  built-in template). Template `colorway` = categorical palette (`--chart-1..6`); heatmap colorscale = the
  `markov.css` sequential ramp; font = Geist/Inter sans with JetBrains Mono tabular numbers; paper/plot
  backgrounds + gridlines from tokens.
- **D-05:** Theme registration happens **before any chart is rendered** — `register_theme()` at module
  import / top of the page (per `.claude/rules/streamlit-conventions.md`).

### Component Library (UI-02)

- **D-06:** Build the four required components to the prototype's contracts (exact props in
  `docs/design-reference/js/ui.jsx`):
  - `kpi_card` — extend stub to support `label, value, unit, delta, delta_suffix` (e.g. `"pp"`),
    `sparkline, accent` (color bar), `icon`, `tooltip/help`, and an empty `"—"` state. Replace the
    `st.metric` fallback with custom HTML/CSS matching `markov.css` `.card`/`.accent-card`/`KPICard`.
  - `transition_heatmap` — **new**. Annotated Plotly heatmap, fixed `[0,1]` color scale (sequential
    ramp), sparsity warning markers on cells `< 20` observations.
  - `monte_carlo_fan` — **new**. Plotly fan chart: P10/P50/P90 bands, historical/forecast vertical
    separator, explicit legend.
  - `empty_state` — extend stub to match prototype styling (icon + title + description + optional CTA).
- **D-07:** Fix stale/misattributed TODO comments while in these files: `kpi_card.py` says "Phase 05",
  `theme.css` says "Phase 05", `domains/brand_share/service.py` says "Phase 03". **All are Phase 02 work** —
  update or remove these comments.

### Brand Share Page IA (BS-06) — from `docs/design-reference/js/pages2.jsx`

- **D-08:** Single page `app/pages/1_Brand_Share.py`. A page-level **control strip** (shared across tabs),
  rendered above the tabs: Dataset select (labeled, with sub-caption `"{n} transitions · {n} periods ·
  {n} states"`), model picker as a **segmented/radio** control (m1/m2/m3) with the model formula shown as
  a tooltip, horizon slider (1–24, default 12), and a primary **"Run Forecast"** button.
- **D-09:** A **KPI strip** below the controls and above the tabs: **Forecasted leader / Biggest gainer
  (Δpp) / Biggest loser (Δpp)** — computed from the forecast result (matches prototype; replaces generic
  KPIs).
- **D-10:** Four `st.tabs`: **Overview / Transition Matrix / Monte Carlo / Model Comparison**.
  - **Overview** — left: stacked-area market-share forecast (all brands; historical solid + forecast
    dashed + confidence band, driven by the primary model). Right: the **stationary-distribution panel**
    (see D-13/D-14).
  - **Transition Matrix** — heatmap (BS-02) + sequential legend + `<20 obs` marker.
  - **Monte Carlo** — fan chart (BS-03) for a selected brand + final-state histogram; controls for start
    brand, horizon, n_simulations (default 10,000), seed (default 42, randomizable).
  - **Model Comparison** — three model cards (m1/m2/m3 with formula, MAPE/Brier/log-loss, "Best fit"
    badge on the **computed** winner) + metrics table (best value per column bolded) + walk-forward
    backtest table + interpretation paragraph (BS-04, see D-12).

### Forecast Flow & Behavior

- **D-11:** Compute **all three** models on "Run Forecast". The segmented picker selects the **primary**
  model that drives the Overview stacked-area chart and the heatmap; the Model Comparison tab always shows
  all three. The **heatmap renders on dataset-select** (cheap); the forecast / fan chart / comparison are
  **gated behind "Run Forecast"**. For time-varying m2/m3, the heatmap shows the **most-recent-period Pₜ**
  with a period label.

### Model Comparison Copy (BS-04)

- **D-12:** Interpretation = an **auto-generated verdict** paragraph naming the best overall model and
  **why**, in business terms (e.g. *"m2 wins because brand-switching rates are shifting over time, which a
  constant-matrix m1 can't capture"*), shown as plain prose; **plus** a static **"How to read these
  metrics"** expander defining MAPE/Brier/log-loss in plain English. The "Best fit" badge and the named
  winner derive from **computed** metrics, never hardcoded.

### Stationary Distribution (BS-05)

- **D-13:** Always computed from the **m1 (constant) matrix**, regardless of the primary pick — it is the
  only well-defined equilibrium. Compute via the dominant **left eigenvector** of P; if it does not yield a
  valid probability vector, fall back to **power-iteration** (Pⁿ until convergence); if that also fails,
  show an `st.warning` instead of a chart.
- **D-14:** Lives in the **Overview tab's right-side panel**, replacing the prototype's mocked "Model
  insights" card. Bar chart labeled **"Long-run equilibrium (if these rates persist…)"**, values sum to
  1.0, with a **visible subcaption caveat**: *"Assumes today's transition rates hold indefinitely — a
  what-if, not a prediction."*

### Page States & Errors (BS-06)

- **D-15:** Initial state — once a dataset is selected, the heatmap renders immediately; the Overview /
  Monte Carlo / Comparison tabs show an `empty_state` placeholder until "Run Forecast" is clicked.
- **D-16:** Loading — `st.spinner("Running 10,000 simulations…")` for the Monte Carlo (sub-second on a
  `@st.cache_data` hit).
- **D-17:** Errors — sparse cells (`<20` obs) get a warning badge on the heatmap **plus** an `st.warning`
  summary, but the forecast still runs (the math is valid, just noisier). A `DatasetTooSparseError`
  surfaces as an actionable `st.error` ("merge sparse states or pick a longer range"). Never silently block.

### Domain Service & Result Contract (BS-01)

- **D-18:** Redefine `BrandShareForecastResult` to hold **structured NumPy arrays only — NO Plotly
  coupling**. Remove the current `forecast_chart_json: dict` field (it violates BS-01). Intended contents
  (exact field names = planner discretion within this constraint): per-model forecast arrays
  (`dict["m1"|"m2"|"m3", np.ndarray]`, each shape `(horizon, n_states)`), historical share array,
  `confidence_bands` (`dict[float, np.ndarray]`), `transition_matrix` (+ most-recent Pₜ for m2/m3) and
  `observation_counts`, `stationary_distribution` (`np.ndarray`), per-model `accuracy_metrics`
  (`dict[str, dict[str, float]]`), walk-forward backtest arrays, and brand labels. All Plotly figure
  construction happens in `app/components`, never in `domains/`.
- **D-19:** `service.list_datasets()` delegates to `core.db.queries.list_datasets` filtered to the
  brand_share domain. `service.run_forecast(dataset_id, model_type, horizon)` orchestrates:
  `build_transition_matrix` → `M1/M2/M3.forecast` → `monte_carlo_simulate` → `calibrate_probability` →
  `metrics` → stationary. (`monte_carlo_simulate.start_state` accepts an initial probability vector per
  Phase 01 D-13.) The "Phase 03" TODOs in the stub are wrong — this is Phase 02.

### Caching (Streamlit Cloud 1 GB constraint)

- **D-20:** Wrap the expensive forecast in `@st.cache_data`, keyed by `(dataset_id, primary_model,
  horizon, n_simulations, seed)`. DuckDB connection via `@st.cache_resource`. The second-level DuckDB
  cache (`transition_matrices` / `simulation_runs` tables) is **optional** for Phase 02 — `@st.cache_data`
  is the primary cache; add the DB cache layer only if cheap. No 10k-sim cold runs on every widget change.

### Scope vs Prototype

- **D-21:** Track the prototype's **visual standard** for BS-01..06. Implement the **cheap** prototype
  extras: Overview stacked-area forecast, final-state histogram, walk-forward backtest table. **Defer**
  the costly extras (see Deferred Ideas): click-a-cell matrix detail panel, matrix smoothing control,
  raw-vs-calibrated probability table.

### Claude's Discretion

- Exact Plotly trace styling (will be pinned by `UI-SPEC.md` from `/gsd:ui-phase 02`).
- Exact `BrandShareForecastResult` field names/types within the NumPy-only constraint (D-18).
- Whether the final-state histogram / backtest table are separate components or inline page code.
- Segmented-control implementation (`st.segmented_control` vs horizontal `st.radio`).
- Where the stationary helper lives (`core/models.py` vs a domain helper).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design System (NEW — derive UI-SPEC + implementation from these)
- `docs/design-reference/README.md` — provenance and how to use the reference set
- `docs/design-reference/markov.css` — design token layer; source of truth for `app/styles/theme.css` and `plotly_theme.py`
- `docs/design-reference/js/ui.jsx` — component contracts (KPICard, Select, Segmented, Slider, Button, Tabs, Card, ChartContainer, Badge, Tooltip, Input, Sparkline, Legend)
- `docs/design-reference/js/charts.jsx` — chart construction patterns (StackedArea, FanChart, Heatmap `seqRamp`, Histogram, MiniForecast, Legend)
- `docs/design-reference/js/pages2.jsx` — Brand Share page IA (control strip, KPI strip, 4 sub-tabs, panels)
- `docs/design-reference/js/data.jsx` — mock data shapes (what each panel/chart expects)
- `docs/design-reference/js/shell.jsx` — app shell (aspirational; approximate in Streamlit)
- `docs/design-reference/shots/churn.png` — rendered app-shell screenshot (visual ground truth)
- `app/styles/theme.css` — current tokens (to be replaced/extended from `markov.css`)
- `.streamlit/config.toml` — Streamlit theme (`primaryColor #4338CA`, etc.)

### Markov Math
- `docs/MARKOV-MODELS.md` — Chan (2015) m1/m2/m3 equations; stationary-distribution context
- `docs/MONTE-CARLO.md` — fan chart bands (P10/P50/P90), calibration, walk-forward validation

### Data / Core API
- `core/db/queries.py` — `Dataset`, `list_datasets`, `get_dataset`, `load_transitions`, `build_transition_matrix` (matrix + obs counts; `smoothing` param)
- `core/models.py` — `M1Homogeneous`, `M2TimeVarying`, `M3Extended`, `validate_transition_matrix`, `ForecastResult`
- `core/simulation.py` — `monte_carlo_simulate`, `calibrate_probability`, `compute_quantile_bands`, `SimulationResult`
- `core/metrics.py` — MAPE, Brier, log-loss
- `core/exceptions.py` — `DatasetTooSparseError`, `DatasetNotFoundError`, etc.
- `docs/DATABASE.md` — schema; `docs/API-REFERENCE.md` — core API surface; `docs/DATASETS.md` — seeded datasets
- `.planning/phases/01-markov-engine/01-CONTEXT.md` — Phase 01 decisions (esp. D-13 `start_state`, result-type shapes)

### Rules
- `.claude/rules/streamlit-conventions.md` — page structure, components, theming, loading/error states
- `.claude/rules/markov-patterns.md` — validation, `MIN_OBSERVATIONS_PER_CELL=20`, stationary, forbidden practices
- `.claude/rules/data-storage.md` — DuckDB patterns, `@st.cache_resource` / `@st.cache_data`
- `.claude/rules/coding-style.md`, `.claude/rules/python-conventions.md` — style, type hints, numerical code

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/models.py`: `M1Homogeneous`, `M2TimeVarying`, `M3Extended`, `validate_transition_matrix`,
  `ForecastResult` (`forecast_array`, `confidence_bands`, `model_type`, `horizon`, `accuracy_metrics`).
  **No stationary field** — add a helper for BS-05.
- `core/simulation.py`: `monte_carlo_simulate` (`start_state` accepts `int` or probability vector per
  Phase 01 D-13 — the fan chart uses the vector form), `calibrate_probability`, `compute_quantile_bands`,
  `SimulationResult`.
- `core/metrics.py`: MAPE, Brier, log-loss — ready for BS-04.
- `core/db/queries.py`: `Dataset`, `list_datasets`, `get_dataset`, `load_transitions`,
  `build_transition_matrix` (returns matrix + obs counts; has a `smoothing` param), `bulk_insert_transitions`.
- `core/exceptions.py`: `DatasetTooSparseError`, `DatasetNotFoundError`, `InvalidTransitionMatrixError`,
  `UnsupportedModelError`.
- `app/components/`: `kpi_card` (stub → extend), `empty_state` (stub → extend), `section_header` (usable).
- `app/styles/theme.css`: current token set — extend/replace from `docs/design-reference/markov.css`.

### Established Patterns
- 3-layer: `app/pages` → `domains/*/service.py` → `core/`. No `import streamlit` in `core/` or `domains/`.
- `@st.cache_resource` for the DuckDB connection; `@st.cache_data` for forecast results.
- `@dataclass(frozen=True)` for result value objects.
- Parameterized DuckDB queries only; all SQL wrapped in `core/db/queries.py`.

### Integration Points
- `domains/brand_share/service.py` — implement `list_datasets` + `run_forecast` (BS-01) and **redefine**
  `BrandShareForecastResult` (drop the Plotly dict field).
- `app/pages/1_Brand_Share.py` — **new** (BS-06).
- `app/styles/plotly_theme.py` — **new** (UI-01); registered via `register_theme()`.
- `app/components/transition_heatmap.py`, `app/components/monte_carlo_fan.py` — **new** (UI-02).
- Stationary-distribution helper — **new** (eigenvector + power-iteration fallback), `core/models.py` or domain.

</code_context>

<specifics>
## Specific Ideas

- Prototype brand-share domain = Indonesian e-commerce (Shopee / Tokopedia / Lazada / TikTok Shop / Blibli
  / Bukalapak, 6 states). Our seeded data is a **synthetic FMCG DGP** (Phase 01 D-01) — labels differ; the
  page is fully data-driven, so the dataset name in the selector reflects the **actual seeded dataset**,
  not the prototype's "Consumer E-commerce 2024".
- Model formula tooltips (from prototype): m1 `Y₍ₜ₊₁₎ = Yₜ·P`, m2 `Y₍ₜ₊₁₎ = Yₜ·Pₜ`, m3 `Q₍ₜ₊₁₎ = (G⊙Qₜ)·Pₜ`.
- `markov.css` component metrics: `--sidebar-w: 240px`, `--topbar-h: 56px` (Streamlit's sidebar differs —
  approximate, don't hard-fight it).
- Heatmap sequential ramp is `--chart-seq-1..5` (`#EEF2FF → #1E1B4B`); the `<20 obs` warning marker uses
  `--color-warning` (`#D97706`).
- Full interactive prototype (`MarkovLens _standalone_.html`, ~1.6 MB) lives in the original `Markov/`
  export (not committed) for a live walkthrough.

</specifics>

<deferred>
## Deferred Ideas

- **Click-a-cell transition-matrix detail panel** (prob / obs / CI / self-transition note) — prototype
  Page 6; Streamlit click-event interactivity is costly. Defer to a later polish pass.
- **Matrix smoothing control** (Off / Laplace / Bayesian) — prototype Page 6; `build_transition_matrix`
  has a `smoothing` param, but exposing the UI control is deferred.
- **Raw-vs-calibrated probability table** — prototype Page 7; `calibrate_probability` exists, the table is
  a nice-to-have. Defer.
- **Custom app shell** (bespoke sidebar nav, top-bar global search ⌘K, dark-mode toggle, notifications,
  avatar) — prototype `shell.jsx`; Streamlit's native sidebar approximates. Dark mode + global search
  deferred.
- **Home dashboard wiring, CSV export, Settings page** — Phase 04 (HOME-01, RPT-01, SET-01).
- **Churn page** (Sankey, what-if simulator) — Phase 03; reuses the Phase 02 design system.
- **Dataset upload via Settings UI** — v2 (DATA-04).

*Reviewed todos (not folded): none — todo backlog was empty for Phase 02.*

</deferred>

---

*Phase: 02-design-system-brand-share*
*Context gathered: 2026-05-29*
