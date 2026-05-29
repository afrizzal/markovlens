---
phase: 01-markov-engine
plan: 05
type: execute
wave: 4
depends_on:
  - 02
  - 03
  - 04
files_modified:
  - data/seed/telco_churn.csv
  - data/SOURCES.md
  - .gitignore
  - scripts/seed_data.py
  - tests/integration/test_queries.py
  - README.md
autonomous: false
requirements:
  - DATA-02
user_setup:
  - service: ibm-telco-csv
    why: "Reference dataset for churn domain — must be committed to repo before seed script can populate DuckDB"
    dashboard_config:
      - task: "Download IBM Telco Customer Churn CSV"
        location: "https://www.kaggle.com/datasets/blastchar/telco-customer-churn (file: WA_Fn-UseC_-Telco-Customer-Churn.csv) — Claude executes the download via Kaggle CLI or direct curl if credentials are available; otherwise the human places the file at data/seed/telco_churn.csv before running the seed script"
must_haves:
  truths:
    - "data/seed/telco_churn.csv is committed to the repo (D-02, D-03)"
    - "data/SOURCES.md exists and documents IBM Telco origin + license context (D-04)"
    - ".gitignore allows data/seed/*.csv to be tracked while data/raw/ and data/*.duckdb stay ignored (D-03)"
    - "README.md links the Kaggle source page and attributes IBM Telco (D-05)"
    - "scripts/seed_data.py populates transitions table with synthetic FMCG DGP (D-01) and IBM Telco discretized data (D-02)"
    - "scripts/seed_data.py is idempotent — running twice produces identical row counts (D-23)"
    - "scripts/seed_data.py writes at least 5 rows to the forecasts table (Roadmap Success Criterion 5)"
    - "Seed script uses validate_transitions_df, build_transition_matrix, ndarray_to_json from core/"
  artifacts:
    - path: "data/seed/telco_churn.csv"
      provides: "IBM Telco Customer Churn raw CSV (committed)"
      min_lines: 5000
    - path: "data/SOURCES.md"
      provides: "Dataset attribution and license context"
      contains: "Telco"
    - path: ".gitignore"
      provides: "Updated to track data/seed/*.csv while excluding data/raw/ and data/*.duckdb"
      contains: "!data/seed/"
    - path: "README.md"
      provides: "User-visible attribution + Kaggle source link for IBM Telco (D-05)"
      contains: "blastchar/telco-customer-churn"
    - path: "scripts/seed_data.py"
      provides: "Synthetic FMCG DGP + IBM Telco ingest + reference forecasts populate DuckDB"
      contains: "synthetic_fmcg"
  key_links:
    - from: "scripts/seed_data.py"
      to: "core.db.connection.init_schema"
      via: "from core.db.connection import"
      pattern: "from core\\.db\\.connection import"
    - from: "scripts/seed_data.py"
      to: "core.models.M1Homogeneous"
      via: "from core.models import for reference forecasts"
      pattern: "from core\\.models import"
    - from: "scripts/seed_data.py"
      to: "core.db.serialization.ndarray_to_json"
      via: "ndarray_to_json for forecast_json column"
      pattern: "ndarray_to_json"
    - from: "scripts/seed_data.py"
      to: "DELETE WHERE dataset_id"
      via: "Idempotency via D-23 pattern"
      pattern: "DELETE FROM .* WHERE dataset_id"
---

<objective>
Populate DuckDB with synthetic FMCG brand share data (D-01) and IBM Telco churn data (D-02) plus 5+ reference forecasts. Make the seed script idempotent via D-23 DELETE-before-INSERT.

Purpose: Phase 04 Home dashboard requires the forecasts table to be non-empty on cold start. Phase 02/03 domain pages need both registered datasets present for dropdown population. Without this script, no demo can run end-to-end.

