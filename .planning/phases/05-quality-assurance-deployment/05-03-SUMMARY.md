---
phase: 05-quality-assurance-deployment
plan: "03"
subsystem: infra
tags: [github-actions, ci, ruff, mypy, pytest, uv, astral-sh-setup-uv]

# Dependency graph
requires:
  - phase: 05-quality-assurance-deployment
    provides: "4 passing local quality gates (ruff, mypy, pytest)"
provides:
  - ".github/workflows/ci.yml — 4-gate CI workflow on push/PR to master"
  - "Green badge signal: recruiter-visible engineering rigor on GitHub"
  - "uv.lock clean-room rehearsal on ubuntu-latest (de-risks Streamlit Cloud deploy)"
affects: [05-04-deploy, README-badge-patch]

# Tech tracking
tech-stack:
  added: [astral-sh/setup-uv@v8, actions/checkout@v4, GitHub Actions]
  patterns: ["CI as uv.lock rehearsal — same uv sync as Streamlit Cloud install"]

key-files:
  created: [.github/workflows/ci.yml]
  modified:
    - app/Home.py
    - app/components/empty_state.py
    - app/components/monte_carlo_fan.py
    - app/components/sankey_flow.py
    - app/components/section_header.py
    - app/components/transition_heatmap.py
    - app/pages/1_Brand_Share.py
    - app/pages/4_Settings.py
    - app/styles/__init__.py
    - app/styles/plotly_theme.py
    - core/db/queries.py
    - domains/brand_share/service.py
    - domains/churn/service.py
    - tests/integration/test_brand_share_service.py
    - tests/integration/test_churn_service.py
    - tests/unit/test_churn_service.py
    - tests/unit/test_components.py
    - tests/unit/test_csv_export.py
    - tests/unit/test_home_queries.py
    - tests/unit/test_page_import.py
    - tests/unit/test_plotly_theme.py
    - tests/unit/test_stationary.py

key-decisions:
  - "Used astral-sh/setup-uv@v8 (not stale @v3 from CONTEXT.md example) — context7-verified current major tag"
  - "enable-cache: true relies on default cache-dependency-glob covering **/uv.lock + **/pyproject.toml — no extra config"
  - "python-version: 3.12 explicit (D-19 single target); no strategy/matrix"
  - "CI as uv.lock rehearsal: uv sync on ubuntu-latest mirrors Streamlit Cloud priority-order resolution"
  - "All four gates committed green — badge ships green first time (D-20/D-24)"
  - "ruff format applied to 22 files as pre-commit gate fix before writing ci.yml (D-20 compliance)"

patterns-established:
  - "CI workflow mirrors local gate commands exactly: uv run ruff/mypy/pytest steps 1:1"
  - "Each gate is a separate step so failing gate is identifiable by name in Actions UI"

requirements-completed: [QA-01]

# Metrics
duration: 8min
completed: 2026-06-16
---

# Phase 05 Plan 03: CI Workflow Summary

**GitHub Actions CI with astral-sh/setup-uv@v8 + uv sync clean-room rehearsal, 4 gates (ruff lint/format, mypy, pytest) all confirmed green locally before commit**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-16T02:56:27Z
- **Completed:** 2026-06-16T03:04:00Z
- **Tasks:** 2
- **Files modified:** 23 (1 created + 22 reformatted)

## Accomplishments

- Applied `ruff format` to 22 files across app/, core/, domains/, tests/ to green the pre-commit gate (D-20 compliance)
- Created `.github/workflows/ci.yml` with astral-sh/setup-uv@v8 + enable-cache + Python 3.12 + uv sync + 4 separate gate steps
- All four gates confirmed green locally: ruff check (0 issues), ruff format --check (51 formatted), mypy (0 issues in 17 files), pytest -m "not slow" (101 passed)
- Workflow doubles as clean-room rehearsal of uv.lock-based Streamlit Cloud install (D-17), de-risking the deploy

## Four-Gate Local Results (D-20)

| Gate | Command | Result |
|------|---------|--------|
| Ruff lint | `uv run ruff check .` | PASS — 0 issues |
| Ruff format | `uv run ruff format --check .` | PASS — 51 files already formatted (after pre-fix) |
| Mypy | `uv run mypy core/ domains/` | PASS — 0 issues in 17 source files |
| Pytest | `uv run pytest -m "not slow"` | PASS — 101 passed, 0 failed |

