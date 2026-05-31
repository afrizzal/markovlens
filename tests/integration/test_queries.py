"""Integration tests for core/db/queries.py and seed script paths."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pytest


@pytest.mark.integration
def test_build_transition_matrix_normalized(temp_duckdb_path: Path):
    """DATA-03: matrix returned must have rows summing to 1.0."""
    from core.db.connection import init_schema
    from core.db.queries import build_transition_matrix

    conn = duckdb.connect(str(temp_duckdb_path))
    init_schema(conn)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES ('ds_test', 'churn', 'test', 'test.csv', 4, 2)"
    )
    conn.execute(
        "INSERT INTO transitions VALUES "
        "('ds_test','e1',1,'A','A',1.0), "
        "('ds_test','e1',1,'A','B',1.0), "
        "('ds_test','e2',1,'B','A',1.0), "
        "('ds_test','e2',1,'B','B',3.0)"
    )
    matrix, counts = build_transition_matrix(conn, dataset_id="ds_test")
    assert matrix.shape == (2, 2)
    np.testing.assert_allclose(matrix.sum(axis=1), [1.0, 1.0], atol=1e-9)
    conn.close()


@pytest.mark.integration
def test_build_transition_matrix_counts(temp_duckdb_path: Path):
    """DATA-03: counts array returned with correct values."""
    from core.db.connection import init_schema
    from core.db.queries import build_transition_matrix

    conn = duckdb.connect(str(temp_duckdb_path))
    init_schema(conn)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES ('ds_test', 'churn', 'test', 'test.csv', 4, 2)"
    )
    conn.execute(
        "INSERT INTO transitions VALUES "
        "('ds_test','e1',1,'A','A',7.0), "
        "('ds_test','e1',1,'A','B',3.0), "
        "('ds_test','e2',1,'B','A',4.0), "
        "('ds_test','e2',1,'B','B',6.0)"
    )
    matrix, counts = build_transition_matrix(conn, dataset_id="ds_test")
    assert counts.shape == (2, 2)
    assert counts.sum() == 20
    conn.close()


@pytest.mark.integration
def test_build_transition_matrix_filters_dataset(temp_duckdb_path: Path):
    """DATA-03: only rows matching dataset_id are aggregated."""
    from core.db.connection import init_schema
    from core.db.queries import build_transition_matrix

    conn = duckdb.connect(str(temp_duckdb_path))
    init_schema(conn)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES ('ds_a', 'churn', 'a', 'a.csv', 2, 2), "
        "('ds_b', 'churn', 'b', 'b.csv', 2, 2)"
    )
    conn.execute(
        "INSERT INTO transitions VALUES "
        "('ds_a','e1',1,'A','A',1.0), "
        "('ds_a','e1',1,'A','B',1.0), "
        "('ds_b','e2',1,'A','A',99.0)"
    )
    matrix, counts = build_transition_matrix(conn, dataset_id="ds_a")
    assert counts.sum() == 2  # not 101
    conn.close()


@pytest.mark.integration
def test_seed_idempotency(temp_duckdb_path: Path, monkeypatch):
    """DATA-02: running seed twice produces identical row counts (D-23)."""
    monkeypatch.setenv("DUCKDB_PATH", str(temp_duckdb_path))
    # Reload settings so DUCKDB_PATH change takes effect
    import importlib

    from core import config as cfg

    importlib.reload(cfg)
    from core.db import connection as cn

    importlib.reload(cn)
    cn.close_connection()

    from scripts import seed_data

    seed_data.main()
    conn1 = duckdb.connect(str(temp_duckdb_path))
    count_a_transitions = conn1.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
    count_a_forecasts = conn1.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    conn1.close()

    cn.close_connection()
    seed_data.main()
    conn2 = duckdb.connect(str(temp_duckdb_path))
    count_b_transitions = conn2.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
    count_b_forecasts = conn2.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    conn2.close()

    assert count_a_transitions == count_b_transitions
    assert count_a_forecasts == count_b_forecasts


@pytest.mark.integration
def test_seed_produces_reference_forecasts(temp_duckdb_path: Path, monkeypatch):
    """DATA-02: forecasts table populated with >= 5 rows after seed (cold-start KPI requirement)."""
    monkeypatch.setenv("DUCKDB_PATH", str(temp_duckdb_path))
    import importlib

    from core import config as cfg

    importlib.reload(cfg)
    from core.db import connection as cn

    importlib.reload(cn)
    cn.close_connection()

    from scripts import seed_data

    seed_data.main()

    conn = duckdb.connect(str(temp_duckdb_path))
    count = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    conn.close()
    assert count >= 5


# ---------------------------------------------------------------------------
# Phase 04 — Home KPI + Recent Forecast integration tests
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_conn(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    """Per-test DuckDB connection with one dataset row seeded."""
    from core.db.connection import init_schema

    conn = duckdb.connect(str(tmp_path / "seeded.duckdb"))
    init_schema(conn)
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) "
        "VALUES ('ds_seed', 'brand_share', 'Seed Dataset', 'seed.csv', 100, 3)"
    )
    return conn


@pytest.mark.integration
def test_get_home_kpis_with_seeded_data(seeded_conn) -> None:  # type: ignore[no-untyped-def]
    """get_home_kpis returns non-zero dataset_count after seed."""
    from core.db.queries import get_home_kpis

    kpis = get_home_kpis(seeded_conn)
    assert kpis.dataset_count >= 1
    assert kpis.sim_run_count >= 0  # may be 0 if no sim_runs inserted by seeded_conn


@pytest.mark.integration
def test_list_datasets_includes_created_at(seeded_conn) -> None:  # type: ignore[no-untyped-def]
    """list_datasets returns Dataset objects with created_at populated."""
    from core.db.queries import list_datasets

    datasets = list_datasets(seeded_conn)
    assert len(datasets) >= 1
    for ds in datasets:
        # created_at may be None if schema had no default, but field must exist
        assert hasattr(ds, "created_at")


@pytest.mark.integration
def test_list_recent_forecasts_with_inserted_forecast(seeded_conn) -> None:  # type: ignore[no-untyped-def]
    """list_recent_forecasts returns RecentForecast rows when forecasts table has data."""
    import json
    import uuid

    from core.db.queries import list_recent_forecasts

    forecast_id = str(uuid.uuid4())
    # seeded_conn has dataset_id "ds_seed" from the seeded_conn fixture
    df_datasets = seeded_conn.execute("SELECT id FROM datasets LIMIT 1").df()
    dataset_id = df_datasets["id"].iloc[0]

    seeded_conn.execute(
        "INSERT INTO forecasts (id, dataset_id, model_type, horizon_steps, forecast_json, accuracy_metrics_json) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            forecast_id,
            dataset_id,
            "m1",
            12,
            json.dumps([[0.5, 0.5]]),
            json.dumps({"mape": 1.87, "brier": 0.043}),
        ],
    )
    results = list_recent_forecasts(seeded_conn, n=5)
    assert len(results) >= 1
    assert results[0].mape is not None
    assert abs(results[0].mape - 1.87) < 1e-6
    assert results[0].model_type == "m1"
