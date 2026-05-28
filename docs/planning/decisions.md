# Technical Decisions Log (ADR-style)

> Append-only log of technical decisions with rationale. Newest at top.

---

## 2026-05-28 — Use Streamlit + streamlit-shadcn-ui as web framework

**Context:** Need to pick a UI framework for BA/BI portfolio piece. Target audience is recruiters and data analysts. Solo developer, 4-week timeline.

**Decision:** Use Streamlit augmented with `streamlit-shadcn-ui` and custom CSS theme.

**Why:**
- Fastest path from Python code to polished BA-grade dashboard
- Streamlit Cloud free tier gives always-on demo URL (critical for recruiter clicks)
- `streamlit-shadcn-ui` brings shadcn-quality components into Streamlit
- Custom CSS via `st.markdown(unsafe_allow_html=True)` covers the rest
- Avoids JS context-switching for solo Python dev

**Impact:**
- All UI logic lives in `app/` (Streamlit-only)
- Pages auto-discovered from `app/pages/` (numeric prefix = order)
- Design tokens defined as CSS variables in `app/styles/theme.css`
- Plotly themed via template in `app/styles/plotly_theme.py`

**Alternatives considered:**
- Next.js + Python FastAPI — over-engineering, splits attention across two stacks
- Dash — more powerful but uglier defaults, steeper learning
- NiceGUI / Reflex — newer, less battle-tested for production demos

---

## 2026-05-28 — Use DuckDB as storage layer

**Context:** Need an embedded database for storing datasets, computed transition matrices, simulation cache, and forecasts. Must work on Streamlit Cloud free tier (no external services). User is new to Python and wants a beginner-friendly DB.

**Decision:** Use DuckDB (file: `data/markovlens.duckdb`) for all persistent data.

**Why:**
- 10-100x faster than SQLite for analytical queries (column store, vectorized execution)
- Reads CSV/Parquet directly via `SELECT * FROM 'path.parquet'` — no import step needed
- Integrates seamlessly with Pandas (`.df()` method) and NumPy (`.fetchnumpy()`)
- File-based — works on Streamlit Cloud without external service
- ACID transactions for safety
- Native Python API simpler than SQLAlchemy
- Beginner-friendly — `pip install duckdb`, `import duckdb`, done

**Impact:**
- Schema in `core/db/schema.sql` (simple `CREATE TABLE IF NOT EXISTS`)
- Connection singleton in `core/db/connection.py`
- Queries wrapped in `core/db/queries.py` (no raw SQL scattered in app/)
- No ORM — keep it simple
- `*.duckdb` files gitignored (binary, regenerable from raw CSVs)
- Migrations: simple `if not exists` blocks (no Alembic — overkill)

**Alternatives considered:**
- SQLite — too slow for aggregations on > 100k rows
- PostgreSQL — overkill, requires server, complicates Streamlit Cloud deploy
- Pandas + Parquet only — no SQL, harder to reproduce analysis
- Polars — complementary to DuckDB but not a storage layer

---

## 2026-05-28 — Use uv as Python package manager

**Context:** Need a package manager for solo Python project. User is new to Python and wants minimal tooling complexity.

**Decision:** Use `uv` (from Astral) for all dependency and Python version management.

**Why:**
- 10-100x faster than pip/poetry (written in Rust)
- Single tool: venv + dependency resolution + install + Python version
- Simpler syntax: `uv add <pkg>`, `uv run <cmd>`, `uv sync`
- `uv run` auto-activates the venv — no manual `source .venv/bin/activate`
- Becoming Python community standard in 2025+
- Fewer concepts for a Python beginner to learn

**Impact:**
- `pyproject.toml` declares all deps under `[project]` and `[dependency-groups]`
- `.python-version` pins Python 3.12
- CI/scripts always prefix commands with `uv run`
- Never use `pip install` directly — always `uv add <pkg>` then `uv sync`
- User manual step: install uv via PowerShell `irm https://astral.sh/uv/install.ps1 | iex`

