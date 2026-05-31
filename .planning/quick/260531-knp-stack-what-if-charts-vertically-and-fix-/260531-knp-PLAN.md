---
phase: quick-260531-knp
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/components/sankey_flow.py
  - app/pages/2_Churn.py
autonomous: false
requirements:
  - QUICK-KNP-01  # Stack baseline & scenario charts vertically in What-If panel
  - QUICK-KNP-02  # Fix overlap between Scenario Impact card and chart title
  - QUICK-KNP-03  # Increase per-chart height to ~300px for legibility

must_haves:
  truths:
    - "On Churn page > What-If Simulator tab, the right column shows Scenario Impact card, then a clear vertical gap, then a Baseline chart on top of a Scenario chart (both full column width)."
    - "The 'Baseline vs. scenario — state mix over horizon' chart title no longer visually overlaps the orange 'Scenario Impact' callout card above it."
    - "Each of the two stacked-area panels is approximately 300px tall with readable axis labels, x-axis tick labels, and legend."
    - "Existing churn/sankey unit tests still pass (build_whatif_chart still exposes 'baseline' and 'modified' stackgroups)."
  artifacts:
    - path: "app/components/sankey_flow.py"
      provides: "build_whatif_chart returning a 2-row (vertically stacked) subplot figure ~640px tall total"
      contains: "rows=2"
    - path: "app/pages/2_Churn.py"
      provides: "What-If right column with explicit spacer between Scenario Impact card and the chart"
      contains: "tab_whatif"
  key_links:
    - from: "app/pages/2_Churn.py (with right block)"
      to: "app/components/sankey_flow.build_whatif_chart"
      via: "st.plotly_chart(fig_whatif, use_container_width=True)"
      pattern: "build_whatif_chart\\("
---

<objective>
Pure UI polish on the Customer Churn page's What-If Simulator tab. The right column currently renders the baseline + scenario state-mix comparison as a single Plotly figure with two SIDE-BY-SIDE subplots (`make_subplots(rows=1, cols=2, ...)`). At ~50% column width this becomes cramped: axis labels get squished, the chart title visually collides with the orange "SCENARIO IMPACT" callout card above it, and the 12-period stacked area is hard to read.

Fix three things in `app/pages/2_Churn.py` and `app/components/sankey_flow.py`:
1. Stack the two charts VERTICALLY (Baseline on top, Scenario below) — full column width each.
2. Add a visible spacer between the Scenario Impact card and the first chart so the title no longer overlaps.
3. Bump per-chart height to ~300px (total figure ≈ 640px including title + bottom legend) for legibility.

