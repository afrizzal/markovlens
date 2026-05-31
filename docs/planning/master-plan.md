# MarkovLens — Master Plan

> Living document. Updated when architecture, vision, or patterns evolve.
>
> Last updated: 2026-05-31

## 1. Vision

**MarkovLens** is a multi-domain forecasting workbench that demonstrates how Markov chain modeling can be applied across business problems. The product ships with two distinct domains (brand share, customer churn) running on a shared engine, proving the developer's ability to abstract, generalize, and ship polished data products.

**Audience:** primarily recruiters reviewing this as a Business Analyst / BI portfolio piece; secondarily, business analysts who want to forecast switching/retention dynamics in their own domain.

**Success criteria:**
1. Live demo URL on Streamlit Cloud (recruiter clicks → working app in 5 seconds)
2. Two complete domain demonstrations with real data
3. Story-driven README that hooks a senior reader in 60 seconds
4. Documentation good enough that another developer could pick up and contribute
5. Lead to at least one job interview within 60 days of launch

## 2. Core Value Proposition

> "Same math, different stories — Markov chains applied to real business decisions."

Most BA/BI portfolios show EDA on Titanic/Iris/Boston Housing. MarkovLens shows applied probability + interactive forecasting + production engineering on multiple real datasets. The unfair advantage: **academic rigor** (Chan 2015 IJICIC) + **modern calibration techniques** (Becker 2026 longshot bias) + **deployable artifact** (live URL).

## 3. Architecture

### Layered Design

```
┌─────────────────────────────────────────────────────┐
│  app/  (Streamlit UI — pages, components, styles)   │  ← User-facing
└───────────────────┬─────────────────────────────────┘
                    │ (calls)
┌───────────────────▼─────────────────────────────────┐
│  domains/  (brand_share/, churn/ — orchestration)   │  ← Domain logic
└───────────────────┬─────────────────────────────────┘
                    │ (calls)
┌───────────────────▼─────────────────────────────────┐
│  core/  (models, simulation, metrics, db, io)       │  ← Pure engine
└───────────────────┬─────────────────────────────────┘
                    │ (reads/writes)
┌───────────────────▼─────────────────────────────────┐
│  data/markovlens.duckdb  +  data/raw/*.parquet      │  ← Storage
└─────────────────────────────────────────────────────┘
```

**Rules:**
- `core/` is **domain-agnostic** and **Streamlit-free**. Pure functions + DB writes only.
- `domains/` orchestrates: takes raw user request, calls `core/`, returns domain-shaped results.
- `app/` is Streamlit-only. No Markov computation here.
- Tests cover `core/` to >80%; `domains/` to >60%; `app/` is manually QA'd.

### Data Flow (Example: Brand Share Forecast)

```
User clicks "Run Forecast"
  ↓
app/pages/1_Brand_Share.py
  ↓
domains/brand_share/service.py::run_forecast()
  ↓
core/models.py::build_m2_matrix(transitions)
  ↓
core/simulation.py::monte_carlo(matrix, n_steps=12)
  ↓
core/simulation.py::calibrate_probability(raw)
  ↓
core/db/queries.py::save_forecast(result)
  ↓
domains/brand_share/transforms.py::shape_for_chart(result)
  ↓
back to app/ → Plotly fan chart
```

## 4. Agreed Patterns

### 4.1 Database

- **DuckDB** as embedded analytical DB (file: `data/markovlens.duckdb`)
- Schema in `core/db/schema.sql`, simple `CREATE TABLE IF NOT EXISTS`
- All queries via `core/db/queries.py`
- See [.claude/rules/data-storage.md](../../.claude/rules/data-storage.md)

### 4.2 Markov Models

Implement Chan (2015) formulations m1, m2, m3 in v1. Defer m4 to v0.2.

```python
# core/models.py
class M1Homogeneous:
    """Constant transition matrix P. Y_{t+1} = Y_t · P."""

class M2TimeVarying:
    """Time-varying P_t. Y_{t+1} = Y_t · P_t."""

class M3Extended:
    """With growth multiplier G. Q_{t+1} = (G ⊙ Q_t) · P_t."""
```

