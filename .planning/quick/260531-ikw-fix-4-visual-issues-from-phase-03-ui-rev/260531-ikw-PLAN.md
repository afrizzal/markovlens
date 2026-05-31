---
phase: quick-260531-ikw
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/pages/2_Churn.py
  - app/components/sankey_flow.py
  - tests/unit/test_churn_service.py
autonomous: false
requirements:
  - UI-FIX-CHURN-01
  - UI-FIX-CHURN-02
  - UI-FIX-CHURN-03
  - UI-FIX-CHURN-04
must_haves:
  truths:
    - "KPI strip accents read green / cyan / red / amber (KPI 1-4) matching the design reference"
    - "SCENARIO IMPACT card accent is green when the scenario lowers churn, red/amber when it raises churn, neutral when no override is applied"
    - "The key numbers in the impact narrative render at 24px bold (.t-h2) with colored mono spans"
    - "A 5-item horizontal color legend appears directly above the Sankey chart on the Overview tab"
  artifacts:
    - path: "app/pages/2_Churn.py"
      provides: "Corrected KPI accent tokens, conditional impact-card accent, .t-h2 narrative HTML, Sankey legend row"
    - path: "app/components/sankey_flow.py"
      provides: "impact_summary() returning structured impact (direction + accent token + HTML fragments) and a state_legend_html() builder"
  key_links:
    - from: "app/pages/2_Churn.py"
      to: "app/components/sankey_flow.py impact_summary"
      via: "import + call in What-If right panel"
      pattern: "impact_summary\\("
    - from: "app/pages/2_Churn.py"
      to: "app/components/sankey_flow.py state_legend_html"
      via: "import + st.markdown above st.plotly_chart on Overview tab"
      pattern: "state_legend_html\\("
---

<objective>
Fix exactly the 4 visual issues raised in the Phase 03 UI review (`.planning/phases/03-churn-domain/03-UI-REVIEW.md`) on the Customer Churn page. All four are presentation-layer concerns: KPI accent token assignment, conditional scenario-impact accent, impact-narrative typography, and a missing Sankey state-color legend.

Purpose: Raise the Color pillar (2/4) and Visuals pillar (3/4) toward the design reference (`docs/design-reference/js/pages3.jsx`) so the Churn page reads as a polished portfolio piece rather than a student project.
Output: Updated `app/pages/2_Churn.py` + two new pure helpers in `app/components/sankey_flow.py` (`impact_summary`, `state_legend_html`) + unit tests for the new helpers.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/phases/03-churn-domain/03-UI-REVIEW.md
@app/pages/2_Churn.py
@app/components/sankey_flow.py
@app/components/kpi_card.py
@app/styles/theme.css

# Design ground truth for all 4 fixes — Churn pages are lines 11-162
@docs/design-reference/js/pages3.jsx

<constraints>
- `core/` and `domains/` must NOT import streamlit/plotly. `app/components/sankey_flow.py` is already pure-Plotly (no streamlit) — KEEP it that way. New helpers there must return HTML strings / dataclasses, NOT call `st.*`.
- Pages own Plotly Figure construction and HTML rendering; components return figures/strings. The legend (Issue 4) is static HTML/CSS, NOT a Plotly legend — render it page-side via `st.markdown(..., unsafe_allow_html=True)`.
- All colors come from CSS tokens in `app/styles/theme.css` (`--state-*`, `--color-*`, `--chart-*`). No new hardcoded hex in the page. The legend swatches may reference `var(--state-*)` directly in inline style (consistent with existing accent-card usage at `2_Churn.py:271`).
- ASCII `->` is used deliberately for Windows console encoding safety in `impact_narrative` (per CONTEXT.md). Do NOT switch to the unicode arrow in any console-bound string. The legend/narrative HTML rendered into the browser MAY use proper labels but keep arrows ASCII to stay consistent.
- Conventional commits; one logical commit per task is fine, or a single squashed commit at the end. Use `rtk git`.
</constraints>

<interfaces>
<!-- Contracts the executor needs — extracted from the codebase, use directly. -->

From app/components/kpi_card.py — kpi_card signature (accent is a CSS color string):
```python
def kpi_card(
    label: str,
    value: str,
    *,
    unit: str | None = None,
    delta: float | None = None,
    delta_suffix: str = "%",
    sparkline: list[float] | None = None,
    accent: str = "var(--color-primary)",   # <-- the token to fix in Issue 1
    icon: str | None = None,
    tooltip: str | None = None,
) -> None: ...
```

