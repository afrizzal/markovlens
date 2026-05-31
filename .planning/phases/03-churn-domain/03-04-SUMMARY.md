---
phase: 03-churn-domain
plan: 04
status: complete
completed: 2026-05-31
tests_passing: 81
tests_added: 6
files_modified: 4
commits:
  - 655c22b  # Task 1: page skeleton
  - 1efb8e9  # Task 2: What-If tab + smoke test
  - 1e76686  # Bug fix 1: overlapping stackgroups
  - a7e5ebb  # Bug fix 2: shared_yaxes=False
  - latest   # Bug fix 3 (ROOT CAUSE): _apply_overrides lock + 4 tests
  - latest   # Task 4: docs update
---

# Plan 03-04 Summary — Churn Page

## What Was Built

`app/pages/2_Churn.py` — the full 2-tab Customer Churn page (CH-04).

**Overview tab**: temporal Sankey (`build_sankey_figure`) + period scrubber
(st.slider driving an inline HTML flex distribution bar) + 4-KPI strip
(retention rate, avg lifetime, expected churn, revenue at risk with Rp tooltip).

**What-If Simulator tab**: accordion sliders by from-state (`st.expander`),
live before/after stacked-area chart (`build_whatif_chart`), SCENARIO IMPACT
narrative card (`impact_narrative`), Reset all ghost button. Cached via
`@st.cache_data` keyed on `frozenset(overrides.items())` — no Run button needed.

Smoke test added to `tests/unit/test_page_import.py` (CH-04 Wave 0 green).

## Key Bug Found and Fixed

**Root cause (iteration 3):** `_apply_overrides` in `domains/churn/service.py`
was normalizing the override away. Old code set `P[i,j] = val` then divided
the entire row by `row_sum` — so a slider move to 0.50 on a row where
remaining cells summed to 0.07 resulted in `0.50/0.57 = 0.877`, a 5pp change
instead of 43pp. Chart was nearly identical to baseline.

Fix: lock modified cells at target values; redistribute remaining mass
`(1 - sum_of_overrides)` to unmodified cells proportional to their baseline
weights. 4 unit tests lock this behavior permanently:
- `test_apply_overrides_locks_modified_cell_exactly` (Telco trace)
- `test_apply_overrides_redistributes_remaining_proportionally`
- `test_apply_overrides_clamp_sum_exceeds_one`
- `test_apply_overrides_all_baseline_mass_on_modified_cells`

## Requirements Satisfied

- CH-04: Full Churn page (2 tabs, control strip, KPI strip, Overview + What-If)
- Browser-verified: Sankey renders with Churned node RED, what-if chart visibly updates

## Docs Updated

- CLAUDE.md: `/Churn` row → ✅ Implemented (Phase 03) with 2-tab description
- README.md: Phase 03 roadmap checkbox ticked, project tree annotations updated
