# Phase 04: Home, Export & Settings — Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the app into a coherent product:

- **HOME-01** — `app/Home.py` KPI strip sourced from real DuckDB data (datasets count, sim runs, last forecast MAPE, last forecast timestamp). Recent Forecasts list from `forecasts` table. Empty states handled gracefully.
- **RPT-01** — CSV export via `st.download_button` inside Brand Share page and Churn page. Download contains the forecast result array + transition matrix shaped as CSV rows.
- **SET-01** — `app/pages/4_Settings.py` with Datasets tab (listing with name, domain, rows, states, created_at + "Re-run seed script" button), Preferences tab (read-only), Appearance tab (locked to indigo v1), About tab (static version info).

The Markov engine (Phase 01), design system + Brand Share (Phase 02), and Churn domain (Phase 03) are complete and called — not modified. QA/Deployment (Phase 05) is out of scope here.

</domain>

<decisions>
## Implementation Decisions

### Home Dashboard KPI Wiring (HOME-01)

- **D-01**: Four KPI cards matching the design reference (pages2.jsx PageDashboard):
  1. **Active Models** — hardcoded `3` (m1/m2/m3 — constant for v1); tooltip lists the three models.
  2. **Datasets Registered** — `SELECT COUNT(*) FROM datasets` via new `get_home_kpis()` query.
  3. **Last Forecast (MAPE)** — `SELECT accuracy_metrics_json FROM forecasts ORDER BY created_at DESC LIMIT 1`; parse `mape` key from JSON. Show `"—"` if forecasts table is empty.
  4. **Simulations Run** — `SELECT COUNT(*) FROM simulation_runs`.

- **D-02**: Recent Forecasts section lists the last 5 forecasts from `forecasts` table (id, dataset_id → name via join, model_type, created_at, mape from accuracy_metrics_json). Each row shows dataset name + model badge + date + MAPE badge. Empty state message if table is empty.

- **D-03**: Home KPI query (`get_home_kpis()`) goes in `core/db/queries.py` to preserve the no-SQL-in-app rule. Returns a `HomeKpis` frozen dataclass.

- **D-04**: `list_recent_forecasts(conn, n=5)` also goes in `core/db/queries.py`. Returns `list[RecentForecast]` frozen dataclass.

- **D-05**: `Dataset.created_at: datetime | None` field added to the existing `Dataset` dataclass. `list_datasets()` query extended to include `created_at`. This is a non-breaking change (all callers use keyword access on the dataclass fields).

### CSV Export (RPT-01)

- **D-06**: Export target on Brand Share page: the forecast result for the current session — `BrandShareForecastResult` fields `m1_forecast`, `m2_forecast`, `m3_forecast` (horizon×n_states), and `transition_matrix` (n_states×n_states). Shaped as two CSV sections: "# Forecast" header + rows, then "# Transition Matrix" header + rows. State labels used as column headers.

- **D-07**: Export target on Churn page: `ChurnAnalysisResult.baseline_forecast` (horizon×n_states) + `transition_matrix`. Same two-section CSV format for consistency.

- **D-08**: Serialize to CSV bytes in a module-level helper `_forecast_to_csv_bytes(result, state_labels)` inside each page file. No new module needed — the helper is 15-20 lines, inline in the page. CSV bytes built via `io.StringIO` + `csv.writer`.

- **D-09**: Download button filename: `markovlens_brand_share_forecast_{timestamp}.csv` and `markovlens_churn_forecast_{timestamp}.csv`. Timestamp from `datetime.now().strftime("%Y%m%d_%H%M")`.

- **D-10**: Download button placed in Overview tab (Brand Share) and Overview tab (Churn) next to the KPI strip, or as a small ghost button in the tab header area. Not gated behind "Run Forecast" — only visible once result exists in session state.

### Settings Page (SET-01)

- **D-11**: 4-tab layout matching design reference (pages3.jsx PageSettings): Datasets / Preferences / Appearance / About. Tab nav via `st.tabs()` — simpler than the custom sidebar-card pattern in the design reference; Streamlit `st.tabs` is the idiomatic equivalent.

