---
plan: 01-05
phase: 01-markov-engine
status: completed
completed_at: 2026-05-29
requirements_met:
  - DATA-02
key_files:
  created:
    - data/seed/telco_churn.csv
    - data/SOURCES.md
  modified:
    - .gitignore
    - scripts/seed_data.py
    - tests/integration/test_queries.py
    - README.md
---

# Plan 01-05: Data Seeding — Summary

## What Was Built

Populated DuckDB with two datasets: synthetic FMCG brand share (D-01) and IBM Telco churn (D-02). Implemented idempotent seed script, committed the Telco CSV reference dataset, and verified 5+ reference forecasts for cold-start dashboard (Roadmap SC 5).

## IBM Telco CSV Provenance

- **File:** `data/seed/telco_churn.csv`
- **Origin:** IBM Watson Sample Data (`WA_Fn-UseC_-Telco-Customer-Churn.csv`)
- **Source:** https://www.kaggle.com/datasets/blastchar/telco-customer-churn
- **Rows:** 7044 lines (header + 7043 customer rows)
- **Commit decision (D-02/D-03):** CSV committed to repo for Streamlit Cloud cold-start deployability — no Kaggle credentials needed at runtime
- **Verification:** `git ls-files data/seed/telco_churn.csv` → `data/seed/telco_churn.csv` ✓

## Synthetic FMCG DGP Parameters

- **Brands:** Alpha, Beta, Gamma, Delta, Epsilon (n=5)
- **Periods:** 24 (monthly, ~2 years)
- **Initial share:** `[0.35, 0.25, 0.20, 0.12, 0.08]`
- **Base P matrix:** Hand-crafted row-stochastic 5×5 with high diagonal (stable market)
- **Variability:** Dirichlet noise with concentration=200 per period (small variation → M2/M3 interesting)
- **Result:** 600 weighted transition rows inserted

## Idempotency Mechanism (D-23)

`_delete_dataset_rows(conn, dataset_id)` issues DELETE on 6 tables in dependency order before any INSERT:
```
forecasts → transition_matrices (+ simulation_runs via subquery) → scenarios → transitions → datasets
```
Running `uv run python scripts/seed_data.py` twice produces identical row counts (verified by `test_seed_idempotency`).

## Final Row Counts

| Table | Rows |
|-------|------|
| datasets | 2 (brand_share, churn) |
| transitions | 7,632 (600 FMCG + 7,032 Telco) |
| transition_matrices | 26 |
| forecasts | 7 (2 brand_share + 3 churn m1 + 2 extras) |

**Roadmap SC 5 satisfied:** forecasts ≥ 5 ✓

## README D-05 Attribution

Added `## Data Sources` section to `README.md` linking `blastchar/telco-customer-churn` (Kaggle slug) and referencing `data/SOURCES.md`.

## .gitignore Update

Replaced the `# Data — never commit` section to add `!data/seed/` and `!data/seed/*.csv` allowlist directives while keeping `data/markovlens.duckdb` and `data/raw/` ignored (D-03).

## Integration Tests

Un-skipped `test_seed_idempotency` and `test_seed_produces_reference_forecasts` in `tests/integration/test_queries.py`. All 5 integration tests pass ✓.

## Self-Check: PASSED

- `data/seed/telco_churn.csv` committed, 7044 lines, `customerID/tenure/Churn` header ✓
- `data/SOURCES.md` documents Telco + FMCG origin + license context ✓
- `.gitignore` contains `!data/seed/*.csv` ✓
- `README.md` contains `blastchar/telco-customer-churn` ✓
- `scripts/seed_data.py` idempotent — two runs produce identical counts ✓
- `forecasts` table has ≥ 5 rows (actual: 7) ✓
- All 5 integration tests pass ✓
- DATA-02 complete ✓
