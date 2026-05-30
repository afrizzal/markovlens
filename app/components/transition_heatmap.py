"""Transition Matrix Heatmap component (BS-02).

Renders an annotated Plotly heatmap with a fixed [0, 1] color scale,
per-cell percentage annotations, and sparsity warning markers on cells
with fewer than ``SPARSE_OBS_THRESHOLD`` observations.
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.styles.plotly_theme import HEATMAP_COLORSCALE

# No magic number — matches MIN_OBSERVATIONS_PER_CELL in markov-patterns.md
SPARSE_OBS_THRESHOLD: int = 20


def _build_heatmap_figure(
    matrix: np.ndarray,
    obs_counts: np.ndarray,
    state_labels: list[str],
    *,
    period_label: str | None = None,
    height: int = 400,
) -> go.Figure:
    """Build and return the Plotly heatmap figure (no Streamlit side effects).

    Parameters
    ----------
    matrix : np.ndarray
        Shape (n, n), values in [0, 1].  Rows = from-state, cols = to-state.
    obs_counts : np.ndarray
        Shape (n, n), integer observation counts per cell.
    state_labels : list[str]
        Length n ordered state names for axes.
    period_label : str | None
        Optional period suffix appended to subtitle, e.g. "Period 12 (most recent)".
    height : int
        Chart height in pixels.

    Returns
    -------
    go.Figure
        Assembled Plotly figure ready for ``st.plotly_chart``.
    """
    n = len(state_labels)

    heatmap_trace = go.Heatmap(
        z=matrix,
        x=state_labels,
        y=state_labels,
        colorscale=HEATMAP_COLORSCALE,
        zmin=0,
        zmax=1,
        showscale=False,
        hovertemplate="%{y} → %{x}: %{z:.1%} · %{customdata:,} obs<extra></extra>",
        customdata=obs_counts,
    )

    fig = go.Figure(data=[heatmap_trace])

    # Per-cell value annotations and sparsity markers
    annotations: list[dict] = []
    for i in range(n):
        for j in range(n):
            v = float(matrix[i, j])
            # Text color: white for dark cells (v >= 0.55), dark for light cells
            # (luminance threshold per UI-SPEC §2 / RESEARCH Pattern 8)
            text_color = "#FFFFFF" if v >= 0.55 else "#0A0A0A"
            cell_text = f"{v * 100:.0f}%" if v >= 0.10 else f"{v * 100:.1f}%"

            annotations.append(
                {
                    "x": j,
                    "y": i,
                    "text": cell_text,
                    "showarrow": False,
                    "font": {
                        "family": "JetBrains Mono, monospace",
                        "size": 12,
                        "color": text_color,
                    },
                    "xref": "x",
                    "yref": "y",
                }
            )

            # Sparsity warning marker — top-right offset within the cell
            if obs_counts[i, j] < SPARSE_OBS_THRESHOLD:
                annotations.append(
                    {
                        "x": j,
                        "y": i,
                        "text": "⚠",  # ⚠
                        "showarrow": False,
                        "xshift": 14,
                        "yshift": -12,
                        "font": {
                            "color": "#D97706",
                            "size": 10,
                        },
                        "xref": "x",
                        "yref": "y",
                    }
                )

    fig.update_layout(
        annotations=annotations,
        height=height,
        yaxis={"autorange": "reversed"},
        # Square aspect for n × n grid
        xaxis={"scaleanchor": "y", "constrain": "domain"},
    )

    return fig


def transition_heatmap(
    matrix: np.ndarray,
    obs_counts: np.ndarray,
    state_labels: list[str],
    *,
    title: str = "Transition probabilities",
    subtitle: str = "Rows = from-state · Columns = to-state",
    period_label: str | None = None,
    height: int = 400,
) -> None:
    """Render an annotated transition matrix heatmap.

    Parameters
    ----------
    matrix : np.ndarray
        Shape (n, n), values in [0, 1].
    obs_counts : np.ndarray
        Shape (n, n), integer observation counts.
    state_labels : list[str]
        Length n ordered state names.
    title : str
        Card header title.
    subtitle : str
        Card header subtitle.  ``period_label`` is appended if provided.
    period_label : str | None
        Optional period suffix for m2/m3 models.
    height : int
        Chart height in pixels.
    """
    full_subtitle = subtitle
    if period_label is not None:
        full_subtitle = f"{subtitle} · {period_label}"

    # Card header via custom HTML
    st.markdown(
        f"""<div class="card accent-card" style="--accent: var(--chart-1); padding: var(--space-5);">
  <div class="t-h3">{title}</div>
  <div class="t-xs t-ter">{full_subtitle}</div>
</div>""",
        unsafe_allow_html=True,
    )

    fig = _build_heatmap_figure(
        matrix,
        obs_counts,
        state_labels,
        period_label=period_label,
        height=height,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Sequential legend caption
    n_sparse = int((obs_counts < SPARSE_OBS_THRESHOLD).sum())
    st.markdown(
        """<div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
  <div class="t-xs t-ter">
    <span>Low</span>
    <span style="display:inline-block; width:120px; height:12px;
      background: linear-gradient(to right, #EEF2FF, #C7D2FE, #818CF8, #4338CA, #1E1B4B);
      border-radius:2px; vertical-align:middle; margin:0 4px;"></span>
    <span>High</span>
  </div>
  <div class="t-xs" style="color:var(--color-warning);">&#9888; Fewer than 20 observations</div>
</div>""",
        unsafe_allow_html=True,
    )

    if n_sparse > 0:
        st.warning(
            f"⚠ {n_sparse} cell{'s' if n_sparse > 1 else ''} "
            f"{'have' if n_sparse > 1 else 'has'} fewer than 20 observations — "
            "estimates are noisy. Consider merging sparse states or collecting more data."
        )
