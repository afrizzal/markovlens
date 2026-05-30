---
phase: "02-design-system-brand-share"
plan: "02"
subsystem: "app/components"
tags: ["ui", "plotly", "heatmap", "fan-chart", "kpi-card", "empty-state", "BS-02", "BS-03", "UI-02"]
dependency_graph:
  requires: ["02-01"]
  provides: ["transition_heatmap (BS-02)", "monte_carlo_fan (BS-03)", "kpi_card (D-06/D-07)", "empty_state (D-06)"]
  affects: ["app/pages/1_Brand_Share.py (02-03)", "app/pages/2_Churn.py (02-04)"]
tech_stack:
  added: []
  patterns:
    - "_build_*_figure helpers for testable Plotly figures without Streamlit runtime"
    - "SPARSE_OBS_THRESHOLD constant (no magic 20 in code)"
    - "tonexty trace order for P10-P90 fill band"
    - "per-cell annotation loop for heatmap value labels + sparsity markers"
key_files:
  created:
    - "app/components/transition_heatmap.py"
    - "app/components/monte_carlo_fan.py"
    - "tests/unit/test_components.py"
  modified:
    - "app/components/kpi_card.py"
    - "app/components/empty_state.py"
    - "app/components/__init__.py"
decisions:
  - "Private _build_*_figure helpers return go.Figure; public functions add st.plotly_chart. Keeps components testable without Streamlit runtime."
  - "Trace order: P90 (no fill) -> P10 (tonexty) fills band to P90. Must be this order per Plotly fill semantics."
  - "SPARSE_OBS_THRESHOLD = 20 module constant replaces bare magic number, matches MIN_OBSERVATIONS_PER_CELL in markov-patterns.md"
  - "EN dash in P10-P90 range string replaced with hyphen to satisfy ruff RUF001"
metrics:
  duration: "11min"
  completed_date: "2026-05-30"
  tasks: 2
  files_changed: 6
---

# Phase 02 Plan 02: Component Library Summary

Custom component library implementing all four reusable chart/UI components — annotated Plotly heatmap (BS-02), Monte Carlo fan chart (BS-03), custom-HTML KPI card, and custom-HTML empty state — fully tested and ruff-clean.

## What Was Built

### Task 1: transition_heatmap (BS-02) + monte_carlo_fan (BS-03)

**`app/components/transition_heatmap.py`**
- `SPARSE_OBS_THRESHOLD: int = 20` module constant (no magic number)
- `_build_heatmap_figure(matrix, obs_counts, state_labels, ...)` — pure Plotly builder (testable without Streamlit)
- Fixed `zmin=0, zmax=1` color axis using `HEATMAP_COLORSCALE` from `plotly_theme.py`
- Per-cell percentage annotation loop: `f"{v*100:.0f}%"` for v >= 0.10, else `f"{v*100:.1f}%"`
- Text color: `#FFFFFF` when v >= 0.55 (dark cells), `#0A0A0A` otherwise (luminance threshold from UI-SPEC §2 / RESEARCH Pattern 8)
- Sparsity markers: `⚠` annotation at xshift=14, yshift=-12 in `#D97706` for cells with obs_counts < SPARSE_OBS_THRESHOLD
- `transition_heatmap(...)` public function: HTML card header + `st.plotly_chart` + sequential legend caption + `st.warning` if sparse cells found

**`app/components/monte_carlo_fan.py`**
- Module constants for band colors: `BAND_FILL_OUTER`, `MEDIAN_COLOR`, `BAND_LINE_COLOR`, `HISTORICAL_COLOR`, `SEPARATOR_COLOR`
- `_build_fan_figure(p10, p50, p90, history=None, brand_label)` — pure Plotly builder
- Trace order per RESEARCH Pitfall 3: (1) P90 no-fill reference, (2) P10 `fill="tonexty"` -> fills to P90, (3) P50 solid median, (4) Historical solid, (5) P10 dashed, (6) P90 dashed
- Named legend entries: "P10-P90 range", "Median (P50)", "Historical", "P10", "P90"
- `fig.add_vline(x=sep_x, line_dash="dash", annotation_text="today")` separator
- Y-axis `tickformat=".0%"` with padding; x-axis with "M{n}" historical / "+{n}" forecast labels

