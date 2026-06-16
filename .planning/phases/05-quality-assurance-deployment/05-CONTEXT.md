# Phase 05: Quality Assurance & Deployment — Context

**Gathered:** 2026-06-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the app publicly accessible and verifiably correct:

- **QA-01/02/03** — Test suite already green (101 tests, 89%+ core coverage, 81-86% domains). Add targeted tests for uncovered Markov-math paths in `core/models.py` and `core/simulation.py` only. No coverage chase to 95%.
- **DEPLOY-01** — App deployed to Streamlit Cloud; auto-seeds on cold start via `ensure_seeded()` + `@st.cache_resource(show_spinner=...)`.
- **DEPLOY-02** — Production smoke check completed in `docs/DEPLOYMENT.md`.

The Markov engine, design system, Brand Share, Churn, Home, CSV export, and Settings pages are complete and NOT modified. This phase ships what's already built.

</domain>

<decisions>
## Implementation Decisions

### QA — Coverage

- **D-01**: Ship at current coverage: 89%+ `core/`, 81-86% `domains/`. This exceeds QA-01 (>80%) and QA-03 (>60%) targets. Do NOT chase 95%.
- **D-02**: Only targeted new tests for uncovered Markov-math lines in `core/models.py` (lines 53, 60, 116-117, 132-134, 186, 191, 228, 233, 238, 242, 260) and `core/simulation.py` (lines 165, 185, 205, 247, 255, 278-279). Skip service/page coverage gaps — too few returns on the domain-layer effort.
- **D-03**: QA-02 (integration tests for `core/db/`) is already satisfied by `tests/integration/test_queries.py` (8 tests covering `build_transition_matrix`, seed idempotency, `get_home_kpis`, `list_recent_forecasts`). No new integration tests needed.

### Cold Start Auto-Seeding (DEPLOY-01)

- **D-04**: `ensure_seeded(conn)` lives in `core/db/init.py`. It checks the `forecasts` table as the seed sentinel — if `SELECT COUNT(*) FROM forecasts` returns 0, it runs the seed pipeline. Forecasts table is chosen because it's the last table populated by `seed_data.py` (after transitions + matrices + simulation_runs), making it the most reliable "seed complete" signal.

- **D-05**: `ensure_seeded()` is called from the shared `@st.cache_resource` `get_db()` function used by all pages:
  ```python
  @st.cache_resource(show_spinner="Preparing demo data…")
  def get_db():
      conn = get_connection()
      ensure_seeded(conn)
      return conn
  ```
  Rationale: `show_spinner` fires **only on cache miss** (cold start), silent on warm reruns. Deep-link to `/Brand_Share` seeds correctly because all pages share the same `get_db()`. The spinner shows on whichever page loads first, not just Home.

- **D-06**: Seed is light (synthetic FMCG generated in-code + pandas apply over ~7k Telco CSV rows). Use bare `@st.cache_resource(show_spinner=...)` — do NOT add `st.status` or progress bar.

- **D-07**: Seed is idempotent via D-23 (delete-where-dataset_id before INSERT). If seeding fails and retried, no orphan rows accumulate. No extra transaction wrapper needed.

- **D-08**: Failure behavior — env-aware:
  - **Dev** (`APP_ENV=development`): `st.error("Seed failed: {e}")` + `st.exception(e)` + `log.exception`
  - **Prod** (`APP_ENV=production` / unset): `st.warning("Demo data not available yet — KPIs may show dashes")` + `log.exception`
  - App always continues loading after failure; it never blocks.

- **D-09**: `data/seed/telco_churn.csv` (977KB) is already committed and tracked by git (`!data/seed/*.csv` in .gitignore). The synthetic FMCG dataset is generated in-code. Cold-start data IS reachable on Streamlit Cloud — there is no FileNotFoundError risk.

### Dependency Format (Streamlit Cloud Deploy)

- **D-10**: Rely on the already-committed `uv.lock`. Streamlit Community Cloud resolves in priority order: `uv.lock → Pipfile → environment.yml → requirements.txt → pyproject.toml`. The `uv.lock` is detected first and installs with uv, exact-pinned and identical to local.
- **D-11**: Do NOT add `requirements.txt`. It would be outranked by `uv.lock` and silently ignored — redundant and misleading.
- **D-12**: Pre-deploy verification: `git ls-files --error-unmatch uv.lock` (confirm tracked), and confirm no stray dependency file inside `app/` that could shadow the root `uv.lock`.
- **D-13**: Keep `uv export --format requirements-txt` as a manual break-glass only if a uv build ever fails on Cloud (which would also require removing/renaming `uv.lock`).

