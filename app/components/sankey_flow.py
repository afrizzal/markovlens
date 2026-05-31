"""Sankey ribbon flow component (CH-02) and what-if stacked-area chart + narrative (CH-03).

Pure Plotly figure builders — no Streamlit imports. All functions are unit-testable.

The Sankey uses SVG cubic bezier path shapes (go.Figure + layout.shapes).
See D-01 in CONTEXT.md: do NOT use the built-in Sankey trace (loses temporal dimension).
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Color constants — rgba prefixes (alpha appended by caller).
# Keys are normalized state labels: lower-case, no '-', no ' '.
# Values are derived from docs/design-reference/markov.css --state-* tokens.
# ---------------------------------------------------------------------------
STATE_COLOR_PREFIX: dict[str, str] = {
    "active":      "rgba(5,150,105,",    # --state-active:      #059669
    "atrisk":      "rgba(217,119,6,",    # --state-atrisk:      #D97706
    "inactive":    "rgba(161,161,170,",  # --state-inactive:    #A1A1AA
    "reactivated": "rgba(8,145,178,",    # --state-reactivated: #0891B2
    "churned":     "rgba(220,38,38,",    # --state-churned:     #DC2626 (red, CH-02)
}
DEFAULT_COLOR_PREFIX: str = "rgba(100,100,100,"

# Sankey layout constants — match JSX reference: W=820, H=380, col_w=13, gap=7
SANKEY_W: int = 820
SANKEY_H: int = 380
SANKEY_PAD_TOP: int = 10
SANKEY_PAD_BOTTOM: int = 10
SANKEY_COL_W: int = 13
SANKEY_GAP: int = 7
NODE_MIN_SHARE: float = 0.002   # states below this share are not drawn as nodes
FLOW_MIN_SHARE: float = 0.0015  # ribbons below this flow are skipped
RIBBON_ALPHA: str = "0.24)"
NODE_ALPHA: str = "1.0)"

# ---------------------------------------------------------------------------
# What-if stacked-area color constants — full rgba with alpha baked in.
# Keys are normalized state labels (same normalization as above).
# ---------------------------------------------------------------------------
STATE_COLORS_SOLID: dict[str, str] = {
    "active":      "rgba(5,150,105,0.8)",
    "atrisk":      "rgba(217,119,6,0.8)",
    "inactive":    "rgba(161,161,170,0.8)",
    "reactivated": "rgba(8,145,178,0.8)",
    "churned":     "rgba(220,38,38,0.8)",
}
STATE_COLORS_FAINT: dict[str, str] = {k: v.replace("0.8)", "0.18)") for k, v in STATE_COLORS_SOLID.items()}
DEFAULT_SOLID: str = "rgba(100,100,100,0.8)"
DEFAULT_FAINT: str = "rgba(100,100,100,0.18)"
WHATIF_HEIGHT: int = 360


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _norm_label(label: str) -> str:
    """Normalize a state label to a dict key: lower-case, no hyphens/spaces."""
    return label.lower().replace("-", "").replace(" ", "")


def _color_prefix(label: str, state_colors: dict[str, str] | None) -> str:
    """Return the rgba prefix string for a state label.

    Parameters
    ----------
    label : str
        Raw state label (e.g. "At-Risk", "active").
    state_colors : dict[str, str] | None
        Caller-supplied override map (normalized keys -> rgba prefix strings).
        Falls back to STATE_COLOR_PREFIX, then DEFAULT_COLOR_PREFIX.

    Returns
    -------
    str
        rgba prefix ending with a trailing comma, e.g. "rgba(220,38,38,".
    """
    key = _norm_label(label)
    if state_colors and key in state_colors:
        return state_colors[key]
    return STATE_COLOR_PREFIX.get(key, DEFAULT_COLOR_PREFIX)


# ---------------------------------------------------------------------------
# CH-02: Temporal Sankey ribbon figure
# ---------------------------------------------------------------------------

def build_sankey_figure(
    state_distribution_over_time: np.ndarray,
    transition_matrix: np.ndarray,
    state_labels: list[str],
    state_colors: dict[str, str] | None = None,
    *,
    n_cols: int = 8,
    highlight_period: int | None = None,
) -> go.Figure:
    """Build a temporal multi-period Sankey ribbon chart using SVG bezier shapes.

    Each column represents one period. Ribbon width is proportional to
    ``state_distribution_over_time[t, i] * transition_matrix[i, j]``
    (= raw transition flow), satisfying CH-02 "link width proportional to
    raw counts". Node colors come from the churn state palette; the Churned
    node renders in red (``rgba(220,38,38,...)``) per D-01.

    Parameters
    ----------
    state_distribution_over_time : np.ndarray
        Shape (n_periods, n_states). MUST include period 0 as the first row —
        the Sankey assumes the first column is the starting distribution.
    transition_matrix : np.ndarray
        Shape (n_states, n_states). Row-stochastic transition matrix.
    state_labels : list[str]
        Ordered state labels; indices match matrix rows/cols.
    state_colors : dict[str, str] | None
        Optional override map {normalized_label: rgba_prefix_string}.
        Normalized = lower-case, no hyphens/spaces. Keys must end with ",".
    n_cols : int
        Number of period columns to render. Clamped to the number of rows in
        ``state_distribution_over_time`` to guard against short horizons.
    highlight_period : int | None
        Reserved for future use (D-02 scrubber). Currently unused; all
        ribbons render at uniform RIBBON_ALPHA.

    Returns
    -------
    go.Figure
        Plotly figure with bezier path shapes (ribbons) and rect shapes
        (nodes). Ready for ``st.plotly_chart``.

    Notes
    -----
    Implementation is a direct Python port of the JSX Sankey component in
    ``docs/design-reference/js/charts.jsx`` (lines 195-258).
    Does NOT use the built-in Sankey trace — temporal dimension requires
    per-column layout (D-01 mandates SVG bezier path shapes instead).
    """
    # Guard against horizons shorter than requested n_cols (Pitfall 2)
    n_cols = min(n_cols, state_distribution_over_time.shape[0])

    W, H, PT, PB = SANKEY_W, SANKEY_H, SANKEY_PAD_TOP, SANKEY_PAD_BOTTOM
    col_w, gap = SANKEY_COL_W, SANKEY_GAP
    ih = H - PT - PB

    def x_col(c: int) -> float:
        return 8 + (c / (n_cols - 1)) * (W - 16 - col_w)

    def xr(c: int) -> float:
        return x_col(c) + col_w  # right edge of column c

    def xl(c: int) -> float:
        return x_col(c)  # left edge of column c

    # --- Node layout per column (same as JSX) ---
    layout: list[dict[int, dict[str, float]]] = []
    for c in range(n_cols):
        d = state_distribution_over_time[c]
        active_states = [(i, float(v)) for i, v in enumerate(d) if v > NODE_MIN_SHARE]
        total_gap = gap * (len(active_states) - 1)
        yy = float(PT)
        nodes: dict[int, dict[str, float]] = {}
        for i, v in active_states:
            h = v * (ih - total_gap)
            nodes[i] = {"y0": yy, "y1": yy + h, "v": v}
            yy += h + gap
        layout.append(nodes)

    # --- Edge (ribbon) shapes ---
    shapes: list[dict] = []
    for c in range(n_cols - 1):
        d = state_distribution_over_time[c]
        src_off = np.zeros(len(state_labels))
        tgt_off = np.zeros(len(state_labels))
        for i in range(len(state_labels)):
            if i not in layout[c]:
                continue
            for j in range(len(state_labels)):
                flow = float(d[i]) * float(transition_matrix[i, j])
                if flow < FLOW_MIN_SHARE or j not in layout[c + 1]:
                    continue
                sH = layout[c][i]["y1"] - layout[c][i]["y0"]
                tH = layout[c + 1][j]["y1"] - layout[c + 1][j]["y0"]
                s_scale = sH / (float(d[i]) if float(d[i]) > 1e-12 else 1.0)
                t_scale = tH / (float(state_distribution_over_time[c + 1][j]) or 1.0)
                sy0 = layout[c][i]["y0"] + float(src_off[i])
                sy1 = sy0 + flow * s_scale
                ty0 = layout[c + 1][j]["y0"] + float(tgt_off[j])
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
                prefix = _color_prefix(state_labels[i], state_colors)
                shapes.append(
                    {
                        "type": "path",
                        "path": path,
                        "fillcolor": f"{prefix}{RIBBON_ALPHA}",
                        "line": {"width": 0},
                        "xref": "x",
                        "yref": "y",
                    }
                )

    # --- Node rectangles ---
    for c, nodes in enumerate(layout):
        for i, nd in nodes.items():
            prefix = _color_prefix(state_labels[i], state_colors)
            shapes.append(
                {
                    "type": "rect",
                    "x0": x_col(c),
                    "y0": nd["y0"],
                    "x1": x_col(c) + col_w,
                    "y1": nd["y1"],
                    "fillcolor": f"{prefix}{NODE_ALPHA}",
                    "line": {"width": 0},
                    "xref": "x",
                    "yref": "y",
                }
            )

    fig = go.Figure()
    # Invisible scatter for hover at edge midpoints
    fig.add_trace(
        go.Scatter(
            x=[],
            y=[],
            mode="markers",
            marker={"opacity": 0},
            showlegend=False,
        )
    )
    fig.update_layout(
        shapes=shapes,
        xaxis={
            "range": [0, W],
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
        },
        yaxis={
            "range": [0, H],
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
        },
        height=H,
        margin={"l": 0, "r": 0, "t": 8, "b": 24},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ---------------------------------------------------------------------------
# CH-03: What-if stacked-area chart
# ---------------------------------------------------------------------------

def build_whatif_chart(
    baseline_dist: np.ndarray,
    modified_dist: np.ndarray,
    state_labels: list[str],
) -> go.Figure:
    """Build a stacked-area before/after chart for the what-if simulator.

    Renders two stacked-area groups on the same figure:
    - ``stackgroup="baseline"`` — faint (opacity ~0.18) to show the baseline forecast.
    - ``stackgroup="modified"`` — solid (opacity ~0.8) to show the modified scenario.

    Opacity is set via the rgba alpha in ``fillcolor`` only — NOT via the
    trace-level ``opacity`` parameter (Plotly 6.x anti-pattern per RESEARCH).

    Parameters
    ----------
    baseline_dist : np.ndarray
        Shape (horizon+1, n_states) — baseline state distribution over time.
    modified_dist : np.ndarray
        Shape (horizon+1, n_states) — modified scenario state distribution.
    state_labels : list[str]
        Ordered state labels; indices match columns of the distribution arrays.

    Returns
    -------
    go.Figure
        Plotly figure with ``stackgroup="baseline"`` and ``stackgroup="modified"``
        Scatter traces. Ready for ``st.plotly_chart``.
    """
    fig = go.Figure()
    periods = list(range(len(baseline_dist)))
    for i, label in enumerate(state_labels):
        key = _norm_label(label)
        faint = STATE_COLORS_FAINT.get(key, DEFAULT_FAINT)
        solid = STATE_COLORS_SOLID.get(key, DEFAULT_SOLID)
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=baseline_dist[:, i].tolist(),
                stackgroup="baseline",
                name=label,
                fillcolor=faint,
                line={"color": "rgba(0,0,0,0)", "width": 0},
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=modified_dist[:, i].tolist(),
                stackgroup="modified",
                name=label,
                fillcolor=solid,
                line={"color": "rgba(0,0,0,0)", "width": 0},
                showlegend=True,
                legendgroup=label,
            )
        )
    fig.update_layout(
        height=WHATIF_HEIGHT,
        yaxis={"tickformat": ".0%", "range": [0, 1.05]},
        title="Baseline vs. scenario — state mix over horizon",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.3,
            "xanchor": "center",
            "x": 0.5,
        },
    )
    return fig


# ---------------------------------------------------------------------------
# CH-03: Impact narrative helper
# ---------------------------------------------------------------------------

def impact_narrative(
    overrides: dict[tuple[int, int], float],
    baseline_P: np.ndarray,
    baseline_dist: np.ndarray,
    modified_dist: np.ndarray,
    state_labels: list[str],
    n_customers: int,
) -> str:
    """Return a one-sentence impact narrative driven by the largest delta transition.

    Parameters
    ----------
    overrides : dict[tuple[int, int], float]
        Slider overrides keyed on ``(from_state_idx, to_state_idx)``.
        Empty dict returns the default prompt string.
    baseline_P : np.ndarray
        Shape (n_states, n_states) — baseline transition matrix.
    baseline_dist : np.ndarray
        Shape (horizon+1, n_states) — baseline state distribution.
    modified_dist : np.ndarray
        Shape (horizon+1, n_states) — modified scenario distribution.
    state_labels : list[str]
        Ordered state labels.
    n_customers : int
        Total customer count (used to convert fractional churn delta to headcount).

    Returns
    -------
    str
        One-sentence narrative. Uses ASCII ``->`` (not unicode arrow) to avoid
        Windows console encoding issues.
        Examples:
        - "Adjust a slider to model a retention scenario."
        - "Reducing active -> churned by 5pp saves 120 customers."
        - "Increasing atrisk -> churned by 3pp costs 78 customers."
    """
    if not overrides:
        return "Adjust a slider to model a retention scenario."

    # Find the transition with the largest absolute delta from baseline
    best_key = max(overrides, key=lambda k: abs(overrides[k] - baseline_P[k[0], k[1]]))
    i, j = best_key
    delta_pp = (overrides[best_key] - baseline_P[i, j]) * 100
    direction = "Reducing" if delta_pp < 0 else "Increasing"

    churned_idx = next(
        (k for k, s in enumerate(state_labels) if _norm_label(s) == "churned"), -1
    )

    if churned_idx >= 0:
        churn_delta = (
            baseline_dist[-1, churned_idx] - modified_dist[-1, churned_idx]
        ) * n_customers
        sign = "saves" if churn_delta > 0 else "costs"
        # ASCII -> avoids Windows console encoding issues (context_notes requirement)
        return (
            f"{direction} {state_labels[i]} -> {state_labels[j]} by {abs(delta_pp):.0f}pp "
            f"{sign} {abs(churn_delta):.0f} customers."
        )

    return f"{direction} {state_labels[i]} -> {state_labels[j]} by {abs(delta_pp):.0f}pp."
