---
name: decision-duckdb
description: DuckDB chosen as embedded analytical database. File-based, no server. Reads Parquet/CSV natively. 10-100x faster than SQLite for aggregates.
metadata:
  type: project
---

**Decision:** Use DuckDB (file: `data/markovlens.duckdb`) as the storage layer.

**Why:**
- File-based, no server (vs PostgreSQL)
- 10-100x faster than SQLite for analytical queries (column store + vectorized exec)
- Reads CSV/Parquet directly: `SELECT * FROM 'data/raw/x.csv'`
- Integrates seamlessly with Pandas (`.df()` method)
- Works on Streamlit Cloud free tier (no external service needed)
- User wanted to learn Python + DB simultaneously — DuckDB is beginner-friendly

**How to apply:**
- All persistent data via DuckDB connection in `core/db/connection.py`
- Schema in `core/db/schema.sql` with simple `CREATE TABLE IF NOT EXISTS`
- No ORM (SQLAlchemy overkill); use native DuckDB Python API
- Datasets gitignored — regenerate from raw via `scripts/seed_data.py`

**Alternatives rejected:**
- SQLite — too slow for aggregations on > 100k rows
- PostgreSQL — overkill, requires server, complicates deployment
- Pandas + Parquet only — no SQL, harder to reproduce analysis
