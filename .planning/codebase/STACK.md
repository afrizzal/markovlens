# Technology Stack

**Analysis Date:** 2026-05-29

## Languages

**Primary:**
- Python 3.12+ - Core application language (required by `pyproject.toml`)
- SQL (DuckDB dialect) - Data persistence and querying via `core/db/schema.sql`
- YAML - Streamlit configuration

**Secondary:**
- CSS - Custom theming via `app/styles/theme.css`

## Runtime

**Environment:**
- Python 3.12+ (enforced via `requires-python = ">=3.12"` in `pyproject.toml`)

**Package Manager:**
- `uv` (Astral) - Modern Python package/virtual environment manager
- Lockfile: `uv.lock` (present)
- No pip used directly; all dependencies managed through `pyproject.toml`

## Frameworks

**Core:**
- Streamlit 1.40.0+ - Web application framework (multi-page app via `app/Home.py` and `app/pages/`)
- streamlit-shadcn-ui 0.1.18+ - UI component library with modern design system
- streamlit-extras 0.5.0+ - Additional Streamlit utilities and helpers

**Numerical/Scientific:**
- NumPy 2.0.0+ - Vectorized numerical computations for Markov chains
- Pandas 2.2.0+ - DataFrames for data manipulation and transitions
- SciPy 1.14.0+ - Scientific functions (linear algebra, statistics)
- scikit-learn 1.5.0+ - Machine learning utilities and preprocessing

**Visualization:**
- Plotly 5.24.0+ - Interactive charts (heatmaps, fan charts, Sankey diagrams)

**Testing:**
- pytest 8.3.0+ - Test runner with markers (`slow`, `integration`)
- pytest-cov 6.0.0+ - Code coverage reporting
- pytest-mock 3.14.0+ - Mocking and fixture support

**Build/Dev:**
- ruff 0.7.0+ - Unified linting and code formatting
- mypy 1.13.0+ - Type checking (strict mode for `core/` and `domains/`)
- ipykernel 6.29.0+ - Jupyter kernel for notebook development
- jupyter 1.1.0+ - Notebook environment
- nbformat 5.10.0+ - Notebook format support

## Key Dependencies

**Critical:**
- duckdb 1.1.0+ - Embedded analytical database (file-based, no server required)
  - Location: `data/markovlens.duckdb`
  - Connection: `core/db/connection.py` (singleton pattern)
  - Why it matters: All persistent data, caching, and analytical queries route through DuckDB
  
- pyarrow 18.0.0+ - Apache Arrow for efficient data serialization
  - Used by DuckDB for Parquet I/O
  - Enables native Parquet/CSV reading without intermediate Python objects

**Configuration & Environment:**
- python-dotenv 1.0.0+ - Environment variable loading from `.env`
- pydantic 2.9.0+ - Data validation and modeling
- pydantic-settings 2.6.0+ - Configuration management via Pydantic (used in `core/config.py`)

**Reporting:**
- reportlab 4.2.0+ - PDF report generation (deferred to Phase 04)

## Configuration

**Environment:**
- Configuration source: `core/config.py` (Pydantic-Settings)
- Settings loaded from `.env` file (template: `.env.example`)
- Key env vars:
  - `DUCKDB_PATH` - Path to DuckDB file (default: `data/markovlens.duckdb`)
  - `APP_ENV` - `development` | `production` (default: `development`)
  - `LOG_LEVEL` - Logging verbosity (default: `INFO`)
  - `DEFAULT_RANDOM_SEED` - Monte Carlo reproducibility (default: `42`)
  - `STREAMLIT_SERVER_PORT` - Web server port (default: `8501`)
  - `STREAMLIT_BROWSER_GATHER_USAGE_STATS` - Telemetry (default: `false`)

**Build:**
- `pyproject.toml` - Primary configuration (dependencies, tool settings, metadata)
- `.streamlit/config.toml` - Streamlit UI configuration
  - Theme: light with primary color #4338CA
  - Server: headless, runOnSave enabled
  - Max upload: 200 MB
  - Error details: enabled for development

**Linting & Formatting:**
- ruff: 100 character line length, targets Python 3.12
- Excludes: `notebooks/`, `data/`, `reports/`
- Selected rules: E, F, I, N, W, UP, B, SIM, RUF, C4, PT
- Per-file ignores: `tests/*` ignores S101 (assert_used)

**Type Checking:**
- mypy: Python 3.12, `warn_return_any=true`, `warn_unused_configs=true`
- Non-strict mode globally; enforcement expected via IDE integration

**Testing:**
- pytest: testpaths = `tests/`, strict markers enabled
- Markers: `slow` (deselectable), `integration` (DuckDB-based tests)
- Run: `uv run pytest`

## Platform Requirements

**Development:**
- Python 3.12+
- 500MB+ free disk (DuckDB file + venv)
- Terminal/shell for `uv` commands

**Production (Streamlit Cloud):**
- Deployment target: Streamlit Cloud (free tier)
- Resource constraints: ~1GB RAM, 1 CPU
- DuckDB file size limit: < 500MB (gitignored)
- No long-running background processes

---

*Stack analysis: 2026-05-29*
