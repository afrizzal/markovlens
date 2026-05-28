# Database Schema — DuckDB

> Source of truth: `core/db/schema.sql`. This document mirrors the schema for reference and developer onboarding.

## Why DuckDB?

See [decisions.md § 2026-05-28 DuckDB](planning/decisions.md). Summary: file-based, no server, 10-100x faster than SQLite for analytics, reads Parquet/CSV natively.

## File Location

```
data/markovlens.duckdb         # Main file (gitignored)
data/markovlens.duckdb.wal     # Write-ahead log (gitignored)
```

Auto-created on first connection. Initialize schema with `core.db.init_schema(conn)`.

## Schema Diagram (ASCII)

```
┌─────────────────────────┐
│ datasets                │
├─────────────────────────┤
│ id              PK      │
│ domain                  │
│ name                    │
│ source_path             │
│ row_count               │
│ n_states                │
│ metadata_json           │
│ created_at              │
└─────────┬───────────────┘
          │ 1:N
          ▼
┌─────────────────────────┐         ┌─────────────────────────┐
│ transitions             │         │ transition_matrices     │
├─────────────────────────┤         ├─────────────────────────┤
│ dataset_id   FK         │         │ id              PK      │
│ entity_id               │         │ dataset_id      FK      │
│ period                  │         │ model_type              │
│ from_state              │         │ period                  │
│ to_state                │         │ matrix_json             │
│ weight                  │         │ n_observations          │
└─────────────────────────┘         │ computed_at             │
                                    └─────────┬───────────────┘
                                              │ 1:N
                                              ▼
                                    ┌─────────────────────────┐
                                    │ simulation_runs         │
                                    ├─────────────────────────┤
                                    │ id              PK      │
                                    │ matrix_id       FK      │
                                    │ start_state             │
                                    │ n_steps                 │
                                    │ n_simulations           │
                                    │ final_distribution_json │
                                    │ quantile_paths_json     │
                                    │ raw_probability         │
                                    │ calibrated_probability  │
                                    │ seed                    │
                                    │ created_at              │
                                    └─────────────────────────┘

┌─────────────────────────┐         ┌─────────────────────────┐
│ forecasts               │         │ scenarios               │
├─────────────────────────┤         ├─────────────────────────┤
│ id              PK      │         │ id              PK      │
│ dataset_id      FK      │         │ dataset_id      FK      │
│ model_type              │         │ name                    │
│ horizon_steps           │         │ description             │
│ forecast_json           │         │ modified_transitions_jsn│
│ accuracy_metrics_json   │         │ result_json             │
│ created_at              │         │ created_at              │
└─────────────────────────┘         └─────────────────────────┘
```

## Tables

### `datasets`

Registered datasets available for forecasting.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | VARCHAR | PRIMARY KEY | e.g., `"ds_ecommerce_brand_2024"` |
| `domain` | VARCHAR | NOT NULL | `"brand_share"` or `"churn"` |
| `name` | VARCHAR | NOT NULL | Human-readable, displayed in UI |
| `source_path` | VARCHAR | NOT NULL | Path to raw file in `data/raw/` |
| `row_count` | BIGINT | | Number of raw rows |
| `n_states` | INTEGER | | Number of discrete states |
| `metadata_json` | JSON | | Domain-specific metadata (state names, time unit, etc.) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### `transitions`

Raw transition observations in long format.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `dataset_id` | VARCHAR | FK → `datasets.id` | Indexed |
| `entity_id` | VARCHAR | NOT NULL | Customer ID, brand-holder ID, etc. |
| `period` | INTEGER | NOT NULL | Time step (1, 2, 3, ...) |
| `from_state` | VARCHAR | NOT NULL | State at start of period |
| `to_state` | VARCHAR | NOT NULL | State at end of period |
| `weight` | DOUBLE | DEFAULT 1.0 | Aggregated data may use > 1 |

**Indexes:**
- `(dataset_id, period)` — for time-window queries
- `(dataset_id, from_state, to_state)` — for matrix aggregation

### `transition_matrices`