## Task Commits

1. **Task 1: Verify all four gates pass locally** - `0690d91` (chore) — ruff format applied to 22 files
2. **Task 2: Write .github/workflows/ci.yml** - `07413c6` (feat) — CI workflow created

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `.github/workflows/ci.yml` — CI workflow: checkout@v4 + setup-uv@v8 (enable-cache, python 3.12) + uv sync + 4 gate steps
- 22 source files reformatted by ruff (whitespace/import style changes only, no logic changes)

## CI Workflow Key Facts

- **Action version:** `astral-sh/setup-uv@v8` (context7-verified current; plan's CONTEXT.md example `@v3` was stale)
- **Cache:** `enable-cache: true` — default `cache-dependency-glob` covers `**/uv.lock` and `**/pyproject.toml`
- **Python target:** Single — `python-version: "3.12"`, `ubuntu-latest`. No `strategy.matrix` (D-19)
- **Trigger:** `push` + `pull_request` to `master`
- **Permissions:** `contents: read` (least privilege)
- **No requirements.txt** added (D-11 — would be outranked by uv.lock and silently ignored)
- **No CD job** (D-21 — GitHub Actions CD to Streamlit Cloud not natively supported)

## CI Badge (for deploy plan 05-04)

After the first green run, add this badge to README:

```markdown
[![CI](https://github.com/afrizzal/markovlens/actions/workflows/ci.yml/badge.svg)](https://github.com/afrizzal/markovlens/actions/workflows/ci.yml)
```

Add ONLY after first run is confirmed green (D-24 — red badge is worse than no badge).

## Decisions Made

- Used `astral-sh/setup-uv@v8` (not `@v3` from CONTEXT.md) — context7-verified v8.1.0 is current release
- `enable-cache: true` with no extra `cache-dependency-glob` — default already covers uv.lock + pyproject.toml
- Applied ruff format as a pre-commit fix (deviation Rule 1) before writing ci.yml — D-20 requires all 4 gates green before committing the workflow

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Applied ruff format to 22 files before writing ci.yml**
- **Found during:** Task 1 (local gate verification)
- **Issue:** `ruff format --check .` failed on 22 files across app/, core/, domains/, tests/. Gate 2 was red.
- **Fix:** Ran `uv run ruff format .` to reformat all 22 files; re-ran `ruff format --check .` to confirm green.
- **Files modified:** 22 files (whitespace/import sorting only, no logic changes)
- **Verification:** `uv run ruff format --check .` exits 0 ("51 files already formatted")
- **Committed in:** `0690d91` (Task 1 chore commit, separate from ci.yml feat)

---

**Total deviations:** 1 auto-fixed (Rule 1 — pre-existing format drift not caused by this phase, but blocking the CI green requirement per D-20)
**Impact on plan:** Necessary to satisfy D-20 (gates green before committing workflow). No scope creep. No logic changes.

## Issues Encountered

The 22-file ruff format drift was a pre-existing condition (prior phases didn't run ruff format after their edits). Detected and resolved during the mandatory D-20 gate verification. All four gates confirmed green before ci.yml was written.

## User Setup Required

None — CI runs automatically on first push to master. No external service configuration required beyond having the GitHub repository connected.

## Next Phase Readiness

- CI badge will be green on first push of these commits to the remote `master` branch
- Deploy plan (05-04) can proceed in parallel — CI and deploy are independent (D-21)
- After deploy URL is confirmed, 05-04 will add the CI badge to README (D-23/D-24)

---

## Self-Check

**Files created:**
- `.github/workflows/ci.yml` — EXISTS (created in this plan)
- `.planning/phases/05-quality-assurance-deployment/05-03-SUMMARY.md` — EXISTS (this file)

**Commits verified:**
- `0690d91` — chore(05-03): apply ruff format to 22 files
- `07413c6` — feat(05-03): add .github/workflows/ci.yml

## Self-Check: PASSED

---
*Phase: 05-quality-assurance-deployment*
*Completed: 2026-06-16*