- **D-12**: Datasets tab: table rendered via `st.dataframe()` or `st.table()` with columns: Name, Domain, Rows, States, Created. "Re-run seed script" button calls `subprocess.run(["uv", "run", "python", "scripts/seed_data.py"])` in a spinner. Button is in a danger expander ("Advanced") to prevent accidental clicks. Dataset upload (DATA-04) is v2 — do NOT add an upload drawer.

- **D-13**: Preferences tab: read-only display of current defaults (n_simulations=10,000, seed=42, horizon=12 months). Values from `core.config.settings`. No edit controls for v1.

- **D-14**: Appearance tab: theme token note only — "Theme locked to light mode in v1". No interactive toggles.

- **D-15**: About tab: MarkovLens v0.1.0, MIT license, links to GitHub + docs.

- **D-16**: Settings page is `4_Settings.py`. Numbered prefix ensures it appears last in sidebar.

### Claude's Discretion

- Whether Recent Forecasts renders as a custom HTML table or `st.dataframe()` (lean toward `st.dataframe` with column config for cleanliness).
- Exact CSV column order (alphabetical state labels or sorted by most active state first — use sorted alphabetical to match `queries.py` convention).
- Whether `HomeKpis` and `RecentForecast` dataclasses live in `core/db/queries.py` directly or a new `core/db/home_queries.py` file (lean toward keeping in `queries.py` unless it grows beyond ~30 lines).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Reference (visual ground truth)
- `docs/design-reference/js/pages2.jsx` — PageDashboard (Page 4): KPI cards, Recent Forecasts list, Quick actions section, Methodology card
- `docs/design-reference/js/pages3.jsx` — PageSettings (Page 12): 4-tab layout, Datasets table, Preferences, Appearance, About
- `docs/design-reference/js/data.jsx` — RECENT[] data shape (reference for Recent Forecasts list structure)
- `docs/design-reference/shots/landing.png` — visual ground truth for Home page
- `docs/design-reference/shots/ds.png` — design system reference screenshot

### Prior Phase Context
- `.planning/phases/02-design-system-brand-share/02-CONTEXT.md` — design system decisions (D-01..D-21)
- `.planning/phases/03-churn-domain/03-CONTEXT.md` — Churn service structure, ChurnAnalysisResult fields
- `.planning/phases/02-design-system-brand-share/02-04-PLAN.md` — Brand Share page structure (pattern to follow for Settings + for where to insert download button)

### Markov & App Code
- `app/Home.py` — current scaffold (KPI strip hardcoded, Recent Forecasts placeholder)
- `app/pages/1_Brand_Share.py` — full page; insert download button after KPI strip in Overview tab
- `app/pages/2_Churn.py` — full page; insert download button in Overview tab
- `app/styles/__init__.py` — `inject_theme()` + `register_theme()` for Settings page header
- `app/components/kpi_card.py` — reuse for Home KPI strip
- `app/components/empty_state.py` — use for empty forecasts list
- `core/db/queries.py` — extend with `HomeKpis`, `RecentForecast`, `get_home_kpis()`, `list_recent_forecasts()`, `created_at` on `Dataset`
- `core/db/schema.sql` — forecasts table: id, dataset_id, model_type, horizon_steps, forecast_json, accuracy_metrics_json, created_at
- `core/db/connection.py` — `get_connection()` singleton
- `core/config.py` — `settings` for Preferences tab defaults
- `scripts/seed_data.py` — called by Settings "Re-run seed" button
- `domains/brand_share/service.py` — `BrandShareForecastResult` fields for CSV export
- `domains/churn/service.py` — `ChurnAnalysisResult` fields for CSV export

