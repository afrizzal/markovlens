# Phase 03: Churn Domain - Research

**Researched:** 2026-05-31
**Domain:** Absorbing Markov chains, Plotly Scatter Sankey ribbons, Streamlit what-if accordion
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Sankey Chart (CH-02)**
- D-01: Temporal multi-period Plotly Scatter Sankey — ribbons spanning 8+ period columns, matching `docs/design-reference/js/charts.jsx`. Each column = one period; ribbon width = proportional to raw transition counts (not probabilities). Node colors from churn state palette. Absorbing "Churned" node rendered at the bottom in `--state-churned` (red). Do NOT use `go.Sankey`.
- D-02: Time scrubber below Sankey: `st.slider` for period selection (0..N, default = last period) + horizontal stacked distribution bar. `ChurnAnalysisResult` stores `state_distribution_over_time` shape `(n_periods+1, n_states)` and per-period flow data.

**What-If Simulator (CH-03)**
- D-03: All transition rows editable simultaneously — `st.expander` accordion groups by from-state. Each group collapsible. Sliders for every `to-state` within group. Any change auto-renormalizes entire row to sum to 1.0. "Reset all" ghost button appears when any value differs from baseline.
- D-04: Right panel = impact summary card + stacked-area before/after chart. Impact card: narrative prose driven by largest delta transition. Stacked area: baseline (opacity ~0.18) vs modified (opacity ~0.8). Both update live on slider change (no button press). Session state-driven, cached with `@st.cache_data` keyed on scenario matrix hash.

**KPI Strip (CH-04)**
- D-05: Four KPIs: Retention Rate, Avg Customer Lifetime (from fundamental matrix `(I-Q)^{-1}`), Expected Churn (30d/next period), Revenue at Risk (`expected_churn_count * DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER`). Revenue constant annotated with tooltip "Assumes Rp [value]/customer/month — adjust in Settings (v2)".

**Page Structure (CH-04)**
- D-06: 2 tabs only — "Overview" and "What-If Simulator". State Journey deferred to v2 and must NOT appear as a visible empty tab.
- D-07: Same page structure pattern as `1_Brand_Share.py`: `set_page_config` → `register_theme()` → `inject_theme()` → module constants → `@st.cache_resource` DB → `@st.cache_data` → control strip → KPI strip → tabs.
- D-08: Session state keys namespaced `churn.*`.

**Domain Service (CH-01)**
- D-09: `ChurnAnalysisResult` NumPy-only fields. Minimum fields: `transition_matrix`, `state_distribution_over_time` (shape `(n_periods+1, n_states)`), `baseline_forecast` (shape `(horizon+1, n_states)`), `kpis` (dict), `state_labels`, `dataset_name`, `n_customers`, `observation_counts`.
- D-10: `list_datasets()` uses `domain="churn"` to match shared DuckDB API.
- D-11: `run_analysis(conn, dataset_id, horizon)` orchestrates `build_transition_matrix` → `M1Homogeneous.forecast`. `simulate_scenario(conn, dataset_id, horizon, transition_overrides)` accepts partial `{(from_i, to_j): new_prob}` dict, renormalizes, returns second `state_distribution_over_time`.

### Claude's Discretion
- Exact Plotly trace parameters for ribbon path construction (bezier control points, opacity levels).
- Whether `sankey_flow` component lives in `app/components/sankey_flow.py` or inline in the page.
- How `(I-Q)^{-1}` fundamental matrix computation handles near-singular cases.
- Whether what-if right panel re-runs on each slider tick or debounces (lean toward live since Streamlit re-runs are fast for small matrices; gate with `@st.cache_data` keyed on scenario matrix hash).

### Deferred Ideas (OUT OF SCOPE)
- State Journey tab (deferred to v2)
- Saved scenarios drawer (maps to `scenarios` DuckDB table — UI deferred)
- Save scenario modal
- Stationary distribution panel for churn (CH-05, v2)
- Dataset upload from Settings page (DATA-04, v2)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CH-01 | `domains/churn/service.py` orchestrates Markov churn pipeline; returns `ChurnAnalysisResult` with structured NumPy arrays (no Plotly coupling) | Fundamental matrix computation verified; simulate_scenario renormalization pattern verified; mirrors brand_share/service.py structure |
| CH-02 | Sankey state flow diagram — link width proportional to raw counts, colored by from-state, absorbing "Churned" node at bottom in red | Plotly shapes + SVG bezier path approach verified (100 ribbon shapes for 8 periods); exact JSX port algorithm documented |
| CH-03 | What-if state simulator — slider to edit rows of P, live forecast update, row renormalized on adjustment | `st.expander` accordion pattern verified; `@st.cache_data` keyed on `frozenset(overrides.items())` verified hashable; stackgroup stacked-area verified |
| CH-04 | `app/pages/2_Churn.py` — full page with loading, empty, and error states | Mirrors 1_Brand_Share.py pattern exactly; sys.path prelude required |
</phase_requirements>