### DuckDB Path on Streamlit Cloud

- **D-14**: Keep the existing repo-relative default `data/markovlens.duckdb` from `core/config.py`. Do NOT switch default to `/tmp` (Linux-only, breaks local dev on Windows). The Streamlit Cloud filesystem is ephemeral, which is fine because `ensure_seeded()` repopulates on each cold boot.
- **D-15**: Required fix in `core/db/connection.py`: add `Path(settings.duckdb_path).parent.mkdir(parents=True, exist_ok=True)` before `duckdb.connect(...)`. On a fresh Cloud clone, the gitignored `data/` directory won't exist and `duckdb.connect` will fail with "No such file or directory" without this guard.
- **D-16**: `DUCKDB_PATH` remains an optional env-var override. `pydantic-settings` already reads it from the environment; Streamlit secrets populate the environment. No secrets required for a standard deploy — the override is available for free if needed later.

### CI / GitHub Actions

- **D-17**: Add `.github/workflows/ci.yml`. Use `uv` via `astral-sh/setup-uv` + `uv sync` — this doubles as a clean-room rehearsal of the `uv.lock`-based Streamlit Cloud install and de-risks the deploy.
- **D-18**: CI gates (all must pass): `ruff check .`, `ruff format --check .`, `mypy core/ domains/`, `pytest -m "not slow"`.
- **D-19**: Single matrix: Python 3.12 on Ubuntu. No OS/version matrix — single-target portfolio app.
- **D-20**: Verify all 4 gates pass locally before committing the workflow. The CI badge ships green, never red — a red badge is worse than no badge.
- **D-21**: CI and deploy are independent workstreams within Phase 05 — run in parallel; neither blocks the other.

### README & Portfolio Polish

- **D-22**: README story written NOW (deploy-independent, written on a fresh brain): why Markov chains, the two domains, how to interpret outputs, 3-layer architecture, math credibility (Chan 2015 + Becker calibration). Include screenshots captured from the local app (`uv run streamlit run app/Home.py`). This does not require the live URL.
- **D-23**: README FINAL PATCH (5 min after deploy + green CI): replace "Demo (coming soon)" with live URL, add CI badge (only once green), flip roadmap status to "deployed."
- **D-24**: Add CI badge to README only after the badge is green — a red badge signals sloppiness to recruiters.

### Claude's Discretion

