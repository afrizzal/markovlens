"""Monte Carlo Fan Chart component (BS-03).

Renders a Plotly fan chart with P10/P50/P90 quantile bands, a historical/forecast
vertical separator, and an explicit named legend.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# Band fill and line colors derived from --chart-1 (#4338CA)
BAND_FILL_OUTER: str = "rgba(67,56,202,0.13)"
MEDIAN_COLOR: str = "#4338CA"  # --chart-1
BAND_LINE_COLOR: str = "rgba(67,56,202,0.5)"
HISTORICAL_COLOR: str = "#0A0A0A"  # --color-text-primary
SEPARATOR_COLOR: str = "rgba(82,82,91,0.5)"  # --color-text-secondary muted


def _build_fan_figure(
    p10: np.ndarray,
    p50: np.ndarray,
    p90: np.ndarray,
    *,
    history: np.ndarray | None = None,
    brand_label: str = "Brand",
    height: int = 400,
) -> go.Figure:
    """Build and return the Plotly fan chart figure (no Streamlit side effects).

    Parameters
    ----------
    p10 : np.ndarray
        Shape (n_steps,) — 10th percentile path.
    p50 : np.ndarray
        Shape (n_steps,) — median (50th percentile) path.
    p90 : np.ndarray
        Shape (n_steps,) — 90th percentile path.
    history : np.ndarray | None
        Shape (n_hist,) — historical actuals to prepend.
    brand_label : str
        Label for the brand/series shown in chart title.
    height : int
        Chart height in pixels.

    Returns
    -------
    go.Figure
        Assembled Plotly figure ready for ``st.plotly_chart``.
    """
    n_hist = len(history) if history is not None else 0
    n_steps = len(p50)

    # X-axis ranges:
    # Historical:  0 .. n_hist-1  labelled "M{k}"
    # Forecast:    n_hist-1 .. n_hist-1+n_steps  so the band connects at last historical
    # (When no history, forecast starts at 0.)
    hist_x = list(range(n_hist))
    # Forecast x starts one step before the end of history so the line connects
    forecast_start = max(0, n_hist - 1)
    forecast_x = list(range(forecast_start, forecast_start + n_steps))

    # Tick labels
    total_len = forecast_start + n_steps
    tickvals = list(range(total_len))
    ticktext: list[str] = []
    for idx in tickvals:
        if idx < n_hist:
            ticktext.append(f"M{idx + 1}")
        else:
            offset = idx - (n_hist - 1) if n_hist > 0 else idx + 1
            ticktext.append(f"+{offset}")

    # --- Trace order per UI-SPEC §3 / RESEARCH Pitfall 3 ---
    # 1. P90 reference line (no fill) — must come BEFORE P10 for tonexty
    # 2. P10 line with fill="tonexty" → fills to P90 (previous trace)
    # 3. P50 solid median
    # 4. Historical solid (if provided)
    # 5. P10 dashed label line
    # 6. P90 dashed label line

    traces: list[go.BaseTraceType] = []

    # Trace 1: P90 reference (no fill, no legend entry for the outer band itself)
    traces.append(
        go.Scatter(
            x=forecast_x,
            y=p90.tolist(),
            mode="lines",
            line={"color": BAND_LINE_COLOR, "width": 0},
            showlegend=False,
            name="_p90_ref",
            hoverinfo="skip",
        )
    )

    # Trace 2: P10 with tonexty fill -> creates the P10-P90 band
    traces.append(
        go.Scatter(
            x=forecast_x,
            y=p10.tolist(),
            mode="lines",
            fill="tonexty",
            fillcolor=BAND_FILL_OUTER,
            line={"color": BAND_LINE_COLOR, "width": 0},
            name="P10-P90 range",
            showlegend=True,
            hoverinfo="skip",
        )
    )

    # Trace 3: P50 solid median
    traces.append(
        go.Scatter(
            x=forecast_x,
            y=p50.tolist(),
            mode="lines",
            line={"color": MEDIAN_COLOR, "width": 2.5},
            name="Median (P50)",
            showlegend=True,
        )
    )

    # Trace 4: Historical solid line (if provided)
    if history is not None and n_hist > 0:
        traces.append(
            go.Scatter(
                x=hist_x,
                y=history.tolist(),
                mode="lines",
                line={"color": HISTORICAL_COLOR, "width": 2},
                name="Historical",
                showlegend=True,
            )
        )

    # Trace 5: P10 dashed label line
    traces.append(
        go.Scatter(
            x=forecast_x,
            y=p10.tolist(),
            mode="lines",
            line={"color": BAND_LINE_COLOR, "width": 1, "dash": "dot"},
            name="P10",
            showlegend=True,
        )
    )

    # Trace 6: P90 dashed label line
    traces.append(
        go.Scatter(
            x=forecast_x,
            y=p90.tolist(),
            mode="lines",
            line={"color": BAND_LINE_COLOR, "width": 1, "dash": "dot"},
            name="P90",
            showlegend=True,
        )
    )

    fig = go.Figure(data=traces)

    # Separator: vertical dashed line at the last historical x position
    sep_x = float(n_hist - 1) if n_hist > 0 else 0.0
    fig.add_vline(
        x=sep_x,
        line_dash="dash",
        line_color=SEPARATOR_COLOR,
        line_width=1,
        annotation_text="today",
        annotation_position="top",
        annotation_font={"size": 10, "family": "JetBrains Mono, monospace"},
    )

    # Y-axis padding
    all_vals = np.concatenate([p10, p90])
    y_lo = float(all_vals.min()) - 0.01
    y_hi = float(all_vals.max()) + 0.01

    fig.update_layout(
        height=height,
        yaxis={
            "tickformat": ".0%",
            "range": [y_lo, y_hi],
            "gridcolor": "#E4E4E7",
        },
        xaxis={
            "tickvals": tickvals,
            "ticktext": ticktext,
            "gridcolor": "#E4E4E7",
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.35,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 12, "color": "#52525B"},
        },
        showlegend=True,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
    )

    return fig


def monte_carlo_fan(
    p10: np.ndarray,
    p50: np.ndarray,
    p90: np.ndarray,
    *,
    history: np.ndarray | None = None,
    brand_label: str = "Brand",
    n_simulations: int = 10_000,
    seed: int = 42,
    height: int = 400,
) -> None:
    """Render a Monte Carlo fan chart with P10/P50/P90 bands.

    Parameters
    ----------
    p10 : np.ndarray
        Shape (n_steps,) — 10th percentile path.
    p50 : np.ndarray
        Shape (n_steps,) — median path.
    p90 : np.ndarray
        Shape (n_steps,) — 90th percentile path.
    history : np.ndarray | None
        Shape (n_hist,) — historical actuals (prepended before forecast).
    brand_label : str
        Brand or series name for display.
    n_simulations : int
        Number of Monte Carlo paths simulated.
    seed : int
        Random seed used in simulation.
    height : int
        Chart height in pixels.
    """
    subtitle = f"{n_simulations:,} simulated paths · P10 / P50 / P90 bands · seed {seed}"

    st.markdown(
        f"""<div class="card accent-card" style="--accent: var(--chart-1); padding: var(--space-5);">
  <div class="t-h3">Forecast fan chart</div>
  <div class="t-xs t-ter">{subtitle}</div>
</div>""",
        unsafe_allow_html=True,
    )

    fig = _build_fan_figure(
        p10,
        p50,
        p90,
        history=history,
        brand_label=brand_label,
        height=height,
    )
    st.plotly_chart(fig, use_container_width=True)