From app/components/sankey_flow.py — existing narrative helper (returns a flat string):
```python
def impact_narrative(
    overrides: dict[tuple[int, int], float],
    baseline_P: np.ndarray,
    baseline_dist: np.ndarray,
    modified_dist: np.ndarray,
    state_labels: list[str],
    n_customers: int,
) -> str: ...
# Empty overrides -> "Adjust a slider to model a retention scenario."
# Else -> "Reducing active -> churned by 5pp saves 120 customers."
#         direction = "Reducing"/"Increasing"; sign = "saves"/"costs"
#         churn_delta = (baseline_dist[-1, churned] - modified_dist[-1, churned]) * n_customers
#         saves  => churn_delta > 0  => retention IMPROVES  => green
#         costs  => churn_delta < 0  => retention WORSENS   => red/amber
```

From app/styles/theme.css — relevant tokens (light mode shown; dark variants exist):
```
--state-active: #059669 (green)   --state-atrisk: #D97706 (amber)
--state-inactive: #A1A1AA (grey)  --state-reactivated: #0891B2 (cyan)
--state-churned: #DC2626 (red)
--chart-1: #4338CA (indigo)       --chart-4: #0891B2 (cyan)
--color-success: #059669          --color-danger: #DC2626
--color-warning: #D97706          --color-text-tertiary: #A1A1AA
--color-primary: #4338CA
.t-h2 { font-size: var(--fs-24); font-weight: 600; }   /* 24px bold target */
.mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.accent-card::before { ... background: var(--accent, var(--color-primary)); }
```

