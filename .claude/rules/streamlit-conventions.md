# Streamlit Conventions

## Page Structure

```
app/
├── Home.py                       # Landing — runs at root /
├── pages/                        # Streamlit auto-discovers (numeric prefix = order)
│   ├── 1_Brand_Share.py
│   ├── 2_Churn.py
│   ├── 3_Reports.py
│   └── 4_Settings.py
├── components/                   # Reusable Streamlit components
│   ├── kpi_card.py
│   ├── transition_heatmap.py
│   ├── monte_carlo_fan.py
│   └── empty_state.py
└── styles/
    └── theme.css                 # Custom CSS injected via st.markdown
```

## Page File Template

```python
"""Brand Share Forecaster page."""
import streamlit as st

from app.components import kpi_card, transition_heatmap
from app.styles import inject_theme
from domains.brand_share import service

st.set_page_config(
    page_title="Brand Share — MarkovLens",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

# ── Header ──────────────────────────────────────────────
st.title("Brand Share Forecaster")
st.caption("Predict market share evolution using Markov chain models")

# ── Controls ────────────────────────────────────────────
with st.container():
    col_dataset, col_model, col_horizon, col_run = st.columns([3, 2, 2, 1])
    dataset_id = col_dataset.selectbox("Dataset", options=service.list_datasets())
    model_type = col_model.selectbox("Model", ["m1", "m2", "m3"])
    horizon = col_horizon.slider("Months ahead", 1, 24, 12)
    run = col_run.button("Run Forecast", type="primary", use_container_width=True)

# ── Results ─────────────────────────────────────────────
if run:
    with st.spinner("Running forecast..."):
        result = service.run_forecast(dataset_id, model_type, horizon)
    render_results(result)
```

## Session State Rules

- Prefix keys with page name: `st.session_state["brand_share.forecast"]` not `st.session_state["forecast"]`
- Initialize defaults in a single block at top of page
- Use `@st.cache_data` for pure functions, `@st.cache_resource` for connections (DuckDB)

```python
# ✅ Cache DB connection
@st.cache_resource
def get_db_connection():
    return duckdb.connect("data/markovlens.duckdb")

# ✅ Cache pure forecast (auto-invalidated on input change)
@st.cache_data
def cached_forecast(dataset_id: str, model_type: str, horizon: int) -> ForecastResult:
    return service.run_forecast(dataset_id, model_type, horizon)
```

## Layout Patterns

### KPI Strip
```python
cols = st.columns(4)
for col, kpi in zip(cols, kpis):
    with col:
        kpi_card(label=kpi.label, value=kpi.value, delta=kpi.delta, sparkline=kpi.spark)
```

### Tabs for Sub-Views
```python
tab_overview, tab_matrix, tab_simulate, tab_compare = st.tabs([
    "Overview", "Transition Matrix", "Monte Carlo", "Model Comparison"
])
with tab_matrix:
    render_transition_heatmap(matrix)
```

### Two-Column Detail View
```python
main, side = st.columns([0.65, 0.35], gap="large")
main.plotly_chart(fan_chart, use_container_width=True)
with side:
    st.subheader("Final State Distribution")
    side.plotly_chart(histogram, use_container_width=True)
```

## Plotly Theming

All charts use the project palette + theme defined in `app/styles/plotly_theme.py`:

```python
import plotly.io as pio
from app.styles.plotly_theme import MARKOVLENS_THEME
pio.templates["markovlens"] = MARKOVLENS_THEME
pio.templates.default = "markovlens"
```

Chart constraints:
- Title via `fig.update_layout(title=...)` — never hard-code in HTML
- Axis titles short (`"Probability"` not `"Probability of transition"`)
- Hover templates use the project number formatting (`Rp 1.2M` not `1,200,000`)
- Use `use_container_width=True` always — never fixed widths

## Custom CSS

Inject via `st.markdown(..., unsafe_allow_html=True)` from `app/styles/theme.css`:

```python
def inject_theme() -> None:
    css = Path("app/styles/theme.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
```

Use CSS variables matching the design tokens from the design system.

## Empty States

Every list/table view must handle empty data:

```python
if not results:
    empty_state(
        icon="📊",
        title="No forecasts yet",
        description="Click 'Run Forecast' to generate your first projection.",
        action=("Run forecast now", lambda: st.session_state.update(run_forecast=True)),
    )
    return
```

## Loading States

- **Spinner** for < 5s operations: `with st.spinner("..."):`
- **Progress bar** for > 5s with known steps:
  ```python
  progress = st.progress(0)
  for i, step in enumerate(steps):
      do_step()
      progress.progress((i + 1) / len(steps))
  ```
- **Status** for unknown duration:
  ```python
  with st.status("Running simulation...", expanded=False) as status:
      ...
      status.update(label="Done", state="complete")
  ```

## Error Handling in UI

```python
try:
    result = service.run_forecast(...)
except DatasetTooSparseError as e:
    st.error(f"Not enough data: {e}")
    st.info("Try selecting a longer date range or merging sparse states.")
    return
except Exception as e:
    st.error(f"Unexpected error: {e}")
    if st.session_state.get("dev_mode"):
        st.exception(e)
    return
```

## DO NOT

- ❌ Mix Markov computation into page files — all logic in `domains/*/service.py`
- ❌ Use `st.experimental_*` APIs — deprecated, may break
- ❌ Hard-code colors in Plotly — use theme template
- ❌ Skip `set_page_config()` — must be first Streamlit call per page
- ❌ Write to DuckDB from page files — go through `domains/*/service.py`
