# Phase 05: Quality Assurance & Deployment — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-16
**Phase:** 05-quality-assurance-deployment
**Areas discussed:** Cold start seeding, Dependency format, Portfolio polish

---

## Cold Start Seeding

| Option | Description | Selected |
|--------|-------------|----------|
| In Home.py startup block | Add ensure_seeded() call right after _get_db() in Home.py | |
| In a new core/db/init.py module | Clean separation: ensure_seeded() in core/db/init.py, called from Home.py | ✓ (initial) |
| In the DB connection singleton | get_connection() triggers seeding if schema is fresh | |

**Seed failure behavior:**

| Option | Description | Selected |
|--------|-------------|----------|
| st.warning and continue | App loads with warning; user can re-seed from Settings | ✓ |
| st.error and stop the page | Hard stop with actionable error | |
| Silent continue (show dashes) | Matches current Home.py behavior | |

**Spinner UX — user's actual selection (verbatim):**

> Use the cache decorator's built-in spinner:
> `@st.cache_resource(show_spinner="Preparing demo data…")`
> on the shared `get_db()` — NOT a manual Home.py spinner block.
> 
> Why: (1) `show_spinner` fires only on cache miss (cold start), silent on warm reruns.
> (2) "On Home" is the wrong frame — the seed lives in shared `get_db()` so deep-links to
> `/Brand_Share` still seed. A spinner hard-coded into Home.py wouldn't show on that path.

**User's choice:** `@st.cache_resource(show_spinner="Preparing demo data…")` on shared `get_db()`; env-aware failure (st.warning prod / st.error+st.exception dev); forecasts table as sentinel; `ensure_seeded()` in `core/db/init.py`

---

## Dependency Format

| Option | Description | Selected |
|--------|-------------|----------|
| Generate requirements.txt | uv export --format requirements-txt; pip-friendly | |
| pyproject.toml only + packages.txt | PEP 517 install; newer Streamlit Cloud behavior | |
| Both requirements.txt + pyproject.toml | Belt-and-suspenders | |

**User's actual choice (verbatim):**

> Rely on the already-committed uv.lock. Streamlit Community Cloud resolves dependencies in
> priority order: `uv.lock → Pipfile → environment.yml → requirements.txt → pyproject.toml`.
> The uv.lock is detected first and installs with uv, exact-pinned.
> A requirements.txt would be outranked and silently ignored — don't add one.
> Break-glass: `uv export --format requirements-txt` only if uv build ever fails on Cloud.

**DuckDB path choice (verbatim):**

> Keep repo-relative default `data/markovlens.duckdb` from core/config.py.
> Do NOT switch to /tmp (Linux-only, breaks local dev).
> Required fix: `Path(settings.duckdb_path).parent.mkdir(parents=True, exist_ok=True)`
> in `core/db/connection.py` — otherwise fresh Cloud clone fails (data/ dir doesn't exist).
> DUCKDB_PATH remains optional override; no secrets required.

---

## Portfolio Polish (CI + README)

**CI workflow:**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — add CI workflow | .github/workflows/ci.yml with pytest + ruff + mypy | ✓ |
| No — ship first, CI later | Get live URL first | |

**User's CI notes (verbatim):**

> Use uv (astral-sh/setup-uv + uv sync) — doubles as clean-room rehearsal of uv.lock install.
> Gates: `ruff check .`, `ruff format --check .`, `mypy core/ domains/`, `pytest -m "not slow"`.
> Single Python 3.12 on Ubuntu — no OS/version matrix.
> Verify all 4 gates pass locally before committing.
> Badge ships green, never red — a red badge is worse than none.
> CI and deploy are independent workstreams — run in parallel.

**README priority:**

| Option | Description | Selected |
|--------|-------------|----------|
| Update README after deploy | Placeholder stays until URL known | |
| Write full story README now | Story on fresh brain, URL placeholder later | ✓ |

**User's README split (verbatim):**

> NOW (deploy-independent): the full story — why Markov chains, two domains, how to interpret
> outputs, 3-layer architecture, math credibility (Chan 2015 + Becker calibration) — plus
> screenshots from local app.
> 
> FINAL PATCH (after deploy + green CI): replace 'Demo (coming soon)' with live URL, add
> CI badge (only once green), flip roadmap status to deployed.

---

## Claude's Discretion

- Shared `app/db.py` vs per-page `_get_db()` copy (lean: `app/db.py`)
- Seed pipeline extraction: import from `scripts/seed_data.py` vs inline in `core/db/init.py`
- Screenshot selection for README: lean toward Brand Share Monte Carlo + Churn Sankey as hero shots

## QA Coverage Decision (added at close)

**User explicitly added at context creation:**

> Ship at 89% core / 81-86% domains.
> Only targeted new tests for uncovered Markov-math paths in `core/models.py` and
> `core/simulation.py`. Do NOT chase 95%.

## Deferred Ideas

- GitHub Actions CD (auto-deploy) — Streamlit Cloud free tier doesn't support natively
- Sentry error tracking — skip for v1
- Automated screenshots via Playwright — capture manually instead
- Custom domain — future optional step
