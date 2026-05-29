# Design Reference — MarkovLens

**Imported:** 2026-05-29 (Phase 02 prerequisite, via `/gsd:discuss-phase 02`)
**Source:** AI-generated design prototype (`Markov/` export) — a 12-page React/Tailwind "Design Contract" mock of the full MarkovLens app.

## What this is

This folder is the **visual ground truth** for the MarkovLens UI. The Phase 02 UI design contract
(`UI-SPEC.md`, produced by `/gsd:ui-phase 02`) **MUST be derived from these assets** — not generated
from scratch via design questioning. Likewise the design-system implementation (UI-01 `plotly_theme.py`
+ extended `theme.css`, UI-02 component library) ports these tokens and patterns into Streamlit.

## Contents

| Path | What it defines |
|---|---|
| `markov.css` | **Design token layer** — colors (light + dark), sequential heatmap ramp, categorical palette, churn-state colors, spacing/radius/shadow, type scale, motion, and full component CSS (buttons, cards, badges, inputs, segmented, slider, table, tabs, tooltip, skeleton). Source of truth for `app/styles/theme.css`. |
| `js/ui.jsx` | Component contracts: `KPICard`, `Select`, `Segmented`, `Slider`, `Button`, `Tabs`, `Card`, `ChartContainer`, `Badge`, `Tooltip`, `Input`, `Sparkline`, `Legend`, `Icon`. |
| `js/charts.jsx` | Chart construction patterns: `StackedArea`, `FanChart`, `Heatmap` (`seqRamp`), `Sankey`, `Histogram`, `MiniForecast`, `Legend`. |
| `js/pages2.jsx` | **Brand Share page IA** (Phase 02): control strip, KPI strip, 4 sub-tabs (Overview / Transition Matrix / Monte Carlo / Model Comparison), side panels. |
| `js/pages1.jsx` | Design-system showcase, landing/login. |
| `js/pages3.jsx` | Churn / What-If / Reports (Phase 03+). |
| `js/shell.jsx` | App shell (sidebar nav, top bar, search, dark-mode toggle) — **aspirational**; approximate with Streamlit's native multipage sidebar. |
| `js/app.jsx`, `js/data.jsx`, `js/icons.jsx` | Router/page registry, mock data shapes (what each panel expects), icon set. |
| `shots/churn.png` | Rendered app-shell screenshot — sidebar + top bar + breadcrumb layout. |
| `shots/landing.png`, `shots/ds.png` | Additional rendered views. |

## Important framing

- The prototype is **React/Tailwind**; the app is **Streamlit**. Translate tokens/patterns into
  Streamlit-achievable form (CSS injection + Plotly template + components). The bespoke shell
  (custom sidebar, top-bar search, ⌘K, notifications) is a north star, not a hard requirement —
  approximate it; do not block on pixel-replicating it.
- Mock data labels (Shopee/Tokopedia/… e-commerce) are illustrative. The real Brand Share page is
  data-driven off the seeded **synthetic FMCG** dataset, so labels will differ.
- The full interactive single-file prototype (`MarkovLens _standalone_.html`, ~1.6 MB) was **not**
  committed; it lives in the original `Markov/` export if a live walkthrough is needed.
