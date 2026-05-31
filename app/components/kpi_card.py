"""KPI Card component — custom-HTML metric tile (UI-02, D-06/D-07).

Renders a styled KPI card with an accent top-bar, label, large value, optional
delta indicator, and optional sparkline SVG.  Matches the ``KPICard`` component
contract from ``docs/design-reference/js/ui.jsx`` (line 99-122).
"""

from __future__ import annotations

import streamlit as st


def _sparkline_svg(data: list[float], *, accent: str, width: int = 96, height: int = 28) -> str:
    """Generate a minimal inline SVG polyline for the sparkline.

    Parameters
    ----------
    data : list[float]
        8-12 data points (any numeric range; normalized internally).
    accent : str
        Stroke color — the card's ``accent`` CSS variable string.
    width : int
        SVG viewBox width in px.
    height : int
        SVG viewBox height in px.

    Returns
    -------
    str
        SVG markup string (empty string if data has fewer than 2 points).
    """
    if len(data) < 2:
        return ""
    lo, hi = min(data), max(data)
    span = (hi - lo) or 1.0
    pad = 2

    def _x(i: int) -> float:
        return i * (width - 1) / (len(data) - 1)

    def _y(v: float) -> float:
        return (height - pad) - ((v - lo) / span) * (height - 2 * pad)

    points = " ".join(f"{_x(i):.1f},{_y(v):.1f}" for i, v in enumerate(data))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" style="display:block;">'
        f'<polyline points="{points}" fill="none" stroke="{accent}" stroke-width="1.5" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f"</svg>"
    )


def kpi_card(
    label: str,
    value: str,
    *,
    unit: str | None = None,
    delta: float | None = None,
    delta_suffix: str = "%",
    sparkline: list[float] | None = None,
    accent: str = "var(--color-primary)",
    icon: str | None = None,
    tooltip: str | None = None,
) -> None:
    """Render a single KPI metric card with custom HTML.

    Parameters
    ----------
    label : str
        Uppercase label text rendered via ``.t-label``.
    value : str
        Primary metric value.  Use ``"---"`` for empty/loading state.
    unit : str | None
        Optional unit suffix in smaller tertiary text (e.g. ``"%"``).
    delta : float | None
        Signed delta value.  Positive uses success color with up-arrow,
        negative uses danger color with down-arrow.
        Omitted when ``None`` or when ``value == "---"``.
    delta_suffix : str
        Unit after the delta value (default ``"%"``; use ``"pp"`` for
        percentage points).
    sparkline : list[float] | None
        8-12 data points for a mini sparkline SVG.
    accent : str
        CSS color value for the top accent bar and sparkline stroke.
    icon : str | None
        Unicode symbol or short text label shown before the label.
    tooltip : str | None
        Hover tooltip text added as ``title`` attribute on the label row.
    """
    is_empty = value == "---" or value == "—"

    # Icon in top-right corner (faded, accent-colored; matches prototype lines 25-28)
    corner_icon_html = ""
    if icon is not None:
        corner_icon_html = (
            f'<div style="position:absolute;top:var(--space-3,12px);right:var(--space-3,12px);'
            f'opacity:0.35;color:{accent};line-height:0;">{icon}</div>'
        )

    # Label row
    tooltip_attr = f' title="{tooltip}"' if tooltip else ""
    label_html = (
        f'<div class="t-label" style="display:flex;align-items:center;"{tooltip_attr}>{label}</div>'
    )

    # Value row
    unit_html = (
        f'<span class="t-xs t-ter mono" style="margin-left:2px;">{unit}</span>'
        if unit is not None
        else ""
    )
    value_style = (
        "font-size:var(--fs-32);font-weight:600;"
        "font-family:var(--font-mono);"
        "letter-spacing:-0.02em;line-height:1.2;"
    )
    if is_empty:
        value_html = f'<div class="t-ter mono" style="{value_style}">{value}</div>'
    else:
        value_html = f'<div class="mono" style="{value_style}">{value}{unit_html}</div>'

    # Delta row (only when delta provided and value is not empty placeholder)
    delta_html = ""
    if delta is not None and not is_empty:
        if delta >= 0:
            arrow = "&#9650;"  # ▲
            color = "var(--color-success)"
        else:
            arrow = "&#9660;"  # ▼
            color = "var(--color-danger)"
        delta_html = (
            f'<div class="mono" style="font-size:var(--fs-12);font-weight:600;'
            f'color:{color};margin-top:var(--space-1);">'
            f"{arrow} {abs(delta):.1f}{delta_suffix}"
            f"</div>"
        )

    # Sparkline SVG below value/delta
    sparkline_html = ""
    if sparkline is not None and len(sparkline) >= 2:
        svg = _sparkline_svg(sparkline, accent=accent)
        sparkline_html = f'<div style="margin-top:var(--space-2);">{svg}</div>'

    card_html = (
        f'<div class="card accent-card card-pad" '
        f'style="--accent:{accent};padding:var(--space-5);'
        f"display:flex;flex-direction:column;gap:var(--space-3);"
        f'position:relative;">'
        f"{corner_icon_html}"
        f"{label_html}"
        f"{value_html}"
        f"{delta_html}"
        f"{sparkline_html}"
        f"</div>"
    )

    st.markdown(card_html, unsafe_allow_html=True)