Out of scope (do NOT touch):
- Slider logic / row renormalization
- KPI cards, icons, deltas
- Sankey chart on Overview tab
- Impact narrative WORDING (build_whatif_chart's neighbour `impact_narrative` / `impact_summary` are untouched)
- Period scrubber on Overview tab
- Any non-Plotly behavior

Purpose: Improve the polish gap flagged by user; aligns the What-If tab with the Phase 03 prototype fidelity bar set by commit 5462f9b.
Output: Two edited files, one Streamlit human-verify checkpoint, no behavior change, no new tests.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@.claude/rules/streamlit-conventions.md
@.claude/rules/coding-style.md
@app/pages/2_Churn.py
@app/components/sankey_flow.py

<interfaces>
<!-- Current `build_whatif_chart` signature (unchanged by this plan): -->

From app/components/sankey_flow.py (around line 308):
```python
def build_whatif_chart(
    baseline_dist: np.ndarray,   # shape (horizon+1, n_states)
    modified_dist: np.ndarray,   # shape (horizon+1, n_states)
    state_labels: list[str],
) -> go.Figure: ...
```

Current implementation key facts (lines ~338–399):
- Uses `make_subplots(rows=1, cols=2, subplot_titles=("Baseline", "Scenario"), shared_yaxes=False, horizontal_spacing=0.06)`
- Adds baseline traces to `row=1, col=1` (stackgroup="baseline", faint fill, `showlegend=False`)
- Adds modified traces to `row=1, col=2` (stackgroup="modified", solid fill, `showlegend=True`)
- `WHATIF_HEIGHT: int = 360` constant at module level (line 56)
- `fig.update_yaxes(tickformat=".0%", range=[0, 1.05])` applies to both panels
- `fig.update_xaxes(title_text="Period")` — currently applies to col=1+col=2 in same row
- `fig.update_yaxes(showticklabels=True, row=1, col=2)` — ensures right-panel y-axis labels visible
- Layout title: "Baseline vs. scenario — state mix over horizon"
- Legend: horizontal, anchored at the bottom (`y=-0.35`)

Existing unit-test contract that MUST still hold (tests/unit/test_churn_service.py:186):
```python
def test_build_whatif_chart_has_two_stackgroups() -> None:
    fig = build_whatif_chart(base, mod, ["active", "atrisk", "churned"])
    groups = {getattr(t, "stackgroup", None) for t in fig.data}
    assert "baseline" in groups
    assert "modified" in groups
    assert len(fig.data) >= 2
```
Both `stackgroup="baseline"` and `stackgroup="modified"` must remain in the output.

Current right-column rendering in `app/pages/2_Churn.py` (lines ~427–458):
```python
with right:
    horizon_val = st.session_state.get(f"{PAGE_NS}.horizon", DEFAULT_HORIZON)
    baseline_dist = result.baseline_forecast
    if overrides:
        modified_dist = _cached_scenario(ds.id, horizon_val, frozenset(overrides.items()))
    else:
        modified_dist = baseline_dist
    summary = impact_summary(...)
    st.markdown(
        f'<div class="card accent-card" style="--accent:{summary.accent_token};'
        f'padding:var(--space-5);">'
        f'<div class="t-label">SCENARIO IMPACT</div>'
        f'<div style="margin-top:var(--space-2);">{summary.html}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    fig_whatif = build_whatif_chart(baseline_dist, modified_dist, result.state_labels)
    st.plotly_chart(fig_whatif, use_container_width=True)
```
The spacer/margin-bottom fix goes right between the `</div>` closing the SCENARIO IMPACT card and the `build_whatif_chart` call.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Rewire build_whatif_chart to vertically stacked subplots (rows=2, cols=1)</name>
  <files>app/components/sankey_flow.py</files>
  <action>
    Convert `build_whatif_chart` from a horizontal 1x2 subplot layout to a vertical 2x1 subplot layout (Baseline on top, Scenario below). Keep the signature, return type, stackgroup names, and trace count IDENTICAL — only layout coordinates and sizing change.

    Step 1 — Update the module-level height constant at line 56 to reflect the new per-panel height:
    ```python
    WHATIF_HEIGHT: int = 640   # ~300px per panel + title + bottom legend (was 360 for side-by-side)
    ```

    Step 2 — In `build_whatif_chart` (around lines 341–347), change the `make_subplots` call from horizontal (rows=1, cols=2) to vertical (rows=2, cols=1):
    ```python
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Baseline", "Scenario"),
        shared_xaxes=True,
        vertical_spacing=0.12,
    )
    ```
    Notes:
    - `shared_xaxes=True` is appropriate here: both panels share the same Period x-axis. This also means the Period tick labels render only once under the lower panel, which reduces clutter.
    - Drop `shared_yaxes=False` and `horizontal_spacing=0.06` — both are 1x2-specific.
    - `vertical_spacing=0.12` gives breathing room between subplot titles and the panel above without wasting space.

    Step 3 — Update both `fig.add_trace(..., row=1, col=1)` and `fig.add_trace(..., row=1, col=2)` calls so:
    - Baseline trace (faint fill, `stackgroup="baseline"`, `showlegend=False`) goes to `row=1, col=1` — UNCHANGED (top panel).
    - Modified/scenario trace (solid fill, `stackgroup="modified"`, `showlegend=True`, `legendgroup=label`) goes to `row=2, col=1` — CHANGED from `row=1, col=2`.

    Step 4 — Replace the post-loop axis/layout block (lines ~383–399) with:
    ```python
    fig.update_yaxes(tickformat=".0%", range=[0, 1.05])  # applies to both rows
    # With shared_xaxes=True the Period title belongs only on the bottom panel
    fig.update_xaxes(title_text="Period", row=2, col=1)
    fig.update_layout(
        height=WHATIF_HEIGHT,
        title="Baseline vs. scenario — state mix over horizon",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.18,
            "xanchor": "center",
            "x": 0.5,
        },
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    ```
    Notes:
    - Remove the `fig.update_yaxes(showticklabels=True, row=1, col=2)` line — it was a 1x2 quirk; both vertical rows have visible y-tick labels by default.
    - Tighten the legend `y` from `-0.35` to `-0.18`: with a 640px figure the legend would otherwise float much further below the bottom panel than necessary.

    Step 5 — Update the docstring (lines ~313–338) to reflect the new layout. Specifically:
    - Change "Renders two adjacent stacked-area panels" → "Renders two stacked-area panels arranged VERTICALLY (Baseline on top, Scenario below)".
    - Change references to "Left panel" → "Top panel"; "Right panel" → "Bottom panel".
    - Rewrite the "Side-by-side panels are required..." paragraph to: "Stacked-vertical panels are required because single-panel overlapping stackgroups make the baseline invisible under the solid modified traces (both occupy y=0..1). At ~50% column width the previous side-by-side layout (rows=1, cols=2) made axis labels and the legend too cramped — vertical stacking gives each panel the full column width."
    - Keep the rgba alpha note unchanged (it's still accurate).

    Do NOT touch:
    - The trace construction loop body (faint/solid colors, `_norm_label`, `STATE_COLORS_FAINT`, `STATE_COLORS_SOLID`, `DEFAULT_FAINT`, `DEFAULT_SOLID`).
    - The `showlegend=False` on baseline / `showlegend=True` on modified pattern.
    - `legendgroup=label`.
    - Any other function in the file.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_churn_service.py::test_build_whatif_chart_has_two_stackgroups -x</automated>
    Plus: `uv run ruff check app/components/sankey_flow.py` returns clean.
  </verify>
  <done>
    - `build_whatif_chart` returns a figure with `rows=2, cols=1` subplot grid.
    - Both `stackgroup="baseline"` and `stackgroup="modified"` are still present (test still passes).
    - `WHATIF_HEIGHT` constant is 640.
    - Docstring updated to describe the vertical layout.
    - Ruff clean on the modified file.
  </done>
</task>

<task type="auto">
  <name>Task 2: Add explicit spacer between Scenario Impact card and chart in 2_Churn.py</name>
  <files>app/pages/2_Churn.py</files>
  <action>
    Add a visible vertical gap between the orange-bordered SCENARIO IMPACT callout card and the `st.plotly_chart(fig_whatif, ...)` call below it, so the chart's "Baseline vs. scenario — state mix over horizon" title no longer overlaps the bottom edge of the impact card.

    In the `with right:` block (around lines 428–458), between the `st.markdown(...)` that renders the SCENARIO IMPACT card and the line `fig_whatif = build_whatif_chart(...)`, insert:

    ```python
    # Spacer — prevents the chart title from overlapping the SCENARIO IMPACT card above
    st.markdown(
        '<div style="height:var(--space-5,20px);"></div>',
        unsafe_allow_html=True,
    )
    ```

    Why this approach (vs. CSS margin on the impact card):
    - The impact card uses an inline-style `padding:var(--space-5);` but no `margin-bottom`. We don't want to touch the shared `.card.accent-card` CSS class because it's reused by the Overview tab's state-flow header (line ~331) where the existing layout looks fine.
    - An inline 20px spacer div is the minimal, localized fix — single line of intent, easy to delete if Streamlit ever adds proper gap support between blocks in a column.
    - Use the `--space-5` CSS variable (matches the impact card's own padding scale) with a `20px` fallback for clarity.

    Do NOT:
    - Change the SCENARIO IMPACT card markup itself (accent token, t-label class, summary.html, padding).
    - Touch the Overview tab's state-flow header card (same class, different tab).
    - Add any `st.divider()` — that would render a horizontal rule, which we don't want here.
    - Touch the `left` column (sliders).
    - Touch any KPI / icon / scrubber / Sankey code.

    Per .claude/rules/streamlit-conventions.md the file already uses inline-style `st.markdown(..., unsafe_allow_html=True)` for spacers elsewhere (e.g., line 212 `st.markdown("<br>", unsafe_allow_html=True)` in the control strip), so this pattern is consistent with the page's existing conventions.
  </action>
  <verify>
    <automated>uv run ruff check app/pages/2_Churn.py</automated>
    Plus: `uv run python -c "import importlib.util; spec = importlib.util.spec_from_file_location('p', 'app/pages/2_Churn.py')"` — i.e., the file at minimum parses. (No new tests required — pure layout change.)
  </verify>
  <done>
    - A single `st.markdown('<div style="height:var(--space-5,20px);"></div>', unsafe_allow_html=True)` call sits between the SCENARIO IMPACT card markdown and the `fig_whatif = build_whatif_chart(...)` line.
    - Ruff clean on the modified file.
    - No other code in `2_Churn.py` is altered.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 3: Visual verification of What-If layout in browser</name>
  <what-built>
    - `build_whatif_chart` now returns a 2-row vertically stacked Plotly figure (Baseline on top, Scenario on bottom), 640px tall total.
    - The What-If Simulator tab's right column has a 20px spacer between the SCENARIO IMPACT card and the chart.
  </what-built>
  <how-to-verify>
    1. From the project root, run: `uv run streamlit run app/Home.py`
    2. Browser opens at http://localhost:8501. Click **Customer Churn** in the left sidebar.
    3. In the Cohort selector pick any churn dataset (e.g., the first one). Leave horizon at 12. Click **Run Analysis**. Wait for the KPI strip to populate.
    4. Click the **What-If Simulator** tab (second tab).
    5. In the right column, expand the first "From <state>" accordion in the LEFT column and move any one slider by 10–20%. The right column will update.
    6. Verify ALL of:
       - [ ] The orange "SCENARIO IMPACT" callout card is followed by a visible vertical gap (roughly 20px of empty space).
       - [ ] Below the gap, the chart title **"Baseline vs. scenario — state mix over horizon"** is fully visible and does NOT visually overlap the bottom edge of the SCENARIO IMPACT card.
       - [ ] The **Baseline** subplot panel sits ON TOP, and the **Scenario** subplot panel sits BELOW it (not side-by-side).
       - [ ] Each panel is roughly 300px tall — the 12-period stacked area is easy to read.
       - [ ] X-axis tick labels (0..12) appear ONCE under the bottom (Scenario) panel; the **"Period"** axis title is visible there.
       - [ ] Y-axis percentage tick labels (0%..100%) are visible on BOTH panels.
       - [ ] The horizontal legend (active / atrisk / inactive / reactivated / churned) sits at the bottom of the figure and is not clipped.
       - [ ] The left column (slider accordions) is unchanged.
       - [ ] The Overview tab's Sankey + period scrubber are unchanged (sanity check — switch tabs and back).
    7. If everything above is true → reply "approved". If anything is wrong, describe what.
  </how-to-verify>
  <resume-signal>Reply "approved" — or describe issues to revise.</resume-signal>
</task>

</tasks>

<verification>
- `uv run pytest tests/unit/test_churn_service.py -x` → all churn-service tests pass (test_build_whatif_chart_has_two_stackgroups in particular).
- `uv run pytest` → full suite still green (81/81 baseline from STATE.md).
- `uv run ruff check app/ tests/` → clean.
- Manual: Customer Churn → What-If Simulator → adjust slider → right column shows Impact card → gap → Baseline chart (top) → Scenario chart (bottom), both full-width, ~300px tall, no overlap.
</verification>

<success_criteria>
- `app/components/sankey_flow.py::build_whatif_chart` uses `make_subplots(rows=2, cols=1, ...)` instead of `rows=1, cols=2`.
- `WHATIF_HEIGHT == 640`.
- Modified trace is added to `row=2, col=1` (not `row=1, col=2`); baseline trace stays at `row=1, col=1`.
- Existing test `test_build_whatif_chart_has_two_stackgroups` still passes (both stackgroups present).
- `app/pages/2_Churn.py` has exactly one new `st.markdown` spacer between the SCENARIO IMPACT card and the `build_whatif_chart` invocation.
- Human visual checkpoint approved: no overlap, vertical stacking confirmed, legibility improved.
- No regressions: full pytest suite green; ruff clean.
</success_criteria>

<output>
After completion, create `.planning/quick/260531-knp-stack-what-if-charts-vertically-and-fix-/260531-knp-SUMMARY.md` describing:
- The two files edited and the specific layout changes (rows=2,cols=1; height=640; spacer div).
- Commit hash for the change.
- Confirmation that test_build_whatif_chart_has_two_stackgroups still passes and full suite is green.
- Note for `docs/planning/task-progress.md` — quick task 260531-knp moved to Done.
</output>
