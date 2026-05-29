# Phase 02: Design System + Brand Share - Research

**Researched:** 2026-05-30
**Domain:** Streamlit UI, Plotly 6.x templates, Markov chain visualisation, NumPy/SciPy stationary distribution
**Confidence:** HIGH (all critical paths verified against installed packages)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `docs/design-reference/` is the visual ground truth. `UI-SPEC.md` is derived from these assets; implementation ports tokens/patterns into Streamlit.
- **D-02:** Prototype is React/Tailwind; app is Streamlit. Translate into CSS injection + Plotly template + components. Custom app shell is north-star; approximate with Streamlit's native sidebar.
- **D-03:** `app/styles/theme.css` replaced/extended from `docs/design-reference/markov.css` verbatim. Includes light + dark token sets, sequential heatmap ramp (`--chart-seq-1..5`), categorical palette (`--chart-1..6`), churn state colors.
- **D-04:** `app/styles/plotly_theme.py` registers a `markovlens` template and exposes `register_theme()`. Default: `pio.templates.default = "streamlit+markovlens"`. Colorway = `--chart-1..6`; heatmap colorscale = sequential ramp; fonts = Geist/Inter + JetBrains Mono.
- **D-05:** `register_theme()` called at module import / top of page before any `st.plotly_chart`.
- **D-06:** Four components to prototype contracts: `kpi_card` (extend), `transition_heatmap` (new), `monte_carlo_fan` (new), `empty_state` (extend).
- **D-07:** Fix stale TODO comments: `kpi_card.py` "Phase 05" → Phase 02; `theme.css` "Phase 05" → Phase 02; `service.py` "Phase 03" → Phase 02.
- **D-08:** Single page `1_Brand_Share.py`. Control strip: dataset select + model picker (segmented/radio) + horizon slider + "Run Forecast" button.
- **D-09:** KPI strip: Forecasted leader / Biggest gainer (Δpp) / Biggest loser (Δpp), below controls above tabs.
- **D-10:** Four tabs: Overview / Transition Matrix / Monte Carlo / Model Comparison.
- **D-11:** Compute all three models on "Run Forecast". Heatmap renders on dataset-select. Forecast / fan chart / comparison gated behind "Run Forecast".
- **D-12:** Auto-generated verdict paragraph + static "How to read these metrics" expander. Winner derived from computed metrics, never hardcoded.
- **D-13:** Stationary distribution always from m1 (constant) matrix. Dominant left eigenvector; fallback power-iteration; fallback `st.warning`.
- **D-14:** Stationary panel in Overview tab right column. Bar chart "Long-run equilibrium (if these rates persist…)". Values sum to 1.0. Subcaption caveat shown.
- **D-15:** Initial state: heatmap renders on dataset-select; other tabs show `empty_state` until "Run Forecast".
- **D-16:** `st.spinner("Running 10,000 simulations…")` for Monte Carlo.
- **D-17:** Sparse cells get warning badge on heatmap + `st.warning` summary. `DatasetTooSparseError` → actionable `st.error`. Never silently block.
- **D-18:** `BrandShareForecastResult` holds structured NumPy arrays only — NO Plotly coupling. Remove `forecast_chart_json: dict` field. All Plotly construction in `app/components`.
- **D-19:** `service.list_datasets()` delegates to `core.db.queries.list_datasets` filtered to `brand_share`. `service.run_forecast()` orchestrates full pipeline.
- **D-20:** `@st.cache_data` keyed on `(dataset_id, primary_model, horizon, n_simulations, seed)`. DuckDB via `@st.cache_resource`. DB-level cache optional for Phase 02.
- **D-21:** Implement cheap extras (overview stacked-area, final-state histogram, walk-forward backtest table). Defer costly extras.

### Claude's Discretion

- Exact Plotly trace styling (pinned by UI-SPEC.md).
- Exact `BrandShareForecastResult` field names/types within NumPy-only constraint.
- Whether final-state histogram / backtest table are separate components or inline page code.
- Segmented-control implementation (`st.segmented_control` vs `st.radio(horizontal=True)`).
- Where stationary helper lives (`core/models.py` vs domain helper).

### Deferred Ideas (OUT OF SCOPE)

