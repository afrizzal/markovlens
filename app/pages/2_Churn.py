"""Customer Churn page for MarkovLens."""

from __future__ import annotations

# stdlib
import csv
import io
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path so `from app.X`, `from core.X`, `from domains.X` resolve.
# Streamlit adds the entry-script dir (app/) to sys.path, not the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# third-party
import numpy as np  # noqa: E402
import streamlit as st  # noqa: E402

# ── Page Config (first Streamlit call — must precede all other st.* calls) ─
st.set_page_config(
    page_title="Customer Churn — MarkovLens",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# local — imported after streamlit so register_theme() can compose the template
from app.components.empty_state import empty_state  # noqa: E402
from app.components.kpi_card import kpi_card  # noqa: E402
from app.components.sankey_flow import (  # noqa: E402
    build_sankey_figure,
    build_whatif_chart,
    impact_summary,
    state_legend_html,
)
from app.styles import inject_theme, register_theme  # noqa: E402
from core.db.connection import get_connection  # noqa: E402
from core.exceptions import DatasetTooSparseError  # noqa: E402
from domains.churn import service  # noqa: E402

# ── Register Plotly template before any chart is rendered ──────────────────
register_theme()
inject_theme()

# ---------------------------------------------------------------------------
# Module constants — no magic numbers
# ---------------------------------------------------------------------------
PAGE_NS: str = "churn"
# Lucide SVG icon strings — passed to kpi_card icon= kwarg (prototype lines 25-28)
_SVG_OPEN = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
_ICON_USERS: str = (
    f'{_SVG_OPEN}<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
    f'<circle cx="9" cy="7" r="4"/>'
    f'<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
    f'<path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
)
_ICON_CLOCK: str = (
    f'{_SVG_OPEN}<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
)
_ICON_TRENDING_UP: str = (
    f'{_SVG_OPEN}<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>'
    f'<polyline points="16 7 22 7 22 13"/></svg>'
)
_ICON_DOLLAR: str = (
    f'{_SVG_OPEN}<line x1="12" y1="1" x2="12" y2="23"/>'
    f'<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>'
)
DEFAULT_HORIZON: int = 12
HORIZON_MIN: int = 1
HORIZON_MAX: int = 24
SANKEY_N_COLS: int = 8
REVENUE_TOOLTIP: str = "Assumes Rp 50,000/customer/month — adjust in Settings (v2)"
# Stacked distribution bar colors for the scrubber (hex, light mode) keyed by normalized label
STATE_BAR_COLORS: dict[str, str] = {
    "active": "#059669",
    "atrisk": "#D97706",
    "inactive": "#A1A1AA",
    "reactivated": "#0891B2",
    "churned": "#DC2626",
}


# ---------------------------------------------------------------------------
# CSV export helper (RPT-01)
# ---------------------------------------------------------------------------


def _churn_csv_bytes(result: service.ChurnAnalysisResult) -> bytes:
    """Serialize churn analysis result to CSV bytes (two sections: Forecast + Transition Matrix)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    labels = result.state_labels

    # Baseline forecast section
    w.writerow(["# Baseline Forecast", "model=m1"])
    w.writerow(["period", *labels])
    for period, row in enumerate(result.baseline_forecast):
        w.writerow([period, *[f"{v:.6f}" for v in row]])

    # Transition Matrix section
    w.writerow([])
    w.writerow(["# Transition Matrix"])
    w.writerow(["from_state", *labels])
    for i, label in enumerate(labels):
        w.writerow([label, *[f"{v:.6f}" for v in result.transition_matrix[i]]])

    return buf.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# Cached infrastructure
# ---------------------------------------------------------------------------


@st.cache_resource
def _get_db():
    return get_connection()


@st.cache_data(show_spinner=False)
def _cached_analysis(dataset_id: str, horizon: int):
    return service.run_analysis(_get_db(), dataset_id, horizon)


@st.cache_data(show_spinner=False)
def _cached_scenario(dataset_id: str, horizon: int, overrides_frozen: frozenset) -> np.ndarray:
    """Cache simulate_scenario keyed on (dataset_id, horizon, frozenset(overrides.items()))."""
    return service.simulate_scenario(_get_db(), dataset_id, horizon, dict(overrides_frozen))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _norm_label(label: str) -> str:
    """Normalize state label to a bar-color dict key."""
    return label.lower().replace("-", "").replace(" ", "")


def _stacked_bar_html(distribution: np.ndarray, state_labels: list[str]) -> str:
    """Build inline-HTML flex bar for the period scrubber (Pitfall 6 — NOT a Plotly chart).

    Parameters
    ----------
    distribution : np.ndarray
        Shape (n_states,) — state distribution fractions at a selected period.
    state_labels : list[str]
        Ordered state labels matching distribution indices.

    Returns
    -------
    str
        HTML string with a flex div row, one child per state.
    """
    segments = []
    for i, label in enumerate(state_labels):
        share = float(distribution[i])
        if share < 0.001:
            continue
        norm = _norm_label(label)
        color = STATE_BAR_COLORS.get(norm, "#A1A1AA")
        title = f"{label}: {share * 100:.1f}%"
        # Inline % label for segments > 8% (prototype pages3.jsx:41)
        label_txt = (
            (
                f'<span style="font-size:11px;color:#fff;font-weight:600;'
                f'font-family:var(--font-mono,monospace);">{share * 100:.0f}%</span>'
            )
            if share > 0.08
            else ""
        )
        segments.append(
            f'<div style="flex:{share:.6f};height:28px;background:{color};'
            f'overflow:hidden;display:grid;place-items:center;" title="{title}">'
            f"{label_txt}"
            f"</div>"
        )
    inner = "".join(segments)
    return (
        '<div style="display:flex;height:28px;border-radius:var(--radius-sm, 4px);'
        f'overflow:hidden;border:1px solid var(--color-border-subtle,#E4E4E7);">'
        f"{inner}</div>"
    )


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------


def main() -> None:
    """Render the Customer Churn page."""
    # -- Header ---------------------------------------------------------------
    st.title("Customer Churn")
    st.caption("Model customer state flow and retention with an absorbing Markov chain.")

    # -- Load datasets --------------------------------------------------------
    datasets = service.list_datasets(_get_db())
    if not datasets:
        empty_state(
            "empty",
            "No churn datasets registered",
            "Run the seed script: uv run python scripts/seed_data.py",
        )
        st.stop()

    # -- Control strip --------------------------------------------------------
    with st.container(border=True):
        col_ds, col_horizon, col_run = st.columns([3, 2, 1])

        with col_ds:
            ds = st.selectbox(
                "Cohort",
                options=datasets,
                format_func=lambda d: d.name,
                key=f"{PAGE_NS}.dataset",
            )
            if ds is not None:
                st.markdown(
                    f'<div class="t-xs t-ter mono">'
                    f"{ds.row_count:,} transitions "
                    f"&middot; {ds.n_states} states"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        with col_horizon:
            horizon = st.slider(
                "Time horizon",
                HORIZON_MIN,
                HORIZON_MAX,
                DEFAULT_HORIZON,
                format="%d months",
                key=f"{PAGE_NS}.horizon",
            )

        with col_run:
            st.markdown("<br>", unsafe_allow_html=True)
            run = st.button(
                "Run Analysis",
                type="primary",
                use_container_width=True,
                key=f"{PAGE_NS}.run",
            )

    # -- Session state init / dataset-change guard ----------------------------
    st.session_state.setdefault(f"{PAGE_NS}.result", None)
    st.session_state.setdefault(f"{PAGE_NS}.prev_dataset_id", None)

    if ds is not None:
        prev_ds = st.session_state.get(f"{PAGE_NS}.prev_dataset_id")
        if prev_ds is not None and prev_ds != ds.id:
            st.session_state[f"{PAGE_NS}.result"] = None
            # Clear all what-if slider keys when cohort changes (so sliders reset)
            keys_to_remove = [k for k in st.session_state if k.startswith(f"{PAGE_NS}.what_if.")]
            for k in keys_to_remove:
                del st.session_state[k]
        st.session_state[f"{PAGE_NS}.prev_dataset_id"] = ds.id

    # -- Run analysis on button click -----------------------------------------
    if run and ds is not None:
        with st.spinner("Running churn analysis..."):
            try:
                analysis_result = _cached_analysis(ds.id, horizon)
                st.session_state[f"{PAGE_NS}.result"] = analysis_result
            except DatasetTooSparseError as e:
                st.error(str(e))
                st.info(
                    "Try selecting a longer date range or merging states with fewer than 20 observations."
                )
            except Exception as e:
                st.error(f"Unexpected error: {e}")

    result = st.session_state.get(f"{PAGE_NS}.result")

    # -- KPI strip (D-05) — 4 cards ------------------------------------------
    kpi_cols = st.columns(4)

    if result is not None:
        k = result.kpis
        # Compute forecast-trend deltas from baseline_forecast (mid-horizon → end)
        _bf = result.baseline_forecast
        _sl = result.state_labels
        _ai = next((idx for idx, s in enumerate(_sl) if s.lower() == "active"), 0)
        _ci = next((idx for idx, s in enumerate(_sl) if s.lower() == "churned"), -1)
        _h = _bf.shape[0] - 1
        _mid = max(1, _h // 2)
        _init_a = float(_bf[0, _ai])
        _mid_a = float(_bf[_mid, _ai])
        _end_a = float(_bf[_h, _ai])
        # Retention delta (pp): active share trend from mid to end, normalised to initial
        _ret_delta: float | None = (
            round((_end_a - _mid_a) / _init_a * 100, 1) if _init_a > 1e-12 else None
        )
        # Expected churn delta: negated so positive = fewer churning = green arrow (improvement)
        _p_ch = float(result.transition_matrix[_ai, _ci]) if _ci >= 0 else 0.0
        _churn_delta: float = round((_mid_a - _end_a) * result.n_customers * _p_ch)

        with kpi_cols[0]:
            kpi_card(
                "RETENTION RATE",
                f"{k['retention_rate'] * 100:.1f}",
                unit="%",
                accent="var(--state-active)",
                delta=_ret_delta,
                delta_suffix="pp",
                icon=_ICON_USERS,
            )
        with kpi_cols[1]:
            lt = k["avg_lifetime"]
            lt_display = "—" if (lt != lt) else f"{lt:.1f}"  # NaN check via self-comparison
            kpi_card(
                "AVG CUSTOMER LIFETIME",
                lt_display,
                unit="periods",
                accent="var(--chart-4)",
                icon=_ICON_CLOCK,
            )
        with kpi_cols[2]:
            kpi_card(
                "EXPECTED CHURN (next period)",
                f"{k['expected_churn']:.0f}",
                unit="cust",
                accent="var(--state-churned)",
                delta=_churn_delta,
                delta_suffix=" cust",
                icon=_ICON_TRENDING_UP,
            )
        with kpi_cols[3]:
            rar = k["revenue_at_risk"]
            kpi_card(
                "REVENUE AT RISK",
                f"Rp {rar / 1_000_000:.1f}M",
                accent="var(--state-atrisk)",
                tooltip=REVENUE_TOOLTIP,
                icon=_ICON_DOLLAR,
            )
    else:
        for col in kpi_cols:
            with col:
                kpi_card("--", "--")

    # CSV export download button (RPT-01)
    if st.session_state.get(f"{PAGE_NS}.result") is not None:
        _result_for_export = st.session_state[f"{PAGE_NS}.result"]
        _ts = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button(
            label="Download churn CSV",
            data=_churn_csv_bytes(_result_for_export),
            file_name=f"markovlens_churn_forecast_{_ts}.csv",
            mime="text/csv",
            key="churn_download_csv",
            help="Download transition matrix and baseline forecast as CSV",
        )

    # -- Tabs (D-06 — EXACTLY 2 tabs) ----------------------------------------
    tab_overview, tab_whatif = st.tabs(["Overview", "What-If Simulator"])

    # ── Tab: Overview ────────────────────────────────────────────────────────
    with tab_overview:
        if result is None:
            empty_state(
                "chart",
                "No analysis yet",
                "Select a cohort and click Run Analysis to model customer state flow.",
            )
        else:
            # Sankey chart header
            st.markdown(
                '<div class="card accent-card" style="--accent:var(--state-active);padding:var(--space-5);">'
                '<div class="t-h3">State flow over time</div>'
                '<div class="t-xs t-ter">Ribbon width = customers moving between states; '
                "Churned (red) is absorbing</div>"
                "</div>",
                unsafe_allow_html=True,
            )

            # Build and render the temporal Sankey — use baseline_forecast so snapshot
            # datasets (1 historical period) still show a full n_cols forecast horizon
            fig_sankey = build_sankey_figure(
                result.baseline_forecast,
                result.transition_matrix,
                result.state_labels,
                n_cols=SANKEY_N_COLS,
            )
            # 5-item color legend above the Sankey (Issue 4 — pages3.jsx:32)
            st.markdown(state_legend_html(result.state_labels), unsafe_allow_html=True)
            st.plotly_chart(fig_sankey, use_container_width=True)

            # Time scrubber (D-02) — range from baseline_forecast (horizon+1 rows)
            n_cols_actual = min(SANKEY_N_COLS, result.baseline_forecast.shape[0])
            period = st.slider(
                "Period",
                0,
                n_cols_actual - 1,
                n_cols_actual - 1,
                format="P%d",
                key=f"{PAGE_NS}.scrub_period",
            )

            # Distribution label row
            st.markdown(
                f'<div class="t-xs t-ter mono" style="margin-bottom:4px;">'
                f"Distribution at P{period} — drag to scrub"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Stacked distribution bar — inline HTML flex (Pitfall 6: NOT a Plotly chart)
            dist_at_period = result.baseline_forecast[period]
            bar_html = _stacked_bar_html(dist_at_period, result.state_labels)
            st.markdown(bar_html, unsafe_allow_html=True)

    # ── Tab: What-If Simulator ────────────────────────────────────────────────
    with tab_whatif:
        if result is None:
            empty_state(
                "chart",
                "No analysis yet",
                "Run an analysis on the Overview tab first, then return here to model retention scenarios.",
            )
        else:
            left, right = st.columns([0.5, 0.5], gap="large")

            # LEFT — accordion sliders (Pattern 5, D-03)
            baseline_P = result.transition_matrix  # noqa: N806 (Chan 2015 math notation)
            overrides: dict[tuple[int, int], float] = {}
            any_changed = False

            with left:
                st.markdown(
                    '<div class="t-h3">Adjust transition probabilities</div>'
                    '<div class="t-xs t-ter">Each row auto-renormalizes to 100%. '
                    "Ghost value = baseline.</div>",
                    unsafe_allow_html=True,
                )

                for i, from_label in enumerate(result.state_labels):
                    with st.expander(f"From {from_label}", expanded=(i == 0)):
                        for j, to_label in enumerate(result.state_labels):
                            baseline_val = float(baseline_P[i, j])
                            baseline_pct = round(baseline_val * 100)
                            key = f"{PAGE_NS}.what_if.{i}_{j}"
                            # Initialize as percentage (0-100); display-only change (Pitfall 3)
                            if key not in st.session_state:
                                st.session_state[key] = float(baseline_pct)
                            current_pct = st.slider(
                                f"-> {to_label}  (baseline {baseline_pct}%)",
                                0.0,
                                100.0,
                                step=1.0,
                                format="%.0f%%",
                                key=key,
                            )
                            current = current_pct / 100.0  # convert to 0-1 for matrix
                            if abs(current - baseline_val) > 1e-6:
                                overrides[(i, j)] = current
                                any_changed = True

                if any_changed and st.button("Reset all", key=f"{PAGE_NS}.reset"):
                    for i_r in range(len(result.state_labels)):
                        for j_r in range(len(result.state_labels)):
                            st.session_state.pop(f"{PAGE_NS}.what_if.{i_r}_{j_r}", None)
                    st.rerun()

            # RIGHT — live impact card + before/after chart (D-04)
            with right:
                horizon_val = st.session_state.get(f"{PAGE_NS}.horizon", DEFAULT_HORIZON)
                baseline_dist = result.baseline_forecast

                if overrides:
                    modified_dist = _cached_scenario(
                        ds.id, horizon_val, frozenset(overrides.items())
                    )
                else:
                    modified_dist = baseline_dist

                summary = impact_summary(
                    overrides,
                    baseline_P,
                    baseline_dist,
                    modified_dist,
                    result.state_labels,
                    result.n_customers,
                )

                st.markdown(
                    f'<div class="card accent-card" style="--accent:{summary.accent_token};'
                    f'padding:var(--space-5);">'
                    f'<div class="t-label">SCENARIO IMPACT</div>'
                    f'<div style="margin-top:var(--space-2);">{summary.html}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # Spacer — prevents the chart title from overlapping the SCENARIO IMPACT card above
                st.markdown(
                    '<div style="height:var(--space-5,20px);"></div>',
                    unsafe_allow_html=True,
                )

                fig_whatif = build_whatif_chart(baseline_dist, modified_dist, result.state_labels)
                st.plotly_chart(fig_whatif, use_container_width=True)


main()
