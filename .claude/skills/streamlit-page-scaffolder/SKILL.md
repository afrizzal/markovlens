---
name: streamlit-page-scaffolder
description: Scaffold a new Streamlit page that follows MarkovLens conventions — set_page_config, theme injection, layout grid, KPI strip, tabs, error handling. Use when creating a new page in app/pages/.
allowed-tools: Read, Write, Edit
---

# Streamlit Page Scaffolder

Generate a new Streamlit page that conforms to the project's conventions, theme, and component patterns.

## When to Use

- Creating any file under `app/pages/N_<Name>.py`
- Creating `app/Home.py` (root page)
- Refactoring an existing page to match conventions

## Page Template

```python
"""<Page purpose> page for MarkovLens."""
from __future__ import annotations

import streamlit as st

from app.components import (
    empty_state,
    kpi_card,
    section_header,
)
from app.styles import inject_theme
from domains.<domain> import service

# ── Page Config (must be first Streamlit call) ─────────────
st.set_page_config(
    page_title="<Title> — MarkovLens",
    page_icon="<single emoji or favicon>",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

# ── Session State Init ──────────────────────────────────────
PAGE_NS = "<page_namespace>"  # e.g., "brand_share"
if f"{PAGE_NS}.initialized" not in st.session_state:
    st.session_state[f"{PAGE_NS}.initialized"] = True
    st.session_state[f"{PAGE_NS}.last_result"] = None

# ── Header ──────────────────────────────────────────────────
section_header(
    title="<Page Title>",
    description="<One-line description>",
)

# ── Controls ────────────────────────────────────────────────
with st.container():
    col_a, col_b, col_c, col_run = st.columns([3, 2, 2, 1])
    # ... selectboxes, sliders, etc.
    run = col_run.button("Run", type="primary", use_container_width=True)

# ── Loading + Error Handling ────────────────────────────────
if run:
    try:
        with st.spinner("Computing..."):
            result = service.run(...)
        st.session_state[f"{PAGE_NS}.last_result"] = result
    except service.DatasetTooSparseError as e:
        st.error(f"Not enough data: {e}")
        st.info("Try selecting a longer date range or merging sparse states.")
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        if st.session_state.get("dev_mode"):
            st.exception(e)
        st.stop()

# ── Empty State ─────────────────────────────────────────────
result = st.session_state.get(f"{PAGE_NS}.last_result")
if result is None:
    empty_state(
        icon="<icon>",
        title="No <thing> yet",
        description="Click 'Run' above to generate your first <thing>.",
    )
    st.stop()

# ── KPI Strip ───────────────────────────────────────────────
kpi_cols = st.columns(4)
for col, kpi in zip(kpi_cols, result.kpis):
    with col:
        kpi_card(label=kpi.label, value=kpi.value, delta=kpi.delta)

# ── Tabs (sub-views) ────────────────────────────────────────
tab_overview, tab_detail, tab_compare = st.tabs(["Overview", "Detail", "Compare"])

with tab_overview:
    st.plotly_chart(result.overview_chart, use_container_width=True)

with tab_detail:
    st.plotly_chart(result.detail_chart, use_container_width=True)

with tab_compare:
    st.dataframe(result.comparison_df, use_container_width=True, hide_index=True)
```

## Procedure

1. **Ask user (or infer from path):** page name, namespace, domain it belongs to
2. **Generate the file** at `app/pages/<N>_<Name>.py` with template above
3. **Replace placeholders** with concrete values
4. **Verify imports** — components and service must exist (create stubs if needed)
5. **Update CLAUDE.md** — add row to App Pages table

## Output

After writing the file:
- Print the path created
- List any new component stubs or service stubs that need implementing
- Suggest the next step (implement service, design chart, write test)

## DO NOT

- ❌ Skip `st.set_page_config()` — must be first Streamlit call
- ❌ Put Markov logic in the page file — wrap in `domains/*/service.py`
- ❌ Use `st.experimental_*` APIs (deprecated)
- ❌ Hardcode colors — use the theme