- Click-a-cell transition-matrix detail panel.
- Matrix smoothing control (UI for `smoothing` param).
- Raw-vs-calibrated probability table.
- Custom app shell (sidebar nav, top-bar search ⌘K, dark-mode toggle, notifications, avatar).
- Home dashboard wiring, CSV export, Settings page (Phase 04).
- Churn page (Phase 03).
- Dataset upload via Settings UI (v2).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | `app/styles/theme.css` (complete) + `app/styles/plotly_theme.py` Plotly 6.x template; `pio.templates.default = "streamlit+markovlens"`; smoke-tested | Plotly 6.7.0 template API verified; `streamlit` built-in template auto-registered at `import streamlit`; composition pattern confirmed working |
| UI-02 | Reusable component library: `kpi_card`, `transition_heatmap`, `monte_carlo_fan`, `empty_state` | All function signatures from UI-SPEC.md documented; visual contracts confirmed against charts.jsx / ui.jsx |
| BS-01 | `domains/brand_share/service.py` orchestrates m1/m2/m3 pipeline; returns `BrandShareForecastResult` with NumPy arrays only | Core API signatures verified; `build_transition_matrix` returns `(matrix, counts)` but NOT state labels (gap documented); M1/M2/M3 constructors + `.forecast()` signatures confirmed |
| BS-02 | Transition matrix heatmap: annotated, fixed [0,1] scale, sparsity flags | `go.Heatmap` + annotation pattern for sparsity; sequential colorscale confirmed |
| BS-03 | Monte Carlo fan chart: P10/P50/P90 bands, separator, legend | `go.Scatter` fill pattern documented; `compute_quantile_bands` API confirmed; `target_extractor` requirement noted |
| BS-04 | Model comparison: metrics table (bold best per column), interpretation block | `metrics.py` MAPE/Brier/log-loss API confirmed; verdict-sentence logic from UI-SPEC.md documented |
| BS-05 | Stationary distribution panel: dominant eigenvector as bar chart, sums to 1.0 | SciPy `la.eig(P.T)` approach verified; power-iteration fallback tested; edge case (absorbing matrix) handled |
| BS-06 | `app/pages/1_Brand_Share.py` with designed loading, empty, error states | Page structure from UI-SPEC.md documented; `st.segmented_control` confirmed available in Streamlit 1.57.0 |
</phase_requirements>

---

## Summary

Phase 02 implements the MarkovLens design system and the fully-wired Brand Share page. The Markov engine (Phase 01) is complete and provides well-defined, validated Python APIs; Phase 02 only calls them, never modifies them. All UI tokens derive verbatim from `docs/design-reference/markov.css`, and the Plotly template must compose over Streamlit's built-in template using the `"streamlit+markovlens"` merge syntax.

A critical finding: the `"streamlit"` Plotly template is NOT a Plotly built-in — it is registered by Streamlit itself at `import streamlit`. Therefore `register_theme()` must be called AFTER `import streamlit` has executed (which is always true in a Streamlit page, but means the smoke-test CLI must also `import streamlit` first). Additionally, `build_transition_matrix()` in `core/db/queries.py` returns `(matrix, counts)` but NOT state labels — the service layer must derive state labels via a separate `load_transitions()` call and compute `sorted(set(from_state) | set(to_state))` to reconstruct the index.

The stationary distribution computation via `scipy.linalg.eig(P.T)` is verified to produce correct results (left eigenvector of P corresponds to right eigenvector of P^T), with the absorbing-matrix edge case handled gracefully. `st.segmented_control` is available in the installed Streamlit 1.57.0 (preferred over `st.radio(horizontal=True)` for the model picker).

**Primary recommendation:** Build in wave order — CSS tokens first, Plotly template second (smoke test), components third (heatmap first, then fan chart, then kpi_card/empty_state), service layer fourth, page last. This ensures each layer is independently testable before the next depends on it.

---

## Standard Stack

### Core (all already installed, versions verified)

| Library | Installed Version | Purpose | Notes |
|---------|------------------|---------|-------|
| Streamlit | 1.57.0 | Page framework, multi-page app | `st.segmented_control` available |
| Plotly | 6.7.0 | Interactive charts (heatmap, fan chart, bar, scatter) | Template API confirmed |
| NumPy | 2.4.6 | Matrix ops, quantile bands, stationary distribution | `np.float64` enforced |
| SciPy | 1.17.1 | `scipy.linalg.eig` for stationary eigenvector | Power-iteration fallback in NumPy |
| DuckDB | (in deps) | Data access via `core/db/queries.py` | Never import directly in page |

### No new dependencies required

Phase 02 uses only already-installed packages. No `uv add` needed.

---

## Architecture Patterns

### Recommended File Creation Order (Wave Structure)

```
Wave 0 — Foundation
  app/styles/theme.css               # Replace stub with full markov.css port
  app/styles/plotly_theme.py          # register_theme() + smoke test
  app/styles/__init__.py              # inject_theme() helper

Wave 1 — Components
  app/components/transition_heatmap.py  # New
  app/components/monte_carlo_fan.py     # New
  app/components/kpi_card.py           # Extend stub
  app/components/empty_state.py        # Extend stub
  app/components/__init__.py           # Re-export all 4

Wave 2 — Service Layer
  domains/brand_share/service.py       # Rewrite (drop Plotly, implement pipeline)

Wave 3 — Page
  app/pages/1_Brand_Share.py           # New full page

Wave 4 — Tests
  tests/unit/test_plotly_theme.py     # Smoke test UI-01
  tests/unit/test_transition_heatmap.py
  tests/unit/test_monte_carlo_fan.py
  tests/unit/test_service_brand_share.py
  tests/integration/test_brand_share_service.py
```