See [.claude/rules/markov-patterns.md](../../.claude/rules/markov-patterns.md) for validation rules.

### 4.3 Monte Carlo

- 10,000 simulations default
- Reproducible via `seed` parameter (default 42)
- Always apply **longshot calibration** (Becker 2026 table) before returning probabilities
- Cache results in DuckDB `simulation_runs` table

### 4.4 UI

- **Streamlit** + `streamlit-shadcn-ui` + custom CSS theme
- Color tokens defined in `app/styles/theme.css` (CSS variables)
- Plotly theme template in `app/styles/plotly_theme.py`
- Layout: sidebar nav + main content area, max-width 1440px
- See [.claude/rules/streamlit-conventions.md](../../.claude/rules/streamlit-conventions.md)

### 4.5 Documentation

After every coding session, update (in this order):
1. `docs/planning/task-progress.md`
2. `docs/planning/decisions.md` (if new decision)
3. `CLAUDE.md` (if new page/module)
4. `README.md` (if user-visible change)
5. `manual-book.md` (if workflow changed)

## 5. Roadmap (High-Level)

| Phase | Goal | Status |
|---|---|---|
| **01** | Markov engine core (m1/m2/m3 + Monte Carlo + calibration + walk-forward validation) | ✅ Done — 90.76% coverage, 40 tests |
| **02** | Design system + Brand Share domain (heatmap, fan chart, model comparison, stationary) | ✅ Done — 61 tests, live at /Brand_Share |
| **03** | Customer Churn domain (absorbing chain, Sankey state flow, what-if simulator) | ✅ Done — 81 tests, live at /Churn |
| **04** | Home dashboard wired to real KPIs + CSV export + Settings page | 🔲 Next |
| **05** | Coverage gate + deploy to Streamlit Cloud + production smoke check | 🔲 Pending |

Detailed phase plans in `.planning/phases/NN-*/` (created via `/gsd:plan-phase N`).

> **Note on phase numbering:** The GSD workflow system (`.planning/`) uses 01-05 numbering. Earlier drafts of this document used a different 00-07 numbering. The GSD numbering is authoritative — see `.planning/STATE.md` for live status.

## 6. Non-Goals (Explicit)

To keep v1 focused:

- ❌ Real-time data ingestion (batch only)
- ❌ Multi-user / auth (single-user demo)
- ❌ Mobile-optimized layout (desktop-first)
- ❌ Model m4 (non-Markov) — deferred to v0.2
- ❌ Predictive ML beyond Markov (no XGBoost, no LSTM) — purity of demo
- ❌ Polymarket/crypto trading integration — domain risk for BA portfolio
- ❌ Internationalization beyond ID/EN docs

## 7. Constraints

- **Solo developer** (user + Claude Code as pair)
- **Timeline:** 4 weeks to recruiter-ready v0.1
- **Stack:** Python 3.12 + Streamlit + DuckDB only — no JS frontend
- **Hosting:** Streamlit Cloud free tier (1GB RAM, 1 CPU, no persistent disk)
- **Data:** Public Kaggle datasets only (no proprietary)
- **Storage:** DuckDB file < 500MB
- **Token budget:** dual-terminal pattern (Opus brainstorm, Sonnet execute) to manage cost

## 8. Open Questions

- [ ] Custom domain for live demo? (e.g., `markovlens.app`)
- [ ] Add unit tests via GitHub Actions CI?
- [ ] Add screenshots/animated GIFs to README?
- [ ] Translate manual-book to other languages beyond ID/EN?

## 9. References

- Chan, K. C. (2015). *Market Share Modelling and Forecasting Using Markov Chains and Alternative Models*. IJICIC 11(4). [PDF available locally at `docs/references/`]
- Becker (2026). *72.1M Polymarket Trade Analysis*. [Empirical calibration table source]
- Streamlit docs: https://docs.streamlit.io
- DuckDB Python docs: https://duckdb.org/docs/api/python/overview
