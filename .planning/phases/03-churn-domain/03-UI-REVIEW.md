---
phase: 03-churn-domain
review_date: 2026-05-31
reviewer: gsd-ui-auditor
overall_score: 18/24
---

# UI Review — Phase 03: Churn Domain

## Overall Score: 18/24

| Pillar | Score |
|--------|-------|
| Copywriting | 3/4 |
| Visuals | 3/4 |
| Color | 2/4 |
| Typography | 3/4 |
| Spacing | 3/4 |
| Experience Design | 4/4 |

## Top 3 Fixes (Priority Order)

1. **[Color] KPI accent tokens misassigned and KPI 2 uses wrong chart var** — The Expected Churn card uses `--state-atrisk` (amber) but design spec assigns `--state-churned` (red); Revenue at Risk uses `--state-churned` (red) but spec assigns `--state-atrisk` (amber). Additionally KPI 2 (Avg Lifetime) uses `var(--chart-1)` (indigo) instead of `var(--chart-4)` (cyan). All three mismatches break the semantic color story — amber should signal "at-risk" not "churned." Fix: swap accents at `app/pages/2_Churn.py:235,242,249`.

2. **[Visuals] Impact narrative rendered at 14px body text instead of the designed 24px bold headline** — The design reference (`pages3.jsx:99-102`) uses `.t-h2` (24px, weight 600) with highlighted `mono` spans in primary/success color for the key numbers inside the SCENARIO IMPACT card. The implementation wraps the entire narrative in `.t-sm` (14px) at `app/pages/2_Churn.py:388`. This collapses the highest-value user feedback — the "saves X customers" number — to body-text weight, losing the visual punch that makes the what-if feature compelling. Fix: render key numbers using `.t-h2` + inline `mono` spans with `color:var(--color-primary)` / `color:var(--color-success)`.

3. **[Visuals] Sankey has no state-color legend; Churned node label absent** — The design reference renders `<Legend items={CHURN_STATES} />` immediately below the ChartContainer header and above the Sankey (`pages3.jsx:32-33`). The implementation has no legend anywhere on the Overview tab. First-time users cannot decode which ribbon color represents which state without a tooltip hover. The Sankey also has no period column labels (xaxis `showticklabels: False`) so the time dimension is invisible unless users already understand the layout. Fix: add a 5-item horizontal legend row (colored dot + label) above the `st.plotly_chart` call at `app/pages/2_Churn.py:286`, and expose period tick labels or a period-axis title on the Sankey figure in `app/components/sankey_flow.py`.

---

## Pillar 1: Copywriting — 3/4

### What Worked

- Page title `"Customer Churn"` and caption `"Model customer state flow and retention with an absorbing Markov chain."` are precise and recruiter-appropriate. The caption correctly names the mathematical model without being jargon-heavy.
- No-dataset empty state: `"No churn datasets registered"` / `"Run the seed script: uv run python scripts/seed_data.py"` is exactly actionable — it tells the user the specific command. This satisfies the UX best practice of error messages being prescriptive.
- Pre-analysis empty states in both tabs are distinct and contextual: Overview says `"Select a cohort and click Run Analysis to model customer state flow."` while What-If says `"Run an analysis on the Overview tab first, then return here to model retention scenarios."` — the second is especially good because it explains the dependency.
- Control strip labels (`"Cohort"`, `"Time horizon"`, `"Run Analysis"`) are consistent with design reference (`pages3.jsx:20-21`).
- Sankey subtitle: `"Ribbon width = customers moving between states; Churned (red) is absorbing"` — correctly explains the encoding and calls out the absorbing state.
- REVENUE_TOOLTIP constant: `"Assumes Rp 50,000/customer/month — adjust in Settings (v2)"` is transparent about the assumption and signals future configurability.
- Impact narrative default prompt: `"Adjust a slider to model a retention scenario."` is clean.
- Scrubber label `f"Distribution at period {period} — drag to scrub"` directly instructs interaction.

