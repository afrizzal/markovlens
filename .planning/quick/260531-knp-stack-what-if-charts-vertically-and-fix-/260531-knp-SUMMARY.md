---
phase: quick-260531-knp
plan: 01
subsystem: app/components, app/pages
tags: [streamlit, plotly, ui-polish, churn, what-if]
type: quick
requires: []
provides:
  - "build_whatif_chart returns vertically stacked 2-row subplot figure (~640px tall)"
  - "What-If Simulator right column has 20px spacer between SCENARIO IMPACT card and chart"
affects:
  - app/components/sankey_flow.py
  - app/pages/2_Churn.py
tech-stack:
  added: []
  patterns:
    - "make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12) for stacked-area comparisons"
    - "Inline <div style='height:var(--space-5,20px)'> as localized vertical gap between Streamlit blocks"
key-files:
  created: []
  modified:
    - app/components/sankey_flow.py
    - app/pages/2_Churn.py
decisions:
  - "Use shared_xaxes=True so Period tick labels render only under bottom panel (less clutter)"
  - "Inline 20px spacer div instead of touching shared .card.accent-card CSS (Overview tab reuses that class)"
  - "WHATIF_HEIGHT bumped 360 -> 640 (≈300px per panel + title + bottom legend)"
metrics:
  duration: ~12min
  completed: "2026-05-31"
  tests-passed: "86/86"
  ruff: "clean"
requirements:
  - QUICK-KNP-01
  - QUICK-KNP-02
  - QUICK-KNP-03
---

# Quick Task 260531-knp: Stack What-If Charts Vertically & Fix Overlap Summary

Pure UI polish on Churn → What-If Simulator: side-by-side baseline/scenario stacked-area subplots reflowed to vertical stack with a 20px spacer above the chart to fix the chart-title collision with the SCENARIO IMPACT callout card.

## What Changed

### 1. `app/components/sankey_flow.py` — `build_whatif_chart`

| Item | Before | After |
|---|---|---|
| Subplot grid | `rows=1, cols=2` | `rows=2, cols=1` |
| Cross-axis sharing | `shared_yaxes=False` + `horizontal_spacing=0.06` | `shared_xaxes=True` + `vertical_spacing=0.12` |
| Baseline trace placement | `row=1, col=1` | `row=1, col=1` (unchanged — top panel) |
| Modified trace placement | `row=1, col=2` | `row=2, col=1` (now bottom panel) |
| `WHATIF_HEIGHT` | `360` | `640` (≈ 300px per panel + title + legend) |
| Period x-axis title | `fig.update_xaxes(title_text="Period")` (both panels) | `fig.update_xaxes(title_text="Period", row=2, col=1)` (bottom only — `shared_xaxes=True`) |
| Right-y-axis force-show | `fig.update_yaxes(showticklabels=True, row=1, col=2)` | Removed (vertical layout doesn't need it) |
| Legend `y` | `-0.35` | `-0.18` (tighter under 640px figure) |
| Docstring | "side-by-side", "Left/Right panel" | "vertically stacked", "Top/Bottom panel" |

Signature, return type, trace count, `stackgroup="baseline"` / `stackgroup="modified"`, `showlegend` pattern, `legendgroup`, and trace colors are all UNCHANGED. The unit-test contract `test_build_whatif_chart_has_two_stackgroups` is unaffected.

### 2. `app/pages/2_Churn.py` — What-If right column

Added one `st.markdown` spacer div between the SCENARIO IMPACT card and `st.plotly_chart(fig_whatif, ...)`:

```python
st.markdown(
    '<div style="height:var(--space-5,20px);"></div>',
    unsafe_allow_html=True,
)
```

Localized — no change to the shared `.card.accent-card` CSS class (still used by the Overview tab's state-flow header card).

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | `8f81ce7` | `refactor(quick-knp-01): vertically stack what-if subplots in build_whatif_chart` |
| 2 | `1d26846` | `fix(quick-knp-02): add 20px spacer between SCENARIO IMPACT card and what-if chart` |

## Verification

- `uv run pytest tests/unit/test_churn_service.py -k whatif` → 1 passed, 16 deselected. `test_build_whatif_chart_has_two_stackgroups` still passes (both `"baseline"` and `"modified"` stackgroups present in `fig.data`).
- `uv run pytest -q` → **86 passed in 11.64s** (no regressions; STATE.md baseline was 81, the additional 5 came from prior quick tasks 260531-p03 / 260531-ikw).
- `uv run ruff check app/ tests/` → clean.
- `uv run python -c "import importlib.util; spec = importlib.util.spec_from_file_location('p', 'app/pages/2_Churn.py')"` → parses.

## Deviations from Plan

None — plan executed exactly as written.

## Pending

- Task 3 (human visual verification on `uv run streamlit run app/Home.py` → Customer Churn → What-If Simulator tab) is awaiting the user's "approved" reply. Code work is complete; pending only the visual gate.

## Note for `docs/planning/task-progress.md`

Quick task **260531-knp** ready to move to **Done** once visual verification is approved.
Hashes: `8f81ce7`, `1d26846`.

## Self-Check: PASSED

- `app/components/sankey_flow.py` modified — verified (commit `8f81ce7`).
- `app/pages/2_Churn.py` modified — verified (commit `1d26846`).
- `test_build_whatif_chart_has_two_stackgroups` passes — verified.
- Full suite 86/86 — verified.
- Ruff clean — verified.
