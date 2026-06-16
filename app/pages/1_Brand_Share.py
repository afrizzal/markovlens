"""Brand Share Forecaster page for MarkovLens."""

from __future__ import annotations

# stdlib
import csv
import io
import random
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
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

# ── Page Config (first Streamlit call — must precede all other st.* calls) ─
st.set_page_config(
    page_title="Brand Share — MarkovLens",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# local — imported after streamlit so register_theme() can compose the template
from app.components.empty_state import empty_state  # noqa: E402
from app.components.kpi_card import kpi_card  # noqa: E402
from app.components.monte_carlo_fan import monte_carlo_fan  # noqa: E402
from app.components.transition_heatmap import transition_heatmap  # noqa: E402
from app.db import get_db  # noqa: E402
from app.styles import inject_theme, register_theme  # noqa: E402
from core.db.queries import build_transition_matrix, load_transitions  # noqa: E402
from core.exceptions import DatasetTooSparseError  # noqa: E402
from domains.brand_share import service  # noqa: E402

# ── Register Plotly template before any chart is rendered (D-05) ───────────
register_theme()
inject_theme()

# ---------------------------------------------------------------------------
# Module constants — no magic numbers
# ---------------------------------------------------------------------------
PAGE_NS: str = "brand_share"
DEFAULT_HORIZON: int = 12
HORIZON_MIN: int = 1
HORIZON_MAX: int = 24
DEFAULT_N_SIMULATIONS: int = 10_000
DEFAULT_SEED: int = 42
SPARSE_OBS_THRESHOLD: int = 20
MODEL_OPTIONS: list[str] = ["m1", "m2", "m3"]
MODEL_TOOLTIPS: dict[str, str] = {
    "m1": "Y_{t+1} = Yt*P - constant transition matrix",
    "m2": "Y_{t+1} = Yt*Pt - time-varying matrix per period",
    "m3": "Q_{t+1} = (G x Qt)*Pt - time-varying with growth multiplier (absolute counts)",
}
CATEGORICAL_COLORS: list[str] = [
    "#4338CA",
    "#059669",
    "#D97706",
    "#0891B2",
    "#DC2626",
    "#7C3AED",
]

# ---------------------------------------------------------------------------
# Reason sentences for Model Comparison verdict (D-12)
# ---------------------------------------------------------------------------
_MODEL_REASON: dict[str, str] = {
    "m1": "A constant-matrix model works well here - brand-switching rates appear stable over the observed periods.",
    "m2": "A time-varying model captures shifting brand-switching rates that a constant-matrix m1 cannot.",
    "m3": "The extended model with growth multiplier better captures changes in total market size alongside shifting switching rates.",
}


# ---------------------------------------------------------------------------
# CSV export helper (RPT-01)
# ---------------------------------------------------------------------------


def _brand_share_csv_bytes(result: service.BrandShareForecastResult) -> bytes:
    """Serialize forecast result to CSV bytes (two sections: Forecast + Transition Matrix)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    labels = result.state_labels

    # Forecast section — use best_model forecast
    forecast = result.forecasts.get(result.best_model)
    if forecast is None:
        forecast = result.forecasts["m1"]

    w.writerow(["# Forecast", f"model={result.best_model}"])
    w.writerow(["period", *labels])
    for period, row in enumerate(forecast):
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


@st.cache_data(show_spinner=False)
def _cached_forecast(
    dataset_id: str,
    model_type: str,
    horizon: int,
    n_simulations: int,
    seed: int,
):
    return service.run_forecast(
        get_db(),
        dataset_id,
        model_type,
        horizon,
        n_simulations=n_simulations,
        seed=seed,
    )


@st.cache_data(show_spinner=False)
def _dataset_period_count(dataset_id: str) -> int:
    """Return distinct period count for the dataset (cheap, cached by dataset_id)."""
    return int(load_transitions(get_db(), dataset_id)["period"].nunique())


# ---------------------------------------------------------------------------
# Private figure helpers (testable — no Streamlit side effects)
# ---------------------------------------------------------------------------


def _build_overview_figure(
    historical_shares: np.ndarray,
    forecast: np.ndarray,
    state_labels: list[str],
    horizon: int,
    model: str,
) -> go.Figure:
    """Build stacked-area market-share forecast figure.

    Historical periods shown as solid traces; forecast as dashed/lower-opacity.
    A vertical 'today' separator marks the last historical period.

    Parameters
    ----------
    historical_shares : np.ndarray
        Shape (n_hist, n_states) -- historical share matrix.
    forecast : np.ndarray
        Shape (horizon, n_states) -- forecast share matrix.
    state_labels : list[str]
        State names indexed to the share arrays.
    horizon : int
        Number of forecast steps (for subtitle).
    model : str
        Active model id (m1/m2/m3) for subtitle.

    Returns
    -------
    go.Figure
        Assembled Plotly stacked-area figure.
    """
    n_hist = historical_shares.shape[0]
    n_states = len(state_labels)

    # x indices: historical 0..n_hist-1, forecast n_hist..n_hist+horizon-1
    hist_x = list(range(n_hist))
    forecast_x = list(range(n_hist, n_hist + forecast.shape[0]))

    # Tick labels
    total_len = n_hist + forecast.shape[0]
    tickvals = list(range(total_len))
    ticktext: list[str] = []
    for idx in tickvals:
        if idx < n_hist:
            ticktext.append(f"M{idx + 1}")
        else:
            ticktext.append(f"+{idx - n_hist + 1}")

    traces: list[go.BaseTraceType] = []
    for i in range(n_states):
        color = CATEGORICAL_COLORS[i % len(CATEGORICAL_COLORS)]
        label = state_labels[i]

        # Historical trace (solid, opacity 0.92)
        traces.append(
            go.Scatter(
                x=hist_x,
                y=historical_shares[:, i].tolist(),
                name=label,
                mode="lines",
                line={"color": color, "width": 2},
                fill="tonexty" if i > 0 else "tozeroy",
                stackgroup="hist",
                opacity=0.92,
                legendgroup=label,
                showlegend=True,
            )
        )

        # Forecast trace (dashed, lower opacity) -- connects at last historical x
        forecast_y = forecast[:, i].tolist()
        connect_x = [n_hist - 1, *forecast_x] if n_hist > 0 else forecast_x
        connect_y = [float(historical_shares[-1, i]), *forecast_y] if n_hist > 0 else forecast_y

        traces.append(
            go.Scatter(
                x=connect_x,
                y=connect_y,
                name=f"{label} (forecast)",
                mode="lines",
                line={"color": color, "width": 2, "dash": "dash"},
                fill="tonexty" if i > 0 else "tozeroy",
                stackgroup="forecast",
                opacity=0.40,
                legendgroup=label,
                showlegend=False,
            )
        )

    fig = go.Figure(data=traces)

    # "today" vertical separator at last historical index
    sep_x = float(n_hist - 1) if n_hist > 0 else 0.0
    fig.add_vline(
        x=sep_x,
        line_dash="dash",
        line_color="rgba(82,82,91,0.5)",
        annotation_text="today",
        annotation_position="top",
        annotation_font={"size": 10, "family": "JetBrains Mono, monospace"},
    )

    fig.update_layout(
        title="Market share forecast",
        xaxis={
            "tickvals": tickvals,
            "ticktext": ticktext,
            "gridcolor": "#E4E4E7",
        },
        yaxis={
            "tickformat": ".0%",
            "gridcolor": "#E4E4E7",
            "range": [0, 1.05],
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.35,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 12},
        },
        height=400,
    )

    return fig


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------


def main() -> None:
    """Render the Brand Share Forecaster page."""
    # -- Header ---------------------------------------------------------------
    st.title("Brand Share Forecaster")
    st.caption("Predict market share evolution from consumer switching data.")

    # -- Load datasets --------------------------------------------------------
    datasets = service.list_datasets(get_db())
    if not datasets:
        empty_state(
            "empty",
            "No datasets registered",
            "Run the seed script to populate datasets: uv run python scripts/seed_data.py",
        )
        st.stop()

    # -- Control strip --------------------------------------------------------
    with st.container(border=True):
        col_ds, col_model, col_horizon, col_run = st.columns([3, 2, 2, 1])

        with col_ds:
            ds = st.selectbox(
                "Dataset",
                options=datasets,
                format_func=lambda d: d.name,
                key=f"{PAGE_NS}.dataset",
            )
            if ds is not None:
                n_periods_val = _dataset_period_count(ds.id)
                st.markdown(
                    f'<div class="t-xs t-ter mono">'
                    f"{ds.row_count:,} transitions "
                    f"&middot; {n_periods_val:,} periods "
                    f"&middot; {ds.n_states} states"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        with col_model:
            try:
                model = st.segmented_control(
                    "Model",
                    options=MODEL_OPTIONS,
                    default="m1",
                    key=f"{PAGE_NS}.model",
                    help=" | ".join(f"{k}: {v}" for k, v in MODEL_TOOLTIPS.items()),
                )
            except AttributeError:
                model = st.radio(
                    "Model",
                    MODEL_OPTIONS,
                    horizontal=True,
                    key=f"{PAGE_NS}.model_radio",
                    help=" | ".join(f"{k}: {v}" for k, v in MODEL_TOOLTIPS.items()),
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
                "Run Forecast",
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
        st.session_state[f"{PAGE_NS}.prev_dataset_id"] = ds.id

    # -- Run forecast on button click -----------------------------------------
    if run and ds is not None:
        active_model_run = model if model else "m1"
        with st.spinner("Running forecast across all three models..."):
            try:
                forecast_result = _cached_forecast(
                    ds.id,
                    active_model_run,
                    horizon,
                    DEFAULT_N_SIMULATIONS,
                    DEFAULT_SEED,
                )
                st.session_state[f"{PAGE_NS}.result"] = forecast_result
            except DatasetTooSparseError as e:
                st.error(str(e))
                st.info(
                    "Try selecting a longer date range or merging states with fewer than 20 observations."
                )
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                st.info("If this persists, re-run the seed script or check the logs.")

    result = st.session_state.get(f"{PAGE_NS}.result")
    active_model: str = model if model else "m1"

    # -- KPI strip ------------------------------------------------------------
    kpi_cols = st.columns(3)

    if result is not None:
        fc_arr = result.forecasts[active_model]
        final_shares = fc_arr[-1]
        state_labels = result.state_labels

        leader_idx = int(np.argmax(final_shares))
        leader_label = state_labels[leader_idx]

        first_hist = (
            result.historical_shares[0] if len(result.historical_shares) > 0 else final_shares
        )
        delta_shares = final_shares - first_hist
        pos_idxs = np.where(delta_shares > 0)[0]
        neg_idxs = np.where(delta_shares < 0)[0]

        gainer_label: str = "no gainer"
        gainer_delta: float | None = None
        if len(pos_idxs) > 0:
            gainer_idx = int(pos_idxs[int(np.argmax(delta_shares[pos_idxs]))])
            gainer_label = state_labels[gainer_idx]
            gainer_delta = float(delta_shares[gainer_idx]) * 100

        loser_label: str = "no loser"
        loser_delta: float | None = None
        if len(neg_idxs) > 0:
            loser_idx = int(neg_idxs[int(np.argmin(delta_shares[neg_idxs]))])
            loser_label = state_labels[loser_idx]
            loser_delta = float(delta_shares[loser_idx]) * 100

        with kpi_cols[0]:
            kpi_card("FORECASTED LEADER", leader_label, accent="var(--chart-1)")
        with kpi_cols[1]:
            kpi_card(
                "BIGGEST GAINER",
                gainer_label,
                delta=gainer_delta,
                delta_suffix="pp",
                accent="var(--chart-2)",
            )
        with kpi_cols[2]:
            kpi_card(
                "BIGGEST LOSER",
                loser_label,
                delta=loser_delta,
                delta_suffix="pp",
                accent="var(--chart-5)",
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
            label="Download forecast CSV",
            data=_brand_share_csv_bytes(_result_for_export),
            file_name=f"markovlens_brand_share_forecast_{_ts}.csv",
            mime="text/csv",
            key="brand_share_download_csv",
            help="Download transition matrix and forecast as CSV",
        )

    # -- Tabs -----------------------------------------------------------------
    tab_overview, tab_matrix, tab_mc, tab_compare = st.tabs(
        ["Overview", "Transition Matrix", "Monte Carlo", "Model Comparison"]
    )

    # ── Tab: Overview ────────────────────────────────────────────────────────
    with tab_overview:
        if result is None:
            empty_state(
                "chart",
                "No forecast yet",
                "Select a dataset and click Run Forecast to generate market share projections.",
            )
        else:
            main_col, side_col = st.columns([0.65, 0.35], gap="large")

            with main_col:
                fig_overview = _build_overview_figure(
                    result.historical_shares,
                    result.forecasts[active_model],
                    result.state_labels,
                    horizon,
                    active_model,
                )
                subtitle_ov = (
                    f"Historical (solid) + {horizon}-month forecast (dashed) · model {active_model}"
                )
                st.markdown(
                    f'<div class="card accent-card" style="--accent:var(--chart-1);padding:var(--space-5);">'
                    f'<div class="t-h3">Market share forecast</div>'
                    f'<div class="t-xs t-ter">{subtitle_ov}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.plotly_chart(fig_overview, use_container_width=True)

            with side_col:
                # Stationary distribution panel (D-13 / D-14 / SC-5)
                st.markdown(
                    '<div class="card accent-card" style="--accent:var(--color-primary);padding:var(--space-5);">'
                    '<div class="t-h3">Long-run equilibrium</div>'
                    '<div class="t-xs t-ter" style="font-style:italic;">'
                    "Assumes today's transition rates hold indefinitely - a what-if, not a prediction."
                    "</div></div>",
                    unsafe_allow_html=True,
                )
                # SC-5: consume result.stationary_distribution inside the Overview block
                if result.stationary_distribution is None:
                    st.warning(
                        "Could not compute stationary distribution for this matrix. "
                        "The matrix may be absorbing or near-singular."
                    )
                else:
                    stat_dist = result.stationary_distribution
                    n_states_stat = len(result.state_labels)
                    colors_stat = [
                        CATEGORICAL_COLORS[i % len(CATEGORICAL_COLORS)]
                        for i in range(n_states_stat)
                    ]
                    fig_stat = go.Figure(
                        go.Bar(
                            x=stat_dist.tolist(),
                            y=result.state_labels,
                            orientation="h",
                            marker_color=colors_stat,
                            text=[f"{v * 100:.1f}%" for v in stat_dist],
                            textposition="outside",
                        )
                    )
                    fig_stat.update_layout(
                        height=280,
                        xaxis={"range": [0, 1], "tickformat": ".0%"},
                        yaxis={"autorange": "reversed"},
                        margin={"l": 8, "r": 16, "t": 8, "b": 8},
                    )
                    st.plotly_chart(fig_stat, use_container_width=True)

    # ── Tab: Transition Matrix ────────────────────────────────────────────────
    with tab_matrix:
        if ds is not None:
            try:
                hm_matrix, hm_counts = build_transition_matrix(get_db(), ds.id)
                if result is not None:
                    hm_states: list[str] = result.state_labels
                else:
                    _df_hm = load_transitions(get_db(), ds.id)
                    hm_states = sorted(set(_df_hm["from_state"]) | set(_df_hm["to_state"]))

                period_label_arg: str | None = None
                if active_model in ("m2", "m3") and result is not None:
                    period_label_arg = f"Period {result.n_periods} (most recent)"

                transition_heatmap(
                    hm_matrix,
                    hm_counts,
                    state_labels=hm_states,
                    period_label=period_label_arg,
                )

                n_sparse = int((hm_counts < SPARSE_OBS_THRESHOLD).sum())
                if n_sparse > 0:
                    st.warning(
                        f"⚠ {n_sparse} cells have fewer than 20 observations "
                        "- estimates are noisy. "
                        "Consider merging sparse states or collecting more data."
                    )

            except Exception as e:
                st.error(f"Could not build transition matrix: {e}")
        else:
            empty_state(
                "chart",
                "No forecast yet",
                "Select a dataset and click Run Forecast to generate market share projections.",
            )

    # ── Tab: Monte Carlo ──────────────────────────────────────────────────────
    with tab_mc:
        if result is None:
            empty_state(
                "chart",
                "No forecast yet",
                "Select a dataset and click Run Forecast to generate market share projections.",
            )
        else:
            mc_main, mc_side = st.columns([0.65, 0.35], gap="large")

            with mc_main:
                state_labels_mc = result.state_labels

                mc_ctrl_a, mc_ctrl_b = st.columns([1, 1])
                with mc_ctrl_a:
                    start_brand = st.selectbox(
                        "Start brand",
                        options=state_labels_mc,
                        key=f"{PAGE_NS}.mc_start_brand",
                    )
                with mc_ctrl_b:
                    mc_horizon = st.slider(
                        "Time horizon",
                        HORIZON_MIN,
                        HORIZON_MAX,
                        horizon,
                        format="%d mo",
                        key=f"{PAGE_NS}.mc_horizon",
                    )

                mc_sims_col, _ = st.columns([2, 1])
                with mc_sims_col:
                    mc_n_sims = st.slider(
                        "Simulations",
                        1000,
                        50000,
                        DEFAULT_N_SIMULATIONS,
                        step=1000,
                        key=f"{PAGE_NS}.mc_n_sims",
                    )

                mc_seed_col, mc_rand_col = st.columns([2, 1])
                with mc_seed_col:
                    mc_seed = st.number_input(
                        "Seed",
                        value=DEFAULT_SEED,
                        key=f"{PAGE_NS}.mc_seed",
                    )
                with mc_rand_col:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Randomize", key=f"{PAGE_NS}.mc_randomize"):
                        st.session_state[f"{PAGE_NS}.mc_seed"] = random.randint(0, 99999)
                        st.rerun()

                run_sim = st.button(
                    "Run Simulation",
                    type="primary",
                    key=f"{PAGE_NS}.mc_run_sim",
                )

                st.session_state.setdefault(f"{PAGE_NS}.mc_result", None)

                if run_sim:
                    with st.spinner(f"Running {mc_n_sims:,} simulations..."):
                        try:
                            mc_result = _cached_forecast(
                                ds.id,
                                active_model,
                                mc_horizon,
                                mc_n_sims,
                                int(mc_seed),
                            )
                            st.session_state[f"{PAGE_NS}.mc_result"] = mc_result
                        except Exception as e:
                            st.error(f"Simulation error: {e}")

                mc_display_result = st.session_state.get(f"{PAGE_NS}.mc_result") or result

                p10 = mc_display_result.confidence_bands[0.10]
                p50 = mc_display_result.confidence_bands[0.50]
                p90 = mc_display_result.confidence_bands[0.90]

                # History for fan chart: leading brand share over historical periods
                history_arr: np.ndarray | None = None
                if (
                    mc_display_result.historical_shares.shape[0] > 0
                    and start_brand in state_labels_mc
                ):
                    brand_idx = state_labels_mc.index(start_brand)
                    history_arr = mc_display_result.historical_shares[:, brand_idx]

                monte_carlo_fan(
                    p10,
                    p50,
                    p90,
                    history=history_arr,
                    brand_label=start_brand or "Brand",
                    n_simulations=mc_n_sims,
                    seed=int(mc_seed),
                )

            with mc_side:
                n_states_mc = len(state_labels_mc)
                fc_arr_mc = mc_display_result.forecasts[active_model]
                final_mc_shares = (
                    fc_arr_mc[-1] if fc_arr_mc.shape[0] > 0 else np.ones(n_states_mc) / n_states_mc
                )
                st.markdown(
                    f'<div class="card accent-card" style="--accent:var(--chart-1);padding:var(--space-5);">'
                    f'<div class="t-h3">Final state distribution</div>'
                    f'<div class="t-xs t-ter">Where {start_brand} lands at +{mc_horizon}mo</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                fig_final = go.Figure(
                    go.Bar(
                        x=state_labels_mc,
                        y=final_mc_shares.tolist(),
                        marker_color=CATEGORICAL_COLORS[0],
                        text=[f"{v * 100:.0f}%" for v in final_mc_shares],
                        textposition="outside",
                    )
                )
                fig_final.update_layout(
                    height=350,
                    yaxis={"tickformat": ".0%", "range": [0, 1.1]},
                    margin={"l": 8, "r": 8, "t": 8, "b": 8},
                )
                st.plotly_chart(fig_final, use_container_width=True)

    # ── Tab: Model Comparison ─────────────────────────────────────────────────
    with tab_compare:
        if result is None:
            empty_state(
                "chart",
                "No forecast yet",
                "Select a dataset and click Run Forecast to generate market share projections.",
            )
        else:
            # -- Model cards (3 columns) --------------------------------------
            model_cols = st.columns(3)
            for i, m in enumerate(MODEL_OPTIONS):
                metrics_m = result.accuracy_metrics.get(m, {})
                m_mape = metrics_m.get("mape", float("nan"))
                m_brier = metrics_m.get("brier", float("nan"))
                is_best = m == result.best_model

                ring_style = "box-shadow:0 0 0 2px var(--color-primary);" if is_best else ""
                badge_html = (
                    '<span class="badge badge-success" '
                    'style="position:absolute;top:8px;right:8px;">'
                    "Best fit</span>"
                    if is_best
                    else ""
                )
                formula = MODEL_TOOLTIPS.get(m, "")
                color_id = "var(--color-primary)" if is_best else "var(--color-text-tertiary)"

                card_inner = (
                    f'<div class="card card-pad" '
                    f'style="position:relative;{ring_style}padding:var(--space-5);">'
                    f"{badge_html}"
                    f'<div class="t-h3 mono" style="color:{color_id};">{m}</div>'
                    f'<div class="t-xs t-sec mono" style="margin-top:var(--space-2);">{formula}</div>'
                    f'<div style="margin-top:var(--space-4);">'
                    f'<span style="font-size:var(--fs-32);font-weight:600;font-family:var(--font-mono);">'
                    f"{m_mape:.2f}%</span>"
                    f'<span class="t-xs t-ter" style="margin-left:4px;">MAPE</span>'
                    f"</div>"
                    f'<div class="t-xs t-sec mono" style="margin-top:var(--space-2);">'
                    f"Brier: {m_brier:.4f}"
                    f"</div></div>"
                )
                with model_cols[i]:
                    st.markdown(card_inner, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # -- Metrics table (bold best per column) -------------------------
            st.markdown("**Model accuracy comparison** - MAPE down | Brier down | Log-loss down")

            metrics_data = result.accuracy_metrics
            mape_vals = {m: metrics_data[m]["mape"] for m in MODEL_OPTIONS}
            brier_vals = {m: metrics_data[m]["brier"] for m in MODEL_OPTIONS}
            ll_vals = {m: metrics_data[m]["log_loss"] for m in MODEL_OPTIONS}
            best_mape_m = min(mape_vals, key=mape_vals.__getitem__)
            best_brier_m = min(brier_vals, key=brier_vals.__getitem__)
            best_ll_m = min(ll_vals, key=ll_vals.__getitem__)

            def _cell(val: float, is_best_cell: bool, fmt: str = ".4f") -> str:
                formatted = f"{val:{fmt}}"
                return f"<strong>{formatted}</strong>" if is_best_cell else formatted

            table_rows = ""
            for m in MODEL_OPTIONS:
                table_rows += (
                    "<tr>"
                    f'<td class="mono">{m}</td>'
                    f'<td class="num">{_cell(mape_vals[m], m == best_mape_m, ".2f")}%</td>'
                    f'<td class="num">{_cell(brier_vals[m], m == best_brier_m)}</td>'
                    f'<td class="num">{_cell(ll_vals[m], m == best_ll_m)}</td>'
                    "</tr>"
                )

            table_html = (
                '<table class="tbl" style="width:100%;border-collapse:collapse;margin-top:8px;">'
                "<thead><tr>"
                '<th class="t-xs t-sec" style="text-align:left;padding:6px;">Model</th>'
                '<th class="t-xs t-sec" style="text-align:right;padding:6px;">MAPE</th>'
                '<th class="t-xs t-sec" style="text-align:right;padding:6px;">Brier</th>'
                '<th class="t-xs t-sec" style="text-align:right;padding:6px;">Log-loss</th>'
                "</tr></thead>"
                f"<tbody>{table_rows}</tbody>"
                "</table>"
            )
            st.markdown(table_html, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # -- Walk-forward backtest table ----------------------------------
            if result.backtest_results:
                st.markdown("**Walk-forward backtest**")
                bt_rows = ""
                for bt in result.backtest_results:
                    period_bt = bt.get("period", "--")
                    mape_bt = bt.get("mape", None)
                    brier_bt = bt.get("brier", None)
                    mape_cell = f"{mape_bt:.2f}%" if mape_bt is not None else "--"
                    brier_cell = f"{brier_bt:.4f}" if brier_bt is not None else "--"
                    bt_rows += (
                        "<tr>"
                        f"<td>{period_bt}</td>"
                        f'<td class="num">{mape_cell}</td>'
                        f'<td class="num">{brier_cell}</td>'
                        "</tr>"
                    )
                bt_table = (
                    '<table class="tbl" style="width:100%;border-collapse:collapse;">'
                    "<thead><tr>"
                    '<th class="t-xs t-sec" style="text-align:left;padding:6px;">Period</th>'
                    '<th class="t-xs t-sec" style="text-align:right;padding:6px;">MAPE</th>'
                    '<th class="t-xs t-sec" style="text-align:right;padding:6px;">Brier</th>'
                    "</tr></thead>"
                    f"<tbody>{bt_rows}</tbody>"
                    "</table>"
                )
                st.markdown(bt_table, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

            # -- Verdict paragraph (D-12) -------------------------------------
            best_m = result.best_model
            best_m_mape = result.accuracy_metrics[best_m]["mape"]
            reason = _MODEL_REASON.get(best_m, "")
            verdict = (
                f"**{best_m}** gives the best overall fit (MAPE {best_m_mape:.2f}%). "
                f"{reason} "
                "Use the **'How to read these metrics'** expander below for definitions."
            )
            st.markdown(verdict)

            with st.expander("How to read these metrics", expanded=False):
                st.markdown(
                    "- **MAPE** (Mean Absolute Percentage Error): average forecast error as a % "
                    "of the actual value. Lower is better. < 2% is excellent for market share.\n"
                    "- **Brier score**: mean squared error on probability forecasts. "
                    "Ranges 0-1; lower is better.\n"
                    "- **Log-loss**: penalises confident wrong predictions more heavily. "
                    "Lower is better."
                )


main()