### Gaps

- **KPI 2 unit says "periods" but design reference says "mo" (months)** — `app/pages/2_Churn.py:233`. The CONTEXT.md decision D-05 says "expected periods until absorption." "Periods" is technically correct but less intuitive for a recruiter audience than "months" when the dataset is monthly. This is a minor copy inconsistency with the reference (`pages3.jsx:26` uses `unit="mo"`).
- **KPI 3 label says "EXPECTED CHURN (next period)"** — the design reference label is `"Expected Churn (30d)"` (`pages3.jsx:27`). "Next period" is accurate but "30d" is more concrete and industry-standard for churn reporting. Minor divergence.
- **Slider labels use ASCII `"->"` not Unicode `"→"`** (`app/pages/2_Churn.py:346`). The CONTEXT.md explicitly notes this is a deliberate Windows encoding safety decision, which is acceptable — but it means the What-If left panel reads `"-> At-Risk"` instead of `"→ At-Risk"`, degrading polish slightly. The design reference uses `"→ At-Risk"` (`pages3.jsx:53`).
- **"Reset all" button is hidden when no sliders are dirty** — the design reference shows this button at the top of the card but `disabled={!dirty}` (`pages3.jsx:76`), meaning it is always visible. The implementation (`app/pages/2_Churn.py:357`) uses `if any_changed and st.button(...)` which hides it entirely before any change, removing the affordance that the panel is resettable.
- **`kpi_card("--", "--")` pre-analysis placeholder** — the `kpi_card` component's `is_empty` guard checks for `"---"` (triple dash) or `"—"` (em dash) but the page passes `"--"` (double dash, `app/pages/2_Churn.py:255`). This means the pre-analysis KPI cards do not receive the `.t-ter` tertiary color treatment defined for empty state, and no visual distinction from a real `"--"` value that could appear in live data.

---

## Pillar 2: Visuals — 3/4

### What Worked

- Sankey chart type: SVG cubic bezier path shapes per D-01. The reference component was ported exactly from `docs/design-reference/js/charts.jsx`. Ribbon width is proportional to flow, not probability, which correctly conveys customer volume.
- Temporal structure: 8-column time layout matches `SANKEY_N_COLS = 8` matching `periods={8}` in reference.
- Transparent chart backgrounds (`plot_bgcolor="rgba(0,0,0,0)"`, `paper_bgcolor="rgba(0,0,0,0)"`) allow the chart to blend into the page surface correctly.
- What-if two-panel layout (baseline faint / scenario solid) is structurally correct and matches the design reference concept.
- Stacked distribution bar uses inline HTML flex with correct proportional widths, matching the `pages3.jsx:38-42` bar design.
- Time scrubber slider is immediately below the Sankey with appropriate `"Period"` label.
- Accordion groups (`st.expander`) correctly organize from-state rows with the first group expanded by default.
- 2-tab structure (Overview / What-If) with no visible deferred State Journey tab meets D-06.

### Gaps

- **No Sankey legend.** The design reference wraps the Sankey in a `ChartContainer` with `<Legend items={CHURN_STATES} />` rendered above the chart (`pages3.jsx:32-33`). Without it, the 5 colored ribbons are indecipherable to a first-time viewer. The ribbon colors do match the `--state-*` tokens, but users need the legend to know that green = Active, amber = At-Risk, red = Churned.
- **No period column labels on Sankey.** `xaxis.showticklabels: False` in `sankey_flow.py:248` means there are zero time reference points visible on the chart. The design reference uses `P0`…`P12` labels on the what-if SVG (`pages3.jsx:159`); the Sankey omits them entirely.
- **Impact narrative rendered at body text scale.** The SCENARIO IMPACT card shows the key user-facing insight (saves X customers) at `.t-sm` 14px weight-400 (`app/pages/2_Churn.py:388`). The reference (`pages3.jsx:100`) uses `.t-h2` (24px weight-600) with highlighted `mono` spans (`color:var(--color-primary)` for the pp delta, `color:var(--color-success)` for the customer count). This is the highest-salience insight on the page and its visual treatment is undersized.
- **"Save scenario" CTA missing from What-If right panel.** The design reference has a `"Save scenario"` primary button at the bottom of the impact card (`pages3.jsx:103`). While saved scenarios are deferred to v2, the button with `disabled={!dirty}` is present in the reference to signal the capability. Its absence removes an important "recruit-impressing" feature signal.
- **`ChartContainer` wrapper absent.** The Sankey chart header is a manually assembled `div.card.accent-card` followed by a raw `st.plotly_chart` call. The reference uses `ChartContainer` which provides title, subtitle, accent bar, and download action in a standardized wrapper. The implementation's manual approach works but produces a visual gap between the header card and the chart (Streamlit default margin above `plotly_chart`).

