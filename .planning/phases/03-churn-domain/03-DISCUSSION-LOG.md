# Phase 03: Churn Domain - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-31
**Phase:** 03-churn-domain
**Areas discussed:** Sankey chart type, What-if simulator scope, KPI strip metrics, Page tab count

---

## Sankey Chart Type

| Option | Description | Selected |
|--------|-------------|----------|
| Temporal Plotly Scatter (prototype match) | Multi-period ribbon flow using Plotly Scatter paths, bezier ribbons per period column, matches design reference visual | ✓ |
| Aggregate Plotly go.Sankey | Standard Plotly Sankey, states as nodes, aggregated transitions as links, loses time dimension | |
| You decide | Claude picks the approach | |

**User's choice:** Temporal Plotly Scatter (prototype match)
**Notes:** None

---

## Sankey Time Scrubber

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — include the scrubber | st.slider below Sankey, horizontal stacked bar updates with period distribution | ✓ |
| No — static Sankey only | Full temporal Sankey without period-scrubbing interactivity | |

**User's choice:** Yes — include the scrubber
**Notes:** None

---

## What-If Simulator Scope

| Option | Description | Selected |
|--------|-------------|----------|
| All rows, accordion groups | 'From Active', 'From At-Risk', etc. collapsible panels, sliders per transition, auto-renormalize | ✓ |
| One row at a time | Dropdown to select from-state, sliders for that row only | |
| You decide | Claude picks | |

**User's choice:** All rows, accordion groups
**Notes:** None

---

## What-If Right Panel

| Option | Description | Selected |
|--------|-------------|----------|
| Impact card + stacked area chart | Narrative impact prose + baseline vs. scenario stacked-area chart | ✓ |
| Side-by-side distribution bars | Two horizontal stacked bars at forecast horizon | |

**User's choice:** Impact card + stacked area chart
**Notes:** None

---

## KPI Strip — Revenue at Risk

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded per-customer assumption | DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER constant, shown in tooltip, matches 4-KPI prototype layout | ✓ |
| Replace with At-Risk Customer Count | Count-based KPI, fully data-derived, no assumptions | |
| Show 3 KPIs only (drop Revenue at Risk) | Retention Rate, Avg Lifetime, Expected Churn | |

**User's choice:** Hardcoded per-customer assumption
**Notes:** None

---

## Page Tab Count

| Option | Description | Selected |
|--------|-------------|----------|
| 2 tabs: Overview + What-If Simulator | Only implement scoped content, no empty tabs visible | ✓ |
| 3 tabs: Overview + State Journey + What-If Simulator | Adds empty State Journey placeholder | |

**User's choice:** 2 tabs: Overview + What-If Simulator
**Notes:** State Journey deferred to v2

---

## Claude's Discretion

- Exact Plotly ribbon path construction (bezier control points, opacity levels)
- Whether `sankey_flow` component is its own file or inline page code
- How fundamental matrix computation handles near-singular absorbing cases
- Whether what-if panel re-runs live on each slider tick or debounces behind a button

## Deferred Ideas

- State Journey tab — individual customer-path visualization (v2)
- Saved scenarios drawer + save modal (v2)
- Churn stationary distribution panel, CH-05 (v2)
