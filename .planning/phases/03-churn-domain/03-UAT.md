---
status: complete
phase: 03-churn-domain
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md]
started: 2026-05-31T06:45:00Z
updated: 2026-05-31T07:10:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Churn Page Loads
expected: Navigate to Customer Churn in the sidebar. The page loads with a title, a dataset selector, and exactly 2 tabs: "Overview" and "What-If Simulator". No errors or missing-data warnings appear on first load.
result: pass

### 2. Sankey Ribbon Rendering
expected: In the Overview tab, a temporal Sankey diagram renders with colored ribbon flows between states across time periods. The Churned node and its incoming ribbons appear in red. Ribbons for Active state appear in green. The chart has no visible Plotly-native Sankey widgets — just custom SVG-style ribbons on a clean figure.
result: pass

### 3. Period Scrubber + Distribution Bar
expected: Below the Sankey, there is a period slider. Dragging it to different periods updates an inline horizontal bar showing the distribution of customers across states for that period. The bar segments change color per state (green=Active, red=Churned, etc.).
result: pass

### 4. Sankey State Legend
expected: Directly above the Sankey chart, there is a horizontal row of 5 color swatches with state labels (e.g., "Active", "At-Risk", "Inactive", "Reactivated", "Churned"). Each swatch color matches the ribbon color used in the Sankey for that state. (This is a new addition from the UI-review quick task.)
result: pass

### 5. KPI Strip — Values
expected: Below or above the Sankey, 4 KPI cards appear: Retention Rate (%), Avg Customer Lifetime (periods), Expected Churn Next Period (count), Revenue at Risk (Rp format). All cards show non-zero numeric values derived from the dataset.
result: pass

### 6. KPI Strip — Accent Colors
expected: The 4 KPI cards use the corrected design tokens: KPI 1 (Retention Rate) green accent, KPI 2 (Avg Lifetime) cyan accent, KPI 3 (Expected Churn) red accent, KPI 4 (Revenue at Risk) amber accent. (These were fixed in the UI-review quick task — previously KPI 2/3/4 were misassigned.)
result: pass

### 7. What-If Accordion Sliders
expected: In the "What-If Simulator" tab, sliders are grouped by from-state in expandable accordion sections (st.expander). Each expander header shows the source state name (e.g., "Active →"). Inside, sliders appear for each target state transition (e.g., "→ At-Risk", "→ Churned"). Slider range is 0–100%.
result: pass

### 8. Live Before/After Chart
expected: Moving any slider in the What-If tab immediately updates a stacked-area chart showing two versions side-by-side or overlaid: a faint "baseline" scenario and a bold "modified" scenario. The chart updates without clicking any "Run" button. The chart title or legend distinguishes baseline from modified.
result: pass

### 9. Scenario Impact Narrative + Conditional Accent
expected: Below the what-if chart, a SCENARIO IMPACT card shows a narrative sentence describing the effect (e.g., "Reducing Active → Churned by 5pp saves 120 customers."). Key numbers appear large (24px bold) with highlighted mono spans. When a change IMPROVES retention (lower churn), the card has a GREEN accent. When it WORSENS retention (higher churn), the accent is AMBER or RED. When no scenario is applied, the accent is neutral grey. (Accent logic was fixed in the UI-review quick task.)
result: pass

### 10. Reset All Button
expected: A "Reset all" button appears somewhere in the What-If tab. Clicking it returns all sliders to their baseline values and reverts the before/after chart to show baseline-only (or two identical curves). The scenario impact narrative returns to a neutral/empty state.
result: pass

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