Output:
- Committed data/seed/telco_churn.csv (committed dataset, ~7k rows)
- New data/SOURCES.md with attribution
- Updated .gitignore (allow data/seed/*.csv tracked)
- README.md updated with IBM Telco attribution + Kaggle source link (D-05)
- Fully implemented scripts/seed_data.py with synthetic FMCG DGP + Telco processing + reference forecasts
- 2 remaining integration tests (test_seed_idempotency, test_seed_produces_reference_forecasts) pass green
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-markov-engine/01-CONTEXT.md
@.planning/phases/01-markov-engine/01-RESEARCH.md
@.planning/phases/01-markov-engine/01-VALIDATION.md
@.planning/phases/01-markov-engine/01-02-SUMMARY.md
@.planning/phases/01-markov-engine/01-03-SUMMARY.md
@.planning/phases/01-markov-engine/01-04-SUMMARY.md
@scripts/seed_data.py
@core/db/connection.py
@core/db/queries.py
@core/db/serialization.py
@core/io/loaders.py
@core/models.py
@core/db/schema.sql
@.gitignore
@README.md
@tests/integration/test_queries.py
@.claude/skills/dataset-prepper/SKILL.md
@.claude/rules/data-storage.md

<interfaces>
All consumed contracts are in place from Plans 02, 03, 04:

```python
# core/db/connection.py
from core.db.connection import get_connection, init_schema, close_connection

# core/db/queries.py
from core.db.queries import build_transition_matrix

# core/db/serialization.py
from core.db.serialization import ndarray_to_json

# core/io/loaders.py (DATA-01 minimal helper)
from core.io.loaders import validate_transitions_df

# core/models.py
from core.models import M1Homogeneous, M2TimeVarying

# core/simulation.py
from core.simulation import monte_carlo_simulate
```

DuckDB schema (from core/db/schema.sql):
- `datasets(id, domain, name, source_path, row_count, n_states, metadata_json, created_at)`
- `transitions(dataset_id, entity_id, period, from_state, to_state, weight)`
- `transition_matrices(id, dataset_id, model_type, period, matrix_json, n_observations, computed_at)`
- `forecasts(id, dataset_id, model_type, horizon_steps, forecast_json, accuracy_metrics_json, created_at)`

IBM Telco CSV columns (per RESEARCH.md and SKILL.md): `customerID`, `tenure` (months), `Churn` ("Yes"/"No"). Other ~18 columns are demographic and unused by Phase 01.
</interfaces>
</context>

<tasks>

<task type="checkpoint:human-action" gate="blocking">
  <name>Task 1: Obtain and commit IBM Telco CSV at data/seed/telco_churn.csv (D-02)</name>
  <files>data/seed/telco_churn.csv</files>
  <action>
Attempt to automate the download via Kaggle CLI:
  uv run python -c "import os; print('KAGGLE_USERNAME' in os.environ)"
If True, run: kaggle datasets download -d blastchar/telco-customer-churn -p data/seed --unzip && mv data/seed/WA_Fn-UseC_-Telco-Customer-Churn.csv data/seed/telco_churn.csv

If credentials are missing, ask the user via the checkpoint below to either provide a public mirror URL for curl, or place the file manually.

After the file is at data/seed/telco_churn.csv, run head/wc validation to confirm correctness (see how-to-verify below). After verification succeeds, **stage and commit the CSV** so downstream plans can rely on `git ls-files data/seed/telco_churn.csv` returning the path. Use: `rtk git add data/seed/telco_churn.csv && rtk git commit -m "data(01): commit IBM Telco churn reference CSV (D-02)"`.
  </action>
  <verify>
    <automated>test -f data/seed/telco_churn.csv && head -1 data/seed/telco_churn.csv | grep -q customerID && wc -l data/seed/telco_churn.csv | awk '{exit !( $1 > 7000 && $1 < 7050 )}' && git ls-files data/seed/telco_churn.csv | grep -q telco_churn.csv</automated>
  </verify>
  <done>data/seed/telco_churn.csv exists at correct size and shape (header includes customerID, tenure, Churn; ~7044 rows) AND is tracked by git (committed so subsequent plans / CI can rely on its presence).</done>
  <what-built>
    The IBM Telco Customer Churn CSV (`WA_Fn-UseC_-Telco-Customer-Churn.csv`) must exist at `data/seed/telco_churn.csv` (renamed) AND be tracked/committed by git before any subsequent task can run. CONTEXT.md D-02 confirms this file IS committed to the repo per project decision, but it does not exist yet.

    Claude has attempted CLI-based download options:
    1. `kaggle datasets download -d blastchar/telco-customer-churn -p data/seed --unzip` (requires KAGGLE_USERNAME + KAGGLE_KEY env vars)
    2. Direct fetch from a public mirror via `curl` (Claude can attempt this if user authorizes a specific URL)

    If neither automation path succeeds, the human must place the file manually. Either way, the file must end up committed — Plan 06 has a Task 0 that verifies `git ls-files data/seed/telco_churn.csv` returns the path, and the integration tests in this plan call `seed_data.main()` which hardcodes the path.
  </what-built>
  <how-to-verify>
    1. Confirm one of the following has happened:
       - Claude executed `kaggle datasets download` successfully because credentials were set in env, OR
       - Claude executed `curl -L -o data/seed/telco_churn.csv <public-mirror-url>` with user-confirmed URL, OR
       - You downloaded the CSV from https://www.kaggle.com/datasets/blastchar/telco-customer-churn (file name in the zip is `WA_Fn-UseC_-Telco-Customer-Churn.csv`) and renamed/placed it at `data/seed/telco_churn.csv`.
    2. Run: `ls -la data/seed/telco_churn.csv` — must show a file of approximately 950 KB.
    3. Run: `head -2 data/seed/telco_churn.csv` — must show a header line containing the words `customerID`, `tenure`, `Churn` (among ~21 columns).
    4. Run: `wc -l data/seed/telco_churn.csv` — must show approximately 7044 lines (header + 7043 data rows).
    5. Run: `git ls-files data/seed/telco_churn.csv` — must print `data/seed/telco_churn.csv`. (If empty, the file has not been committed yet — stage with `rtk git add data/seed/telco_churn.csv` and commit before approving.)
  </how-to-verify>
  <resume-signal>Type "approved" when `data/seed/telco_churn.csv` exists, the head/wc checks succeed, AND `git ls-files data/seed/telco_churn.csv` shows it as tracked. Reply with a description of any issue you encountered if the file could not be placed.</resume-signal>
  <acceptance_criteria>
    - `data/seed/telco_churn.csv` exists.
    - First line of file contains the substrings `customerID`, `tenure`, `Churn`.
    - File has between 7000 and 7050 lines total (header + ~7043 rows).
    - `git ls-files data/seed/telco_churn.csv | grep -q "telco_churn.csv"` exits 0 (file is tracked by git — Plan 06 Task 0 will re-check this).
  </acceptance_criteria>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Update .gitignore to track data/seed/*.csv + create data/SOURCES.md + update README.md with D-05 attribution</name>
  <read_first>
    - .gitignore (current state — note lines 41-51 for the data/ section)
    - README.md (current state — locate a sensible section header to add the dataset attribution under, e.g. an existing "Data" or "About" or "Datasets" section, or append a new "Data Sources" section near the bottom)
    - .planning/phases/01-markov-engine/01-CONTEXT.md (D-03, D-04, D-05 — gitignore policy + SOURCES.md requirement + README attribution)
  </read_first>
  <action>
**Step A: Edit `.gitignore`** — Update the `# Data — never commit` section. Replace lines 41-51 (the current data section) with this exact block:

```
# Data — never commit raw or compiled
data/markovlens.duckdb
data/markovlens.duckdb.wal
data/raw/*.csv
data/raw/*.parquet
data/raw/*.zip
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
data/cache/*
!data/cache/.gitkeep
# Seed reference datasets are tracked (D-03) — small, publicly redistributable, needed for cold-start deploy
!data/seed/
!data/seed/*.csv
```

Verify result with: `grep -A 20 "Data — never commit" .gitignore` — output should show the `!data/seed/` allowlist lines.

**Step B: Create `data/SOURCES.md`** with this content:

```markdown
# Dataset Sources

This file documents the origin, license context, and reason-for-commit of every dataset
bundled in `data/seed/`.

## IBM Telco Customer Churn

| Field | Value |
|-------|-------|
| File | `data/seed/telco_churn.csv` |
| Original filename (Kaggle) | `WA_Fn-UseC_-Telco-Customer-Churn.csv` |
| Source | https://www.kaggle.com/datasets/blastchar/telco-customer-churn |
| Origin | IBM Watson Sample Data — Cognos Analytics community resources |
| License context | Effectively public domain — thousands of public GitHub repositories redistribute this CSV as a reference dataset for churn modeling. No restrictive license is attached to the file by IBM or the Kaggle uploader. |
| Rows | ~7043 customers |
| Columns used | `customerID`, `tenure` (months), `Churn` (Yes/No) — other demographic columns are ignored by the Phase 01 seed script |
| Why committed (D-02, D-04) | Deployment convenience for Streamlit Cloud cold start. Without the CSV committed, the cold-start KPI population would require Kaggle credentials inside the Streamlit Cloud secrets store, adding friction with no offsetting benefit. |
| Discretization (D-02) | tenure mapped to ordinal states: `new` (0-12 mo), `growing` (12-24 mo), `mature` (24-48 mo), `loyal` (48+ mo) + absorbing `churned` state |

## Synthetic FMCG Brand Share

| Field | Value |
|-------|-------|
| File | (generated in memory by `scripts/seed_data.py`) |
| Source | Synthetic data-generating process designed for this project |
| Brands | Alpha, Beta, Gamma, Delta, Epsilon |
| Periods | 24 (monthly, ~2 years) |
| Initial share | [0.35, 0.25, 0.20, 0.12, 0.08] |
| Base P matrix | Hand-crafted plausible row-stochastic 5x5 — see seed script docstring |
| Variability | Small Dirichlet noise per period (m2/m3 interesting) |
| Why synthetic | Brand share Kaggle datasets are noisy and inconsistent; a documented synthetic DGP gives the portfolio piece reproducible, paper-comparable numerics without compromising honesty (the README clearly states "synthetic"). |
```

**Step C: Update `README.md` with IBM Telco attribution + Kaggle link (locked decision D-05).**

D-05 from CONTEXT.md: "README attributes source and links to Kaggle page." Add a "## Data Sources" subsection near the bottom of README.md (after the main "About"/"How to Run" content, before any final footer/license section). If the README already has a "Data" or "Datasets" or "Acknowledgements" section, append underneath it instead of creating a new section. Use this content:

```markdown
## Data Sources

| Dataset | Source | Why committed |
|---|---|---|
| IBM Telco Customer Churn | [Kaggle: blastchar/telco-customer-churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) (originally IBM Watson Sample Data) | Cold-start deployability on Streamlit Cloud — see `data/SOURCES.md` for license context |
| Synthetic FMCG brand share | Generated by `scripts/seed_data.py` (5 brands × 24 periods, hand-crafted base P + Dirichlet noise) | Reproducible synthetic DGP — keeps brand share numerics paper-comparable without claiming to use real proprietary data |

See [`data/SOURCES.md`](data/SOURCES.md) for full attribution, discretization rules, and license context.
```

Run `git status` to confirm `.gitignore`, `data/SOURCES.md`, and `README.md` are all staged-able.
  </action>
  <verify>
    <automated>grep -q "!data/seed/" .gitignore && test -f data/SOURCES.md && grep -q "Telco" data/SOURCES.md && grep -q "blastchar/telco-customer-churn" README.md && echo OK</automated>
  </verify>
  <acceptance_criteria>
    - `.gitignore` contains `!data/seed/` (allowlist directive).
    - `.gitignore` contains `!data/seed/*.csv` (allowlist CSV files).
    - `.gitignore` contains `data/markovlens.duckdb` (still ignored).
    - `data/SOURCES.md` exists.
    - `data/SOURCES.md` contains the strings `Telco`, `customerID`, `Synthetic FMCG`, `Dirichlet`.
    - `git check-ignore data/seed/telco_churn.csv` exits nonzero (file is NOT ignored — i.e., it can be tracked).
    - `README.md` contains the substring `blastchar/telco-customer-churn` (Kaggle slug — D-05 attribution).
    - `README.md` contains the substring `data/SOURCES.md` (cross-reference back to attribution file).
  </acceptance_criteria>
  <done>
    .gitignore allows data/seed/*.csv to be tracked. SOURCES.md documents both datasets per D-04. README.md attributes IBM Telco with Kaggle link per D-05.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3a: Implement scripts/seed_data.py helpers (constants, _delete_dataset_rows, _generate_synthetic_fmcg, _load_telco_transitions, _bulk_insert_transitions, _persist_reference_forecast)</name>
  <read_first>
    - scripts/seed_data.py (current 30-line stub — will be replaced; Task 3a creates the imports + constants + helper functions only)
    - core/db/schema.sql (verify all 6 table columns and types)
    - core/models.py (M1Homogeneous, M2TimeVarying constructor signatures from Plan 02 — note D-08 ndarray)
    - core/db/queries.py (build_transition_matrix signature)
    - core/db/serialization.py (ndarray_to_json signature)
    - core/io/loaders.py (validate_transitions_df)
    - data/seed/telco_churn.csv (verify column names — sample first 2 rows via head if needed)
    - .claude/skills/dataset-prepper/SKILL.md (canonical format)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (section "Synthetic FMCG DGP Design" + "Telco Churn State Discretization" + "Pitfall 8: Seed Script Idempotency")
    - .planning/phases/01-markov-engine/01-CONTEXT.md (D-01, D-02, D-23)
  </read_first>
  <behavior>
    - Module top contains the docstring + imports + constants block + helper functions, but NOT yet the public `seed_brand_share`, `seed_churn`, or `main` (those land in Task 3b).
    - `_delete_dataset_rows(conn, dataset_id)` issues DELETE for every dataset-scoped table (forecasts, transition_matrices, simulation_runs, scenarios, transitions, datasets).
    - `_generate_synthetic_fmcg(rng)` returns `(pd.DataFrame transitions, list[np.ndarray] P_t_list)` — the per-period matrices that will be fed to M2TimeVarying.
    - `_load_telco_transitions(csv_path)` reads the CSV and returns a long-format DataFrame with the canonical columns (entity_id, period, from_state, to_state, weight). Raises FileNotFoundError if the CSV is missing.
    - `_bulk_insert_transitions(conn, dataset_id, df)` validates df via validate_transitions_df then inserts via DuckDB native df registration.
    - `_persist_reference_forecast(conn, dataset_id, model_type, horizon, forecast_array)` writes one row to the forecasts table using ndarray_to_json for the JSON column.
    - Running `uv run python -c "import scripts.seed_data as s"` succeeds — no syntax errors, no NameError.
  </behavior>
  <action>
**Replace `scripts/seed_data.py` entirely with this scaffolding.** Task 3a delivers ONLY the docstring, imports, constants, and private helpers. The public entry points (`seed_brand_share`, `seed_churn`, `main`) land in Task 3b — until then there is no `if __name__ == "__main__":` block.

```python
"""Seed local DuckDB with brand-share + churn datasets.

Per CONTEXT.md decisions:
- D-01: Brand share uses a synthetic FMCG data-generating process (5 brands x 24 periods).
- D-02: Churn uses the IBM Telco CSV committed at data/seed/telco_churn.csv with tenure
  discretized into ['new', 'growing', 'mature', 'loyal'] + absorbing 'churned' state.
- D-23: Idempotency via DELETE-WHERE-dataset_id before INSERT for every table.
- DATA-02 Roadmap SC 5: forecasts table must contain >= 5 reference rows after seed.

Synthetic FMCG DGP parameters (Claude's Discretion):
- Brands: Alpha, Beta, Gamma, Delta, Epsilon (n=5)
- Periods: 24 (monthly, simulating ~2 years)
- Initial share: [0.35, 0.25, 0.20, 0.12, 0.08]
- Base P matrix: hand-crafted plausible m1-like row-stochastic 5x5 (see P_BASE_FMCG)
- Per-period variation: small Dirichlet noise around P_BASE (drives M2/M3 interest)
- Aggregate transitions = (share_t[i] * P_BASE[i,j]) scaled to integer 'weight' units

Run with (after Task 3b lands):
    uv run python scripts/seed_data.py
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.db.connection import get_connection, init_schema  # noqa: E402
from core.db.queries import build_transition_matrix  # noqa: E402
from core.db.serialization import ndarray_to_json  # noqa: E402
from core.io.loaders import validate_transitions_df  # noqa: E402
from core.models import M1Homogeneous, M2TimeVarying  # noqa: E402

BRAND_SHARE_DATASET_ID: str = "ds_brand_share_synthetic"
CHURN_DATASET_ID: str = "ds_churn_telco"

FMCG_BRANDS: list[str] = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
FMCG_N_PERIODS: int = 24
FMCG_INITIAL_SHARE: np.ndarray = np.array([0.35, 0.25, 0.20, 0.12, 0.08])
FMCG_TOTAL_MARKET_UNITS: int = 100_000
FMCG_DIRICHLET_CONCENTRATION: float = 200.0  # higher = less noise per period

P_BASE_FMCG: np.ndarray = np.array(
    [
        [0.90, 0.04, 0.03, 0.02, 0.01],
        [0.05, 0.85, 0.05, 0.03, 0.02],
        [0.04, 0.06, 0.82, 0.05, 0.03],
        [0.03, 0.05, 0.06, 0.80, 0.06],
        [0.02, 0.03, 0.05, 0.07, 0.83],
    ],
    dtype=np.float64,
)

TENURE_STATE_BINS: list[tuple[str, int, int | None]] = [
    ("new", 0, 12),
    ("growing", 12, 24),
    ("mature", 24, 48),
    ("loyal", 48, None),
]
CHURNED_STATE: str = "churned"

REFERENCE_FORECAST_HORIZON: int = 12
RNG_SEED: int = 42


def _tenure_to_state(tenure: float) -> str:
    """Map a tenure-in-months value to an ordinal state name."""
    for state, lo, hi in TENURE_STATE_BINS:
        if hi is None and tenure >= lo:
            return state
        if hi is not None and lo <= tenure < hi:
            return state
    return TENURE_STATE_BINS[0][0]


def _delete_dataset_rows(conn, dataset_id: str) -> None:
    """D-23 idempotency: remove every row tied to a dataset_id across all tables."""
    conn.execute("DELETE FROM forecasts WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM transition_matrices WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM simulation_runs WHERE matrix_id IN (SELECT id FROM transition_matrices WHERE dataset_id = ?)", [dataset_id])
    conn.execute("DELETE FROM scenarios WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM transitions WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM datasets WHERE id = ?", [dataset_id])


def _generate_synthetic_fmcg(rng: np.random.Generator) -> tuple[pd.DataFrame, list[np.ndarray]]:
    """Generate synthetic FMCG transitions (long format) + per-period matrices.

    Returns
    -------
    transitions_df : pd.DataFrame
        Columns: entity_id, period, from_state, to_state, weight.
        entity_id is a synthetic aggregate id (one per brand) — weight encodes flow magnitude.
    P_t_list : list[np.ndarray]
        Per-period transition matrices (length FMCG_N_PERIODS), each shape (5, 5).
    """
    P_t_list: list[np.ndarray] = []
    rows: list[dict] = []
    share = FMCG_INITIAL_SHARE.copy()

    for period in range(1, FMCG_N_PERIODS + 1):
        P_t = np.array(
            [rng.dirichlet(P_BASE_FMCG[i] * FMCG_DIRICHLET_CONCENTRATION) for i in range(5)],
            dtype=np.float64,
        )
        P_t_list.append(P_t)

        for i, from_brand in enumerate(FMCG_BRANDS):
            for j, to_brand in enumerate(FMCG_BRANDS):
                flow = share[i] * P_t[i, j] * FMCG_TOTAL_MARKET_UNITS
                if flow >= 1:
                    rows.append(
                        {
                            "entity_id": f"fmcg_agg_{from_brand}",
                            "period": period,
                            "from_state": from_brand,
                            "to_state": to_brand,
                            "weight": float(round(flow)),
                        }
                    )
        share = share @ P_t
        share = share / share.sum()

    return pd.DataFrame(rows), P_t_list


def _load_telco_transitions(csv_path: Path) -> pd.DataFrame:
    """Parse data/seed/telco_churn.csv into long-format transitions.

    IBM Telco CSV has one row per customer with `tenure` (months) and `Churn` (Yes/No).
    For Phase 01 we treat this as a single-period transition: the customer's state
    AT END of period (tenure-discretized OR 'churned') vs an inferred PRIOR state
    (one tenure bracket below their current bracket — a plausible approximation).
    Customers with tenure=0 are excluded (no prior state to infer).
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"data/seed/telco_churn.csv not found at {csv_path}. "
            f"Place the IBM Watson Sample Data CSV at that path. See data/SOURCES.md."
        )
    raw = pd.read_csv(csv_path)
    raw = raw[raw["tenure"] > 0].copy()

    def _prior_state(tenure: float) -> str:
        prior = max(tenure - 1.0, 0.0)
        return _tenure_to_state(prior)

    raw["from_state"] = raw["tenure"].apply(_prior_state)
    raw["to_state"] = np.where(
        raw["Churn"] == "Yes",
        CHURNED_STATE,
        raw["tenure"].apply(_tenure_to_state),
    )
    transitions = pd.DataFrame(
        {
            "entity_id": raw["customerID"].astype(str),
            "period": 1,
            "from_state": raw["from_state"],
            "to_state": raw["to_state"],
            "weight": 1.0,
        }
    )
    return transitions


def _bulk_insert_transitions(conn, dataset_id: str, df: pd.DataFrame) -> int:
    """Insert long-format transitions for a dataset. Uses DuckDB native df param binding."""
    validate_transitions_df(df)
    df = df.assign(dataset_id=dataset_id)[
        ["dataset_id", "entity_id", "period", "from_state", "to_state", "weight"]
    ]
    conn.register("transitions_df", df)
    try:
        conn.execute("INSERT INTO transitions SELECT * FROM transitions_df")
    finally:
        conn.unregister("transitions_df")
    return len(df)


def _persist_reference_forecast(
    conn,
    dataset_id: str,
    model_type: str,
    horizon: int,
    forecast_array: np.ndarray,
) -> None:
    """Insert one row into the forecasts table with serialized forecast_json."""
    conn.execute(
        "INSERT INTO forecasts (id, dataset_id, model_type, horizon_steps, forecast_json) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            str(uuid.uuid4()),
            dataset_id,
            model_type,
            horizon,
            ndarray_to_json(forecast_array),
        ],
    )
```

Do NOT add `seed_brand_share`, `seed_churn`, `main`, or `if __name__ == "__main__":` yet — those belong to Task 3b. The module must still be importable without errors at the end of Task 3a (smoke test: `uv run python -c "import scripts.seed_data as s; print(s.BRAND_SHARE_DATASET_ID)"`).
  </action>
  <verify>
    <automated>uv run python -c "import scripts.seed_data as s; assert s.BRAND_SHARE_DATASET_ID == 'ds_brand_share_synthetic'; assert s.CHURN_DATASET_ID == 'ds_churn_telco'; assert callable(s._delete_dataset_rows); assert callable(s._generate_synthetic_fmcg); assert callable(s._load_telco_transitions); assert callable(s._bulk_insert_transitions); assert callable(s._persist_reference_forecast); print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "def _delete_dataset_rows" scripts/seed_data.py` returns 1 match (D-23 idempotency helper).
    - `grep -n "def _generate_synthetic_fmcg" scripts/seed_data.py` returns 1 match.
    - `grep -n "def _load_telco_transitions" scripts/seed_data.py` returns 1 match.
    - `grep -n "def _bulk_insert_transitions" scripts/seed_data.py` returns 1 match.
    - `grep -n "def _persist_reference_forecast" scripts/seed_data.py` returns 1 match.
    - `grep -E "DELETE FROM (forecasts|transition_matrices|simulation_runs|scenarios|transitions|datasets) WHERE" scripts/seed_data.py` returns at least 5 matches (each table deleted before INSERT per D-23).
    - `grep -c "def seed_brand_share\\|def seed_churn\\|def main" scripts/seed_data.py` returns 0 (these arrive in Task 3b — Task 3a is helpers-only).
    - `grep -c "raise NotImplementedError" scripts/seed_data.py` returns 0 (original stub fully replaced).
    - `uv run python -c "import scripts.seed_data"` exits 0 (module imports cleanly with all expected names defined).
  </acceptance_criteria>
  <done>
    Helper layer of seed_data.py is in place: constants, idempotency DELETEs, synthetic FMCG generator, IBM Telco parser, bulk-insert wrapper, forecast persister. Module imports cleanly; public entry points still pending in Task 3b.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3b: Implement public seed_brand_share, seed_churn, main + un-skip integration tests + run end-to-end</name>
  <read_first>
    - scripts/seed_data.py (after Task 3a — verify helpers are in place)
    - tests/integration/test_queries.py (read test_seed_idempotency and test_seed_produces_reference_forecasts exactly)
    - core/models.py (M1Homogeneous, M2TimeVarying signatures from Plan 02)
    - core/db/queries.py (build_transition_matrix signature)
    - core/db/serialization.py (ndarray_to_json)
    - .planning/phases/01-markov-engine/01-CONTEXT.md (D-01, D-02, D-23 once more — public entry points must wire everything together)
  </read_first>
  <behavior>
    - `seed_brand_share(conn, rng)` calls `_delete_dataset_rows`, inserts the dataset row, runs `_generate_synthetic_fmcg`, bulk-inserts transitions, builds the m1 and m2 reference forecasts, and persists both.
    - `seed_churn(conn, rng)` calls `_delete_dataset_rows`, inserts the dataset row, loads telco transitions via `_load_telco_transitions`, bulk-inserts them, builds the m1 reference forecasts at horizons 6/12/24, and persists all three.
    - `main()` opens the singleton connection, applies schema, calls both seed functions, and prints a summary line.
    - `uv run python scripts/seed_data.py` exits 0. Second invocation also exits 0 and produces identical row counts (D-23 idempotency).
    - The forecasts table contains exactly 5 rows after a clean seed: 2 brand_share (m1, m2) + 3 churn (m1 @ h=6, 12, 24).
  </behavior>
  <action>
Append the public entry points and the `if __name__ == "__main__":` guard to the end of `scripts/seed_data.py` (after `_persist_reference_forecast`). DO NOT touch the helpers or the top imports — Task 3a already shipped them.

```python
def seed_brand_share(conn, rng: np.random.Generator) -> None:
    """Populate brand_share dataset + transitions + 2 reference forecasts."""
    _delete_dataset_rows(conn, BRAND_SHARE_DATASET_ID)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [BRAND_SHARE_DATASET_ID, "brand_share", "Synthetic FMCG (5 brands)", "synthetic", 0, 5],
    )
    transitions_df, P_t_list = _generate_synthetic_fmcg(rng)
    n_inserted = _bulk_insert_transitions(conn, BRAND_SHARE_DATASET_ID, transitions_df)
    conn.execute("UPDATE datasets SET row_count = ? WHERE id = ?", [n_inserted, BRAND_SHARE_DATASET_ID])

    matrix, _counts = build_transition_matrix(conn, dataset_id=BRAND_SHARE_DATASET_ID)
    m1 = M1Homogeneous(P=matrix)
    forecast_m1 = m1.forecast(Y_1=FMCG_INITIAL_SHARE.copy(), horizon=REFERENCE_FORECAST_HORIZON)
    _persist_reference_forecast(
        conn, BRAND_SHARE_DATASET_ID, "m1", REFERENCE_FORECAST_HORIZON, forecast_m1.forecast_array
    )

    P_t_array = np.stack(P_t_list, axis=0)
    m2 = M2TimeVarying(P_t_sequence=P_t_array)
    forecast_m2 = m2.forecast(Y_1=FMCG_INITIAL_SHARE.copy(), horizon=REFERENCE_FORECAST_HORIZON)
    _persist_reference_forecast(
        conn, BRAND_SHARE_DATASET_ID, "m2", REFERENCE_FORECAST_HORIZON, forecast_m2.forecast_array
    )

    print(
        f"  brand_share: {n_inserted} transitions, 2 reference forecasts (m1, m2) persisted"
    )


def seed_churn(conn, rng: np.random.Generator) -> None:
    """Populate churn dataset + transitions + 3 reference forecasts."""
    _delete_dataset_rows(conn, CHURN_DATASET_ID)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            CHURN_DATASET_ID,
            "churn",
            "IBM Telco Customer Churn",
            "data/seed/telco_churn.csv",
            0,
            len(TENURE_STATE_BINS) + 1,
        ],
    )
    csv_path = ROOT / "data" / "seed" / "telco_churn.csv"
    transitions_df = _load_telco_transitions(csv_path)
    n_inserted = _bulk_insert_transitions(conn, CHURN_DATASET_ID, transitions_df)
    conn.execute("UPDATE datasets SET row_count = ? WHERE id = ?", [n_inserted, CHURN_DATASET_ID])

    matrix, counts = build_transition_matrix(conn, dataset_id=CHURN_DATASET_ID)
    Y_1 = counts.sum(axis=1).astype(np.float64)
    Y_1 = Y_1 / Y_1.sum()
    m1 = M1Homogeneous(P=matrix)
    for horizon in (6, 12, 24):
        forecast = m1.forecast(Y_1=Y_1.copy(), horizon=horizon)
        _persist_reference_forecast(
            conn, CHURN_DATASET_ID, "m1", horizon, forecast.forecast_array
        )

    print(
        f"  churn: {n_inserted} transitions, 3 reference forecasts (m1 at h=6,12,24) persisted"
    )


def main() -> None:
    """Initialize schema + load synthetic FMCG + IBM Telco datasets idempotently."""
    print("Connecting to DuckDB...")
    conn = get_connection()
    init_schema(conn)
    print("Schema initialized.")

    rng = np.random.default_rng(RNG_SEED)

    print("\nSeeding brand_share (synthetic FMCG)...")
    seed_brand_share(conn, rng)

    print("\nSeeding churn (IBM Telco)...")
    seed_churn(conn, rng)

    n_datasets = conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    n_transitions = conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
    n_forecasts = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    print(
        f"\nDone. datasets={n_datasets}, transitions={n_transitions}, forecasts={n_forecasts}"
    )


if __name__ == "__main__":
    main()
```

After the public entry points are appended, **un-skip the 2 remaining integration tests** in `tests/integration/test_queries.py`:
- `test_seed_idempotency`
- `test_seed_produces_reference_forecasts`

Then run the script end-to-end:
```bash
uv run python scripts/seed_data.py
uv run python scripts/seed_data.py  # second run for idempotency proof
uv run python -c "import duckdb; c = duckdb.connect('data/markovlens.duckdb'); print(c.execute('SELECT COUNT(*) FROM forecasts').fetchone())"
```

The second `seed_data.py` invocation must complete without errors and produce identical row counts to the first run. The forecasts count must be >= 5 (Roadmap SC 5).

Then run the integration tests:
```bash
uv run pytest tests/integration/test_queries.py -m integration -x -q
```

All 5 tests must pass.
  </action>
  <verify>
    <automated>uv run pytest tests/integration/test_queries.py -m integration -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "def seed_brand_share" scripts/seed_data.py` returns 1 match.
    - `grep -n "def seed_churn" scripts/seed_data.py` returns 1 match.
    - `grep -n "def main()" scripts/seed_data.py` returns 1 match.
    - `grep -n "if __name__ == \"__main__\":" scripts/seed_data.py` returns 1 match.
    - `grep -n "from core\\." scripts/seed_data.py` returns at least 4 matches (uses core/db/connection, core/db/queries, core/db/serialization, core/io/loaders, core/models).
    - `grep -E "f\".*WHERE|f\".*INSERT" scripts/seed_data.py` returns nothing (no f-string SQL injection paths — all queries use `?` parameter binding).
    - `uv run python scripts/seed_data.py` exits 0 on the first invocation.
    - `uv run python scripts/seed_data.py` exits 0 on the SECOND invocation (idempotent — does not raise constraint violation or duplicate-row errors).
    - Manual check: `uv run python -c "import duckdb; c = duckdb.connect('data/markovlens.duckdb'); print('forecasts:', c.execute('SELECT COUNT(*) FROM forecasts').fetchone()[0]); print('datasets:', c.execute('SELECT COUNT(*) FROM datasets').fetchone()[0]); print('transitions:', c.execute('SELECT COUNT(*) FROM transitions').fetchone()[0])"` prints `forecasts: 5`, `datasets: 2`, and `transitions: >= 6000` (Telco contributes ~7000 rows).
    - `uv run pytest tests/integration/test_queries.py -m integration -x -q` exits 0 with `5 passed`.
    - `grep -c "@pytest.mark.skip" tests/integration/test_queries.py` returns 0.
  </acceptance_criteria>
  <done>
    Seed script populates both datasets, writes >= 5 reference forecasts, and is idempotent. All 5 integration tests pass. Roadmap Phase 01 Success Criterion 5 satisfied.
  </done>
</task>

</tasks>

<verification>
After all tasks:
```bash
uv run pytest tests/integration/test_queries.py -m integration -v --tb=short
```
Expected: 5 passed, 0 failed.

Integration with Roadmap Success Criterion 5:
```bash
uv run python scripts/seed_data.py
uv run python -c "
import duckdb
c = duckdb.connect('data/markovlens.duckdb')
for t in ['datasets', 'transitions', 'forecasts']:
    print(f'{t}: {c.execute(f\"SELECT COUNT(*) FROM {t}\").fetchone()[0]}')
print('domains in datasets:', c.execute('SELECT DISTINCT domain FROM datasets').fetchall())
"
```
Output must show forecasts >= 5 and 2 distinct domains (`brand_share`, `churn`).
</verification>

<success_criteria>
- data/seed/telco_churn.csv committed (Task 1 acceptance includes `git ls-files` check).
- data/SOURCES.md documents both datasets.
- .gitignore tracks data/seed/*.csv while keeping data/raw/ and data/*.duckdb ignored.
- README.md attributes IBM Telco + Kaggle link per D-05.
- scripts/seed_data.py populates datasets, transitions, and forecasts idempotently.
- forecasts table has >= 5 rows after seed (Roadmap SC 5).
- All 5 integration tests pass green.
</success_criteria>

<output>
After completion, create `.planning/phases/01-markov-engine/01-05-SUMMARY.md` documenting:
- IBM Telco CSV provenance and commit decision (with git ls-files evidence)
- Synthetic FMCG DGP parameters used
- Idempotency mechanism (D-23 DELETE-before-INSERT helpers)
- Final row counts in each table after running the seed
- README D-05 attribution location (section name + line range)
- DATA-02 marked complete
</output>
