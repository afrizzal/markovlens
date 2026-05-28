# Datasets

> Catalogue of datasets used in MarkovLens with source URLs, schemas, and preprocessing notes.

## Convention

Each dataset is described with:
- **Source** — original URL (Kaggle, public repo, etc.)
- **License** — usage rights
- **Raw file path** — local `data/raw/` location
- **Processed file path** — `data/processed/` Parquet
- **Schema** — original columns + MarkovLens canonical mapping
- **Preprocessing** — transformations applied
- **Sparsity notes** — known data quality issues

---

## brand-share-ecommerce-2024

**Status:** 🟡 TODO — to be sourced during Phase 02

**Source:** _TBD — to be selected from Kaggle_

Candidate options:

1. [Online Retail Dataset](https://www.kaggle.com/datasets/carrie1/ecommerce-data) — UCI repository, December 2010–2011 UK retailer transactions
2. [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — 100k orders 2016-2018, multi-brand
3. [Amazon Product Reviews](https://www.kaggle.com/datasets/kashnitsky/hierarchical-text-classification) — for category-share modeling

**License:** Will vary by source — check before committing

**Raw file:** `data/raw/brand_share.csv` (gitignored)

**Processed file:** `data/processed/brand_share.parquet` (gitignored)

**Canonical schema mapping (target):**

| Original | MarkovLens canonical |
|---|---|
| `customer_id` | `entity_id` |
| `purchase_date` (parsed to YYYY-MM bucket) | `period` |
| `previous_brand_purchased` | `from_state` |
| `brand_purchased` | `to_state` |
| (none) | `weight` = 1.0 |

**Preprocessing steps (planned):**
1. Filter to customers with ≥ 2 purchases
2. Bucket dates to monthly periods
3. For each customer × period: identify primary brand purchased
4. Generate transitions: `(customer_id, period_n, brand_n-1, brand_n)`
5. Aggregate to top-K brands; rest collapsed to "Others"
6. Validate sparsity (≥ 20 obs per cell)

---

## telco-customer-churn

**Status:** 🟡 TODO — to be sourced during Phase 02

**Source:** [Telco Customer Churn (IBM)](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)

**License:** Open use (Kaggle public dataset, IBM sample data)

**Raw file:** `data/raw/telco_churn.csv` (gitignored)

**Processed file:** `data/processed/churn.parquet` (gitignored)

**Original schema:** 7,043 customers × 21 columns including:
- `customerID`
- `tenure` (months as customer)
- `Contract` (Month-to-month, One year, Two year)
- `MonthlyCharges`, `TotalCharges`
- `Churn` (Yes/No, target)
- Plus service usage columns

**Challenge:** original is a SNAPSHOT, not a longitudinal transition dataset. For Markov modeling, we need to **synthesize transitions** by:

1. Defining state based on tenure × charges × usage (e.g., Active / At-Risk / Inactive)
2. Bucketing customers by tenure month to create pseudo-periods
3. Assuming cohort transitions follow the observed churn rate

**Alternative dataset (better for true longitudinal):**
- [Telco Customer Churn (continuous)](https://www.kaggle.com/datasets/yeanzc/telco-customer-churn-ibm-dataset) — has tenure progression

**Canonical schema mapping (target):**

| Derived field | MarkovLens canonical |
|---|---|
| `customerID` | `entity_id` |
| derived month from tenure | `period` |
| derived state (Active/At-Risk/Inactive/Churned) | `from_state` / `to_state` |

**State definition (planned):**
- **Active:** tenure > 6 months, monthly usage stable
- **At-Risk:** monthly charges dropped > 30% OR tech support tickets opened
- **Inactive:** no usage in last 30 days
- **Churned:** `Churn = Yes`
- **Reactivated:** Inactive → Active in subsequent period

---

## Adding a New Dataset

1. Identify source (Kaggle preferred for citability)
2. Download raw file to `data/raw/<name>.csv` (do NOT commit)
3. Document in this file with the conventional fields above
4. Implement preprocessing in `scripts/prepare_<name>.py`
5. Use the `dataset-prepper` skill to load into DuckDB
6. Run validation: `uv run python scripts/validate_<name>.py`
7. Commit the script + this doc update; raw file stays gitignored

## Privacy & Anonymization

If a dataset contains real PII:
- Hash `entity_id` with SHA-256 before loading
- Strip name, email, phone
- Document anonymization in dataset metadata
- See `.claude/rules/project-rules.md` #11

## Data Refresh Cadence

For v0.1 — datasets are static (no refresh).

For v0.2 (potential):
- Add cron job to re-fetch monthly from public sources
- Append new periods to existing transitions
- Recompute matrices + clear simulation cache
