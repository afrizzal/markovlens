"""Cold-start auto-seeding for Streamlit Cloud (DEPLOY-01).

ensure_seeded() repopulates the DuckDB demo data when the forecasts table is
empty. The forecasts table is the seed sentinel (D-04) because seed_data.py
populates it LAST (after transitions + matrices + simulation_runs), making a
non-zero forecasts count the most reliable "seed complete" signal.
"""

from __future__ import annotations

import logging

import duckdb

log = logging.getLogger(__name__)


def ensure_seeded(conn: duckdb.DuckDBPyConnection) -> None:
    """Populate DuckDB with demo data if not already seeded.

    Uses the forecasts table as the seed sentinel — populated last by the seed
    pipeline. Fast path returns immediately when forecasts already has rows.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open connection with schema already applied (init_schema run).
    """
    row = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()
    count = row[0] if row is not None else 0
    if count > 0:
        return  # already seeded — fast path (D-04)

    log.info("forecasts table empty — running cold-start seed pipeline")
    import numpy as np  # deferred: keeps core/db/init.py import-light on warm reruns

    from scripts.seed_data import RNG_SEED, _seed_brand_share, _seed_churn  # deferred: see above

    rng = np.random.default_rng(RNG_SEED)
    _seed_brand_share(conn, rng)
    _seed_churn(conn)
    log.info("Cold-start seed complete")
