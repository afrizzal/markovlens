# Quick Task: 260531-p03 — Churn Polish 6 Gaps

## Status: COMPLETE

## Changes Made

### 1. Bug: Period scrubber range collapse [FIXED]
- `app/pages/2_Churn.py:281` — `build_sankey_figure` now passes `result.baseline_forecast` (not `state_distribution_over_time`), giving consistent n_cols for snapshot datasets
- Lines 292/310 — scrubber range and `dist_at_period` both use `baseline_forecast.shape[0]` = `horizon+1`
- Slider `format="P%d"` → shows P0..P7 labels per prototype

### 2. Fidelity: Slider decimal → percentage [FIXED]
- Slider range changed to 0-100, `format="%.0f%%"`, init state as `float(round(val*100))`
- Internal override values still 0-1 via `current = current_pct / 100`
- Baseline shown in label as `(baseline 93%)` rather than `(baseline 0.93)` — addresses issue 5 (ghost marker) too

### 3. Polish: KPI delta indicators [ADDED]
- Inline delta computation from `baseline_forecast` trend (mid→end of horizon)
- Retention Rate: `_ret_delta` in pp (signed, negative = decline)
- Expected Churn: negated delta so green arrow = improvement (fewer churning)
- Avg Lifetime and Revenue at Risk: no delta (static for homogeneous chain)

### 4. Polish: KPI card icons [ADDED]
- 4 Lucide SVG icon constants defined as module-level strings (`_ICON_USERS`, `_ICON_CLOCK`, `_ICON_TRENDING_UP`, `_ICON_DOLLAR`)
- `app/components/kpi_card.py` updated: icon rendered as absolute top-right corner element (35% opacity, accent-colored) with `position:relative` on card div

### 5. UX: Slider baseline marker [ADDRESSED]
- Handled by issue 2: label now reads `(baseline 93%)` — clear and readable

### 6. Readability: Distribution bar inline % labels [ADDED]
- `_stacked_bar_html` injects `<span>57%</span>` into segments where `share > 0.08`
- White, mono, font-weight 600, font-size 11px per prototype pages3.jsx:41

## Test Changes
- `tests/integration/test_churn_service.py` — added `test_baseline_forecast_shape_matches_horizon_and_states`
- Total: 86 tests pass (was 81 before this task; +5 from this task's new integration test plus the prior quick task)

## Files Changed
- `app/pages/2_Churn.py`
- `app/components/kpi_card.py`
- `tests/integration/test_churn_service.py`