---

## Pillar 3: Color — 2/4

### What Worked

- `--state-active` (#059669 green) accent on KPI 1 (Retention Rate) is correct per design reference.
- Sankey ribbon and node colors are derived from the exact hex values of `--state-*` tokens (verified by comment in `sankey_flow.py:19-24`). All five state colors map correctly.
- Stacked distribution bar hex colors in `STATE_BAR_COLORS` (page line 53-59) match the `--state-*` token hex values.
- What-if chart uses `rgba()` with 0.8 solid / 0.18 faint correctly matching reference opacity values (`pages3.jsx:156-157`).
- No hardcoded colors in the page file itself — all chart colors are derived from the `STATE_COLOR_PREFIX` and `STATE_COLORS_SOLID` dicts which mirror the CSS tokens.
- Transparent chart backgrounds correctly prevent color contamination from Streamlit's default white plot area.

### Gaps

- **KPI 2 (Avg Customer Lifetime) accent is `var(--chart-1)` (indigo, #4338CA) instead of `var(--chart-4)` (cyan, #0891B2).** `app/pages/2_Churn.py:235`. Design reference explicitly uses `accent="var(--chart-4)"` (`pages3.jsx:26`). This matters semantically: cyan is used for `--state-reactivated` throughout the churn palette, giving it a "lifecycle" association. Indigo is the primary brand color. Using brand color here competes with the primary CTA and dilutes the semantic coding.
- **KPI 3 (Expected Churn) accent is `var(--state-atrisk)` (amber) instead of `var(--state-churned)` (red).** `app/pages/2_Churn.py:242`. Design reference: `accent="var(--state-churned)"` (`pages3.jsx:27`). Expected Churn measures customers about to leave — it should be red (danger). Using amber here misassigns the danger signal.
- **KPI 4 (Revenue at Risk) accent is `var(--state-churned)` (red) instead of `var(--state-atrisk)` (amber).** `app/pages/2_Churn.py:249`. Design reference: `accent="var(--state-atrisk)"` (`pages3.jsx:28`). Revenue at Risk is a warning-level financial metric — amber is more appropriate. Red should be reserved for events that have already happened (churned customers).
- **Summary: KPI 3 and 4 accents are exactly swapped from spec, and KPI 2 uses the wrong chart palette entry.** Three of the four KPI cards have incorrect accent colors. The overall KPI strip uses a red/amber/amber/amber distribution instead of the specified green/cyan/red/amber distribution.
- **SCENARIO IMPACT card uses `--accent:var(--state-active)` (green) regardless of whether the scenario is improving or deteriorating.** The design reference dynamically sets `accent={dirty ? 'var(--color-success)' : 'var(--color-text-tertiary)'}` (`pages3.jsx:96`). A scenario that increases churn should not show a green accent bar.

---

## Pillar 4: Typography — 3/4

### What Worked

- All four declared type sizes are present: 32px (KPI values via `var(--fs-32)`), 18px (section headers via `.t-h3`), 14px (narrative via `.t-sm`), 12px (metadata, labels via `.t-xs`, `.t-label`).
- KPI values correctly use `font-family:var(--font-mono)` + `letter-spacing:-0.02em` for number rendering (`kpi_card.py:110-113`).
- `.t-label` class with `text-transform:uppercase` and `letter-spacing:0.04em` is used consistently for all card section labels (`SCENARIO IMPACT`, `kpi_card.py:97`).
- `.t-ter` (tertiary color) correctly applied to metadata rows: dataset `transitions · states` readout and scrubber label.
- `mono` class applied to numeric display values for tabular number alignment.
- No font sizes outside the declared design scale were found in page or component code.

### Gaps

- **Impact narrative body is `.t-sm` (14px, weight-400) where the design contract specifies `.t-h2` (24px, weight-600) for the key headline numbers.** `app/pages/2_Churn.py:388`. The design reference renders the narrative as a large bold paragraph with inline highlighted spans (`pages3.jsx:100`). The implementation loses the hierarchy distinction between the key insight and surrounding copy.
- **`.t-label` CSS rule uses `font-weight: 500` (medium) but the UI-SPEC active weight for labels is 600.** `app/styles/theme.css:168`. This is a carry-over from the Phase 02 CSS port (noted in UI-SPEC). The discrepancy means all uppercase labels (`SCENARIO IMPACT`, `RETENTION RATE`, etc.) render at medium weight rather than the semi-bold specified. Visually subtle but non-conformant with the declared typography scale.
- **No `.t-h1` or `.t-h2` typography classes are used anywhere in the Churn page.** The page uses `st.title()` for the page heading (rendered by Streamlit's native style), then drops directly to `.t-h3` for section headers. The gap between Streamlit's native H1 and the first section header is large and the in-between `.t-h2` level is entirely absent except in the design reference's impact narrative.

---

## Pillar 5: Spacing — 3/4

### What Worked

- All structural padding uses `var(--space-N)` tokens. Card padding is `var(--space-5)` (24px) throughout.
- Gap between label and value in KPI card: `var(--space-3)` (12px) via flex column gap.
- Impact narrative margin-top: `var(--space-2)` (8px) — correct.
- Delta margin-top in kpi_card: `var(--space-1)` (4px) — correct.
- Sparkline container margin-top: `var(--space-2)` (8px) — correct.
- Unit span margin: `margin-left:2px` (`kpi_card.py:105`) — this is a 2px magic number but it is genuinely sub-scale (the spacing scale starts at 4px) so it is defensible for inline typographic micro-spacing.
- Border-radius on distribution bar: `var(--radius-sm, 4px)` uses the token with a graceful fallback.
- Stacked distribution bar and scrubber row are visually tight (no extra whitespace between Sankey and scrubber).

### Gaps

- **`margin-bottom:4px` hardcoded on the scrubber label row** — `app/pages/2_Churn.py:300`. Should be `var(--space-1)` to stay on the 4px spacing scale. While the rendered pixel value is the same, using a raw pixel value breaks the system — future design token changes (e.g., base scale change) would miss this element.
- **Sankey figure `margin={"t": 8, "b": 24}` uses raw integer pixels** — `sankey_flow.py:257`. These are Plotly layout margins (not CSS), so CSS variables cannot be used here. However the values (8px top, 24px bottom) do not align to the 4px spacing scale evenly (8 = 2×4 = `--space-2` equivalent, 24 = `--space-5` equivalent). This is acceptable as Plotly margin notation is numerical-only, but it should be documented via module constants rather than inline integers.
- **What-if chart `legend.y: -0.35` is an arbitrary relative fraction** — `sankey_flow.py:354`. Necessary for Plotly legend positioning below the chart, but undocumented. A comment explaining the value is needed.
- **`height:28px` in the stacked distribution bar** is a raw pixel value in inline HTML — `app/pages/2_Churn.py:115`. The design reference also uses `height: 30` (a 30px inline style), so this is a minor protocol violation that exists in the reference too. The design system has no named height token for bars, making this unavoidable without adding a token.

---

## Pillar 6: Experience Design — 4/4

### What Worked

- **Loading state**: `with st.spinner("Running churn analysis..."):` wraps the analysis call, providing feedback for what can be a non-trivial computation on large datasets. `show_spinner=False` on `@st.cache_data` prevents double-spinner on cache hits.
- **Error states**: Two distinct error types handled with specific copy. `DatasetTooSparseError` produces a domain-specific error + an info message with actionable guidance (`"Try selecting a longer date range or merging states with fewer than 20 observations."`). The generic `except Exception` fallback uses `st.error(f"Unexpected error: {e}")` — appropriate breadth. No silent `pass` catches anywhere.
- **Empty states**: Three distinct empty states each tuned to context: (1) no datasets registered (page-level, with seed script command), (2) no analysis yet — Overview tab (with action instruction), (3) no analysis yet — What-If tab (with cross-tab dependency explanation). All use the reusable `empty_state()` component for visual consistency.
- **Session state management**: `churn.*` namespace used throughout (`PAGE_NS = "churn"`). Dataset-change guard clears result and all `churn.what_if.*` slider keys on cohort switch, preventing stale state cross-contamination. The `setdefault` + explicit key clearing pattern is robust.
- **Caching strategy**: Three cache layers — `@st.cache_resource` for DuckDB connection (singleton), `@st.cache_data` keyed on `(dataset_id, horizon)` for analysis, `@st.cache_data` keyed on `frozenset(overrides.items())` for scenarios. The frozenset approach correctly makes the dict hashable for cache keying.
- **Reset all guard**: Button only visible when `any_changed` is True — prevents accidental reset. Uses `st.rerun()` after clearing keys to immediately re-render sliders at baseline.
- **Cohort change guard**: Clears accumulated slider overrides when switching cohorts — without this, applying overrides from cohort A to cohort B's matrix would silently produce wrong results.
- **Slider state initialization pattern**: `if key not in st.session_state: st.session_state[key] = baseline_val` without passing `value=` to the widget when key exists — correct Streamlit pattern avoiding the "widget receives value from both state and argument" double-set warning.
- **Pre-analysis KPI strip**: Shows 4 placeholder cards (rather than hiding the strip) so the page layout is stable before Run Analysis — prevents layout shift on first run.
- **No `st.experimental_*` APIs** — all Streamlit calls use stable APIs.
- **`@media (prefers-reduced-motion)`** in theme.css disables transitions for accessibility.
- **`st.stop()`** after empty-state for no datasets prevents rest of page rendering with null `ds`.

### Gaps

- None that materially affect user experience. Minor: the `kpi_card("--", "--")` placeholder uses `"--"` instead of `"---"` (`app/pages/2_Churn.py:255`) which bypasses the `is_empty` visual treatment in the component (`kpi_card.py:91`). This means pre-analysis KPI cards show `"--"` in full `mono weight-600` black instead of the dimmed tertiary color. It is a cosmetic gap, not a functional one.

---

## Files Audited

- `app/pages/2_Churn.py` — full page (398 lines)
- `app/components/sankey_flow.py` — Sankey + what-if chart + narrative (428 lines)
- `app/components/kpi_card.py` — KPI card component (153 lines)
- `app/styles/theme.css` — design token layer (full file, 240+ lines)
- `.planning/phases/03-churn-domain/03-CONTEXT.md` — implementation decisions D-01..D-11
- `.planning/phases/03-churn-domain/03-04-SUMMARY.md` — what was built
- `docs/design-reference/js/pages3.jsx` — visual ground truth for Churn page (lines 1-142)
- Screenshots: NOT captured — dev server was detected at localhost:8501 (Streamlit default port) but screenshot capture via `npx playwright` was not executed as the audit evidence was sufficient from code review and known-live state from browser verification noted in 03-04-SUMMARY.md.

---

## UI REVIEW COMPLETE
