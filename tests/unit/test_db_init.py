"""Unit tests for core.db.init.ensure_seeded (DEPLOY-01)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest


def _fresh_conn(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    from core.db.connection import init_schema

    conn = duckdb.connect(str(tmp_path / "init_test.duckdb"))
    init_schema(conn)
    return conn


def test_ensure_seeded_fast_path_when_forecasts_present(tmp_path, monkeypatch):
    """forecasts count > 0 → ensure_seeded returns without invoking seed pipeline."""
    from core.db import init as init_mod

    conn = _fresh_conn(tmp_path)
    # Insert parent dataset row required by the FK constraint on forecasts.dataset_id.
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path) VALUES (?, ?, ?, ?)",
        ["ds_x", "brand_share", "Test DS", "data/test"],
    )
    # Insert a single forecast row so the sentinel is non-zero.
    conn.execute(
        "INSERT INTO forecasts (id, dataset_id, model_type, horizon_steps, forecast_json) "
        "VALUES (?, ?, ?, ?, ?)",
        ["f1", "ds_x", "m1", 12, "[]"],
    )

    called = {"brand": False, "churn": False}

    def _fail_brand(*a, **k):
        called["brand"] = True

    def _fail_churn(*a, **k):
        called["churn"] = True

    monkeypatch.setattr("scripts.seed_data._seed_brand_share", _fail_brand)
    monkeypatch.setattr("scripts.seed_data._seed_churn", _fail_churn)

    init_mod.ensure_seeded(conn)

    assert called == {"brand": False, "churn": False}


@pytest.mark.integration
def test_ensure_seeded_runs_pipeline_when_empty(tmp_path):
    """Empty forecasts table → seed pipeline runs and forecasts ends >= 5 rows."""
    from core.db.init import ensure_seeded

    conn = _fresh_conn(tmp_path)
    pre = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    assert pre == 0

    ensure_seeded(conn)

    post = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    assert post >= 5  # DATA-02 SC 5 — churn seeds 5 + brand seeds 2