From docs/design-reference/js/pages3.jsx — the four targets:
```jsx
// KPI accents (lines 25-28):
//   Retention Rate       accent="var(--state-active)"   (green)  [already correct]
//   Avg Customer Lifetime accent="var(--chart-4)"       (cyan)   [Issue 1: page has --chart-1]
//   Expected Churn (30d) accent="var(--state-churned)"  (red)    [Issue 1: page has --state-atrisk]
//   Revenue at Risk      accent="var(--state-atrisk)"   (amber)  [Issue 1: page has --state-churned]

// Legend above Sankey (lines 31-33):  <Legend items={CHURN_STATES} style={{ marginBottom: 16 }} />
// CHURN_STATES = 5 states, each { label, color } -> a horizontal dot+label row.

// Conditional impact accent (line 96): accent={dirty ? 'var(--color-success)' : 'var(--color-text-tertiary)'}
//   Task refines this: green when improving, red/amber when worsening, neutral when no override.

// Impact narrative typography (lines 99-102):
//   <p className="t-h2" style={{ fontWeight: 600, lineHeight: 1.3 }}>
//     Reducing Active -> At-Risk by <span className="mono" style={{color:'var(--color-primary)'}}>{pp}pp</span>
//     saves <span className="mono" style={{color:'var(--color-success)'}}>{n} customers</span>.
//   </p>
//   (empty state: <p className="t-h3 t-sec" style={{fontWeight:400}}>Adjust a slider...</p>)
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add impact_summary() + state_legend_html() to sankey_flow.py (pure helpers)</name>
  <files>app/components/sankey_flow.py, tests/unit/test_churn_service.py</files>
  <behavior>
    impact_summary(overrides, baseline_P, baseline_dist, modified_dist, state_labels, n_customers) -> ImpactSummary
    - ImpactSummary is a `@dataclass(frozen=True)` with fields:
        applied: bool             (False when overrides is empty)
        direction: str            ("improving" | "worsening" | "neutral")
        accent_token: str         (CSS var string: improving->"var(--color-success)",
                                   worsening->"var(--color-warning)", neutral->"var(--color-text-tertiary)")
        html: str                 (ready-to-render inner HTML for the impact card body)
    - Reuse the existing churn-delta math from impact_narrative (largest-delta transition,
      churn_delta = (baseline_dist[-1, churned] - modified_dist[-1, churned]) * n_customers).
      saves (churn_delta > 0) => "improving"; costs (churn_delta < 0) => "worsening".
    - When applied is False: direction="neutral", accent_token="var(--color-text-tertiary)",
      html = '<p class="t-h3 t-sec" style="font-weight:400;">Adjust a slider to model a retention scenario.</p>'
    - When applied is True: html renders the sentence at .t-h2 with colored mono spans —
      the "{n}pp" span color:var(--color-primary); the "{n} customers" span
      color matches direction (success when improving, danger/warning when worsening).
      Keep the state-name arrow ASCII "->".
    Behavior tests (add to tests/unit/test_churn_service.py, pure NumPy, no DuckDB):
    - Test 1 (empty): impact_summary({}, ...) -> applied is False, direction == "neutral",
      accent_token == "var(--color-text-tertiary)", "Adjust a slider" in html.
    - Test 2 (improving): an override that REDUCES churn (modified churned share < baseline)
      -> direction == "improving", accent_token == "var(--color-success)",
      "t-h2" in html and "saves" in html.
    - Test 3 (worsening): an override that RAISES churn (modified churned share > baseline)
      -> direction == "worsening", accent_token == "var(--color-warning)", "costs" in html.
    state_legend_html(state_labels, *, state_colors=None) -> str
    - Returns a single horizontal flex row: one item per label = colored dot + label text.
    - Dot color resolved from the same normalized-label -> hex map already used for the
      stacked bar. REUSE the normalization (`_norm_label`) already in this module. Provide a
      hex map (mirror STATE_BAR_COLORS from the page, or add a module-level STATE_HEX dict in
      sankey_flow.py keyed by normalized label) so swatch colors match the Sankey ribbons.
    - Use `.t-xs` for labels, `var(--space-*)` for gaps, inline flex. No `st.*` calls.
    Behavior test:
    - Test 4 (legend): state_legend_html(["Active","At-Risk","Churned"]) returns a str that
      contains all three labels and exactly 3 swatch divs (assert html.count("border-radius:50%") == 3
      or an equivalent swatch marker you choose — pick one marker and assert its count == 3).
  </behavior>
  <action>
    Edit `app/components/sankey_flow.py`:
    1. Add a frozen dataclass `ImpactSummary` (import `from dataclasses import dataclass` at top —
       keep import order ruff-clean: stdlib block before third-party).
    2. Add `STATE_HEX: dict[str, str]` module constant keyed by normalized label
       (active=#059669, atrisk=#D97706, inactive=#A1A1AA, reactivated=#0891B2, churned=#DC2626)
       so both the legend swatches and any future reuse stay token-aligned. Comment each with
       its `--state-*` token name (matches the existing STATE_COLOR_PREFIX comment style).
    3. Implement `impact_summary(...)` reusing the largest-delta + churn-delta logic from
       `impact_narrative` (do NOT duplicate the math sloppily — factor the shared
       direction/sign computation into a small private helper `_impact_parts(...)` that both
       `impact_narrative` and `impact_summary` call, OR have impact_summary build on the same
       arithmetic). Build the `.t-h2` HTML with colored mono spans per the interfaces block.
    4. Implement `state_legend_html(state_labels, *, state_colors=None)` returning the flex row.
    5. Append the 4 behavior tests to `tests/unit/test_churn_service.py`. Import the new symbols:
       `from app.components.sankey_flow import ImpactSummary, impact_summary, state_legend_html`.
       NOTE: test_churn_service.py currently imports only from `domains.churn` — adding an
       `app.components.sankey_flow` import is fine (sankey_flow is pure, no streamlit).
    Do NOT remove or change the existing `impact_narrative` signature — the page may keep
    calling it for the plain-string fallback, but Task 2 will switch the page to impact_summary.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_churn_service.py -q</automated>
  </verify>
  <done>impact_summary returns correct (applied, direction, accent_token, html) for empty/improving/worsening cases; state_legend_html returns a swatch+label row for N states; 4 new tests pass; sankey_flow.py still has no streamlit import.</done>
</task>

<task type="auto">
  <name>Task 2: Wire the 4 fixes into 2_Churn.py (KPI accents, conditional impact accent, .t-h2 narrative, legend)</name>
  <files>app/pages/2_Churn.py</files>
  <action>
    Edit `app/pages/2_Churn.py` to apply all four fixes:

    Issue 1 — KPI accent tokens (lines ~235, 242, 249):
    - KPI 2 "AVG CUSTOMER LIFETIME" (line 235): change `accent="var(--chart-1)"` -> `accent="var(--chart-4)"` (cyan, per pages3.jsx:26).
    - KPI 3 "EXPECTED CHURN (next period)" (line 242): change `accent="var(--state-atrisk)"` -> `accent="var(--state-churned)"` (red, per pages3.jsx:27).
    - KPI 4 "REVENUE AT RISK" (line 249): change `accent="var(--state-churned)"` -> `accent="var(--state-atrisk)"` (amber, per pages3.jsx:28).
    - KPI 1 (RETENTION RATE, `--state-active`) is already correct — leave it.

    Issue 4 — Sankey legend (insert BEFORE `st.plotly_chart(fig_sankey, ...)` at line ~286,
    after the Sankey header card markdown block at lines 270-277):
    - Import `state_legend_html` from `app.components.sankey_flow`.
    - Render `st.markdown(state_legend_html(result.state_labels), unsafe_allow_html=True)`
      between the header card and the chart so the 5-item legend sits directly above the Sankey
      (mirrors pages3.jsx:32 `<Legend items={CHURN_STATES} style={{marginBottom:16}} />`).

    Issues 2 + 3 — conditional impact accent + .t-h2 narrative (right panel, lines ~375-391):
    - Import `impact_summary` from `app.components.sankey_flow`.
    - Replace the current `impact_narrative(...)` call + the hardcoded
      `--accent:var(--state-active)` markdown block with:
        summary = impact_summary(overrides, baseline_P, baseline_dist, modified_dist,
                                 result.state_labels, result.n_customers)
        st.markdown(
            f'<div class="card accent-card" style="--accent:{summary.accent_token};'
            f'padding:var(--space-5);">'
            f'<div class="t-label">SCENARIO IMPACT</div>'
            f'<div style="margin-top:var(--space-2);">{summary.html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    - This makes the accent green when improving, amber when worsening, neutral grey when no
      override is applied (Issue 2), and renders the key numbers at .t-h2 with colored mono
      spans (Issue 3). The old `.t-sm` wrapper is removed because summary.html already carries
      its own typography classes (.t-h2 / .t-h3).
    - Update the import line at lines 29-33 accordingly (it currently imports build_sankey_figure,
      build_whatif_chart, impact_narrative — add impact_summary and state_legend_html; you may
      drop impact_narrative from the page import if no longer used, but keep the function in the
      component module).

    Keep all noqa comments (E402 on imports, N806 on baseline_P) intact. Do not touch the
    Sankey figure builder, the scrubber, or the what-if chart.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_page_import.py -q</automated>
  </verify>
  <done>2_Churn.py imports impact_summary + state_legend_html; KPI 2/3/4 accents are chart-4/state-churned/state-atrisk; legend renders above the Sankey; impact card uses summary.accent_token and summary.html; page smoke import test passes.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
  All four UI-review fixes on the Churn page: (1) KPI strip accents now read green/cyan/red/amber for KPI 1-4; (2) the SCENARIO IMPACT card accent bar turns green when a scenario lowers churn, amber when it raises churn, and grey when no slider is touched; (3) the impact narrative's key numbers render at 24px bold with colored mono spans; (4) a 5-item color legend (dot + state label) sits directly above the Sankey on the Overview tab.
  </what-built>
  <how-to-verify>
  1. Start the app: `uv run streamlit run app/Home.py` and open http://localhost:8501.
  2. Go to the "Customer Churn" page. Select a cohort and click "Run Analysis".
  3. KPI strip — confirm accent top-bars read left-to-right: GREEN (Retention Rate), CYAN (Avg Customer Lifetime), RED (Expected Churn), AMBER (Revenue at Risk).
  4. Overview tab — confirm a horizontal legend (5 colored dots + labels: Active/At-Risk/Inactive/Reactivated/Churned, colors matching the Sankey ribbons) appears directly above the Sankey chart.
  5. What-If Simulator tab — with NO sliders moved, the SCENARIO IMPACT card accent bar is GREY and shows "Adjust a slider..." text.
  6. Drag an "From Active -> Churned" slider DOWN (lower churn): accent bar turns GREEN; the narrative shows large bold numbers ("...by Npp" in indigo, "saves N customers" in green) at clearly larger-than-body size.
  7. Drag a churn-increasing slider UP (e.g. From Active -> Churned higher): accent bar turns AMBER and the sentence reads "costs N customers".
  </how-to-verify>
  <resume-signal>Type "approved" or describe any color/typography/legend issues to fix.</resume-signal>
</task>

</tasks>

<verification>
- `uv run pytest tests/unit/test_churn_service.py tests/unit/test_page_import.py -q` passes (new helper tests + page smoke import).
- `uv run pytest -q` full suite still green (no regressions).
- `uv run ruff check app/ tests/` clean (import order, line length).
- `grep -r "import streamlit" app/components/sankey_flow.py` returns empty (component stays pure).
- Human checkpoint confirms the 4 visual fixes render correctly in the live app.
</verification>

<success_criteria>
- KPI 2/3/4 accents are `var(--chart-4)` / `var(--state-churned)` / `var(--state-atrisk)` (KPI 1 unchanged green).
- SCENARIO IMPACT accent is conditional: green=improving, amber=worsening, grey=neutral.
- Impact narrative key numbers render at `.t-h2` (24px/600) with colored `.mono` spans.
- A 5-item static HTML legend (swatch + label) renders above the Sankey on Overview.
- `sankey_flow.py` gains `impact_summary` + `state_legend_html` (pure, no streamlit) with passing unit tests.
- Full test suite + ruff clean; live app verified by human.
</success_criteria>

<output>
After completion, create `.planning/quick/260531-ikw-fix-4-visual-issues-from-phase-03-ui-rev/260531-ikw-SUMMARY.md`.

Post-coding doc updates (per CLAUDE.md / .claude/rules/workflow.md):
- `docs/planning/task-progress.md` — record the UI-fix task as Done + commit hash.
- `docs/planning/decisions.md` — only if a notable decision was made (e.g. introducing ImpactSummary / structured impact return). Optional for pure presentation fixes.
- No App Pages table change (Churn page already listed); no README change unless you consider the polish user-visible enough to note.
</output>
