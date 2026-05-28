---
name: dataset-prepper
description: Convert a raw Kaggle CSV into MarkovLens-ready format — registered dataset row + transitions table population. Use when ingesting a new dataset.
allowed-tools: Read, Write, Edit, Bash
---

# Dataset Prepper

Transform a raw dataset (typically a Kaggle CSV) into the MarkovLens canonical format: a `datasets` table row + populated `transitions` table.

## When to Use

- Adding a new dataset to the project
- Re-processing an existing dataset with cleaned data
- Onboarding a domain-specific source (telco, e-commerce, etc.)

## Canonical Format

The `transitions` table expects **long-format rows**:

| Column | Type | Meaning |
|---|---|---|
| `dataset_id` | VARCHAR | FK to `datasets.id` |
| `entity_id` | VARCHAR | Stable id of the moving entity (customer, brand-holder) |
| `period` | INTEGER | Discrete time step (1, 2, 3, ...) |
| `from_state` | VARCHAR | Entity's state at start of period |
| `to_state` | VARCHAR | Entity's state at end of period |
| `weight` | DOUBLE | Usually 1.0 unless source data is aggregated |

## Procedure

1. **Inspect the raw file:**
   ```bash
   uv run python -c "import pandas as pd; print(pd.read_csv('data/raw/X.csv').head())"
   ```

2. **Identify columns:** entity identifier, time column, state column. Document mapping.

3. **Identify domain:** `brand_share` or `churn` — determines downstream defaults.

4. **Define states:** discrete categories. If raw data is continuous (e.g., price), discretize into N buckets (default 10 per Chan 2015).

5. **Convert to long format:**
   ```python
   # If raw is one row per entity-period:
   df_sorted = df.sort_values(["entity_id", "period"])
   df_sorted["from_state"] = df_sorted.groupby("entity_id")["state"].shift(1)
   transitions = df_sorted.dropna(subset=["from_state"])
   transitions = transitions[["entity_id", "period", "from_state", "to_state"]]
   ```

6. **Validate:**
   - No `NaN` in `entity_id`, `from_state`, `to_state`
   - `period` is integer-valued and monotonic per entity
   - Total observations per state >= 30 (warn if not)

7. **Write to DuckDB:**
   ```python
   from core.db.connection import get_connection
   conn = get_connection()
   
   # Register dataset
   conn.execute("""
       INSERT INTO datasets (id, domain, name, source_path, row_count, n_states)
       VALUES (?, ?, ?, ?, ?, ?)
   """, [dataset_id, domain, name, source_path, len(df), n_states])
   
   # Bulk insert transitions
   conn.execute("""
       INSERT INTO transitions
       SELECT ? AS dataset_id, * FROM transitions_df
   """, [dataset_id])
   ```

8. **Save processed Parquet** for cache/reload: `data/processed/<dataset_id>.parquet`

9. **Update `docs/DATASETS.md`** with the new dataset entry (source link, schema, preprocessing notes).

## Output Format

```
## Dataset Prepped: <dataset_name>

**Source:** <Kaggle URL or local path>
**Domain:** brand_share / churn
**Rows:** 12,345
**Entities:** 482 unique
**Periods:** 24 (monthly, 2024-01 to 2025-12)
**States:** 10 — [list]

**Registered:** datasets.id = "ds_<short_id>"
**Transitions loaded:** 11,863 rows in transitions table
**Sparsity check:** 95/100 cells with >= 20 observations ✅
                   5 sparse cells (rows 7, 9): suggest merging states

**Files:**
- data/raw/<name>.csv (committed: NO, gitignored)
- data/processed/<dataset_id>.parquet (committed: NO)

**Next steps:**
- Run `markov-validator` on initial m1 matrix
- Build first forecast via Brand Share page
```

## DO NOT

- ❌ Commit raw datasets to git (gitignored for size + PII)
- ❌ Process datasets in `app/` files — always in `scripts/` or `core/io/`
- ❌ Skip the sparsity check — sparse cells = noise that breaks downstream simulations
- ❌ Mix `brand_share` and `churn` data in one dataset — keep domains pure
