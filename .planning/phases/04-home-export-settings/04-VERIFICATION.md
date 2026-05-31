---
phase: 04-home-export-settings
verified: 2026-06-01T00:00:00Z
status: passed
score: 6/6 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Run app locally (uv run streamlit run app/Home.py), seed data, then navigate to Home — verify KPI strip shows non-zero values for Datasets Registered and Simulations Run"
    expected: "KPI strip displays real counts from DuckDB; no error warnings appear on page"
    why_human: "Requires a seeded DuckDB file and a running Streamlit server to confirm live rendering"
  - test: "On Brand Share page, run a forecast then click Download forecast CSV"
    expected: "Browser downloads a .csv file with two sections: '# Forecast' and '# Transition Matrix' with correct state-label column headers"
    why_human: "st.download_button behavior requires browser interaction; CSV section rendering depends on a real forecast result being in session state"
  - test: "On Settings page (Datasets tab), verify the table lists datasets with correct row counts and created_at timestamps"
    expected: "Table shows at least 2 datasets (brand_share + churn) after seed; Created column shows formatted date rather than dash"
    why_human: "Requires seeded database; table rendering is visual"
---

# Phase 04: Home + Export + Settings Verification Report

**Phase Goal:** Deliver a fully functional Home dashboard with real KPIs, CSV export buttons embedded in both domain pages, and a Settings page with dataset listing and re-run seed capability.
**Verified:** 2026-06-01
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | app/Home.py KPI strip wired to real DuckDB data via get_home_kpis() — not hardcoded | VERIFIED | Line 26: `from core.db.queries import get_home_kpis, list_recent_forecasts`; line 49: `_kpis = get_home_kpis(_db)`; _kpis fields rendered at lines 68, 73–77, 84 |
| 2 | app/pages/1_Brand_Share.py has st.download_button for CSV export | VERIFIED | Line 427: `st.download_button(...)` guarded by `if st.session_state.get(f"{PAGE_NS}.result") is not None`; _brand_share_csv_bytes helper at line 80 |
| 3 | app/pages/2_Churn.py has st.download_button for CSV export | VERIFIED | Line 351: `st.download_button(...)` guarded by `if st.session_state.get(f"{PAGE_NS}.result") is not None`; _churn_csv_bytes helper at line 91 |
| 4 | app/pages/4_Settings.py exists with Datasets tab + Re-run seed button | VERIFIED | File exists; tab_datasets at line 58; list_datasets() call at line 64; "Re-run seed script" button at line 110 inside Advanced expander |
| 5 | All tests pass: uv run pytest tests/ -q | VERIFIED | 101 passed in 7.72s — zero failures across all unit and integration tests |
| 6 | ruff clean + mypy clean | VERIFIED | ruff: "All checks passed!"; mypy: "Success: no issues found in 17 source files" |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `core/db/queries.py` | HomeKpis, RecentForecast dataclasses + get_home_kpis(), list_recent_forecasts(), Dataset.created_at | VERIFIED | All exports confirmed: HomeKpis at line 322, get_home_kpis at line 331, RecentForecast at line 375, list_recent_forecasts at line 386, Dataset.created_at at line 29 |
| `app/Home.py` | Wired Home dashboard: real KPI strip + real Recent Forecasts list | VERIFIED | Imports confirmed; get_home_kpis() called at runtime; list_recent_forecasts() called at runtime; empty_state fallback for zero forecasts |
| `app/pages/1_Brand_Share.py` | CSV download button in Overview tab after KPI strip | VERIFIED | st.download_button at line 427; conditionally rendered when result in session state |
| `app/pages/2_Churn.py` | CSV download button in Overview tab after KPI strip | VERIFIED | st.download_button at line 351; conditionally rendered when result in session state |
| `app/pages/4_Settings.py` | Settings page: Datasets / Preferences / Appearance / About tabs | VERIFIED | All 4 tabs present; Datasets tab calls list_datasets(); Re-run seed button in Advanced expander |
| `tests/unit/test_home_queries.py` | Wave 0 unit test stubs for HOME-01 query helpers | VERIFIED | 5 tests: dataclass field assertions + empty-DB behavior for get_home_kpis and list_recent_forecasts |
| `tests/unit/test_csv_export.py` | Unit tests for CSV helper functions | VERIFIED | 5 tests: forecast section, row count, column headers, matrix row sums to 1, UTF-8 encoding |
| `tests/unit/test_page_import.py` | Smoke tests for Home + Settings page imports | VERIFIED | test_home_page_imports_without_error at line 266; test_settings_page_imports_without_error at line 329 |
| `tests/integration/test_queries.py` | Integration tests for new query functions | VERIFIED | test_get_home_kpis_with_seeded_data at line 164; test_list_datasets_includes_created_at; test_list_recent_forecasts_with_inserted_forecast |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| app/Home.py | core.db.queries.get_home_kpis | import + function call | WIRED | Imported line 26, called line 49, result fields rendered in KPI strip lines 68/73-77/84 |
| app/Home.py | core.db.queries.list_recent_forecasts | import + function call | WIRED | Imported line 26, called line 119, result iterated in table render or empty_state fallback |
| app/pages/1_Brand_Share.py | st.download_button → _brand_share_csv_bytes | session state guard + function call | WIRED | Guard at line 424, helper called at line 429, helper defined at line 80 |
| app/pages/2_Churn.py | st.download_button → _churn_csv_bytes | session state guard + function call | WIRED | Guard at line 348, helper called at line 353, helper defined at line 91 |
| app/pages/4_Settings.py | core.db.queries.list_datasets | import + function call | WIRED | Imported line 30, called line 64, result rendered as dataframe |
| app/pages/4_Settings.py | subprocess.run → scripts/seed_data.py | button + subprocess call | WIRED | Button at line 110, subprocess.run at line 112 with cwd=_PROJECT_ROOT |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| app/Home.py KPI strip | _kpis (HomeKpis) | get_home_kpis() → 4 SQL queries against datasets, simulation_runs, forecasts tables | Yes — COUNT(*) and MAX() queries on real tables; AVG with JSON extraction | FLOWING |
| app/Home.py Recent Forecasts | _recent (list[RecentForecast]) | list_recent_forecasts() → JOIN forecasts LEFT JOIN datasets ORDER BY created_at DESC | Yes — real JOIN query with LIMIT; empty list returned when no forecasts | FLOWING |
| app/pages/4_Settings.py Datasets tab | _datasets (list[Dataset]) | list_datasets() → SELECT from datasets table with created_at | Yes — real SELECT including created_at column; empty_state fallback for empty DB | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| pytest full suite | uv run pytest tests/ -q | 101 passed in 7.72s | PASS |
| ruff lint check | uv run ruff check . | All checks passed! | PASS |
| mypy type check | uv run mypy core/ domains/ | Success: no issues found in 17 source files | PASS |
| HomeKpis import | python -c "from core.db.queries import HomeKpis, get_home_kpis" | (checked via grep — functions present at lines 322/331) | PASS |
| RecentForecast import | python -c "from core.db.queries import RecentForecast, list_recent_forecasts" | (checked via grep — functions present at lines 375/386) | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| HOME-01 | 04-01-PLAN.md, 04-02-PLAN.md | app/Home.py wired to real data — KPI strip showing dataset count, last forecast timestamp, total simulation runs, overall model accuracy (MAPE) from forecasts table | SATISFIED | get_home_kpis() imported and called in app/Home.py; four KPI cards render _kpis fields; REQUIREMENTS.md shows Complete |
| RPT-01 | 04-03-PLAN.md | CSV export — download forecast results and transition matrix for current session via st.download_button | SATISFIED | st.download_button present in both 1_Brand_Share.py (line 427) and 2_Churn.py (line 351); REQUIREMENTS.md shows Complete |
| SET-01 | 04-04-PLAN.md | app/pages/4_Settings.py — list registered datasets with row count, state count, domain, and last-seeded timestamp; allow re-running seed script | SATISFIED | 4_Settings.py exists with Datasets tab calling list_datasets(); "Re-run seed script" button in Advanced expander; REQUIREMENTS.md shows Complete |