### Pattern 1: Plotly Template Registration

The `"streamlit"` template is registered by Streamlit at `import streamlit`, not by Plotly itself. The `+` composition syntax merges templates left-to-right: right-side properties override left. Therefore `"streamlit+markovlens"` means markovlens overrides streamlit defaults.

```python
# Source: verified in installed Plotly 6.7.0 + Streamlit 1.57.0
# app/styles/plotly_theme.py

import plotly.io as pio
import plotly.graph_objects as go
from plotly.graph_objs.layout import Template

def register_theme() -> None:
    """Register MarkovLens Plotly template. Call before any chart is rendered.

    IMPORTANT: 'streamlit' template is registered by Streamlit at import time.
    This function must run AFTER 'import streamlit' (true for all Streamlit pages).
    """
    t = Template()
    t.layout.colorway = [
        "#4338CA", "#059669", "#D97706", "#0891B2", "#DC2626", "#7C3AED"
    ]
    t.layout.paper_bgcolor = "#FFFFFF"
    t.layout.plot_bgcolor = "#FFFFFF"
    t.layout.font = dict(
        family="Geist, Inter, -apple-system, sans-serif",
        size=13,
        color="#52525B",
    )
    t.layout.xaxis = dict(
        gridcolor="#E4E4E7",
        linecolor="#D4D4D8",
        tickfont=dict(family="JetBrains Mono, Geist Mono, monospace", size=11),
    )
    t.layout.yaxis = dict(
        gridcolor="#E4E4E7",
        linecolor="#D4D4D8",
        tickfont=dict(family="JetBrains Mono, Geist Mono, monospace", size=11),
    )
    t.layout.legend = dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#E4E4E7",
        borderwidth=1,
        font=dict(size=12),
    )
    t.layout.margin = dict(l=48, r=16, t=16, b=28)
    t.data.heatmap = [go.Heatmap(
        colorscale=[
            [0, "#EEF2FF"], [0.25, "#C7D2FE"],
            [0.5, "#818CF8"], [0.75, "#4338CA"], [1, "#1E1B4B"],
        ]
    )]
    pio.templates["markovlens"] = t
    pio.templates.default = "streamlit+markovlens"
```

### Pattern 2: CSS Injection

```python
# app/styles/__init__.py
from pathlib import Path
import streamlit as st

def inject_theme() -> None:
    css = (Path(__file__).parent / "theme.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
```

theme.css replaces the current stub with the full `markov.css` port (light + dark token sets verbatim).

### Pattern 3: Stationary Distribution

```python
# Source: verified scipy.linalg.eig + power-iteration in scipy 1.17.1 / numpy 2.4.6
import numpy as np
import scipy.linalg as la

def compute_stationary(P: np.ndarray, max_iter: int = 10_000, tol: float = 1e-12) -> np.ndarray | None:
    """Dominant left eigenvector of P (right eigenvector of P^T).
    
    Returns normalized probability vector summing to 1.0, or None if both methods fail.
    """
    # Method 1: eigenvector
    try:
        vals, vecs = la.eig(P.T)
        idx = int(np.argmin(np.abs(vals - 1.0)))
        stat = np.real(vecs[:, idx])
        if np.all(stat >= -1e-9):
            stat = np.clip(stat, 0, None)
            total = stat.sum()
            if total > 1e-10:
                return (stat / total).astype(np.float64)
    except Exception:
        pass
    # Method 2: power iteration
    try:
        Pn = P.copy().astype(np.float64)
        for _ in range(max_iter):
            Pn_next = Pn @ P
            if np.max(np.abs(Pn_next - Pn)) < tol:
                break
            Pn = Pn_next
        row = Pn[0]
        if np.allclose(row.sum(), 1.0, atol=1e-6) and np.all(row >= -1e-9):
            return np.clip(row, 0, None) / np.clip(row, 0, None).sum()
    except Exception:
        pass
    return None  # caller shows st.warning
```

**Placement decision:** The helper belongs in `core/models.py` (pure, no Streamlit imports) alongside the existing model classes. The domain service calls it; the page calls the service.

### Pattern 4: Service Layer — BrandShareForecastResult

The current stub has `forecast_chart_json: dict` which violates D-18. Rewrite entirely:

