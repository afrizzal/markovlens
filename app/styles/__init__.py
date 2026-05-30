"""Styling — CSS theme injection + Plotly theme template."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.styles.plotly_theme import register_theme

__all__ = ["inject_theme", "register_theme"]

_THEME_CSS = Path(__file__).parent / "theme.css"


def inject_theme() -> None:
    """Inject custom CSS into the Streamlit page."""
    css = _THEME_CSS.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
