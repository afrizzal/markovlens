---
phase: quick-260531-ikw
plan: 01
subsystem: app/pages, app/components
tags: [ui-fix, churn, kpi, sankey, impact-card, legend, typography]
dependency_graph:
  requires: [Phase-03-complete]
  provides: [UI-FIX-CHURN-01, UI-FIX-CHURN-02, UI-FIX-CHURN-03, UI-FIX-CHURN-04]
  affects: [app/pages/2_Churn.py, app/components/sankey_flow.py]
tech_stack:
  added: []
  patterns:
    - "ImpactSummary frozen dataclass for structured impact return"
    - "state_legend_html() pure HTML builder — no streamlit import in component"
    - "_impact_parts() private helper factors shared churn-delta math"
key_files:
  created: []
  modified:
    - app/components/sankey_flow.py
    - app/pages/2_Churn.py
    - tests/unit/test_churn_service.py
decisions:
  - "Introduced ImpactSummary dataclass so impact accent token and HTML are co-located — avoids duplicating direction logic between the card and the accent bar"
  - "Kept impact_narrative() intact in sankey_flow.py (pure-string fallback) — page no longer imports it but component module API is not broken"
  - "_impact_parts() factors the shared largest-delta + churn-delta computation — called by impact_summary(), avoids code duplication"
metrics:
  duration: "9 minutes"
  completed: "2026-05-31"
  tasks_completed: 2
  tasks_skipped: 1
  files_modified: 3
---

# Quick Task ikw: Fix 4 Visual Issues from Phase 03 UI Review — Summary

**One-liner:** KPI strip accent tokens corrected (green/cyan/red/amber), conditional SCENARIO IMPACT card accent wired via ImpactSummary, impact narrative rendered at .t-h2 bold with colored mono spans, and a 5-item Sankey state-color legend added above the chart.

## Tasks

| # | Name | Status | Commit |
|---|------|--------|--------|
| 1 | Add impact_summary() + state_legend_html() to sankey_flow.py | Done | e915523 |
| 2 | Wire 4 fixes into 2_Churn.py | Done | 60f196b |
| 3 | Human visual verification checkpoint | Skipped (manual) | — |

## What Was Built

### Task 1 — sankey_flow.py additions (e915523)

**`ImpactSummary` frozen dataclass** (`applied: bool`, `direction: str`, `accent_token: str`, `html: str`) — structured return type that co-locates the accent token and rendered HTML so the caller only calls `impact_summary()` once.

**`STATE_HEX: dict[str, str]`** — module-level constant keyed by normalized label (active/atrisk/inactive/reactivated/churned), mirroring `--state-*` CSS tokens. Used by `state_legend_html()` swatch colors.

**`_impact_parts()`** — private helper that factors the shared "largest-delta transition + churn-delta" computation. Called by `impact_summary()` to avoid duplicating the math from `impact_narrative()`.

**`impact_summary()`** — returns `ImpactSummary` with direction-dependent accent token (`--color-success` when improving, `--color-warning` when worsening, `--color-text-tertiary` when neutral) and `.t-h2` HTML with colored `.mono` spans for the pp delta and customer count.

**`state_legend_html()`** — returns a flex HTML div row (one colored dot + label per state). Pure string output, no `st.*` calls. Swatch hex from `STATE_HEX` so colors match the Sankey ribbons.

**4 behavior tests** added to `tests/unit/test_churn_service.py`:
- Test 1 (empty): neutral direction, `--color-text-tertiary` accent, "Adjust a slider" in html
- Test 2 (improving): `"improving"`, `--color-success`, "t-h2" + "saves" in html
- Test 3 (worsening): `"worsening"`, `--color-warning`, "costs" in html
- Test 4 (legend): 3 labels in html, exactly 3 `border-radius:50%` swatch elements

### Task 2 — 2_Churn.py changes (60f196b)

**Issue 1 — KPI accent tokens (lines 236, 243, 250):**
- KPI 2 AVG CUSTOMER LIFETIME: `var(--chart-1)` → `var(--chart-4)` (cyan)
- KPI 3 EXPECTED CHURN: `var(--state-atrisk)` → `var(--state-churned)` (red)
- KPI 4 REVENUE AT RISK: `var(--state-churned)` → `var(--state-atrisk)` (amber)
- KPI 1 RETENTION RATE: unchanged (already `var(--state-active)` green)

**Issue 4 — Sankey legend (line 288):**
- `st.markdown(state_legend_html(result.state_labels), unsafe_allow_html=True)` inserted between the Sankey header card and `st.plotly_chart(fig_sankey, ...)`.

**Issues 2 + 3 — conditional impact accent + .t-h2 narrative:**
- Replaced `impact_narrative(...)` call + hardcoded `--accent:var(--state-active)` wrapper with `impact_summary(...)`.
- Card accent now derives from `summary.accent_token` (green/amber/grey per direction).
- Card body now uses `summary.html` which carries `.t-h2` typography and colored `.mono` spans.
- Import updated: `impact_narrative` removed, `impact_summary` + `state_legend_html` added.

### Task 3 — Human visual verification

Skipped per execution constraints. User should verify at `http://localhost:8501` using the `how-to-verify` steps in the plan:
1. KPI strip: green / cyan / red / amber left-to-right
2. Overview tab: 5-item color legend above Sankey
3. What-If with no sliders: SCENARIO IMPACT card shows grey accent + "Adjust a slider..." text
4. Drag a churn-lowering slider: green accent + bold saves narrative
5. Drag a churn-raising slider: amber accent + bold costs narrative

## Verification Results

```
uv run pytest tests/unit/test_churn_service.py tests/unit/test_page_import.py -q
20 passed in 11.43s

uv run pytest -q
85 passed in 21.08s

uv run ruff check app/ tests/
All checks passed!

grep "import streamlit" app/components/sankey_flow.py
(empty — component stays pure, no streamlit import)
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — no stubs introduced in this task. All 4 fixes wire real behavior (no placeholder values flowing to UI rendering).

## Self-Check: PASSED

- `app/components/sankey_flow.py` modified — file exists and contains ImpactSummary, impact_summary, state_legend_html, STATE_HEX
- `app/pages/2_Churn.py` modified — file exists with correct KPI accents, legend call, impact_summary call
- `tests/unit/test_churn_service.py` modified — file exists with 4 new tests
- Commits e915523 and 60f196b verified in git log
- 85 tests pass, ruff clean