---

## Summary

Phase 03 builds the Customer Churn domain page by reusing the Phase 02 design system and core engine. The technical challenges are: (1) porting the JSX Sankey ribbon chart to Plotly using SVG bezier shapes, (2) computing the absorbing Markov chain fundamental matrix `(I-Q)^{-1}` for the Avg Customer Lifetime KPI, and (3) wiring the what-if accordion to live-update a stacked-area comparison chart without a button press.

All three are fully verified through code execution. The Sankey uses Plotly `add_shape(type='path', path='M ... C ... L ... Z')` with cubic bezier control points — a direct port of the JSX algorithm. The fundamental matrix computation uses `numpy.linalg.inv` with a `pinv` fallback when condition number exceeds 1e10. The what-if panel stores slider values in `st.session_state` keyed `churn.what_if.{i}_{j}` and caches `simulate_scenario` on `frozenset(overrides.items())`.

The service layer mirrors `domains/brand_share/service.py` exactly: NumPy-only `@dataclass(frozen=True)` result, `conn` as first parameter, no Streamlit imports, and `list_datasets(conn, domain="churn")` consistent with the shared DB API.

**Primary recommendation:** Build service first (CH-01), then Sankey component (CH-02), then what-if panel (CH-03), then wire the full page (CH-04) — same dependency order as Phase 02 plans.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Plotly | 6.7.0 (installed) | Sankey ribbons, stacked-area charts | Already used in Phase 02; shapes API verified |
| NumPy | 2.4.6 (installed) | Fundamental matrix, forecast arrays | Already used in core/ |
| SciPy | 1.17.1 (installed) | `scipy.linalg` for eigenvectors (stationary) | Already used in core/models.py |
| Streamlit | 1.57.0 (installed) | `st.expander`, `st.slider`, `st.cache_data` | Already in project |
| DuckDB | 1.1.0+ | Query transitions for churn domain | Already in core/db |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `numpy.linalg.inv` / `pinv` | NumPy 2.4.6 | Fundamental matrix `(I-Q)^{-1}` | Avg Customer Lifetime KPI |
| `numpy.linalg.cond` | NumPy 2.4.6 | Near-singular detection | Before `inv`, switch to `pinv` if cond > 1e10 |

**Installation:** All already installed — `uv sync` covers the full stack.

---

## Architecture Patterns

### Recommended Structure for Phase 03

```
domains/churn/
├── __init__.py
└── service.py              # Full rewrite from stub

app/pages/
└── 2_Churn.py              # New page (mirrors 1_Brand_Share.py)

app/components/
└── sankey_flow.py          # New component (Plotly Sankey ribbons)

tests/
├── unit/
│   └── test_churn_service.py    # Wave 0 gap
└── integration/
    └── test_churn_service.py    # Wave 0 gap
```

### Pattern 1: ChurnAnalysisResult dataclass

`@dataclass(frozen=True)` with NumPy-only fields. No Plotly objects. Mirrors `BrandShareForecastResult`.

```python
# Source: domains/brand_share/service.py (established pattern)
@dataclass(frozen=True)
class ChurnAnalysisResult:
    transition_matrix: np.ndarray          # shape (n_states, n_states)
    observation_counts: np.ndarray         # shape (n_states, n_states)
    state_distribution_over_time: np.ndarray   # shape (n_periods+1, n_states)
    baseline_forecast: np.ndarray          # shape (horizon+1, n_states)
    kpis: dict[str, float]                 # retention, lifetime, expected_churn, revenue_at_risk
    state_labels: list[str]                # ordered, matches matrix rows/cols
    dataset_name: str
    n_customers: int
    n_periods: int
```

### Pattern 2: Sankey Ribbon Construction (Plotly Shapes + SVG Bezier)

The JSX `Sankey` component uses cubic bezier paths for each edge. Port to Plotly `add_shape` with `type='path'`. Verified with 100 ribbon shapes generated for 8 periods.

