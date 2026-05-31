<div align="center">

# MarkovLens

**Multi-Domain Forecasting Workbench**

*Same math, different stories — Markov chains applied to real business decisions.*

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B.svg)](https://streamlit.io)
[![DuckDB](https://img.shields.io/badge/Database-DuckDB-FFF000.svg)](https://duckdb.org)

[Demo (coming soon)](#) · [Documentation](docs/) · [User Guide](manual-book.md)

</div>

---

## What is MarkovLens?

MarkovLens is an interactive forecasting workbench that applies **Markov chain models** to two real business problems:

1. **Brand Share Forecaster** — predict e-commerce brand market share evolution over 6-12 months using consumer brand-switching data
2. **Customer Churn States** — model telco customers as states (Active → At-Risk → Inactive → Churned → Reactivated) and forecast retention

Built on academic foundation ([Chan 2015, IJICIC](docs/MARKOV-MODELS.md)) with modern Monte Carlo calibration techniques (10,000-path simulation, longshot-bias adjustment, walk-forward validation).

## Why This Exists

Most BA/BI tools answer *"what happened?"*. MarkovLens answers *"what will happen, and what's the full distribution of possible outcomes?"* — a question every business decision-maker should be asking.

This repository is also a portfolio piece demonstrating:
- Applied probability theory (Markov chains, Monte Carlo simulation)
- Production-grade Python data application (Streamlit + DuckDB + Plotly)
- Business storytelling through interactive data products

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Package Manager | [uv](https://github.com/astral-sh/uv) |
| Web App | [Streamlit](https://streamlit.io) + [streamlit-shadcn-ui](https://github.com/ObservedObserver/streamlit-shadcn-ui) |
| Numerical | NumPy, Pandas, SciPy, scikit-learn |
| Database | [DuckDB](https://duckdb.org) (embedded analytical DB) |
| Visualization | [Plotly](https://plotly.com/python/) |
| Reporting | ReportLab (PDF), Jupyter (notebooks) |
| Testing | pytest |
| Linting | ruff + mypy |

## Quick Start

### 1. Prerequisites

- Python 3.12+ (or let `uv` install it)
- [uv](https://docs.astral.sh/uv/) package manager

Install uv (Windows PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Setup

```bash
git clone https://github.com/afrizzal/markovlens.git
cd markovlens
uv sync
```

### 3. Seed the Database (first time only)

The app reads from a local DuckDB file populated by the seed script. Required before first run:

```bash
uv run python scripts/seed_data.py
```

Expected output: `Seed complete — datasets=2, transitions=7632, matrices=26, forecasts=7`. The script is **idempotent** — safe to re-run if you want to reset state.

> **Note:** The IBM Telco Customer Churn dataset (`data/seed/telco_churn.csv`) is committed to the repository for zero-friction setup. The synthetic brand share dataset is generated procedurally — see [data/SOURCES.md](data/SOURCES.md).

### 4. Run the App

```bash
uv run streamlit run app/Home.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser. Navigate to **Brand Share** from the sidebar to run forecasts.

### 5. Run Tests

```bash
uv run pytest                                    # Full suite (61 tests, ~7s)
uv run pytest --cov=core --cov=domains           # With coverage report
uv run pytest tests/unit/                        # Unit tests only (faster)
uv run pytest tests/integration/ -m integration  # Integration tests against temp DuckDB
```

## Project Structure

```
markovlens/
├── core/                       # Domain-agnostic Markov engine — pure functions, no Streamlit
│   ├── db/                     # DuckDB schema + connection + queries + JSON serialization
│   ├── io/                     # Dataset loaders (CSV/Parquet → validated DataFrame)
│   ├── models.py               # m1, m2, m3 Markov models (Chan 2015 formulation)
│   ├── simulation.py           # Monte Carlo + Becker longshot calibration + quantile bands
│   ├── metrics.py              # MAPE, Brier score, log-loss
│   └── exceptions.py           # DatasetTooSparseError + domain exceptions
├── domains/                    # Domain orchestration — calls core/, returns NumPy-only dataclasses
│   ├── brand_share/            # Domain 1: brand market share (implemented)
│   └── churn/                  # Domain 2: customer churn states (implemented)
├── app/                        # Streamlit multi-page app — UI only, no math
│   ├── Home.py                 # Landing + executive summary
│   ├── pages/                  # 1_Brand_Share.py (impl), 2_Churn.py (impl)
│   ├── components/             # kpi_card, transition_heatmap, monte_carlo_fan, empty_state
│   └── styles/                 # theme.css + plotly_theme.py
├── data/                       # All gitignored EXCEPT data/seed/ (small reference datasets)
│   ├── seed/                   # Committed reference CSVs (e.g. telco_churn.csv) for cold-start deploy
│   ├── raw/                    # Original Kaggle/source files (gitignored)
│   ├── processed/              # Cleaned Parquet (gitignored)
│   └── markovlens.duckdb       # Generated by seed script (gitignored)
├── docs/
│   ├── design-reference/       # Claude Design output — JSX components, markov.css tokens, screenshots
│   │                           # Visual ground truth for UI work; UI-SPEC.md derived from this
│   ├── planning/               # master-plan.md, decisions.md (ADR log), task-progress.md
│   ├── DATABASE.md             # DuckDB schema reference
│   ├── MARKOV-MODELS.md        # Chan 2015 m1/m2/m3 math + worked examples
│   ├── MONTE-CARLO.md          # Simulation + Becker calibration details
│   ├── DEPLOYMENT.md           # Streamlit Cloud deploy guide
│   ├── DATASETS.md             # Dataset sources + preprocessing
│   └── API-REFERENCE.md        # Public engine API
├── tests/
│   ├── unit/                   # Pure-function tests (no DB)
│   └── integration/            # Real temp DuckDB tests (-m integration)
├── scripts/
│   └── seed_data.py            # Idempotent DB seeding (DELETE-then-INSERT pattern)
├── notebooks/                  # Companion Jupyter case studies (gitignored)
├── reports/                    # Generated PDF exports (gitignored)
└── .planning/                  # GSD workflow state — managed automatically, do not hand-edit
```

### Important conventions before adding code

- **`core/` and `domains/` must NOT import Streamlit or Plotly.** They return NumPy arrays + dataclasses. Charts are constructed in `app/components/` from those arrays. Verify with `python -c "from domains.brand_share.service import run_forecast; print('ok')"`.
- **New Streamlit pages in `app/pages/` must include the sys.path prelude** — see [docs/planning/decisions.md](docs/planning/decisions.md) entry `2026-05-31 — sys.path manipulation in Streamlit entry scripts`. Without it, `from app.X` / `from core.X` / `from domains.X` imports fail at runtime (Streamlit adds the entry-script dir to `sys.path`, not the project root).
- **Frontend work consumes `docs/design-reference/`** as the visual contract — extract tokens from `markov.css`, translate JSX patterns to Streamlit equivalents. Do not invent design decisions from scratch.
- **Decisions log is required reading.** Non-obvious patterns (ruff N999 exemption for Streamlit filenames, pytest `--basetemp` config, transitions-table no-PK rationale) are documented in [docs/planning/decisions.md](docs/planning/decisions.md). Check there before "fixing" something that looks unusual.

## Documentation

| Document | Purpose |
|---|---|
| [User Guide / Manual Book](manual-book.md) | How to use the app (Indonesian + English) |
| [Database Schema](docs/DATABASE.md) | DuckDB tables and query patterns |
| [Markov Models](docs/MARKOV-MODELS.md) | Mathematical formulation (m1/m2/m3) |
| [Monte Carlo](docs/MONTE-CARLO.md) | Simulation + calibration methodology |
| [Deployment](docs/DEPLOYMENT.md) | Streamlit Cloud deploy guide |
| [Datasets](docs/DATASETS.md) | Source datasets and preprocessing |
| [API Reference](docs/API-REFERENCE.md) | Public engine API |
| [Planning Index](docs/planning/README.md) | Master plan, decisions, task progress |

## Status

**Version:** 0.1.0 (Alpha — in active development)

**Current Milestone:** v0.1 — Two-domain forecasting workbench, deployed.

See [docs/planning/task-progress.md](docs/planning/task-progress.md) for live task status and [docs/planning/decisions.md](docs/planning/decisions.md) for the technical decision log.

## Roadmap

- [x] **Phase 00** — Project scaffolding + full documentation
- [x] **Phase 01** — Markov engine core (m1/m2/m3 + Monte Carlo + calibration + walk-forward backtest) — 90.76% coverage, 40 tests
- [x] **Phase 02** — Design system + Brand Share page (heatmap, fan chart, model comparison, stationary distribution) — 61 tests, derived from Claude Design prototype
- [x] **Phase 03** — Customer Churn domain (temporal Sankey state flow + what-if simulator) — page live at /Churn
- [ ] **Phase 04** — Home dashboard wired to real KPIs + CSV export + Settings
- [ ] **Phase 05** — Coverage gate + deploy to Streamlit Cloud + production smoke check

## Data Sources

| Dataset | Source | Why committed |
|---|---|---|
| IBM Telco Customer Churn | [Kaggle: blastchar/telco-customer-churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) (originally IBM Watson Sample Data) | Cold-start deployability on Streamlit Cloud — see `data/SOURCES.md` for license context |
| Synthetic FMCG brand share | Generated by `scripts/seed_data.py` (5 brands × 24 periods, hand-crafted base P + Dirichlet noise) | Reproducible synthetic DGP — keeps brand share numerics paper-comparable without claiming to use real proprietary data |

See [`data/SOURCES.md`](data/SOURCES.md) for full attribution, discretization rules, and license context.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, commit conventions, and pull request workflow.

## License

MIT © 2026 afrizzal — see [LICENSE](LICENSE)

## Acknowledgements

- Ka Ching Chan (2015) — *Market Share Modelling and Forecasting Using Markov Chains and Alternative Models* — International Journal of Innovative Computing, Information and Control, Vol. 11, No. 4. Mathematical foundation for the m1/m2/m3 models.
- Becker (2026) — 72.1M Polymarket trade analysis — empirical basis for the longshot-bias calibration table.