### Rules
- `.claude/rules/streamlit-conventions.md` — page structure, caching, loading/empty/error states
- `.claude/rules/data-storage.md` — DuckDB patterns, parameterized queries
- `.claude/rules/python-conventions.md` — type hints, @dataclass(frozen=True)
- `.claude/rules/coding-style.md` — naming, no magic numbers, comments policy

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/components/kpi_card.py` — `kpi_card(label, value, unit, delta, delta_suffix, accent, icon, tooltip)` — ready
- `app/components/empty_state.py` — `empty_state(icon, title, description, action=None)` — ready
- `app/components/section_header.py` — ready
- `app/styles/__init__.py` — `inject_theme()` + `register_theme()` — call at page top
- `core/db/queries.py` — `Dataset`, `list_datasets(conn, domain=None)`, `get_dataset(conn, id)` — extend, don't replace

### Critical Schema Facts
- `forecasts.accuracy_metrics_json` is JSON; extract `mape` key via DuckDB `json_extract_string()` or Python `json.loads()`.
- `datasets.created_at` already exists in schema — just not included in the `Dataset` dataclass or `list_datasets()` query yet.
- `simulation_runs` table count = total Monte Carlo runs across all sessions; reset on DB wipe.

### Integration Points
- `app/Home.py` — full rewrite of KPI strip + Recent Forecasts section; preserve header, Quick Actions, Methodology card structure
- `app/pages/1_Brand_Share.py` — add ~20-line download button block; minimal change
- `app/pages/2_Churn.py` — add ~20-line download button block; minimal change
- `app/pages/4_Settings.py` — new file; auto-discovered by Streamlit at `/Settings`

### Test Infrastructure
- `tests/unit/` — new `test_home_queries.py` for get_home_kpis + list_recent_forecasts
- `tests/integration/test_queries.py` — existing; extend with integration tests for new query functions
- Pattern: `seeded_conn` fixture from `tests/integration/test_brand_share_service.py` — reuse or mirror for home queries tests
- Smoke test: extend `tests/unit/test_page_import.py` with Settings page import check

</code_context>

<specifics>
## Specific Implementation Notes

### get_home_kpis() query shape
```python
@dataclass(frozen=True)
class HomeKpis:
    dataset_count: int
    sim_run_count: int
    last_forecast_at: datetime | None  # None if forecasts table empty
    avg_mape: float | None             # None if no accuracy_metrics_json

def get_home_kpis(conn: duckdb.DuckDBPyConnection) -> HomeKpis: ...
```

### RecentForecast shape
```python
@dataclass(frozen=True)
class RecentForecast:
    forecast_id: str
    dataset_name: str
    domain: str
    model_type: str
    created_at: datetime
    mape: float | None  # parsed from accuracy_metrics_json

def list_recent_forecasts(conn: duckdb.DuckDBPyConnection, n: int = 5) -> list[RecentForecast]: ...
```

### Dataset.created_at addition
```python
@dataclass(frozen=True)
class Dataset:
    id: str
    domain: str
    name: str
    source_path: str
    row_count: int
    n_states: int
    created_at: datetime | None  # ← NEW; None if schema pre-dates migration
```

### CSV export shape (both domains)
```
period,<state_1>,<state_2>,...,<state_n>
# Forecast (rows = horizon+1 steps including period 0)
0,0.45,0.30,...
1,0.43,0.32,...
...
# Transition Matrix
<from_state_1>,0.90,0.05,...
<from_state_2>,0.03,0.85,...
```

### Settings "Re-run seed" button
```python
import subprocess
with st.spinner("Re-seeding…"):
    result = subprocess.run(
        ["uv", "run", "python", "scripts/seed_data.py"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
    )
if result.returncode == 0:
    st.success("Seed completed.")
    st.cache_resource.clear()  # invalidate DB connection so new data is visible
else:
    st.error(f"Seed failed: {result.stderr[-500:]}")
```

</specifics>

<deferred>
## Deferred Ideas

- **Dataset upload from Settings UI** — DATA-04 (v2); design reference has the drawer but REQUIREMENTS.md marks it out-of-scope for v1. Do NOT implement the upload drawer.
- **Scenarios save/load** — `scenarios` DuckDB table exists but UI is deferred to v2.
- **PDF reports** — RPT-02 (v2); the design reference has a PageReports but scope is CSV-only for v1.
- **Theme toggle** — Appearance tab in design reference supports dark/light; locked to light for v1.
- **Preferences editing** — read-only in v1; sliders/inputs deferred to v2.

*No pending todos matched Phase 04 scope.*

</deferred>

---

*Phase: 04-home-export-settings*
*Context gathered: 2026-06-01*