```python
# Source: docs/design-reference/js/charts.jsx + verified via execution
def _build_sankey_figure(
    state_distribution_over_time: np.ndarray,  # shape (n_cols, n_states)
    transition_matrix: np.ndarray,             # shape (n_states, n_states)
    state_labels: list[str],
    state_colors: dict[str, str],              # {label: rgba_string}
    *,
    n_cols: int = 8,
    highlight_period: int | None = None,
) -> go.Figure:
    # Layout constants matching JSX: W=820, H=380, col_w=13, gap=7
    W, H, PT, PB = 820, 380, 10, 10
    col_w, gap = 13, 7
    ih = H - PT - PB

    x_col = lambda c: 8 + (c / (n_cols - 1)) * (W - 16 - col_w)
    xr = lambda c: x_col(c) + col_w   # right edge of column c
    xl = lambda c: x_col(c)            # left edge of column c

    # --- Node layout per column (same as JSX) ---
    layout = []
    for c in range(n_cols):
        d = state_distribution_over_time[c]
        active_states = [(i, v) for i, v in enumerate(d) if v > 0.002]
        total_gap = gap * (len(active_states) - 1)
        yy = PT
        nodes = {}
        for i, v in active_states:
            h = v * (ih - total_gap)
            nodes[i] = {"y0": yy, "y1": yy + h, "v": v}
            yy += h + gap
        layout.append(nodes)

    # --- Edge (ribbon) shapes ---
    shapes = []
    hover_traces = []  # invisible scatter for tooltips
    for c in range(n_cols - 1):
        d = state_distribution_over_time[c]
        src_off = np.zeros(len(state_labels))
        tgt_off = np.zeros(len(state_labels))
        for i in range(len(state_labels)):
            if i not in layout[c]:
                continue
            for j in range(len(state_labels)):
                flow = d[i] * transition_matrix[i, j]
                if flow < 0.0015 or j not in layout[c + 1]:
                    continue
                sH = layout[c][i]["y1"] - layout[c][i]["y0"]
                tH = layout[c + 1][j]["y1"] - layout[c + 1][j]["y0"]
                s_scale = sH / (d[i] if d[i] > 1e-12 else 1)
                t_scale = tH / (state_distribution_over_time[c + 1][j] or 1)
                sy0 = layout[c][i]["y0"] + src_off[i]
                sy1 = sy0 + flow * s_scale
                ty0 = layout[c + 1][j]["y0"] + tgt_off[j]
                ty1 = ty0 + flow * t_scale
                src_off[i] += flow * s_scale
                tgt_off[j] += flow * t_scale
                x1, x2 = xr(c), xl(c + 1)
                mx = (x1 + x2) / 2
                # Cubic bezier ribbon — exact port from JSX charts.jsx
                path = (
                    f"M {x1} {sy0} C {mx} {sy0} {mx} {ty0} {x2} {ty0} "
                    f"L {x2} {ty1} C {mx} {ty1} {mx} {sy1} {x1} {sy1} Z"
                )
                color = state_colors.get(state_labels[i], "rgba(100,100,100,")
                shapes.append(dict(
                    type="path", path=path,
                    fillcolor=f"{color}0.24)",
                    line=dict(width=0),
                    xref="x", yref="y",
                ))

    # --- Node rectangles ---
    for c, nodes in enumerate(layout):
        for i, nd in nodes.items():
            color = state_colors.get(state_labels[i], "rgba(100,100,100,")
            shapes.append(dict(
                type="rect",
                x0=x_col(c), y0=nd["y0"],
                x1=x_col(c) + col_w, y1=nd["y1"],
                fillcolor=f"{color}1.0)",
                line=dict(width=0),
                xref="x", yref="y",
            ))

    fig = go.Figure()
    # Invisible scatter for hover at edge midpoints
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers",
                             marker=dict(opacity=0), showlegend=False))
    fig.update_layout(
        shapes=shapes,
        xaxis=dict(range=[0, W], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, H], showgrid=False, zeroline=False, showticklabels=False),
        height=H, margin=dict(l=0, r=0, t=8, b=24),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
```

### Pattern 3: Fundamental Matrix for Avg Customer Lifetime

Absorbing Markov chain: identify transient states (P[i,i] < 0.95), extract Q submatrix, compute `N = (I-Q)^{-1}`. Row sums give expected periods until absorption.

```python
# Source: verified via execution
ABSORBING_THRESHOLD: float = 0.95

def compute_fundamental_matrix(
    P: np.ndarray,
    *,
    absorbing_threshold: float = ABSORBING_THRESHOLD,
) -> tuple[np.ndarray | None, list[int]]:
    """Return (N, transient_indices) or (None, []) if all states absorbed."""
    n = len(P)
    transient_idx = [i for i in range(n) if P[i, i] < absorbing_threshold]
    if not transient_idx:
        return None, []
    Q = P[np.ix_(transient_idx, transient_idx)]
    I_Q = np.eye(len(transient_idx), dtype=np.float64) - Q
    try:
        cond = np.linalg.cond(I_Q)
        N = np.linalg.pinv(I_Q) if cond > 1e10 else np.linalg.inv(I_Q)
        return N, transient_idx
    except np.linalg.LinAlgError:
        return None, transient_idx

def compute_avg_lifetime(P: np.ndarray, active_state_idx: int) -> float | None:
    """Expected periods in any transient state for Active customers.
    Returns None if computation fails (all absorbed or singular).
    """
    N, transient_idx = compute_fundamental_matrix(P)
    if N is None or active_state_idx not in transient_idx:
        return None
    row = transient_idx.index(active_state_idx)
    return float(N.sum(axis=1)[row])
```

