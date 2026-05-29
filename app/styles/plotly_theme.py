"""MarkovLens Plotly theme template (UI-01)."""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
from plotly.graph_objs.layout import Template

CATEGORICAL_COLORWAY: list[str] = [
    "#4338CA", "#059669", "#D97706", "#0891B2", "#DC2626", "#7C3AED",
]
HEATMAP_COLORSCALE: list[list] = [
    [0.0, "#EEF2FF"], [0.25, "#C7D2FE"],
    [0.5, "#818CF8"], [0.75, "#4338CA"], [1.0, "#1E1B4B"],
]


def register_theme() -> None:
    """Register the 'markovlens' Plotly template and set the composed default.

    IMPORTANT: the 'streamlit' base template is registered by Streamlit at
    ``import streamlit`` (NOT a Plotly built-in). This function must run after
    Streamlit has been imported — always true inside a Streamlit page, but the
    smoke test/CLI must ``import streamlit`` first (RESEARCH Pitfall 1).
    """
    t = Template()
    t.layout.colorway = CATEGORICAL_COLORWAY
    t.layout.paper_bgcolor = "#FFFFFF"
    t.layout.plot_bgcolor = "#FFFFFF"
    t.layout.font = dict(family="Geist, Inter, -apple-system, sans-serif", size=13, color="#52525B")
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
    t.data.heatmap = [go.Heatmap(colorscale=HEATMAP_COLORSCALE)]
    pio.templates["markovlens"] = t
    pio.templates.default = "streamlit+markovlens"
