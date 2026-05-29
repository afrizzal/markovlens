# Phase 02: Design System + Brand Share - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-29
**Phase:** 02-design-system-brand-share
**Areas discussed:** Forecast flow & layout, Model comparison copy, Stationary distribution, Page states & errors, Overview tab + KPI strip, Dataset selector, Domain result contract, Caching strategy, Design-reference import, Scope vs prototype

---

## Forecast flow & layout

| Question | Options | Selected |
|----------|---------|----------|
| How to run the 3 models on dataset load | Run all 3 at once / Pick one, compare on demand / **All 3 + a 'primary' pick** | All 3 + a 'primary' pick |
| What renders on select vs gated behind Run Forecast | **Heatmap now, forecast gated** / Everything gated / Fully reactive | Heatmap now, forecast gated |
| Horizon control + default | **Slider 1–24, default 12** / Slider 1–12, default 6 / Number input | Slider 1–24, default 12 |
| Page structure | **Tabs** / Single vertical scroll / Two-column results | Tabs |

## Model comparison copy

| Question | Options | Selected |
|----------|---------|----------|
| How the interpretation paragraph is generated | Auto from results / Static explainer / **Auto + static 'how to read'** | Auto + static 'how to read' |
| Tone / audience | Plain English + metric gloss / Concise analyst / **Plain summary + expander** | Plain summary + expander |
| What it emphasizes | **Recommend + why** / Winner per metric only / Educational | Recommend + why |

## Stationary distribution

| Question | Options | Selected |
|----------|---------|----------|
| Which model's matrix | m1 only / Follow primary pick / **Always from m1 matrix** | Always from m1 matrix |
| Caveat communication | **Visible subcaption** / Help tooltip only / Woven into interpretation | Visible subcaption |
| Ill-defined-equilibrium handling | Compute, warn if unstable / Always compute / **Power-iteration fallback** | Power-iteration fallback |

## Page states & errors

| Question | Options | Selected |
|----------|---------|----------|
| Initial state before a forecast | **Heatmap + fan placeholder** / Controls + single empty state / Auto-run default | Heatmap + fan placeholder |
| Monte Carlo loading treatment | **Spinner** / Progress bar / st.status (staged) | Spinner |
| Sparse-data / error handling | **Badge + warn, don't block** / Block on any sparsity / Badge only | Badge + warn, don't block |

## Additional areas selected

User chose to explore: Overview tab + KPI strip, Dataset selector, Domain result contract, Caching
strategy — **and** added a custom directive: import design-reference assets from `Markov/` into
`docs/design-reference/` before `/gsd:ui-phase 02`, with `UI-SPEC.md` derived from those assets.

The imported prototype (`docs/design-reference/js/pages2.jsx`, `data.jsx`, `markov.css`) directly
**answered** the two visual areas, so they were adopted from the reference rather than re-asked:
- **Overview tab + KPI strip** → adopted: shared control strip + KPI strip (Forecasted leader / Biggest
  gainer / Biggest loser) + 4 sub-tabs; Overview left = stacked-area forecast, right = stationary panel.
- **Dataset selector** → adopted: `Select` labeled "Dataset" in the control strip with a
  `"{n} transitions · {n} periods · {n} states"` sub-caption.

The two backend areas were resolved as implementation decisions (Claude's discretion within locked
constraints):
- **Domain result contract** → `BrandShareForecastResult` redefined to NumPy-only (drop Plotly dict).
- **Caching strategy** → `@st.cache_data` keyed by (dataset, model, horizon, n_sims, seed);
  `@st.cache_resource` for the DB connection; DB-table cache optional.

## Scope vs prototype

| Question | Options | Selected |
|----------|---------|----------|
| How closely to track the prototype's extras | **Requirements + proto style** / Match prototype fully / Match, computable-only | Requirements + proto style |
| Where the BS-05 stationary panel lives | **Overview side panel** / Below the stacked area / Its own 5th tab | Overview side panel |

## Claude's Discretion

- Exact Plotly trace styling (deferred to UI-SPEC via `/gsd:ui-phase`)
- Exact `BrandShareForecastResult` field names/types (NumPy-only constraint)
- Histogram / backtest table as components vs inline
- `st.segmented_control` vs horizontal `st.radio` for the model picker
- Location of the stationary-distribution helper

## Deferred Ideas

- Click-a-cell matrix detail panel, matrix smoothing control, raw-vs-calibrated table (prototype extras)
- Custom app shell (sidebar nav, ⌘K search, dark mode, notifications), Home/Export/Settings wiring,
  Churn page, dataset upload