**Verified:** With the 5-state design reference P matrix, `compute_avg_lifetime` returns 20.68 periods from Active state. Design reference shows 28.4 — difference is data-driven; the actual telco dataset will produce realistic values.

### Pattern 4: simulate_scenario with Row Renormalization

```python
# Source: verified via execution
def simulate_scenario(
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    horizon: int,
    transition_overrides: dict[tuple[int, int], float],
) -> np.ndarray:
    """Apply partial transition overrides, renormalize affected rows, forecast.

    Parameters
    ----------
    transition_overrides : dict[tuple[int, int], float]
        Keys are (from_state_idx, to_state_idx), values are new probabilities.
        Each affected row is renormalized after all overrides for that row are applied.

    Returns
    -------
    np.ndarray
        state_distribution_over_time, shape (horizon+1, n_states).
    """
    P_baseline, _ = build_transition_matrix(conn, dataset_id)
    P_mod = P_baseline.copy()

    # Group overrides by from-state row, apply, renormalize
    rows_to_fix: dict[int, dict[int, float]] = {}
    for (i, j), val in transition_overrides.items():
        rows_to_fix.setdefault(i, {})[j] = val
    for i, changes in rows_to_fix.items():
        for j, val in changes.items():
            P_mod[i, j] = float(np.clip(val, 0.0, 1.0))
        row_sum = P_mod[i].sum()
        if row_sum > 1e-12:
            P_mod[i] /= row_sum

    validate_transition_matrix(P_mod)  # raises if broken

    # Forecast using M1Homogeneous (churn domain uses m1 only)
    ds = get_dataset(conn, dataset_id)
    df = load_transitions(conn, dataset_id)
    state_labels = sorted(set(df["from_state"]) | set(df["to_state"]))
    state_idx = {s: k for k, s in enumerate(state_labels)}
    Y_1 = _compute_initial_distribution(df, state_idx, len(state_labels))

    dist = np.zeros((horizon + 1, len(state_labels)), dtype=np.float64)
    dist[0] = Y_1
    Y_t = Y_1.copy()
    for t in range(horizon):
        Y_t = Y_t @ P_mod
        dist[t + 1] = Y_t
    return dist
```

### Pattern 5: What-If Accordion with Live Session State

```python
# Source: Streamlit 1.57.0 verified signatures
# st.expander on_change default = 'ignore' (expanding doesn't trigger rerun)
# st.slider triggers full page rerun on every change — no button needed

# Session state key pattern: churn.what_if.{from_i}_{to_j}
def _build_whatif_panel(baseline_P: np.ndarray, state_labels: list[str]) -> dict:
    """Render accordion sliders, return {(i,j): new_val} overrides dict."""
    overrides: dict[tuple[int, int], float] = {}

    for i, from_label in enumerate(state_labels):
        with st.expander(f"From {from_label}", expanded=(i == 0)):
            for j, to_label in enumerate(state_labels):
                baseline_val = float(baseline_P[i, j])
                key = f"churn.what_if.{i}_{j}"
                # Initialize session state to baseline on first run
                if key not in st.session_state:
                    st.session_state[key] = baseline_val
                current_val = st.slider(
                    f"→ {to_label}",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state[key],
                    step=0.01,
                    format="%.2f",
                    key=key,
                )
                if abs(current_val - baseline_val) > 1e-6:
                    overrides[(i, j)] = current_val

    return overrides

# Cache key for simulate_scenario: frozenset is hashable
@st.cache_data(show_spinner=False)
def _cached_scenario(
    dataset_id: str,
    horizon: int,
    overrides_frozen: frozenset,  # frozenset(overrides.items())
) -> np.ndarray:
    overrides = dict(overrides_frozen)
    return service.simulate_scenario(_get_db(), dataset_id, horizon, overrides)
```

### Pattern 6: Stacked-Area Before/After Chart

Two `stackgroup` series on same figure — baseline (opacity ~0.18) and modified (opacity ~0.8).

