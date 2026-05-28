---
name: decision-streamlit
description: Streamlit chosen as web framework — fastest path to BA-grade dashboards. Augmented with streamlit-shadcn-ui + custom CSS for polished look.
metadata:
  type: project
---

**Decision:** Use Streamlit (with `streamlit-shadcn-ui` + custom CSS) as the web UI framework.

**Why:**
- For Business Analyst / BI portfolio target — Streamlit is the de-facto standard
- 10x faster development than Next.js/React for data apps
- Streamlit Cloud free tier = trivial deploy + always-on demo URL for recruiters
- Native Python — no JS context-switching
- Pairs perfectly with Pandas/Plotly/DuckDB

**Augmentation strategy:**
- `streamlit-shadcn-ui` for polished shadcn-style components (cards, tabs, alerts)
- `streamlit-extras` for additional utilities
- Custom CSS via `st.markdown(unsafe_allow_html=True)` from `app/styles/theme.css`
- Plotly themed via custom template in `app/styles/plotly_theme.py`

**How to apply:**
- Pages auto-discovered from `app/pages/` (Streamlit convention)
- Numeric prefix sets order: `1_Brand_Share.py`, `2_Churn.py`
- All UI logic in `app/`; engine logic in `core/`; never mix
- See `streamlit-conventions.md` rule

**Alternatives rejected:**
- Next.js + Python API — over-engineering for solo BA portfolio
- Dash — more powerful but steeper learning + uglier default UI
- NiceGUI/Reflex — newer, less battle-tested

**Design contract:** Claude Design will produce a React+Tailwind mockup (11 pages). We extract design tokens and port styling to Streamlit theme + custom CSS.
