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

### 3. Run the App

```bash
uv run streamlit run app/Home.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Run Tests

```bash
uv run pytest
```

## Project Structure

```
markovlens/
├── core/                    # Markov engine (reusable across domains)
│   ├── db/                  # DuckDB schema + connection
│   ├── io/                  # Dataset loaders
│   ├── models.py            # m1, m2, m3 Markov models (Chan 2015)
│   ├── simulation.py        # Monte Carlo + calibration
│   └── metrics.py           # Brier, MAPE, log-loss
├── domains/
│   ├── brand_share/         # Domain 1: brand market share
│   └── churn/               # Domain 2: customer churn states
├── app/                     # Streamlit multi-page app
│   ├── Home.py              # Landing + executive summary
│   ├── pages/               # 1_Brand_Share.py, 2_Churn.py, etc.
│   ├── components/          # Reusable UI components
│   └── styles/              # CSS theme
├── notebooks/               # Companion Jupyter case studies
├── tests/                   # pytest test suite
├── data/                    # DuckDB file + raw/processed datasets (gitignored)
├── reports/                 # Generated PDF exports (gitignored)
├── docs/                    # Technical + planning documentation
└── scripts/                 # One-off utility scripts
```

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

**Version:** 0.1.0 (Alpha)

**Current Milestone:** v0.1 — Core engine + Brand Share domain + UI polish

See [task-progress.md](docs/planning/task-progress.md) for live status.

## Roadmap

- [x] Project scaffolding + documentation
- [ ] Phase 1: Markov engine core (m1, m2, m3) + tests
- [ ] Phase 2: Brand Share domain + Streamlit page
- [ ] Phase 3: Customer Churn domain + Streamlit page
- [ ] Phase 4: Polish + deploy to Streamlit Cloud

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