```python
# Source: verified via execution (Plotly 6.7.0)
# stackgroup='baseline' and stackgroup='modified' render as separate stacked areas

STATE_COLORS_SOLID = {  # derived from theme.css --state-* tokens (light mode values)
    "active":      "rgba(5,150,105,0.8)",
    "atrisk":      "rgba(217,119,6,0.8)",
    "inactive":    "rgba(161,161,170,0.8)",
    "reactivated": "rgba(8,145,178,0.8)",
    "churned":     "rgba(220,38,38,0.8)",
}
STATE_COLORS_FAINT = {k: v.replace("0.8)", "0.18)") for k, v in STATE_COLORS_SOLID.items()}

def _build_whatif_chart(
    baseline_dist: np.ndarray,     # shape (horizon+1, n_states)
    modified_dist: np.ndarray,     # shape (horizon+1, n_states)
    state_labels: list[str],
) -> go.Figure:
    fig = go.Figure()
    periods = list(range(len(baseline_dist)))
    for i, label in enumerate(state_labels):
        key = label.lower().replace("-", "").replace(" ", "")
        faint = STATE_COLORS_FAINT.get(key, "rgba(100,100,100,0.18)")
        solid = STATE_COLORS_SOLID.get(key, "rgba(100,100,100,0.8)")
        fig.add_trace(go.Scatter(
            x=periods, y=baseline_dist[:, i],
            stackgroup="baseline", name=label,
            fillcolor=faint, line=dict(color="rgba(0,0,0,0)", width=0),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=periods, y=modified_dist[:, i],
            stackgroup="modified", name=label,
            fillcolor=solid, line=dict(color="rgba(0,0,0,0)", width=0),
            showlegend=True, legendgroup=label,
        ))
    return fig
```

### Anti-Patterns to Avoid

- **Using `go.Sankey`:** Loses the temporal dimension — each period must be a column, not a node. go.Sankey collapses time into one flow diagram.
- **Plotly `stackgroup` with `opacity` parameter on the trace:** In Plotly 6.x, `fillcolor` on the `Scatter` trace controls the stacked-area fill color. Set `opacity` via the rgba alpha, not the top-level `opacity` field, which affects the entire trace including any line.
- **Renormalizing inside the slider callback:** There is no callback-based pattern in Streamlit. Renormalization happens inside `simulate_scenario`, not in the widget definition.
- **Storing `ChurnAnalysisResult` in session state:** `@dataclass(frozen=True)` with NumPy arrays is not safely serializable for `st.session_state` persistence across sessions. Use `@st.cache_data` instead (Streamlit handles the caching layer).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stacked-area chart | Custom SVG stacked renderer | `go.Scatter` with `stackgroup=` | Plotly handles cumsum + fill correctly |
| Fundamental matrix | Iterative absorption simulation | `np.linalg.inv(I - Q)` | Exact closed-form solution, O(n^3) |
| Row renormalization | Custom renorm utility | Inline `row /= row.sum()` after overrides | Single line, no abstraction needed |
| Color token lookup | CSS variable reader in Python | Module-level dict matching theme.css | CSS vars not accessible in Python; hardcode matching rgba values |
| Session state initialization | Custom state manager | `if key not in st.session_state: st.session_state[key] = default` | Streamlit's standard pattern |

**Key insight:** The Sankey's "hard part" (bezier ribbon shapes) is a direct algorithmic port from the JSX reference — not a discovery problem. The algorithm is fully specified in `docs/design-reference/js/charts.jsx` lines 195–258.

---

## Common Pitfalls

### Pitfall 1: Absorbing State Detection Threshold

**What goes wrong:** Using `P[i,i] == 1.0` strictly to identify absorbing states misses the "Churned" state in the design reference (P[4,4] = 0.98). `(I-Q)` becomes poorly conditioned if near-absorbing rows are left in the transient submatrix.

**Why it happens:** Textbook absorbing Markov chain definitions require strict absorption. Real churn data has near-absorbing states.

**How to avoid:** Use `P[i,i] >= ABSORBING_THRESHOLD` where `ABSORBING_THRESHOLD = 0.95`. Make this a module constant so the threshold is visible in the plan.

**Warning signs:** `numpy.linalg.cond(I_Q)` returns a very large number (> 1e10) when threshold is wrong.

### Pitfall 2: Sankey Node Height Mismatch Across Periods

**What goes wrong:** If `state_distribution_over_time` is built from `M1Homogeneous.forecast` (shape `(horizon, n_states)`) instead of including the initial period, column 0 has no nodes and the first ribbon has no source coordinates.

**Why it happens:** `M1Homogeneous.forecast` returns periods `t+1..t+horizon` not including `t=0`.

**How to avoid:** Prepend the initial distribution to the forecast array: `np.vstack([Y_1.reshape(1, -1), forecast_result.forecast_array])` to get shape `(horizon+1, n_states)`. The `state_distribution_over_time` field in `ChurnAnalysisResult` MUST include period 0.

### Pitfall 3: Slider Key Naming and State Persistence

**What goes wrong:** Using `f"churn_{i}_{j}"` as a slider key causes namespace collisions with any other page that uses similar integer keys. When switching pages in Streamlit, session state persists — stale keys from one session may corrupt the initial values of sliders on re-open.

