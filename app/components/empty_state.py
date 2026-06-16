"""Empty State component — custom-HTML fallback for list/table views with no data (UI-02, D-06).

Matches the ``EmptyState`` component contract from
``docs/design-reference/js/ui.jsx`` (line 222-233).
"""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def empty_state(
    icon: str,
    title: str,
    description: str,
    *,
    action_label: str | None = None,
    action_callback: Callable[[], None] | None = None,
) -> None:
    """Render a styled empty-state block with custom HTML.

    Parameters
    ----------
    icon : str
        Unicode symbol or short text displayed in the icon well
        (e.g. ``"---"``, ``"empty"``).
    title : str
        Heading text rendered in ``.t-h3`` (18px semibold).
    description : str
        Explanatory body rendered in ``.t-sm .t-sec`` (14px secondary color).
    action_label : str | None
        Optional CTA button label.  When provided, ``action_callback`` is
        attached as the ``on_click`` handler.
    action_callback : Callable | None
        Callable invoked when the action button is clicked.
    """
    html = f"""<div style="max-width:480px;margin:0 auto;padding:var(--space-7) var(--space-5);
  display:flex;flex-direction:column;align-items:center;text-align:center;gap:var(--space-3);">
  <div style="width:56px;height:56px;border-radius:var(--radius-md);
    background:var(--color-surface-sunken);
    display:flex;align-items:center;justify-content:center;
    font-size:26px;color:var(--color-text-tertiary);">
    {icon}
  </div>
  <div class="t-h3">{title}</div>
  <div class="t-sm t-sec" style="text-wrap:pretty;">{description}</div>
</div>"""

    st.markdown(html, unsafe_allow_html=True)

    if action_label is not None:
        # Streamlit buttons cannot live inside injected HTML
        _col_l, col_btn, _col_r = st.columns([1, 2, 1])
        with col_btn:
            st.button(
                action_label,
                type="primary",
                on_click=action_callback,
                use_container_width=True,
            )
