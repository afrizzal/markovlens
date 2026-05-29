"""Smoke tests for UI-01: Plotly theme template registration.

IMPORTANT: ``import streamlit`` MUST appear before any call to register_theme()
because the 'streamlit' base template is registered by Streamlit at import time
(RESEARCH.md Pitfall 1). Without this the composed default
``"streamlit+markovlens"`` raises ValueError.
"""
from __future__ import annotations

import streamlit  # noqa: F401  — registers 'streamlit' Plotly template (Pitfall 1)
import plotly.io as pio

from app.styles.plotly_theme import register_theme


def test_register_theme_registers_markovlens() -> None:
    """register_theme() must add 'markovlens' to pio.templates."""
    register_theme()
    assert "markovlens" in pio.templates


def test_default_template_is_composed() -> None:
    """After register_theme(), pio.templates.default must be 'streamlit+markovlens'."""
    register_theme()
    assert pio.templates.default == "streamlit+markovlens"


def test_markovlens_colorway() -> None:
    """The markovlens template must use the --chart-1..6 categorical palette."""
    register_theme()
    expected = ["#4338CA", "#059669", "#D97706", "#0891B2", "#DC2626", "#7C3AED"]
    assert list(pio.templates["markovlens"].layout.colorway) == expected