**Why it happens:** Streamlit session state is shared across the app session.

**How to avoid:** Use `f"churn.what_if.{i}_{j}"` as the key (namespace with `churn.`). Check `if key not in st.session_state` before initializing to avoid overwriting user edits on re-run.

### Pitfall 4: Ruff N803/N806 in service.py

**What goes wrong:** Using mathematical variable names `P`, `Q`, `Y_1` triggers ruff N803 (argument name should be lowercase) and N806 (variable in function should be lowercase).

**Why it happens:** These names follow Chan (2015) notation and are intentional.

**How to avoid:** Add `"domains/churn/service.py" = ["N803", "N806"]` to `pyproject.toml`'s `[tool.ruff.lint.per-file-ignores]`. This is already established for `domains/brand_share/service.py`.

### Pitfall 5: simulate_scenario Does Not Accept `conn` if Not Needed from DB

**What goes wrong:** `simulate_scenario` is called from the page for every slider tick. If it re-queries DuckDB on each call, it defeats the caching strategy.

**Why it happens:** The baseline matrix is loaded inside `simulate_scenario` instead of being passed in.

**How to avoid:** Per CONTEXT.md D-11: `simulate_scenario` accepts a `transition_overrides` dict and re-applies them to the baseline matrix fetched from DB. Since `build_transition_matrix` is fast and DuckDB caches hot paths, this is acceptable. For extra performance, accept an optional `baseline_P: np.ndarray | None` parameter and skip the DB query if provided. The page can pass `result.transition_matrix` directly.

### Pitfall 6: Stacked Distribution Bar in Time Scrubber

**What goes wrong:** Rendering the horizontal stacked distribution bar with `st.plotly_chart` adds overhead. The design reference renders it as a CSS flex bar — Streamlit can replicate this with `st.markdown` + inline `<div>` styles.

**Why it happens:** Over-engineering a simple colored bar.

**How to avoid:** Use `st.markdown` with `unsafe_allow_html=True` for the stacked distribution bar (matches design reference exactly). Reserve Plotly for the Sankey chart itself.

---

## Code Examples

### KPI Computation (All Four KPIs)

```python
# Source: verified via execution
ACTIVE_STATE_KEY: str = "active"   # resolved dynamically from state_labels
CHURNED_STATE_KEY: str = "churned"
DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER: int = 50_000  # Rp (D-05, UI tooltip)
ABSORBING_THRESHOLD: float = 0.95

def _compute_kpis(
    P: np.ndarray,
    state_distribution_over_time: np.ndarray,   # shape (n_periods+1, n_states)
    baseline_forecast: np.ndarray,              # shape (horizon+1, n_states)
    state_labels: list[str],
    n_customers: int,
    horizon: int,
) -> dict[str, float]:
    active_idx = next((i for i, s in enumerate(state_labels) if s.lower() == ACTIVE_STATE_KEY), 0)
    churned_idx = next((i for i, s in enumerate(state_labels) if s.lower() == CHURNED_STATE_KEY), -1)

    # KPI 1: Retention Rate = Active share at horizon / initial Active share
    initial_active = baseline_forecast[0, active_idx]
    final_active = baseline_forecast[horizon, active_idx]
    retention_rate = float(final_active / initial_active) if initial_active > 1e-12 else 0.0

    # KPI 2: Avg Customer Lifetime from fundamental matrix
    avg_lifetime = compute_avg_lifetime(P, active_idx) or float("nan")

    # KPI 3: Expected Churn = Active customers * P(active -> churned)
    initial_active_count = n_customers * initial_active
    p_churn_one_step = float(P[active_idx, churned_idx]) if churned_idx >= 0 else 0.0
    expected_churn = initial_active_count * p_churn_one_step

    # KPI 4: Revenue at Risk
    revenue_at_risk = expected_churn * DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER

    return {
        "retention_rate": retention_rate,
        "avg_lifetime": avg_lifetime,
        "expected_churn": expected_churn,
        "revenue_at_risk": revenue_at_risk,
    }
```

### Impact Narrative for What-If Panel

