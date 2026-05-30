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

_PAGES_DIR = Path(__file__).parent / "pages"

st.set_page_config(
    page_title="MarkovLens — Multi-Domain Forecasting Workbench",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Header ──────────────────────────────────────────────────
st.title("MarkovLens")
st.caption("*Same math, different stories — Markov chains applied to real business decisions.*")

st.markdown("---")

# ── KPI Strip (placeholder) ─────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Models", "3", help="m1 (Homogeneous), m2 (Time-varying), m3 (Extended)")
col2.metric("Domains", "2", help="Brand Share + Customer Churn")
col3.metric("Last Forecast Accuracy", "—", help="MAPE — run a forecast to populate")
col4.metric("Simulations Run", "0", help="Monte Carlo paths this month")

st.markdown("---")

# ── Two-column intro ────────────────────────────────────────
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
    st.page_link("pages/1_Brand_Share.py", label="📈 Run Brand Share Forecast", use_container_width=True)
    if (_PAGES_DIR / "2_Churn.py").exists():
        st.page_link("pages/2_Churn.py", label="🔁 Analyze Customer Churn", use_container_width=True)
    else:
        st.markdown("🔁 *Customer Churn — coming in Phase 03*")

st.markdown("---")

# ── Recent Forecasts (placeholder) ──────────────────────────
st.subheader("Recent Forecasts")
st.info("No forecasts yet. Click **Run Brand Share Forecast** above to generate your first projection.")

# ── Methodology card ────────────────────────────────────────
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
