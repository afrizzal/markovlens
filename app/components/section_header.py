"""Section Header — page-section title with optional description."""
from __future__ import annotations

import streamlit as st


def section_header(title: str, description: str | None = None) -> None:
    """Render a section header with optional caption."""
    st.subheader(title)
    if description:
        st.caption(description)
