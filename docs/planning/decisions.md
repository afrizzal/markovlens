# Technical Decisions Log (ADR-style)

> Append-only log of technical decisions with rationale. Newest at top.

---

## 2026-06-16 — Re-seed runs in-process, not via subprocess (DuckDB single-writer lock)

**Context:** On the live Streamlit Cloud deployment, the Settings → Advanced → "Re-run seed script" button failed with `IO Error: Could not set lock on file "…/markovlens.duckdb": Conflicting lock is held in …/python3.12 (PID 88)`. The handler spawned `uv run python scripts/seed_data.py` as a **separate OS process**, which called `get_connection()` → `duckdb.connect(path)` and tried to open the same DuckDB file the running app process already held open via `app/db.py get_db()` (`@st.cache_resource`). DuckDB enforces a single read-write process per file, so the second connection was rejected. This never surfaced in local dev when the app wasn't running, masking the bug until production.

**Decision:** Re-seeding runs **in-process** against the app's existing cached connection — never by spawning a second process.
1. Added a public `seed_database(conn: duckdb.DuckDBPyConnection) -> dict[str, int]` entrypoint in `scripts/seed_data.py` (applies schema, runs `_seed_brand_share` + `_seed_churn`, returns row counts, keeps the `forecasts >= 5` assertion).
2. `main()` now delegates to `seed_database(get_connection())` (CLI behavior unchanged).
3. `app/pages/4_Settings.py` calls `seed_database(get_db())` directly inside the button handler — `subprocess` import removed.

**Why:**
- One process, one writer — eliminates the file-lock conflict entirely (the root cause), rather than papering over it with retries.
- Reuses the same connection the cold-start path already uses (`core/db/init.py ensure_seeded` imports the same `_seed_*` helpers), so behavior is consistent across cold-start auto-seed and manual re-seed.
- Faster and dependency-light on Streamlit Cloud — no `uv` subprocess spin-up, no second venv resolution.
- Idempotent already guaranteed by D-23 DELETE-WHERE in each `_seed_*` helper, so running on the live connection is safe.

**Impact:**
- `scripts/seed_data.py` — new `seed_database()`; `main()` refactored to use it.
- `app/pages/4_Settings.py` — in-process call; richer success message (shows dataset + forecast counts); `subprocess` removed.
- Commit `8d99e15`. 10 related tests (`test_queries.py`, `test_db_init.py`) green; ruff clean.

**Alternatives considered:**
- Close the app's cached connection before spawning the subprocess, then reconnect — rejected: fragile under multiple concurrent Streamlit sessions, and DuckDB lock release/re-acquire timing is racy.
- Retry-with-backoff on the lock — rejected: doesn't fix the cause; the app holds the lock for its whole lifetime, so retries always fail.
- Run seed against an in-memory copy then swap files — rejected: massively over-engineered for a 7k-row demo dataset.

---

## 2026-05-31 — sys.path manipulation in Streamlit entry scripts

**Context:** Brand Share page crashed at runtime with `ModuleNotFoundError: No module named 'app'` on the line `from app.components.empty_state import empty_state`. Pytest passed all imports fine; the failure was Streamlit-runtime-specific. Investigation revealed that Streamlit adds the **entry script's directory** (`app/`) to `sys.path`, not the project root — so `from app.X`, `from core.X`, `from domains.X` all fail at runtime even though they resolve correctly under pytest (where project root is the rootdir).

**Decision:** Every Streamlit entry script (`app/Home.py` and every `app/pages/*.py`) prepends the project root to `sys.path` at the top of the file, before any local imports. Pattern:

```python
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # parents[1] for Home.py
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
```

**Why:**
- Project-root-on-sys.path makes import style uniform across runtime and tests (`from app.X`, `from core.X`, `from domains.X` all work in both contexts)
- Adding the hack at the top of each entry script is reliable — runs before any local import is attempted
- `parents[2]` works from `app/pages/X.py` (3 levels up); `parents[1]` from `app/Home.py` (2 levels up)
- Idempotent — the `if not in sys.path` check prevents duplicate insertion across reloads

**Impact:**
- `app/Home.py` has the hack with `parents[1]`
- `app/pages/1_Brand_Share.py` has the hack with `parents[2]`
- **Every future page file (e.g., Phase 03 `2_Churn.py`, Phase 04 settings pages) MUST include this hack at the top** before any local import
- No changes needed to `core/`, `domains/`, or test setup
- pytest behavior unchanged (project root already in sys.path via rootdir)