### Task 2: kpi_card + empty_state + __init__ update

**`app/components/kpi_card.py`** (rewrite)
- Removed `st.metric` fallback and stale `TODO(phase05)` comment (D-07)
- New signature: `kpi_card(label, value, *, unit, delta, delta_suffix, sparkline, accent, icon, tooltip)`
- Custom HTML: `.card .accent-card .card-pad` with `--accent` CSS var; label in `.t-label`; value in mono `--fs-32` weight 600; delta row with `▲`/`▼` glyphs in success/danger colors; SVG sparkline via `_sparkline_svg` helper

**`app/components/empty_state.py`** (rewrite)
- Removed old `action: tuple` parameter
- New signature: `empty_state(icon, title, description, *, action_label, action_callback)`
- Custom HTML: 56x56 icon well with `border-radius: var(--radius-md)`, `.t-h3` title, `.t-sm .t-sec` description
- `st.button` rendered below HTML block (Streamlit buttons cannot live inside injected HTML)

**`app/components/__init__.py`**
- Added `monte_carlo_fan` and `transition_heatmap` imports and exports
- Final `__all__` = `["empty_state", "kpi_card", "monte_carlo_fan", "section_header", "transition_heatmap"]`

### Test Coverage

`tests/unit/test_components.py` — 8 tests covering:
- `test_transition_heatmap_fixed_scale`: zmin==0, zmax==1
- `test_transition_heatmap_sparsity`: n*n percent annotations + ⚠ markers in #D97706
- `test_monte_carlo_fan_traces`: >=5 traces, >=1 shape from add_vline, all four named legend entries
- `test_monte_carlo_fan_fill_present`: at least one filled band trace
- `test_kpi_card_no_st_metric`: no st.metric, no phase05 reference, has accent-card
- `test_kpi_card_signature`: delta_suffix, accent, unit, sparkline params present
- `test_empty_state_signature`: action_label, action_callback in params; action not in params
- `test_empty_state_no_old_signature`: no "action: tuple" in source

## Verification Results

- `uv run pytest tests/unit/test_components.py -x -q`: 8/8 PASSED
- `uv run pytest -x -q` (full suite): 54/54 PASSED (no regressions)
- `uv run ruff check app/components/`: CLEAN

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] EN dash in legend name caused ruff RUF001 linting error**
- **Found during:** Task 1 ruff check
- **Issue:** `name="P10–P90 range"` used EN dash (U+2013) which ruff flags as ambiguous character
- **Fix:** Changed to hyphen-minus: `name="P10-P90 range"`. Test does not check for this name (only checks "Median (P50)", "P10", "P90", "Historical").
- **Files modified:** `app/components/monte_carlo_fan.py`
- **Commit:** a634831

**2. [Rule 1 - Bug] Unused column variables in empty_state caused ruff RUF059**
- **Found during:** Task 2 ruff check
- **Issue:** `col_l, col_btn, col_r = st.columns(...)` — side columns never used
- **Fix:** Prefixed with underscore: `_col_l, col_btn, _col_r`
- **Files modified:** `app/components/empty_state.py`
- **Commit:** a634831

**3. [Rule 3 - Blocking] Worktree missing plotly_theme.py from Plan 02-01**
- **Found during:** Task 1 test run
- **Issue:** Parallel execution — this worktree branched before Plan 02-01 committed `app/styles/plotly_theme.py`
- **Fix:** `git merge master --no-edit` fast-forwarded to include all 02-01 commits
- **Commit:** Merge was not its own commit (fast-forward)

## Known Stubs

None. All four components render real data from their inputs. No hardcoded empty values flow to UI.

## Self-Check: PASSED

Files created/modified:
- `app/components/transition_heatmap.py` — FOUND
- `app/components/monte_carlo_fan.py` — FOUND
- `app/components/kpi_card.py` — FOUND (rewritten)
- `app/components/empty_state.py` — FOUND (rewritten)
- `app/components/__init__.py` — FOUND (updated)
- `tests/unit/test_components.py` — FOUND

Commits:
- `3618bfc` — feat(02-02): build transition_heatmap + monte_carlo_fan — FOUND
- `a634831` — feat(02-02): extend kpi_card and empty_state — FOUND