Cached computed transition matrices to avoid recomputation.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | VARCHAR | PRIMARY KEY | UUID v4 |
| `dataset_id` | VARCHAR | FK → `datasets.id` | |
| `model_type` | VARCHAR | NOT NULL | `"m1"`, `"m2"`, `"m3"` |
| `period` | INTEGER | NULL | NULL for m1 (constant); set for m2/m3 |
| `matrix_json` | JSON | NOT NULL | Serialized numpy array (list of lists) |
| `n_observations` | INTEGER | | Total observations behind this matrix |
| `computed_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

**Cache key:** `(dataset_id, model_type, period)` — query before computing.

### `simulation_runs`

Monte Carlo result cache.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | VARCHAR | PRIMARY KEY | UUID v4 |
| `matrix_id` | VARCHAR | FK → `transition_matrices.id` | |
| `start_state` | INTEGER | NOT NULL | |
| `n_steps` | INTEGER | NOT NULL | Horizon |
| `n_simulations` | INTEGER | NOT NULL | Default 10,000 |
| `final_distribution_json` | JSON | | Counts per terminal state |
| `quantile_paths_json` | JSON | | p10/p50/p90 path arrays |
| `raw_probability` | DOUBLE | | Before calibration |
| `calibrated_probability` | DOUBLE | | After longshot adjustment |
| `seed` | INTEGER | NULL | For reproducibility |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### `forecasts`

Persisted forecast outputs (for reports + analytics).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | VARCHAR | PRIMARY KEY | |
| `dataset_id` | VARCHAR | FK → `datasets.id` | |
| `model_type` | VARCHAR | NOT NULL | |
| `horizon_steps` | INTEGER | NOT NULL | |
| `forecast_json` | JSON | NOT NULL | State distribution per future period |
| `accuracy_metrics_json` | JSON | NULL | MAPE, Brier, etc. (filled after backtest) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### `scenarios`

Saved what-if scenarios.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | VARCHAR | PRIMARY KEY | |
| `dataset_id` | VARCHAR | FK → `datasets.id` | |
| `name` | VARCHAR | NOT NULL | User-given name |
| `description` | TEXT | NULL | |
| `modified_transitions_json` | JSON | NOT NULL | Diff from baseline matrix |
| `result_json` | JSON | NULL | Cached result if computed |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

## Common Queries

### Get all datasets for a domain

```python
datasets = conn.execute("""
    SELECT id, name, row_count, n_states
    FROM datasets
    WHERE domain = ?
    ORDER BY created_at DESC
""", ["brand_share"]).df()
```

### Count transitions per cell (for sparsity check)

```python
counts = conn.execute("""
    SELECT from_state, to_state, COUNT(*) as n
    FROM transitions
    WHERE dataset_id = ?
    GROUP BY from_state, to_state
""", [dataset_id]).df()
```

### Build m1 (homogeneous) transition matrix in pure SQL

```python
counts = conn.execute("""
    WITH counts AS (
        SELECT from_state, to_state, SUM(weight) as n
        FROM transitions WHERE dataset_id = ?
        GROUP BY from_state, to_state
    ),
    totals AS (
        SELECT from_state, SUM(n) as total
        FROM counts GROUP BY from_state
    )
    SELECT c.from_state, c.to_state, c.n / t.total AS prob
    FROM counts c JOIN totals t USING (from_state)
""", [dataset_id]).df()
# Pivot to NxN matrix in Python
matrix = counts.pivot(index="from_state", columns="to_state", values="prob").fillna(0)
```

### Look up cached matrix

```python
row = conn.execute("""
    SELECT id, matrix_json, n_observations
    FROM transition_matrices
    WHERE dataset_id = ? AND model_type = ? AND (period = ? OR period IS NULL)
    ORDER BY computed_at DESC
    LIMIT 1
""", [dataset_id, model_type, period]).fetchone()
```

## Migration Strategy

No Alembic. Use simple `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE` in `schema.sql`. For breaking changes:

1. Add new column nullable
2. Backfill via `scripts/migrate_NNN.py`
3. Drop old column in follow-up release
4. Document in [decisions.md](planning/decisions.md)

## Backup

- Local dev: nothing — regenerable from `scripts/seed_data.py`
- Streamlit Cloud: same (cold start regenerates from raw CSVs)
- For production deployment: mount persistent volume, daily backup of `markovlens.duckdb`

## Performance Tips

- DuckDB is column-store: prefer `SELECT specific_cols` over `SELECT *`
- Aggregations are fast: prefer SQL `GROUP BY` over `pd.DataFrame.groupby()`
- For repeated queries, materialize a view
- Use `EXPLAIN ANALYZE <query>` to debug slow queries
- DuckDB connections are **thread-safe** but use `cursor()` for concurrent reads

## File Size Management

- Compress JSON columns where possible
- Periodically `VACUUM` to reclaim space
- If file > 500MB (Streamlit Cloud limit): consider Parquet-only architecture for raw `transitions`, keep DB for cache only