**Alternatives considered:**
- Change all `from app.X` imports to `from X` (relying on Streamlit's `app/` injection) — rejected because it breaks pytest (which needs `from app.X`) and creates inconsistency with `from core.X` / `from domains.X` which still need project root
- Use a `conftest.py`-style early-loading module — doesn't apply to Streamlit runtime, only pytest
- Configure Streamlit to set PYTHONPATH — Streamlit has no such config option
- Use `__init__.py` in `app/` to manipulate sys.path — runs only when `app` is imported as a package, but Streamlit treats `Home.py` as a script, so `app/__init__.py` doesn't execute

---

## 2026-05-31 — Phase 02 scope creep on app/Home.py; reaffirm no separate Reports page

**Context:** Phase 02 execution (Design System + Brand Share) modified `app/Home.py` and added `st.page_link` references to `pages/2_Churn.py` (Phase 03 deliverable) and `pages/3_Reports.py` (which was explicitly excluded from v1 per earlier scope decision — CSV export is embedded in domain pages, no separate Reports page in v1). This caused `StreamlitPageNotFoundError` at runtime because the referenced files don't exist. `app/Home.py` is properly a **Phase 04** deliverable (HOME-01 in requirements).

**Decision:** Apply minimal quick fix now without expanding Phase 02 scope further:
1. Make the Churn page link **conditional** on file existence (will activate automatically when Phase 03 ships `pages/2_Churn.py`)
2. **Remove** the Reports page link entirely (no separate Reports page in v1 per scope decision; CSV export will be embedded in Brand Share and Churn pages)
3. Update the "Recent Forecasts" empty-state copy to reference only Brand Share (since Churn isn't available yet)

Defer the proper, complete Home.py rebuild to Phase 04 (HOME-01: wired KPIs from real DB, populated recent forecasts list, etc.).

**Why:**
- Quick fix unblocks Phase 02 verification (Brand Share page must be reachable to manually QA the design system)
- Reaffirming the "no separate Reports page" decision prevents future scope drift — Phase 06 was originally planned for Reports but was folded into per-domain CSV exports during requirements review
- Conditional page link pattern is forward-compatible — no re-edit needed when Phase 03 ships
- Full Home.py rebuild belongs in Phase 04 where KPI strip wiring + recent forecasts integration with the `forecasts` table can be done together

**Impact:**
- `app/Home.py`: conditional Churn link (file-exists check), Reports link removed, intro copy updated
- Phase 04 PLAN.md (when generated) must:
  - Replace the conditional Churn link with an unconditional one
  - Wire real KPIs from DuckDB (dataset count, last forecast timestamp, total runs, average MAPE)
  - Populate "Recent Forecasts" from the `forecasts` table
  - Verify pre-seed forecast count satisfies cold-start UX (per Phase 01 criterion #5)
- Planner agents should respect phase boundaries even when "convenient" forward-references seem helpful — flag as lesson learned for future plan reviews

**Alternatives considered:**
- Full Home.py rebuild now — rejected because it expands Phase 02 scope further (compounding the original creep), and Phase 04 has the proper context to do it right (real DB integration, KPI wiring)
- Remove all page_links including Brand Share — rejected because Brand Share IS deliverable in Phase 02 and the link is functional
- Add a Phase 06 for separate Reports page — already rejected during requirements review; this just reaffirms

---

## 2026-05-29 — Streamlit page filenames exempt from ruff N999

**Context:** During Phase 01 verification, `uv run ruff check .` flagged `app/Home.py` with `N999 Invalid module name: 'Home'` (rule requires lowercase module names). However, Streamlit **mandates** PascalCase filenames for multi-page apps — `Home.py` is the entry script convention, and `pages/1_Brand_Share.py`, `pages/2_Churn.py`, etc. follow the `N_Title_Case.py` pattern that Streamlit uses for sidebar ordering and labeling. The two conventions conflict directly.

**Decision:** Add a scoped exception in `pyproject.toml` to ignore N999 for all files under `app/`:

```toml
[tool.ruff.lint.per-file-ignores]
"app/**/*.py" = ["N999"]
```

**Why:**
- Streamlit's PascalCase requirement is non-negotiable (auto-discovery + sidebar label depend on it)
- Renaming to lowercase would break the Streamlit multi-page app contract
- Per-file inline `# noqa: N999` would scatter the suppression across many files and is fragile
- The scope is bounded — N999 still applies to `core/`, `domains/`, `scripts/`, `tests/` where Python's lowercase convention is appropriate
- This is a known and well-documented convention conflict in the Streamlit community

**Impact:**
- `pyproject.toml` per-file-ignores updated
- `uv run ruff check .` now passes cleanly across the whole project
- Future Streamlit pages (`pages/2_Churn.py`, etc.) inherit the exception automatically
- No code changes needed to existing or future page files

**Alternatives considered:**
- Rename all Streamlit files to lowercase — breaks Streamlit conventions, sidebar labels become ugly (`home`, `1_brand_share`)
- Inline `# noqa: N999` on each file — fragile, easy to forget for new pages, scatters concerns
- Disable N999 project-wide — rejected because the rule is still valuable for `core/`, `domains/`, `scripts/`, `tests/`

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
