"""Settings page for MarkovLens — dataset management and app preferences."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from app.X`, `from core.X`, `from domains.X` resolve.
# Streamlit adds the entry-script dir (app/) to sys.path, not the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

# ── Page Config (first Streamlit call — must precede all other st.* calls) ─
st.set_page_config(
    page_title="Settings — MarkovLens",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# local — imported after streamlit so register_theme() can compose the template
from app.components.empty_state import empty_state  # noqa: E402
from app.db import get_db  # noqa: E402
from app.styles import inject_theme, register_theme  # noqa: E402
from core.config import settings  # noqa: E402
from core.db.queries import list_datasets  # noqa: E402

# ── Register Plotly template before any chart is rendered (D-05) ───────────
register_theme()
inject_theme()

PAGE_NS: str = "settings"
APP_VERSION: str = "0.1.0"
DOMAIN_LABELS: dict[str, str] = {
    "brand_share": "Brand Share",
    "churn": "Customer Churn",
}


# ── Header ────────────────────────────────────────────────────────────────────
st.title("Settings")
st.caption("Manage datasets, appearance and forecasting defaults.")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_datasets, tab_prefs, tab_appearance, tab_about = st.tabs(
    ["Datasets", "Preferences", "Appearance", "About"]
)

# ── Datasets tab ──────────────────────────────────────────────────────────────
with tab_datasets:
    st.subheader("Registered datasets")

    try:
        _conn = get_db()
        _datasets = list_datasets(_conn)
        _db_error: str | None = None
    except Exception as e:
        _datasets = []
        _db_error = str(e)

    if _db_error:
        st.error(f"Could not load datasets: {_db_error}")
    elif not _datasets:
        empty_state(
            icon="🗄️",
            title="No datasets registered",
            description="Run the seed script to populate the database with the built-in datasets.",
        )
    else:
        _rows = []
        for ds in _datasets:
            _created = (
                ds.created_at.strftime("%Y-%m-%d %H:%M") if ds.created_at is not None else "—"
            )
            _rows.append(
                {
                    "Name": ds.name,
                    "Domain": DOMAIN_LABELS.get(ds.domain, ds.domain),
                    "Rows": ds.row_count,
                    "States": ds.n_states,
                    "Created": _created,
                }
            )
        st.dataframe(
            pd.DataFrame(_rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rows": st.column_config.NumberColumn(format="%d"),
                "States": st.column_config.NumberColumn(format="%d"),
            },
        )

    st.markdown("---")

    with st.expander("Advanced"):
        st.warning(
            "**Re-run seed script** will delete and re-insert all built-in datasets. "
            "Any custom data will be lost."
        )
        if st.button("Re-run seed script", type="secondary", key=f"{PAGE_NS}.reseed"):
            with st.spinner("Seeding database…"):
                _result = subprocess.run(
                    ["uv", "run", "python", "scripts/seed_data.py"],
                    capture_output=True,
                    text=True,
                    cwd=str(_PROJECT_ROOT),
                )
            if _result.returncode == 0:
                st.success("Seed completed. Reload the page to see updated counts.")
                st.cache_resource.clear()
            else:
                st.error(f"Seed failed (exit {_result.returncode}):")
                st.code(_result.stderr[-1000:] if _result.stderr else "(no stderr)")

# ── Preferences tab ───────────────────────────────────────────────────────────
with tab_prefs:
    st.subheader("Forecasting defaults")
    st.info("These values are read-only in v1. Edit `.env` to change defaults.")

    _prefs = [
        (
            "Default simulations",
            f"{settings.default_n_simulations:,}",
            "Monte Carlo paths per run (DEFAULT_N_SIMULATIONS)",
        ),
        (
            "Default seed",
            str(settings.default_random_seed),
            "For reproducible simulations",
        ),
        (
            "Default horizon",
            f"{settings.default_n_steps} months",
            "Forecast steps ahead",
        ),
        (
            "Min observations / cell",
            "20",
            "Sparsity warning threshold (MIN_OBSERVATIONS_PER_CELL)",
        ),
    ]

    for _label, _value, _hint in _prefs:
        _col_label, _col_value = st.columns([0.5, 0.5])
        with _col_label:
            st.markdown(f"**{_label}**")
            st.caption(_hint)
        with _col_value:
            st.code(_value, language=None)

# ── Appearance tab ────────────────────────────────────────────────────────────
with tab_appearance:
    st.subheader("Theme")
    st.info("Theme is locked to **light mode** in v1. Dark mode support is planned for v0.2.")
    st.markdown(
        "**Accent color:** Indigo — `#4338CA` "
        "(locked for v1, matches design system token `--color-primary`).\n\n"
        "To inspect the full design token palette, see `app/styles/theme.css` "
        "and the design reference at `docs/design-reference/`."
    )

# ── About tab ─────────────────────────────────────────────────────────────────
with tab_about:
    st.subheader("MarkovLens")
    _col_info, _col_links = st.columns([0.6, 0.4])

    with _col_info:
        st.markdown(
            f"**Version:** v{APP_VERSION}  \n"
            "**License:** MIT\n\n"
            "A multi-domain Markov chain forecasting workbench. Built on Chan (2015) IJICIC "
            "and Becker (2026) longshot-bias calibration.\n\n"
            "- **Engine:** m1 Homogeneous · m2 Time-varying · m3 Extended (Chan 2015)\n"
            "- **Simulation:** 10,000-path Monte Carlo with longshot calibration\n"
            "- **UI:** Streamlit + DuckDB + Plotly"
        )

    with _col_links:
        st.markdown("**Resources**")
        st.page_link("pages/1_Brand_Share.py", label="Brand Share Forecaster")
        st.page_link("pages/2_Churn.py", label="Customer Churn Analyzer")
        st.markdown(
            "[MARKOV-MODELS.md](https://github.com/afrizzal/markovlens/blob/master/docs/MARKOV-MODELS.md)  \n"
            "[MONTE-CARLO.md](https://github.com/afrizzal/markovlens/blob/master/docs/MONTE-CARLO.md)  \n"
            "[manual-book.md](https://github.com/afrizzal/markovlens/blob/master/manual-book.md)"
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption(f"MarkovLens v{APP_VERSION} — Built with Streamlit + DuckDB + Plotly")
