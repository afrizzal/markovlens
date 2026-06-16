---
phase: 05-quality-assurance-deployment
plan: "04"
subsystem: deploy

key-files:
  created:
    - docs/assets/screenshots/home-kpis.jpg
    - docs/assets/screenshots/brand-share-overview.jpg
    - docs/assets/screenshots/churn-what-if.jpg
    - docs/assets/screenshots/settings-datasets.jpg
    - docs/assets/screenshots/README.md
  modified:
    - docs/DEPLOYMENT.md
    - README.md
    - .github/workflows/ci.yml

key-decisions:
  - "astral-sh/setup-uv@v8 does not exist as a published tag — only exact semver (v8.0.0, v8.1.0, v8.2.0). Pinned to v8.2.0 to fix CI."
  - "Hero screenshots: 4 JPG files committed covering Home KPIs, Brand Share Overview, Churn What-If, Settings. Brand Share Monte Carlo and Churn Sankey tabs not separately captured."
  - "MAPE=— and Simulations=0 on cold start is expected behavior — seeded records have NULL MAPE; no Monte Carlo runs on fresh deploy. Datasets=2 is the definitive auto-seed proof."
  - "CI badge added immediately after confirming CI green (run completed success) on the fix commit."

requirements-completed: [DEPLOY-01, DEPLOY-02]

duration: inline
completed: 2026-06-16
---

# Phase 05 Plan 04: Streamlit Cloud Deploy + README Final Patch Summary

**App live at https://markovlens.streamlit.app — DEPLOY-01 and DEPLOY-02 satisfied. README patched with live URL, CI badge, 4 hero screenshots. CI green after fixing setup-uv version tag.**

## Performance

- **Duration:** ~25 min (includes CI investigation + fix)
- **Completed:** 2026-06-16
- **Tasks:** 3 (Task 1 auto, Task 2 human checkpoint, Task 3 auto)

## Accomplishments

### Task 1: D-12 Pre-Deploy Dependency Verification
- `uv.lock` confirmed tracked via `git ls-files --error-unmatch uv.lock` ✓
- No stray dependency file under `app/` (no uv.lock / Pipfile / environment.yml / requirements*.txt / pyproject.toml) ✓
- No `requirements.txt` at repo root (would be outranked by uv.lock and misleading) ✓
- `docs/assets/screenshots/` created with placeholder README listing hero image requirements

### Task 2: Deploy to Streamlit Community Cloud (Human Action)
- App deployed by user at https://markovlens.streamlit.app
- Cold-start smoke check performed via Streamlit Cloud dashboard
- 4 screenshots captured covering all 4 app pages

### CI Fix (discovered during Task 2 prep)
- CI was failing across all 5 runs with: `Unable to resolve action 'astral-sh/setup-uv@v8', unable to find version 'v8'`
- Root cause: astral-sh/setup-uv does not publish major-version aliases (`v8`); only exact semver tags (`v8.2.0`, `v8.1.0`, etc.)
- Fix: updated `.github/workflows/ci.yml` to `astral-sh/setup-uv@v8.2.0`
- First run after fix: **completed success** ✓

### Task 3: DEPLOYMENT.md + README Final Patch
- Added `## Production Smoke Check (DEPLOY-02)` section to DEPLOYMENT.md with all 5 items checked green, live URL, and date
- Checked all Pre-Deploy Checklist items in DEPLOYMENT.md
- Documented two known non-issues in "Known Issues": setup-uv fix and MAPE=— on cold start
- README patches:
  - `[Demo (coming soon)](#)` → `[Live Demo](https://markovlens.streamlit.app)` ✓
  - CI badge added (D-24: gated on confirmed green CI) ✓
  - `## Screenshots` gallery with 4 hero JPGs ✓
  - Phase 04/05 roadmap checkboxes ticked `[x]` ✓

## Task Commits

1. **Task 1** — `dd3ee1f` chore(05-04): pre-deploy D-12 verification + screenshots dir scaffold
2. **CI fix** — `311f302` fix(ci): use astral-sh/setup-uv@v8.2.0 (v8 major alias not published)
3. **Task 3** — `03d071d` docs(05-04): smoke check, README final patch, hero screenshots (D-23/DEPLOY-02)

## Production Smoke Check Results (DEPLOY-02)

| Check | Result |
|-------|--------|
| App loads (Home page ≤60s on cold start) | ✓ PASS |
| Brand Share page renders | ✓ PASS |
| Churn page renders | ✓ PASS |
| Home KPIs show real data (Datasets=2) | ✓ PASS — Datasets=2 confirms ensure_seeded ran |
| CSV export works | ✓ PASS |

**Cold start proof:** Datasets Registered = 2 on first incognito load confirms `ensure_seeded()` ran and populated DuckDB on Streamlit Cloud's ephemeral filesystem.

## D-12 Verification Results

| Check | Result |
|-------|--------|
| `uv.lock` git-tracked | ✓ |
| No stray dependency file under `app/` | ✓ |
| No `requirements.txt` at root | ✓ |

## Deviations from Plan

### Auto-fixed Issues

**1. [Bug] CI failing — astral-sh/setup-uv@v8 tag not published**
- **Found during:** Task 2 prep (checking CI before README badge)
- **Issue:** All 5 CI runs failed with "Unable to resolve action `astral-sh/setup-uv@v8`". The v8 major-version alias was never published by Astral.
- **Fix:** Updated `ci.yml` to pin `astral-sh/setup-uv@v8.2.0` (verified as latest via `gh api repos/astral-sh/setup-uv/releases/latest`)
- **Verification:** CI run `completed success` after fix

**2. [Adapt] Screenshots cover 4 pages, not just 2 hero shots**
- Plan called for `brand-share-fan.png` (Monte Carlo fan tab) and `churn-sankey.png` (Sankey Overview tab)
- User captured screenshots of: Home, Brand Share Overview, Churn What-If, Settings
- Adapted: renamed to descriptive names, used all 4 in a 2×2 gallery table in README. Portfolio coverage is broader than planned.

## Self-Check

**Files created:**
- `docs/assets/screenshots/home-kpis.jpg` — EXISTS
- `docs/assets/screenshots/brand-share-overview.jpg` — EXISTS
- `docs/assets/screenshots/churn-what-if.jpg` — EXISTS
- `docs/assets/screenshots/settings-datasets.jpg` — EXISTS
- `.planning/phases/05-quality-assurance-deployment/05-04-SUMMARY.md` — EXISTS (this file)

**Key artifacts:**
- `docs/DEPLOYMENT.md` — contains "Production Smoke Check (DEPLOY-02)" ✓
- `README.md` — contains `streamlit.app` ✓, `## Screenshots` ✓, CI badge ✓

**Commits verified:**
- `dd3ee1f` — chore(05-04): pre-deploy D-12 verification + screenshots dir scaffold
- `311f302` — fix(ci): use astral-sh/setup-uv@v8.2.0
- `03d071d` — docs(05-04): smoke check, README final patch, hero screenshots

## Self-Check: PASSED

---
*Phase: 05-quality-assurance-deployment*
*Completed: 2026-06-16*