- Exact location of `ensure_seeded()` call in each page file (can be a shared `app/db.py` module or copy-pasted into each page's `_get_db()` — lean toward `app/db.py` for DRY since there are 5 page entry points).
- Whether to extract seed pipeline into importable functions in `scripts/seed_data.py` or inline it in `core/db/init.py` (lean toward import from script to avoid duplication).
- Screenshot selection for README (which views are most recruiter-compelling — lean toward Brand Share Monte Carlo fan chart + Churn Sankey as the hero shots).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 05 goal, success criteria (4 SCs), requirements QA-01..03 + DEPLOY-01..02
- `.planning/REQUIREMENTS.md` — QA-01/02/03, DEPLOY-01/02 acceptance criteria

### Core Infrastructure to Modify
- `core/db/connection.py` — add `mkdir(parents=True, exist_ok=True)` before `duckdb.connect()` (D-15)
- `core/config.py` — `settings.duckdb_path` (keep as-is, just ensure parent dir guard)
- `scripts/seed_data.py` — source of seed pipeline logic; `ensure_seeded()` should import/call into this

### New Files to Create
- `core/db/init.py` — `ensure_seeded(conn)` function
- `.github/workflows/ci.yml` — CI workflow (D-17..D-21)
- Screenshots for README (captured locally)

### Test Infrastructure
- `tests/unit/test_models.py` — extend for uncovered lines (D-02): 53, 60, 116-117, 132-134, 186, 191, 228, 233, 238, 242, 260
- `tests/unit/test_simulation.py` — extend for uncovered lines (D-02): 165, 185, 205, 247, 255, 278-279
- `tests/unit/test_page_import.py` — existing page smoke tests (101 pass; no changes needed)
- `tests/integration/test_queries.py` — existing integration tests (no new tests needed)

### Pages (for get_db() update)
- `app/Home.py` — update `_get_db()` to call `ensure_seeded()` via shared `app/db.py`
- `app/pages/1_Brand_Share.py` — same
- `app/pages/2_Churn.py` — same
- `app/pages/4_Settings.py` — same

### Documentation
- `docs/DEPLOYMENT.md` — smoke-check template exists; complete the checklist post-deploy (DEPLOY-02)
- `README.md` — write story section now; patch URL + CI badge after deploy

### Project Rules
- `.claude/rules/python-conventions.md` — type hints, `@dataclass(frozen=True)`, error handling patterns
- `.claude/rules/data-storage.md` — parameterized queries, DuckDB patterns
- `.claude/rules/project-rules.md` — security rules (no secrets in code), gitignore rules

</canonical_refs>

<code_context>
## Existing Code Insights

### Current Test State
- 101 tests passing, 0 failing, 0 skipped (except `@pytest.mark.slow`)
- `core/` coverage: 88-100% across all modules (exceeds QA-01 >80% target)
- `domains/` coverage: `brand_share/service.py` 81%, `churn/service.py` 86% (exceeds QA-03 >60% target)
- Integration tests: `tests/integration/test_queries.py` 8 tests (satisfies QA-02)

### Key Uncovered Lines to Target (D-02)
- `core/models.py:53,60` — likely edge-case branches in `validate_transition_matrix` or dtype coercion
- `core/models.py:116-117,132-134` — probably error paths in M2/M3 forecast methods
- `core/simulation.py:165,185,205,247,255,278-279` — likely boundary/error cases in walk-forward or calibration

### Seeding Infrastructure (already in place)
- `data/seed/telco_churn.csv` — 977KB, committed (not gitignored via `!data/seed/*.csv`)
- `scripts/seed_data.py` — synthetic FMCG DGP + Telco CSV → populates DuckDB; idempotent via delete-first (D-23)
- `@st.cache_resource` already used on `_get_db()` in every page — just need to add `show_spinner` + `ensure_seeded()` call

### Integration Points
- `core/db/connection.py:get_connection()` — singleton; add `mkdir` guard here (D-15)
- All 4 page files + `app/Home.py` use their own `_get_db()` pattern → consolidate to `app/db.py` (Claude's Discretion)
- `APP_ENV` env var already exists in `core/config.py` via pydantic-settings → use for dev/prod error display (D-08)

### CI-Relevant Facts
- `ruff check .` + `ruff format --check .` — both clean locally
- `mypy core/ domains/` — currently IDE-only enforcement; verify passes in terminal before adding to CI
- `pytest -m "not slow"` — 101 tests, ~11s locally; acceptable CI time

</code_context>

<specifics>
## Specific Implementation Notes

### ensure_seeded() signature
```python
def ensure_seeded(conn: duckdb.DuckDBPyConnection) -> None:
    """Populate DuckDB with demo data if not already seeded.

    Uses forecasts table as seed sentinel — populated last by seed pipeline.
    """
    count = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    if count > 0:
        return  # already seeded — fast path
    # import and call seed pipeline
    ...
```

### get_db() pattern (app/db.py or per-page)
```python
@st.cache_resource(show_spinner="Preparing demo data…")
def get_db() -> duckdb.DuckDBPyConnection:
    conn = get_connection()
    ensure_seeded(conn)
    return conn
```

### connection.py mkdir guard
```python
def get_connection() -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is None:
        db_path = Path(settings.duckdb_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)  # ← NEW
        _connection = duckdb.connect(str(db_path))
        ...
    return _connection
```

### CI workflow structure
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy core/ domains/
      - run: uv run pytest -m "not slow"
```

### Seed failure guard (env-aware)
```python
import logging
log = logging.getLogger(__name__)

try:
    ensure_seeded(conn)
except Exception as e:
    log.exception("Auto-seed failed")
    if settings.app_env == "development":
        st.error(f"Seed failed: {e}")
        st.exception(e)
    else:
        st.warning("Demo data not available yet — KPIs may show dashes.")
```

</specifics>

<deferred>
## Deferred Ideas

- **GitHub Actions CD** (auto-deploy to Streamlit Cloud on merge) — not supported natively by Streamlit Cloud free tier; would need webhook or manual trigger. Future enhancement.
- **Sentry error tracking** — DEPLOYMENT.md mentions this; skip for v1 portfolio.
- **Automated screenshot generation** — Could use Playwright to snapshot pages for README. Overkill for Phase 05; capture screenshots manually from local app.
- **Custom domain** (`markovlens.app`) — DEPLOYMENT.md covers this; optional future step after URL confirmed stable.
- **QA-04 (v2)** — UI smoke tests via Playwright/st.testing — deferred to v2 per REQUIREMENTS.md.

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-quality-assurance-deployment*
*Context gathered: 2026-06-16*
