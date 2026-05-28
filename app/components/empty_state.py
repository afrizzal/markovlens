"""Empty State — shown when a list/table view has no data."""
from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def empty_state(
    icon: str,
    title: str,
    description: str,
    action: tuple[str, Callable[[], None]] | None = None,
) -> None:
    """Render a styled empty-state block."""
    with st.container():
        st.markdown(f"### {icon} {title}")
        st.caption(description)
        if action is not None:
            label, on_click = action
            st.button(label, on_click=on_click, type="primary")