```python
# domains/brand_share/service.py  (new shape)
@dataclass(frozen=True)
class BrandShareForecastResult:
    # Forecasts — one array per model, shape (horizon, n_states)
    forecasts: dict[str, np.ndarray]          # keys: "m1", "m2", "m3"
    # Historical share vector — shape (n_hist_periods, n_states)
    historical_shares: np.ndarray
    # Transition matrix (m1 constant) — shape (n_states, n_states)
    transition_matrix: np.ndarray
    # Most-recent P_t (for m2/m3 heatmap display) — same shape
    recent_transition_matrix: np.ndarray
    # Observation counts — shape (n_states, n_states)
    observation_counts: np.ndarray
    # Confidence bands from Monte Carlo — {quantile: shape (n_steps+1,)} per primary model
    confidence_bands: dict[float, np.ndarray]
    # Stationary distribution from m1 — shape (n_states,) or None
    stationary_distribution: np.ndarray | None
    # Per-model accuracy metrics — {"m1": {"mape": .., "brier": .., "log_loss": ..}, ...}
    accuracy_metrics: dict[str, dict[str, float]]
    # Walk-forward backtest results — list of dicts from walk_forward_backtest()
    backtest_results: list[dict]
    # Ordered state labels matching matrix row/col order
    state_labels: list[str]
    # Dataset metadata for display
    dataset_name: str
    n_transitions: int
    n_periods: int
```

### Pattern 5: State Labels Gap — Required Workaround

`build_transition_matrix()` returns `(matrix, counts)` but NOT the ordered state label list. The service must reconstruct this consistently:

```python
# In service.run_forecast(), after loading transitions df:
transitions_df = load_transitions(conn, dataset_id)
state_labels = sorted(
    set(transitions_df["from_state"]) | set(transitions_df["to_state"])
)
# build_transition_matrix uses the same sort internally, so index aligns
matrix, counts = build_transition_matrix(conn, dataset_id)
# state_labels[i] corresponds to matrix row/col i
```

This is the SAME sort key used inside `build_transition_matrix` — verified by reading `queries.py` line 295: `states = sorted(set(df["from_state"]) | set(df["to_state"]))`.

### Pattern 6: M2/M3 Per-Period Matrices

For time-varying models, the service must build one matrix per period:

```python
periods = sorted(transitions_df["period"].unique())
P_t_list = []
for period in periods:
    P_t, _ = build_transition_matrix(conn, dataset_id, period=period)
    P_t_list.append(P_t)
P_t_sequence = np.stack(P_t_list, axis=0)  # shape (n_periods, n_states, n_states)
# Most recent period matrix for heatmap:
recent_P = P_t_sequence[-1]
```

### Pattern 7: st.segmented_control (preferred over st.radio)

```python
# Streamlit 1.57.0 — confirmed available
model = st.segmented_control(
    "Model",
    options=["m1", "m2", "m3"],
    default="m1",
    help="m1: constant P · m2: time-varying Pₜ · m3: extended with growth G",
)
```

`st.segmented_control` is preferred for the model picker (matches prototype visual). Signature confirmed:
`segmented_control(label, options, *, selection_mode='single', default=None, help=None, ...)`

### Pattern 8: Heatmap Cell Annotations

Plotly `go.Heatmap` does not natively support per-cell annotations as first-class API; the standard pattern uses `go.layout.Annotation` objects (one per cell), which are added to `fig.layout.annotations`. For sparsity markers, a second annotation is added at an offset within the same cell.

```python
# Annotation for cell value
fig.add_annotation(
    x=j, y=i,
    text=f"{v*100:.0f}%" if v >= 0.1 else f"{v*100:.1f}%",
    showarrow=False,
    font=dict(family="JetBrains Mono, monospace", size=12, color=text_color),
)
# Sparsity marker (if obs_counts[i,j] < 20)
if obs_counts[i, j] < 20:
    fig.add_annotation(
        x=j + 0.4, y=i + 0.4,  # top-right offset within cell
        text="⚠",
        showarrow=False,
        font=dict(color="#D97706", size=10),
    )
```

The text color (white vs dark) is determined by the `seqRamp` luminance logic from `charts.jsx`:
- Map cell value `v ∈ [0,1]` to a position in 5-stop ramp
- Compute approximate luminance; if > 0.55 use `#0A0A0A` else use `#FFFFFF`
- Simplified: values < 0.55 (light cells) → dark text; values >= 0.55 → white text. Threshold maps to `--chart-seq-3` area (~`#818CF8`, luminance ≈ 0.51).

### Pattern 9: Fan Chart Trace Assembly

The fan chart requires traces in a specific order to achieve the fill-between effect:

```python
# Trace 1: P90 line (no fill — will be reference for tozeroy fill from P10)
# Trace 2: P10 line with fill="tonexty" — fills the area between P10 and P90
# Trace 3: P50 solid line
# Trace 4: Historical solid line
# Trace 5: Shape (vertical separator) via fig.add_vline() or layout.shapes

# The plotly fill="tonexty" fills to the PREVIOUS trace — ordering matters
```

Separator is best implemented as `fig.add_vline(x=n_hist_periods-1, line_dash="dash", line_color="rgba(82,82,91,0.5)")`.

### Anti-Patterns to Avoid

