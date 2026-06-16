"""MarkovLens — Home / Landing page."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so `from app.X`, `from core.X`, `from domains.X` resolve.
# Streamlit adds the entry-script dir (app/) to sys.path, not the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st  # noqa: E402

st.set_page_config(
    page_title="MarkovLens — Multi-Domain Forecasting Workbench",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.components.empty_state import empty_state  # noqa: E402
from app.components.kpi_card import kpi_card  # noqa: E402
from app.db import get_db  # noqa: E402
from app.styles import inject_theme, register_theme  # noqa: E402
from core.db.queries import get_home_kpis, list_recent_forecasts  # noqa: E402

register_theme()
inject_theme()

DOMAIN_ICON: dict[str, str] = {"brand_share": "📈", "churn": "🔁"}
DOMAIN_COLOR: dict[str, str] = {"brand_share": "#4338CA", "churn": "#059669"}
MODEL_BADGE_COLOR: dict[str, str] = {"m1": "#6366F1", "m2": "#0891B2", "m3": "#7C3AED"}


# ── Header ──────────────────────────────────────────────────
st.title("MarkovLens")
st.caption("*Same math, different stories — Markov chains applied to real business decisions.*")
st.markdown("---")

# ── KPI Strip (real data) ────────────────────────────────────
try:
    _db = get_db()
    _kpis = get_home_kpis(_db)
    _kpi_error: str | None = None
except Exception as e:
    _kpis = None
    _kpi_error = str(e)

col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card(
        label="Active Models",
        value="3",
        icon="📦",
        tooltip="m1 Homogeneous, m2 Time-varying, m3 Extended (Chan 2015)",
        accent="var(--chart-1)",
    )
with col2:
    kpi_card(
        label="Datasets Registered",
        value=str(_kpis.dataset_count) if _kpis else "—",
        icon="🗄️",
        accent="var(--chart-2)",
    )
with col3:
    mape_val = f"{_kpis.avg_mape:.2f}" if (_kpis and _kpis.avg_mape is not None) else "—"
    kpi_card(
        label="Last Forecast (MAPE)",
        value=mape_val,
        unit="%" if (_kpis and _kpis.avg_mape is not None) else "",
        tooltip="Mean Absolute Percentage Error — lower is better",
        accent="var(--chart-4)",
    )
with col4:
    kpi_card(
        label="Simulations Run",
        value=str(_kpis.sim_run_count) if _kpis else "—",
        tooltip="Total Monte Carlo paths across all sessions",
        accent="var(--chart-6)",
    )

if _kpi_error:
    st.warning(f"Could not load KPIs from database: {_kpi_error}")

st.markdown("---")

# ── Two-column intro + Quick Actions ─────────────────────────
left, right = st.columns([0.6, 0.4])

with left:
    st.subheader("What is MarkovLens?")
    st.markdown("""
    MarkovLens is an interactive forecasting workbench that applies **Markov chain models** to two real business problems:

    1. **Brand Share Forecaster** — predict e-commerce brand market share evolution over 6-12 months
    2. **Customer Churn States** — model telco customers as states (Active → At-Risk → Churned → Reactivated) and forecast retention

    Built on academic foundation ([Chan 2015, IJICIC](docs/MARKOV-MODELS.md)) with modern Monte Carlo calibration techniques (10,000-path simulation, longshot-bias adjustment, walk-forward validation).
    """)

with right:
    st.subheader("Quick Actions")
    st.page_link(
        "pages/1_Brand_Share.py", label="📈 Run Brand Share Forecast", use_container_width=True
    )
    st.page_link("pages/2_Churn.py", label="🔁 Analyze Customer Churn", use_container_width=True)

st.markdown("---")

# ── Recent Forecasts ─────────────────────────────────────────
st.subheader("Recent Forecasts")
try:
    _db2 = get_db()
    _recent = list_recent_forecasts(_db2, n=5)
except Exception:
    _recent = []

if not _recent:
    empty_state(
        icon="📊",
        title="No forecasts yet",
        description="Click **Run Brand Share Forecast** or **Analyze Customer Churn** above to generate your first projection.",
    )
else:
    _rows = []
    for fc in _recent:
        _icon = DOMAIN_ICON.get(fc.domain, "📊")
        _mape_str = f"{fc.mape:.2f}% MAPE" if fc.mape is not None else "—"
        _date_str = fc.created_at.strftime("%Y-%m-%d %H:%M") if fc.created_at else "—"
        _rows.append(
            {
                "": _icon,
                "Dataset": fc.dataset_name,
                "Model": fc.model_type,
                "Run at": _date_str,
                "MAPE": _mape_str,
            }
        )
    import pandas as pd

    st.dataframe(
        pd.DataFrame(_rows),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# ── Methodology card ─────────────────────────────────────────
with st.expander("Methodology — how MarkovLens works"):
    st.markdown("""
    Every forecast follows the same 5-step pipeline:

    1. **Build the transition matrix** — discretize historical data into states, compute switching probabilities
    2. **Run Monte Carlo** — simulate 10,000 random paths through the matrix
    3. **Calibrate against bias** — apply Becker (2026) longshot adjustment
    4. **Compute metrics** — MAPE / Brier score on walk-forward backtest
    5. **Visualize** — confidence bands, distributions, what-if scenarios

    See [docs/MARKOV-MODELS.md](https://github.com/afrizzal/markovlens/blob/master/docs/MARKOV-MODELS.md)
    and [docs/MONTE-CARLO.md](https://github.com/afrizzal/markovlens/blob/master/docs/MONTE-CARLO.md) for the math.
    """)

# ── Footer ──────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption("MarkovLens v0.1.0 — Built with Streamlit + DuckDB + Plotly")
