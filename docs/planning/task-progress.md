# Task Progress

> Living document. Updated after every coding session.
>
> Last updated: 2026-05-31 (quick task knp — What-If vertical stack)
>
> **Note:** Phase numbering follows the GSD workflow (`.planning/STATE.md`). Authoritative live state is in `.planning/STATE.md` + `.planning/phases/NN-*/`.

## Conventions

- **Done** — task complete, commit referenced
- **In Progress** — actively being worked on
- **Pending** — planned, not started
- **Blocked** — has a blocker (note what + who)

---

## Phase 01 — Markov Engine Core ✅ Complete

| Task | Status | Commit | Notes |
|---|---|---|---|
| `validate_transition_matrix()` — rows sum 1.0, non-negative, square | ✅ Done | Phase 01 | core/models.py |
| `M1Homogeneous` — constant-P forecast | ✅ Done | Phase 01 | Chan 2015 Eq.(1) |
| `M2TimeVarying` — time-varying P_t forecast | ✅ Done | Phase 01 | Chan 2015 Eq.(2) |
| `M3Extended` — P_t + growth multiplier G | ✅ Done | Phase 01 | Chan 2015 Eq.(3) |
| `monte_carlo_simulate()` — 10k-path simulation, seed, quantile bands | ✅ Done | Phase 01 | core/simulation.py |
| `calibrate_probability()` — Becker 2026 longshot-bias table | ✅ Done | Phase 01 | core/simulation.py |
| `compute_stationary()` — stationary distribution via eigenvector | ✅ Done | Phase 01 | core/models.py |
| `build_transition_matrix()` — from raw transitions DataFrame | ✅ Done | Phase 01 | core/models.py |
| `core/io/loaders.py` — CSV/Parquet → validated DataFrame | ✅ Done | Phase 01 | |
| `core/metrics.py` — MAPE, Brier score, log-loss | ✅ Done | Phase 01 | |
| DuckDB schema (`core/db/schema.sql`) — 6 tables | ✅ Done | abb74af | datasets, transitions, matrices, sim_runs, forecasts, scenarios |
| Connection singleton (`core/db/connection.py`) | ✅ Done | abb74af | get_connection() + init_schema() |
| Query helpers (`core/db/queries.py`) | ✅ Done | 2eb18b0 | register_dataset, list_datasets, load_transitions, build_transition_matrix |
| Synthetic FMCG brand-share seed (5 brands × 24 periods) | ✅ Done | Phase 01 | scripts/seed_data.py |
| IBM Telco churn seed (4 states, 7032 rows) | ✅ Done | Phase 01 | scripts/seed_data.py |
| Unit tests — 40 tests, 90.76% coverage on core/ | ✅ Done | Phase 01 | tests/unit/ |
| Integration tests — 3 DuckDB round-trip tests | ✅ Done | Phase 01 | tests/integration/test_queries.py |

---

## Phase 02 — Design System + Brand Share Domain ✅ Complete

| Task | Status | Commit | Notes |
|---|---|---|---|
| Design system — `app/styles/theme.css` (CSS variables) | ✅ Done | Phase 02 | Extracted from Claude Design prototype (markov.css tokens) |
| Plotly theme template — `app/styles/plotly_theme.py` | ✅ Done | Phase 02 | register_theme() / inject_theme() pattern |
| Shared components — `kpi_card`, `empty_state`, `section_header` | ✅ Done | Phase 02 | app/components/ |
| `transition_heatmap.py` — annotated probability heatmap component | ✅ Done | Phase 02 | app/components/ |
| `monte_carlo_fan.py` — fan chart component with confidence bands | ✅ Done | Phase 02 | app/components/ |
| `domains/brand_share/service.py` — `BrandShareForecastResult` dataclass | ✅ Done | Phase 02 | NumPy-only, 14 fields |
| `app/pages/1_Brand_Share.py` — 4-tab forecaster | ✅ Done | Phase 02 | Overview + Transition Matrix + Monte Carlo + Model Comparison |
| BS smoke test — importlib + mock.patch avoids DB in test env | ✅ Done | Phase 02 | tests/unit/test_page_import.py |
| Walk-forward backtest table | ✅ Done | Phase 02 | Wired to service layer |
| 61 tests passing | ✅ Done | Phase 02 | Includes all Phase 01 + Phase 02 tests |

---

## Phase 03 — Customer Churn Domain ✅ Complete