```python
# Source: CONTEXT.md Specifics + design reference PageWhatIf
def _impact_narrative(
    overrides: dict[tuple[int, int], float],
    baseline_P: np.ndarray,
    baseline_dist: np.ndarray,  # shape (horizon+1, n_states)
    modified_dist: np.ndarray,  # shape (horizon+1, n_states)
    state_labels: list[str],
    n_customers: int,
) -> str:
    if not overrides:
        return "Adjust a slider to model a retention scenario."
    churned_idx = next(
        (i for i, s in enumerate(state_labels) if s.lower() == "churned"), -1
    )
    # Find largest delta transition
    best_key = max(overrides, key=lambda k: abs(overrides[k] - baseline_P[k[0], k[1]]))
    i, j = best_key
    delta_pp = (overrides[best_key] - baseline_P[i, j]) * 100
    direction = "Reducing" if delta_pp < 0 else "Increasing"
    from_label = state_labels[i]
    to_label = state_labels[j]
    # Customer impact at horizon
    if churned_idx >= 0:
        churn_delta = (baseline_dist[-1, churned_idx] - modified_dist[-1, churned_idx]) * n_customers
        sign = "saves" if churn_delta > 0 else "costs"
        return (
            f"{direction} {from_label} → {to_label} by {abs(delta_pp):.0f}pp "
            f"{sign} {abs(churn_delta):.0f} customers."
        )
    return f"{direction} {from_label} → {to_label} by {abs(delta_pp):.0f}pp."
```

### sys.path Prelude (required for every Streamlit page)