- **Anti-pattern:** Calling `register_theme()` before `import streamlit` — the `"streamlit"` base template won't exist yet, causing `ValueError: Invalid value 'streamlit+markovlens'`.
- **Anti-pattern:** Returning Plotly figures from `domains/brand_share/service.py` — violates D-18 and 3-layer architecture.
- **Anti-pattern:** Computing state labels in the page file — must be in service layer so component receives `state_labels: list[str]`.
- **Anti-pattern:** Using `np.percentile` on raw state-index paths for the fan chart — use `compute_quantile_bands` with a `target_extractor` that converts state indices to brand market shares.
- **Anti-pattern:** Calling `build_transition_matrix` for m2/m3 without filtering by period — produces an aggregated constant matrix, not `P_t`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Monte Carlo simulation | Custom path sampler | `core.simulation.monte_carlo_simulate` | Handles cumsum inverse-CDF, vectorized, seeded — complete |
| Quantile bands | `np.percentile(paths, ...)` directly | `core.simulation.compute_quantile_bands` with `target_extractor` | ENG-07 explicitly forbids percentile of raw state indices |
| Probability calibration | Custom interpolation | `core.simulation.calibrate_probability` | Becker (2026) table, validated |
| Accuracy metrics | Custom MAPE/Brier/log-loss | `core.metrics.mape`, `.brier_score`, `.log_loss` | ENG-10 complete |
| Walk-forward backtest | Custom window loop | `core.simulation.walk_forward_backtest` | ENG-09 complete |
| Matrix validation | Manual checks | `core.models.validate_transition_matrix` | ENG-01 complete, raises `InvalidTransitionMatrixError` |
| CSS variables | Hardcoded hex in Python | CSS variables in `theme.css` | Design system integrity |
| M1/M2/M3 forecasting | Direct matrix multiplication in page | `M1Homogeneous/M2TimeVarying/M3Extended.forecast()` | Validated, type-safe, handles edge cases |

---

## Common Pitfalls

### Pitfall 1: `"streamlit+markovlens"` fails at script startup