No orphaned requirements detected. All phase-04 IDs appear in plan frontmatter and are covered.

---

### Anti-Patterns Found

No anti-patterns found. Scanned app/Home.py, app/pages/4_Settings.py, and core/db/queries.py for: TODO/FIXME, placeholder text, return null/empty stubs, hardcoded empty props. None present in phase-04 modified files.

---

### Human Verification Required

#### 1. Home KPI strip with seeded DB

**Test:** Run `uv run python scripts/seed_data.py` then `uv run streamlit run app/Home.py` and open the browser.
**Expected:** KPI strip shows "2" for Datasets Registered, a non-zero number for Simulations Run (after running any forecast), no error warnings visible on page.
**Why human:** Requires a seeded DuckDB file and running Streamlit server to confirm live rendering.

#### 2. CSV download from Brand Share page

**Test:** Navigate to Brand Share, run a forecast, then click "Download forecast CSV" button.
**Expected:** Browser downloads a .csv file containing `# Forecast` and `# Transition Matrix` sections with state labels as column headers.
**Why human:** st.download_button behavior requires browser interaction; actual file content delivery cannot be verified without a running Streamlit session.

#### 3. CSV download from Churn page

**Test:** Navigate to Churn, run analysis, then click "Download churn CSV".
**Expected:** Browser downloads a .csv file with baseline forecast and transition matrix sections.
**Why human:** Same as above — requires running Streamlit session.

#### 4. Settings Datasets tab with seeded data

**Test:** Navigate to Settings after seeding; inspect the Datasets tab table.
**Expected:** Table shows at least 2 rows (brand_share + churn domains); Created column shows formatted timestamps rather than "—".
**Why human:** Requires seeded DB and visual inspection of table rendering.

---

### Gaps Summary

No gaps. All six observable truths are fully verified:
- HOME-01: app/Home.py KPI strip calls get_home_kpis() against four real DuckDB SQL queries; renders live dataset_count, sim_run_count, avg_mape from the database.
- RPT-01: Both domain pages have conditionally rendered st.download_button that calls their respective CSV-bytes helpers with the session state forecast result.
- SET-01: 4_Settings.py exists with 4 tabs; Datasets tab calls list_datasets() and renders a dataframe with name/domain/rows/states/created_at; Re-run seed button fires subprocess.run against scripts/seed_data.py.
- Full test suite (101 tests), ruff, and mypy all pass clean.

---

_Verified: 2026-06-01_
_Verifier: Claude (gsd-verifier)_