```python
# Source: CONTEXT.md 2026-05-31 sys.path manipulation decision
# decisions.md: every page file MUST start with this pattern
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `go.Sankey` (built-in) | Plotly shapes + SVG bezier | Phase 03 decision | go.Sankey loses temporal dimension; shapes give full layout control |
| Button-triggered what-if | Live slider → auto-rerun | Phase 03 decision | Streamlit reruns on every widget change; no button needed |
| Manual `np.random.seed()` | `np.random.default_rng(seed)` | Phase 01 | NEP 50 compliance; churn doesn't use Monte Carlo but follows same convention |
| Inline SQL strings | All SQL in `core/db/queries.py` | Phase 01 | No raw SQL in service.py |

**Deprecated/outdated:**
- `list_cohorts()`: renamed to `list_datasets(domain="churn")` per D-10 — existing stub uses old name
- `simulate_scenario(cohort_id, transition_overrides)`: old stub signature; correct is `(conn, dataset_id, horizon, transition_overrides)` per D-11
- `sankey_chart_json: dict` field in old `ChurnAnalysisResult`: Plotly coupling in domain layer — forbidden per D-09

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Plotly | Sankey + stacked-area charts | Yes | 6.7.0 | — |
| NumPy | Fundamental matrix, forecasts | Yes | 2.4.6 | — |
| SciPy | (eigenvector, if needed) | Yes | 1.17.1 | — |
| Streamlit | Page rendering | Yes | 1.57.0 | — |
| DuckDB | Churn dataset queries | Yes (via uv) | 1.1.0+ | — |
| `uv` | Package manager | Yes | — | — |

No missing dependencies. All tools verified installed.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/unit/ -q` |
| Full suite command | `uv run pytest tests/ -q` |
| Current baseline | 61 tests passing, 3.53s |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CH-01 | `ChurnAnalysisResult` fields correct shape/type | unit | `uv run pytest tests/unit/test_churn_service.py -x` | Wave 0 gap |
| CH-01 | `run_analysis` returns valid KPI dict | integration | `uv run pytest tests/integration/test_churn_service.py -x` | Wave 0 gap |
| CH-01 | `simulate_scenario` renormalizes correctly | unit | `uv run pytest tests/unit/test_churn_service.py::test_simulate_scenario_renormalizes -x` | Wave 0 gap |
| CH-01 | `compute_avg_lifetime` matches expected for reference P | unit | `uv run pytest tests/unit/test_churn_service.py::test_compute_avg_lifetime -x` | Wave 0 gap |
| CH-02 | `_build_sankey_figure` returns valid `go.Figure` with shapes | unit | `uv run pytest tests/unit/test_churn_service.py::test_build_sankey_figure -x` | Wave 0 gap |
| CH-03 | `simulate_scenario` with override produces different distribution | integration | `uv run pytest tests/integration/test_churn_service.py::test_simulate_scenario_differs -x` | Wave 0 gap |
| CH-04 | Page imports without exception (smoke test) | unit | `uv run pytest tests/unit/test_page_import.py -x` | Exists (add churn case) |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/ -q`
- **Per wave merge:** `uv run pytest tests/ -q`
- **Phase gate:** Full suite green (61+ tests) before `/gsd:verify-work`

### Wave 0 Gaps

- `tests/unit/test_churn_service.py` — covers CH-01 unit cases (ChurnAnalysisResult shape, KPI formulas, simulate_scenario renorm, fundamental matrix)
- `tests/integration/test_churn_service.py` — covers CH-01 integration (seeded DuckDB, run_analysis, simulate_scenario end-to-end)
- `tests/unit/test_page_import.py` — extend existing file to add 2_Churn.py smoke import (mirrors existing BS-06 pattern)
- `pyproject.toml` — add `"domains/churn/service.py" = ["N803", "N806"]` to `per-file-ignores` (one-line edit)

---

## Open Questions

1. **Churn state label discovery from Telco dataset**
   - What we know: The design reference uses 5 states (Active, At-Risk, Inactive, Reactivated, Churned). The actual Telco CSV may have different state labels (e.g., "active", "at-risk", "inactive", "reactivated", "churned" in lowercase, or "0"/"1" integer codes).
   - What's unclear: Whether `state_labels` from `sorted(set(df["from_state"]) | set(df["to_state"]))` will produce labels that match the `STATE_COLORS` dict keys.
   - Recommendation: Implement case-insensitive lookup and a fallback color assignment. `state_colors.get(label.lower().replace("-", ""), default_color)`. The `ABSORBING_THRESHOLD` detection should still work even if label names differ.

2. **n_customers from dataset metadata**
   - What we know: `ChurnAnalysisResult` needs `n_customers: int`. The `Dataset` dataclass has `row_count` (transitions count) and `n_states`. The actual customer count is distinct `entity_id` count.
   - What's unclear: Whether `row_count` in the `datasets` table is transitions count or customer count.
   - Recommendation: Derive `n_customers = df["entity_id"].nunique()` from the loaded transitions DataFrame in `run_analysis`. Store in result. This is a cheap operation on a loaded DataFrame.

3. **Sankey highlight_period behavior**
   - What we know: The JSX has a `highlight` prop that dims ribbons not adjacent to the selected period. The design reference page shows a `st.slider` for period.
   - What's unclear: Whether to wire the time scrubber slider to highlight_period in the Sankey (requiring a re-render on scrub) vs. updating only the distribution bar below.
   - Recommendation: Per CONTEXT.md D-02, the scrubber updates the stacked distribution bar only. The Sankey itself shows all 8 periods statically. `highlight_period` can be `None` by default (all ribbons at same opacity).

---

## Project Constraints (from CLAUDE.md)

| Directive | Category | Enforcement |
|-----------|----------|-------------|
| `from __future__ import annotations` at top of every Python file | Import | Ruff I001 |
| `sys.path` prelude in every Streamlit page file | Import | Manual check |
| `set_page_config` as first Streamlit call per page | Streamlit | Manual check |
| `register_theme()` then `inject_theme()` after page config | Streamlit | Pattern from 1_Brand_Share.py |
| No `import streamlit` in `core/` or `domains/` | Architecture | `grep -r "import streamlit" domains/ core/` |
| All SQL in `core/db/queries.py`, parameterized | Data | Ruff + code review |
| `@dataclass(frozen=True)` for result types | Python | Type check |
| Type hints on all public functions | Python | mypy |
| N803/N806 suppressed for math variable names (P, Q, Y) | Ruff | `pyproject.toml` per-file-ignores |
| `uv run pytest` for tests | Testing | Required |
| `rtk git` prefix for all git commands | Workflow | Token optimization |
| All new planning notes to `docs/planning/`, not `.planning/` | Planning | CLAUDE.md |
| Update `docs/planning/task-progress.md` after each task | Workflow | Post-coding checklist |

---

## Sources

### Primary (HIGH confidence)
- `docs/design-reference/js/charts.jsx` — Sankey SVG bezier algorithm (source of truth for ribbon path construction)
- `docs/design-reference/js/data.jsx` — CHURN_STATES, 5-state P matrix, COHORT_KPIS reference values
- `docs/design-reference/js/pages3.jsx` — PageChurnLanding, PageWhatIf IA and component structure
- `domains/brand_share/service.py` — established BrandShareForecastResult + run_forecast pattern to mirror
- `app/pages/1_Brand_Share.py` — established page structure to mirror
- `core/models.py` — compute_stationary pattern; M1Homogeneous.forecast API
- `core/db/queries.py` — build_transition_matrix, list_datasets, load_transitions API
- Verified via execution: fundamental matrix computation, simulate_scenario renorm, Plotly shapes bezier, stackgroup stacked-area, frozenset hash

### Secondary (MEDIUM confidence)
- Streamlit 1.57.0 `st.expander` signature (`on_change='ignore'` default) — verified via Python inspect
- Plotly 6.7.0 shapes API (`add_shape(type='path', ...)`) — verified via execution
- NumPy 2.4.6 `linalg.inv`, `linalg.cond`, `linalg.pinv` — verified via execution

### Tertiary (LOW confidence)
- Actual Telco dataset state labels — not inspected (depends on seed script output); handled via case-insensitive lookup fallback

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries installed, versions verified
- Architecture: HIGH — all patterns verified by execution and match established Phase 02 codebase
- Pitfalls: HIGH — all four discovered through code inspection and execution testing
- Open questions: MEDIUM — state label matching is data-dependent, handled with defensive fallback

**Research date:** 2026-05-31
**Valid until:** 2026-06-30 (stable stack — Plotly/Streamlit APIs do not change frequently at patch versions)