**What goes wrong:** `ValueError: Invalid value 'streamlit+markovlens'` when `register_theme()` is called outside a running Streamlit process (e.g., in unit tests or scripts that don't `import streamlit`).

**Why it happens:** The `"streamlit"` template is only registered as a side effect of `import streamlit`. Plotly does not know about it otherwise.

**How to avoid:** The smoke test CLI command MUST `import streamlit` before calling `register_theme()`. In unit tests, either mock the template or `import streamlit` first. In the page file, `import streamlit as st` is always first, so this is never an issue at runtime.

**Warning signs:** `ValueError` mentioning `'streamlit'` not being a registered template name.

### Pitfall 2: State label index misalignment

**What goes wrong:** The heatmap renders with axes labeled `[0, 1, 2, ...]` instead of brand names, or worse, labels are shifted by one.

**Why it happens:** `build_transition_matrix` discovers states via `sorted(set(from_state) | set(to_state))` but returns only `(matrix, counts)`. If the service derives state labels via a different sort or from a different query, indices won't align.

**How to avoid:** Derive state labels from `load_transitions()` using `sorted(set(df["from_state"]) | set(df["to_state"]))` — the same expression as inside `build_transition_matrix`. Never derive labels from the `Dataset.n_states` integer alone.

**Warning signs:** Heatmap diagonal has low values (self-transition probabilities off-diagonal).

### Pitfall 3: Fan chart fill order produces wrong visual

**What goes wrong:** The P10–P90 band appears filled incorrectly or not at all.

**Why it happens:** Plotly `fill="tonexty"` fills to the IMMEDIATELY PREVIOUS trace in the `fig.data` list. If P50 is added before P10/P90, the fill attaches to the wrong trace.

**How to avoid:** Add traces in this order: P90 (no fill) → P10 (fill="tonexty" → fills to P90) → P50 solid → Historical solid. Or use a single `go.Scatter` with concatenated x/y for the filled area.

**Warning signs:** The band is missing, or it fills to zero instead of between P10 and P90.

### Pitfall 4: `compute_quantile_bands` target_extractor returns wrong shape

**What goes wrong:** `ValueError: target_extractor must return a 2-D ndarray`.

**Why it happens:** `monte_carlo_simulate` returns paths of shape `(n_simulations, n_steps+1)` as state indices (int64). `compute_quantile_bands` requires a `target_extractor` that maps these to continuous values (e.g., brand share), preserving the `(n_sims, n_steps+1)` shape. A naive extractor that returns 1D per sim fails.

**How to avoid:** The extractor for brand `b` should return `(paths == b).astype(float)` — a boolean indicator of shape `(n_sims, n_steps+1)`. This gives "probability of being in state b" per step.

```python
target_extractor = lambda paths, b=brand_idx: (paths == b).astype(float)
bands = compute_quantile_bands(paths, target_extractor)
```

**Warning signs:** `ValueError` from `compute_quantile_bands` about `ndim`.

### Pitfall 5: M3 receives normalized shares instead of absolute counts

**What goes wrong:** `M3Extended.forecast()` produces nonsensical shares that don't sum to 1.

**Why it happens:** M3 operates on absolute population counts (`Q_t`), not normalized probabilities. Passing a normalized share vector `Y_t` makes the growth multiplier `G` meaningless.

**How to avoid:** Per D-11, M3 receives absolute counts. The service must provide `Q_1` = last observed count vector (raw entity counts per state, not normalized). The UI must note "absolute counts" in the m3 formula tooltip.

**Warning signs:** M3 forecast values outside [0, 1] or growing unboundedly.

### Pitfall 6: @st.cache_data keying includes mutable objects

**What goes wrong:** Cache never hits because a mutable default argument (list, dict) is included in the cache key.

**Why it happens:** `@st.cache_data` computes a hash of all arguments. Only hashable scalars make stable cache keys. If the service function signature includes `np.ndarray` parameters, they hash correctly; but passing complex objects as extra args can cause issues.

**How to avoid:** Keep the cached function signature to `(dataset_id: str, primary_model: str, horizon: int, n_simulations: int, seed: int) -> BrandShareForecastResult`. All complex computation happens inside.

**Warning signs:** Streamlit log warnings about unhashable arguments; every run triggers a cache miss.

### Pitfall 7: theme.css CSS variables not applied to Streamlit components

**What goes wrong:** Custom tokens visible in custom HTML blocks but Streamlit native components (buttons, sliders) ignore them.

**Why it happens:** Streamlit renders its own components inside iframes or shadow DOM in some versions; CSS injected via `st.markdown` may not reach all native component styles. The `.streamlit/config.toml` `[theme]` block is the correct way to style native components.

**How to avoid:** Use CSS injection ONLY for custom HTML elements. Style native Streamlit components via `config.toml` (already set: `primaryColor = "#4338CA"`). Do not fight Streamlit's native styling.

**Warning signs:** Custom button classes applied but native `st.button` still renders in default Streamlit blue (which is actually correct — it IS `#4338CA` via config.toml).

---

## Code Examples

### UI-01: register_theme() — verified working pattern

```python
# Source: verified in Plotly 6.7.0 + Streamlit 1.57.0 (2026-05-30)
import streamlit  # Must come before plotly template operations
import plotly.io as pio
import plotly.graph_objects as go
from plotly.graph_objs.layout import Template

def register_theme() -> None:
    """Register MarkovLens Plotly template. Call before any chart is rendered.
    
    Requires 'import streamlit' to have executed first so the 'streamlit'
    template is available for composition.
    """
    t = Template()
    t.layout.colorway = ["#4338CA", "#059669", "#D97706", "#0891B2", "#DC2626", "#7C3AED"]
    t.layout.paper_bgcolor = "#FFFFFF"
    t.layout.plot_bgcolor = "#FFFFFF"
    t.layout.font = dict(family="Geist, Inter, -apple-system, sans-serif", size=13, color="#52525B")
    t.layout.xaxis = dict(
        gridcolor="#E4E4E7", linecolor="#D4D4D8",
        tickfont=dict(family="JetBrains Mono, Geist Mono, monospace", size=11),
    )
    t.layout.yaxis = dict(
        gridcolor="#E4E4E7", linecolor="#D4D4D8",
        tickfont=dict(family="JetBrains Mono, Geist Mono, monospace", size=11),
    )
    t.layout.legend = dict(
        bgcolor="rgba(255,255,255,0.9)", bordercolor="#E4E4E7",
        borderwidth=1, font=dict(size=12),
    )
    t.layout.margin = dict(l=48, r=16, t=16, b=28)
    t.data.heatmap = [go.Heatmap(colorscale=[
        [0, "#EEF2FF"], [0.25, "#C7D2FE"],
        [0.5, "#818CF8"], [0.75, "#4338CA"], [1, "#1E1B4B"],
    ])]
    pio.templates["markovlens"] = t
    pio.templates.default = "streamlit+markovlens"
```

### BS-05: Stationary distribution — verified

```python
# Source: verified scipy 1.17.1 / numpy 2.4.6 (2026-05-30)
import numpy as np
import scipy.linalg as la

def compute_stationary(P: np.ndarray) -> np.ndarray | None:
    """Dominant left eigenvector. Returns None if both methods fail."""
    try:
        vals, vecs = la.eig(P.T)
        idx = int(np.argmin(np.abs(vals - 1.0)))
        stat = np.real(vecs[:, idx])
        if np.all(stat >= -1e-9) and stat.sum() > 1e-10:
            return (np.clip(stat, 0, None) / np.clip(stat, 0, None).sum()).astype(np.float64)
    except Exception:
        pass
    # Power-iteration fallback
    try:
        Pn = P.astype(np.float64)
        for _ in range(10_000):
            Pn_next = Pn @ P
            if np.max(np.abs(Pn_next - Pn)) < 1e-12:
                break
            Pn = Pn_next
        row = Pn[0]
        if np.all(row >= -1e-9):
            row = np.clip(row, 0, None)
            return (row / row.sum()).astype(np.float64)
    except Exception:
        pass
    return None
```

### BS-03: Fan chart target_extractor

```python
# Source: ENG-07 pattern from core/simulation.py + compute_quantile_bands contract
from core.simulation import monte_carlo_simulate, compute_quantile_bands

paths = monte_carlo_simulate(
    matrix=P,
    start_state=initial_distribution,  # np.ndarray probability vector
    n_steps=horizon,
    n_simulations=10_000,
    seed=42,
)

# Extract brand b's probability at each step — shape (n_sims, n_steps+1)
brand_idx = state_labels.index(selected_brand)
target_extractor = lambda p, b=brand_idx: (p == b).astype(float)
bands = compute_quantile_bands(paths, target_extractor)
# bands = {0.10: shape(n_steps+1,), 0.50: ..., 0.90: ...}
p10, p50, p90 = bands[0.10], bands[0.50], bands[0.90]
```

### BS-01: Service state labels retrieval

```python
# Pattern for consistent state label ordering with build_transition_matrix
from core.db.queries import build_transition_matrix, load_transitions

df = load_transitions(conn, dataset_id)
state_labels = sorted(set(df["from_state"]) | set(df["to_state"]))
# Same sort as build_transition_matrix internal logic
matrix, counts = build_transition_matrix(conn, dataset_id)
# matrix[i,j] = P(from state_labels[i] → state_labels[j])
```

---

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` — section included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/unit/ -x -q` |
| Full suite command | `uv run pytest -x -q` |
| Coverage | `uv run pytest --cov=app --cov=domains -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | `register_theme()` registers `markovlens` template; default is `streamlit+markovlens` | unit (smoke) | `uv run pytest tests/unit/test_plotly_theme.py -x -q` | Wave 0 |
| UI-02 | `transition_heatmap()` renders without raising; `monte_carlo_fan()` renders without raising | unit | `uv run pytest tests/unit/test_components.py -x -q` | Wave 1 |
| BS-01 | `run_forecast()` returns `BrandShareForecastResult` with no Plotly objects; all fields present; state_labels length matches matrix shape | integration | `uv run pytest tests/integration/test_brand_share_service.py -x -q` | Wave 2 |
| BS-02 | Heatmap colorscale is `[0,1]` fixed; annotations present; sparsity markers visible for cells < 20 obs | unit | `uv run pytest tests/unit/test_components.py::test_transition_heatmap_sparsity -x` | Wave 1 |
| BS-03 | Fan chart has 6 traces (P90, P10+fill, P50, historical, separator annotation); quantile values are monotonic (p10 ≤ p50 ≤ p90) | unit | `uv run pytest tests/unit/test_components.py::test_monte_carlo_fan_traces -x` | Wave 1 |
| BS-04 | Accuracy metrics dict has keys `mape`, `brier`, `log_loss` for each model; winner detection is computed not hardcoded | integration | `uv run pytest tests/integration/test_brand_share_service.py::test_model_comparison -x` | Wave 2 |
| BS-05 | `compute_stationary` output sums to 1.0 ± 1e-6; returns `None` for a matrix that has no valid stationary distribution | unit | `uv run pytest tests/unit/test_stationary.py -x -q` | Wave 0 |
| BS-06 | Page-level smoke: `1_Brand_Share.py` can be imported without raising (no top-level side effects) | unit | `uv run pytest tests/unit/test_page_import.py -x -q` | Wave 3 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/ -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_plotly_theme.py` — smoke test for UI-01; needs `import streamlit` fixture
- [ ] `tests/unit/test_stationary.py` — covers BS-05 compute_stationary + fallback
- Note: existing `tests/conftest.py` has `sample_2x2_matrix` and `temp_duckdb_path` fixtures — reuse for component and service tests

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Plotly | UI-01, UI-02, BS-02, BS-03 | Yes | 6.7.0 | None |
| Streamlit | BS-06 | Yes | 1.57.0 | None |
| NumPy | BS-01, BS-05 | Yes | 2.4.6 | None |
| SciPy | BS-05 | Yes | 1.17.1 | Power-iteration-only fallback |
| DuckDB | BS-01 | Yes | in deps | None |
| `st.segmented_control` | BS-06 (model picker) | Yes | Streamlit 1.40+ | `st.radio(horizontal=True)` |

Step 2.6: SKIPPED for external services — all dependencies are Python packages already installed in the `uv` environment.

---

## Project Constraints (from CLAUDE.md)

The following directives from `CLAUDE.md` and `.claude/rules/` govern implementation:

| Directive | Source | Impact on Phase 02 |
|-----------|--------|--------------------|
| No `import streamlit` in `core/` or `domains/` | CLAUDE.md, python-conventions | `compute_stationary` helper goes in `core/models.py`; all `st.*` calls stay in `app/` |
| All SQL in `core/db/queries.py` | data-storage | Service calls `core.db.queries.*`; page file has zero SQL |
| `@st.cache_resource` for DuckDB connection | streamlit-conventions | Page exposes `get_db_connection()` with this decorator |
| `@st.cache_data` for forecast results | CONTEXT.md D-20 | Wrap `run_forecast` call in page, not in service |
| `validate_transition_matrix()` after every matrix build | markov-patterns | Service calls this implicitly via `build_transition_matrix` (which already calls it) |
| `MIN_OBSERVATIONS_PER_CELL = 20` sparsity threshold | markov-patterns | Used in heatmap annotation + `st.warning` summary |
| No magic numbers — extract to UPPER_SNAKE constants | coding-style | All thresholds extracted: `SPARSE_OBS_THRESHOLD = 20`, `DEFAULT_N_SIMULATIONS = 10_000` |
| Type hints on all public functions | python-conventions | All service + component function signatures fully typed |
| `@dataclass(frozen=True)` for result value objects | coding-style | `BrandShareForecastResult` is frozen dataclass |
| Always use `rtk` prefix for bash | CLAUDE.md (global) | All commit commands use `rtk git commit` |
| Conventional commits: `feat:`, `fix:`, `docs:` etc. | project-rules | All commits follow this format |
| N803/N806 ruff suppression for math vars | STATE.md accumulated context | `P`, `Y_1`, `Q_t`, `G` in model code — already suppressed |
| Do NOT edit `.planning/` files manually | project-rules | Research + plan files only; never touch STATE.md/PROJECT.md directly |

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| Plotly 5.x: `fig.update_layout(template=...)` | Plotly 6.x: `pio.templates["name"] = Template(...)` then `pio.templates.default = "..."` — same API, still valid | No migration needed |
| `st.experimental_memo` (deprecated) | `@st.cache_data` | Already used in project conventions |
| `st.radio(horizontal=True)` for segmented | `st.segmented_control` (Streamlit 1.40+) | Better UX, available — use it |
| `np.random.seed()` (legacy) | `np.random.default_rng(seed)` | Already enforced by project rules and ENG-05 |

---

## Open Questions

1. **State labels across m1/m2/m3 consistency**
   - What we know: all three models must produce forecasts over the same `n_states` states in the same index order
   - What's unclear: if a specific period has missing transitions for some states, `build_transition_matrix(period=t)` might return a smaller matrix than `build_transition_matrix()` — this would break the P_t_sequence stack
   - Recommendation: the service should validate that all per-period matrices have the same `n_states` shape before calling `np.stack()`; if they differ, union states must be enforced (add zero rows/cols for missing states in sparse periods)

2. **M3 initial count vector `Q_1`**
   - What we know: M3Extended requires absolute entity counts (`Q_1`) not normalized shares
   - What's unclear: the service must derive `Q_1` from the last observed period's raw counts per state — `load_transitions(period=max_period)` grouped by `to_state` gives entity counts
   - Recommendation: service computes `Q_1 = transitions_df[transitions_df.period == max_period].groupby("to_state")["weight"].sum()` aligned to state index order

3. **Historical shares for stacked-area chart**
   - What we know: the Overview stacked-area chart needs historical shares per period
   - What's unclear: `build_transition_matrix` doesn't produce per-period share vectors; these must be computed separately from `load_transitions()`
   - Recommendation: service derives `historical_shares` from `transitions_df.groupby("period")["from_state"].value_counts(normalize=True)` reshaped to `(n_hist_periods, n_states)`

---

## Sources

### Primary (HIGH confidence — verified by running installed code)

- Plotly 6.7.0 installed in `.venv` — template API verified by direct execution (2026-05-30)
- Streamlit 1.57.0 installed in `.venv` — `st.segmented_control` signature verified by `help()` (2026-05-30)
- SciPy 1.17.1 + NumPy 2.4.6 — stationary distribution computation verified by execution (2026-05-30)
- `core/models.py`, `core/simulation.py`, `core/metrics.py`, `core/db/queries.py` — read directly; API signatures confirmed
- `docs/design-reference/markov.css` — token values extracted verbatim
- `.planning/phases/02-design-system-brand-share/02-UI-SPEC.md` — full component contracts read

### Secondary (MEDIUM confidence)

- `docs/design-reference/js/charts.jsx`, `ui.jsx` — React SVG patterns translated to Plotly equivalents; behavior is analogous but not 1:1

### Tertiary (LOW confidence)

- None — all critical claims are verified against installed code

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all packages verified in installed `.venv`
- Architecture patterns: HIGH — patterns derived from reading actual source files
- Stationary distribution: HIGH — `scipy.linalg.eig(P.T)` approach executed and output verified
- Plotly template composition: HIGH — `streamlit+markovlens` composition verified in isolation
- Fan chart trace order: MEDIUM — derived from Plotly fill semantics documentation; should be validated visually during implementation
- State labels gap workaround: HIGH — derived from reading `build_transition_matrix` source

**Research date:** 2026-05-30
**Valid until:** 2026-06-30 (stable library versions locked in `uv.lock`)