**Alternatives considered:**
- pip + venv — too manual, slower
- poetry — more verbose syntax, slower
- conda — too heavy for this project, environment-management overhead

---

## 2026-05-28 — Use GSD as primary planning workflow

**Context:** Need a project planning + tracking system. User already uses GSD productively in social-media-ai (production app). Other options considered: Spec Kit, claude-code-spec-workflow.

**Decision:** Use GSD (Get Shit Done) as primary planning system, supplemented by ad-hoc plans in `docs/planning/plans/` for non-phase work.

**Why:**
- User already battle-tested it
- Provides milestone → roadmap → phase → plan → execute workflow
- Auto-managed `.planning/` state files reduce cognitive load
- Wave-based parallel execution for `/gsd:execute-phase`
- Integrates with state-tracking and verification hooks

**Impact:**
- `.planning/` is GSD-owned — never manually edit
- Custom plans go in `docs/planning/plans/` via `/create-plan` command
- New phases via `/gsd:plan-phase N` then `/gsd:execute-phase N`
- Bug investigations via `/gsd:debug`
- Trivial fixes via `/gsd:fast <desc>`

**Alternatives considered:**
- GitHub Spec Kit — overkill for solo 4-week project; overlap with GSD
- claude-code-spec-workflow — fundamentally the same as GSD; adding both = confusion
- Manual planning in markdown — works but loses tracking discipline

---

## 2026-05-28 — Implement Chan (2015) m1/m2/m3 in v1; defer m4

**Context:** Chan 2015 paper proposes 4 model formulations. Each has different assumptions and complexity.

**Decision:** Implement m1 (Homogeneous), m2 (Time-varying), m3 (Extended with growth multiplier) in v0.1. Defer m4 (Non-Markov, category-based) to v0.2.

**Why:**
- m1/m2/m3 cover the spectrum of market-share modeling assumptions
- m4 is fundamentally different (no transition matrix) and would require separate UI/visualization
- 4-week timeline forces focus
- 3 models is enough to demonstrate model comparison (key portfolio feature)

**Impact:**
- `core/models.py` has 3 classes: `M1Homogeneous`, `M2TimeVarying`, `M3Extended`
- UI model selector has 3 options (m1, m2, m3)
- Model comparison page shows side-by-side accuracy
- README roadmap explicitly lists m4 as v0.2 backlog item

**Alternatives considered:**
- Implement all 4 — risks not finishing v0.1 polish
- Implement only m1 — too thin, doesn't demonstrate model comparison

---

## 2026-05-28 — Apply Becker (2026) longshot-bias calibration as default

**Context:** Raw Monte Carlo simulations systematically overestimate the probability of rare events. Becker (2026) analysis of 72.1M Polymarket trades produced an empirical calibration table.

**Decision:** Apply the Becker calibration table by default to all Monte Carlo outputs. Expose raw probability alongside calibrated for transparency.

**Why:**
- Without calibration, the app would systematically mislead users about tail risk
- Becker table is empirically derived from a massive dataset (most rigorous available)
- Calibration is the differentiator from "homemade Monte Carlo" tutorials
- Showing both raw + calibrated demonstrates understanding of bias

**Impact:**
- `LONGSHOT_CALIBRATION` constant in `core/simulation.py`
- `calibrate_probability(raw_prob: float) -> float` function
- UI shows both numbers with a small "calibration applied" badge
- Documented in `docs/MONTE-CARLO.md`
- Changing the table requires updating citation + rerunning backtests + logging in this file

**Alternatives considered:**
- No calibration — would produce systematically biased probabilities
- Custom calibration from our own data — not enough volume to be meaningful
- User-toggleable — adds UX complexity; default-on with transparency is cleaner

---

## Template for Future Entries

```markdown
## YYYY-MM-DD — <Decision Title>

**Context:** <What problem prompted this decision?>

**Decision:** <What did we decide?>

**Why:** <Bullet list of reasons>

**Impact:** <What code/process changes does this drive?>

**Alternatives considered:**
- Option A — rejected because X
- Option B — rejected because Y
```
