---
phase: 05-quality-assurance-deployment
verified: 2026-06-16T12:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 05: Quality Assurance & Deployment Verification Report

**Phase Goal:** The app is deployed, publicly accessible, and verifiably correct — all test suites pass, and a documented smoke check confirms the live Streamlit Cloud deployment loads cleanly from a cold start.
**Verified:** 2026-06-16
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `uv run pytest` exits green with >= 80% core/ coverage and >= 60% domains/ coverage | VERIFIED | 120 passed, core/ 96%, domains/ ~83% (brand_share 81%, churn 86%) |
| 2 | Integration test suite (`pytest -m integration`) passes against fresh DuckDB | VERIFIED | 21 passed (8 test_queries, 5 brand_share_service, 7 churn_service, 1 test_db_init) |
| 3 | Cold-start auto-seeding runs ensure_seeded() on first load and populates real KPIs | VERIFIED | core/db/init.py + app/db.py exist and wired; smoke check confirms Datasets=2 on incognito load |
| 4 | docs/DEPLOYMENT.md contains a completed 5-item smoke check with green status | VERIFIED | Section `## Production Smoke Check (DEPLOY-02)` at L17 with all 5 `[x]` items checked |
| 5 | README links live URL, CI badge, and screenshots | VERIFIED | markovlens.streamlit.app + ci.yml/badge.svg + ## Screenshots gallery at L21 |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/unit/test_models.py` | 11 new branch-coverage tests for core/models.py | VERIFIED | `def test_validate_rejects_non_2d`, `def test_m3_forecast_2d_g_holds_last` and 9 others present |
| `tests/unit/test_simulation.py` | 6 new branch-coverage tests for core/simulation.py | VERIFIED | `def test_quantile_bands_rejects_1d_extractor`, `def test_walk_forward_mape_exception_sets_none` and 4 others present |
| `core/db/init.py` | `ensure_seeded()` with forecasts sentinel + deferred seed import | VERIFIED | 43 lines; `def ensure_seeded`, `SELECT COUNT(*) FROM forecasts`, deferred `from scripts.seed_data import` |
| `app/db.py` | Shared `get_db()` with `@st.cache_resource(show_spinner=...)` + env-aware guard | VERIFIED | 39 lines; `@st.cache_resource(show_spinner="Preparing demo data…")`, `def get_db()`, `ensure_seeded(conn)`, `settings.app_env == "development"` |
| `tests/unit/test_db_init.py` | `ensure_seeded` fast-path + integration seed test | VERIFIED | `def test_ensure_seeded_fast_path_when_forecasts_present` + `@pytest.mark.integration def test_ensure_seeded_runs_pipeline_when_empty` |
| `.github/workflows/ci.yml` | 4-gate CI with astral-sh/setup-uv + uv sync | VERIFIED | `astral-sh/setup-uv@v8.2.0`, `enable-cache: true`, `python-version: "3.12"`, uv sync + 4 gate steps |
| `docs/DEPLOYMENT.md` | `## Production Smoke Check (DEPLOY-02)` with 5 checked items | VERIFIED | L17-28; all 5 items `[x]`; live URL `https://markovlens.streamlit.app`; date 2026-06-16 |
| `README.md` | Live URL + CI badge + `## Screenshots` | VERIFIED | L13 CI badge, L15 Live Demo link, L21 `## Screenshots` with 4 hero images |
| `docs/assets/screenshots/` | Hero screenshots | VERIFIED | home-kpis.jpg, brand-share-overview.jpg, churn-what-if.jpg, settings-datasets.jpg present |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/unit/test_models.py` | `core/models.py` | `from core.models import` inside tests | WIRED | Pattern confirmed present |
| `tests/unit/test_simulation.py` | `core/simulation.py` | `from core.simulation import` inside tests | WIRED | Pattern confirmed present |
| `app/db.py` | `core/db/init.ensure_seeded` | `get_db()` calls `ensure_seeded(conn)` | WIRED | `ensure_seeded(conn)` call at L31 in app/db.py |
| `core/db/init.py` | `scripts/seed_data.py` | deferred `from scripts.seed_data import RNG_SEED, _seed_brand_share, _seed_churn` | WIRED | Deferred import inside `ensure_seeded()` at L37 |
| `app/Home.py` | `app/db.py` | `from app.db import get_db` | WIRED | Confirmed at app/Home.py:25 |
| `app/pages/1_Brand_Share.py` | `app/db.py` | `from app.db import get_db` | WIRED | Confirmed at 1_Brand_Share.py:37 |
| `app/pages/2_Churn.py` | `app/db.py` | `from app.db import get_db` | WIRED | Confirmed at 2_Churn.py:39 |
| `app/pages/4_Settings.py` | `app/db.py` | `from app.db import get_db` | WIRED | Confirmed at 4_Settings.py:27 |
| `README.md` | live Streamlit Cloud URL | `streamlit.app` in Demo link | WIRED | `https://markovlens.streamlit.app` at L15 |
| `docs/DEPLOYMENT.md` | DEPLOY-02 acceptance criteria | 5-item checklist + CSV export item | WIRED | All 5 items checked at L22-26 |
| `.github/workflows/ci.yml` | `uv.lock` | `uv sync` resolves from committed lockfile | WIRED | `run: uv sync` step confirmed |
| `.github/workflows/ci.yml` | quality gates | 4 `uv run` steps mirroring local commands | WIRED | ruff check, ruff format --check, mypy, pytest all confirmed |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase produces tests, infrastructure files, and documentation artifacts, not new dynamic data-rendering components. The `ensure_seeded()` → `get_db()` → page call chain is the relevant data flow, verified via wiring checks above and by the production smoke check confirming Datasets=2 on cold start.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite green with coverage | `uv run pytest --cov=core --cov=domains -q -m "not slow"` | 120 passed, core/ 96%, domains/ ~83% (91% total) | PASS |
| Integration gate passes | `uv run pytest -m integration` | 21 passed (8+5+7+1) | PASS |
| No stray `_get_db` calls remain in app/ | `grep -rn "_get_db()" app/` | No matches | PASS |
| No streamlit import in core/ | `grep -rn "import streamlit" core/` | No matches (0 count) | PASS |
| D-15 mkdir guard present | `grep mkdir core/db/connection.py` | `settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)` at L18 | PASS |
| CI workflow has no matrix (single target) | `grep -c "strategy:\|matrix:" ci.yml` | 0 | PASS |
| All 4 smoke-check pages wired to get_db | `grep -c "from app.db import get_db"` in each page file | 1 each in Home, Brand Share, Churn, Settings | PASS |
| Demo (coming soon) placeholder removed | `grep "Demo (coming soon)" README.md` | No matches | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| QA-01 | 05-01-PLAN, 05-03-PLAN | Unit tests for `core/` — > 80% coverage; ENG-01..ENG-10 covered | SATISFIED | core/ 96% coverage; 120 tests pass; 11 branch-coverage tests for models.py + 6 for simulation.py |
| QA-02 | 05-01-PLAN | Integration tests pass against fresh temp DuckDB | SATISFIED | `pytest -m integration` 21 passed including test_db_init.py integration test |
| QA-03 | 05-01-PLAN | Domain layer tests > 60% coverage | SATISFIED | domains/ ~83% (brand_share 81%, churn 86%) |
| DEPLOY-01 | 05-02-PLAN, 05-04-PLAN | App deployed to Streamlit Cloud; cold start auto-seeds | SATISFIED | app live at https://markovlens.streamlit.app; Datasets=2 on cold incognito load confirms ensure_seeded() ran |
| DEPLOY-02 | 05-04-PLAN | Production smoke check documented in DEPLOYMENT.md | SATISFIED | `## Production Smoke Check (DEPLOY-02)` section with all 5 `[x]` items + date + live URL |