| Task | Status | Commit | Notes |
|---|---|---|---|
| Wave 0 test scaffolds — CH-01/02/03 unit + integration stubs | ✅ Done | 58a5c68 | tests/unit/test_churn_service.py, tests/integration/test_churn_service.py |
| `domains/churn/service.py` — `ChurnAnalysisResult` dataclass + full service | ✅ Done | 90d5d3b | absorbing-chain detection, fundamental matrix, KPIs, state_distribution_over_time |
| `compute_avg_lifetime()` — fundamental matrix approach | ✅ Done | 90d5d3b | Returns None if no transient states |
| `simulate_scenario()` + `_apply_overrides()` — lock-target redistribution fix | ✅ Done | 4f9e471 | Bug: old code renormalized overrides away; fix: lock modified cells, redistribute remaining proportionally |
| `app/components/sankey_flow.py` — SVG bezier Sankey (CH-02) | ✅ Done | 7b94bf3 | go.Figure with shape-based ribbons (not go.Sankey per D-01) |
| `build_whatif_chart()` — side-by-side subplots, before/after stacked-area (CH-03) | ✅ Done | 3af795e | Two separate y-axes (shared_yaxes=False) |
| `impact_narrative()` — largest-delta sentence (CH-03) | ✅ Done | 3af795e | ASCII "->" for Windows console encoding safety |
| `app/pages/2_Churn.py` — 2-tab Churn page (CH-04) | ✅ Done | 655c22b | Overview (Sankey + scrubber + 4-KPI) + What-If (accordion + live chart + impact card) |
| Churn page smoke test | ✅ Done | 1efb8e9 | tests/unit/test_page_import.py |
| 4 unit tests locking `_apply_overrides` locked-cell behavior | ✅ Done | 4f9e471 | Regression protection for the root-cause bug |
| 81 tests passing, 89% overall coverage | ✅ Done | Phase 03 | core/ ~92%, brand_share ~81%, churn ~86% |
| CLAUDE.md + README.md updated for /Churn | ✅ Done | 54a118d | App Pages table, roadmap, project tree |

---

## Quick Task ikw — Churn UI-Review Visual Fixes ✅ Complete

| Task | Status | Commit | Notes |
|---|---|---|---|
| `impact_summary()` + `state_legend_html()` pure helpers in sankey_flow.py | ✅ Done | e915523 | ImpactSummary dataclass, STATE_HEX dict, 4 behavior tests |
| Wire 4 fixes into 2_Churn.py (KPI accents, legend, impact card) | ✅ Done | 60f196b | Issues 1-4 from Phase 03 UI review |
| Human visual verification | ⏭ Skipped (manual) | — | User to verify live at localhost:8501 |
| 85 tests passing, ruff clean | ✅ Done | 60f196b | No regressions from Phase 03 baseline |

---

## Quick Task knp — What-If Vertical Stack + Impact Card Spacer ✅ Complete

| Task | Status | Commit | Notes |
|---|---|---|---|
| Rewire `build_whatif_chart` to vertically stacked subplots (rows=2, cols=1, shared_xaxes, 640px) | ✅ Done | 8f81ce7 | app/components/sankey_flow.py — Baseline top / Scenario bottom; legend y retuned to -0.18 |
| Add 20px spacer between SCENARIO IMPACT card and what-if chart in 2_Churn.py | ✅ Done | 1d26846 | Inline `<div style="height:var(--space-5,20px);">` — avoids touching shared `.card.accent-card` |
| Human visual verification | ✅ Approved | — | User confirmed layout fix at localhost:8501 |
| 86 tests passing, ruff clean | ✅ Done | 8f81ce7 | `test_build_whatif_chart_has_two_stackgroups` still passes after row swap |

---

## Phase 04 — Home Dashboard + Export + Settings 🔲 Not Started

| Task | Status | Notes |
|---|---|---|
| Home KPI wiring — real DB counts (models, forecasts, accuracy) | 🟡 Pending | app/Home.py (currently scaffold) |
| CSV export — download button inside Brand Share + Churn pages | 🟡 Pending | RPT-01 |
| Settings page (`4_Settings.py`) — dataset listing + "Re-run seed" button | 🟡 Pending | |
| Phase plan via `/gsd:plan-phase 04` | 🟡 Pending | |

---

## Phase 05 — QA + Deploy 🔲 Not Started

| Task | Status | Notes |
|---|---|---|
| Coverage gate enforcement (CI or pre-push hook) | 🟡 Pending | core/ ≥ 80%, domains/ ≥ 60% |
| GitHub Actions CI (lint + test) | 🟡 Pending | |
| Streamlit Cloud account + repo connect | 🟡 Pending | User manual step |
| Seed script runs on cold deploy (DuckDB ephemeral) | 🟡 Pending | |
| Production smoke check (all pages load, charts render) | 🟡 Pending | |
| README live demo URL + badge | 🟡 Pending | |
| Phase plan via `/gsd:plan-phase 05` | 🟡 Pending | |

---

## Blocked / Issues

_None currently._
