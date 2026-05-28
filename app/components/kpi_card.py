"""KPI Card — styled metric tile with optional delta and sparkline."""
from __future__ import annotations

import streamlit as st


def kpi_card(
    label: str,
    value: str | int | float,
    delta: str | float | None = None,
    help_text: str | None = None,
    sparkline: list[float] | None = None,
) -> None:
    """Render a single KPI tile.

    For v0.1, falls back to st.metric. Phase 05 polish will swap to custom HTML.
    """
    # TODO(phase05): swap for custom HTML/CSS card matching design system
    st.metric(label=label, value=value, delta=delta, help=help_text)
    if sparkline is not None:
        st.line_chart(sparkline, height=40)