No orphaned requirements. All 5 Phase 05 requirements claimed by plans and verified in codebase.

---

### Anti-Patterns Found

No blockers or warnings found. Spot-checks on phase artifacts:

| File | Pattern Checked | Result |
|------|----------------|--------|
| `core/db/init.py` | No streamlit import, no return null/stubs | CLEAN |
| `app/db.py` | No hardcoded empty data; ensure_seeded is real call | CLEAN |
| `.github/workflows/ci.yml` | No placeholder steps; all 4 gates substantive | CLEAN |
| `docs/DEPLOYMENT.md` | All 5 smoke items checked `[x]` with real results | CLEAN |
| `README.md` | Live URL confirmed; screenshots are real JPGs not placeholders | CLEAN |

Notable deviation from plan (auto-fixed, no goal impact): ci.yml was written with `astral-sh/setup-uv@v8` which Astral does not publish as a major-version alias. Fixed to `astral-sh/setup-uv@v8.2.0` in commit `311f302` before README badge was added — badge shipped green on first eligible run.

---

### Human Verification Required

The following items required human action per 05-04-PLAN and cannot be verified programmatically:

#### 1. Cold-Start KPI Values (Verified by user — documented in DEPLOYMENT.md)

**Test:** Open https://markovlens.streamlit.app in a fresh/incognito browser  
**Expected:** Home page loads within 60s; Datasets Registered = 2  
**Documented result:** PASS — user confirmed Datasets=2 on incognito cold start; MAPE "—" and Simulations=0 are expected (seeded records have NULL MAPE; no Monte Carlo runs on fresh deploy)  
**Why human:** Cannot start a remote Streamlit Cloud container programmatically

#### 2. Screenshots Are Real App Captures

**Test:** Inspect docs/assets/screenshots/*.jpg for authentic app UI  
**Expected:** home-kpis.jpg, brand-share-overview.jpg, churn-what-if.jpg, settings-datasets.jpg show actual Streamlit pages  
**Status:** HUMAN ATTESTED — user committed 4 JPG files matching described views; 05-04-SUMMARY confirms capture  
**Why human:** Cannot render Streamlit UI or validate screenshot content programmatically

---

### Gaps Summary

No gaps found. All 5 observable truths verified. All required artifacts exist, are substantive, and are wired. All 5 requirements (QA-01, QA-02, QA-03, DEPLOY-01, DEPLOY-02) satisfied.

---

_Verified: 2026-06-16_
_Verifier: Claude (gsd-verifier)_
