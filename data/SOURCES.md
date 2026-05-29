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
