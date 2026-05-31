"""Unit tests for Home dashboard query helpers (HOME-01)."""
from __future__ import annotations


def test_home_kpis_dataclass_fields() -> None:
    """HomeKpis has the required 4 fields."""
    from core.db.queries import HomeKpis

    fields = set(HomeKpis.__dataclass_fields__)
    assert fields == {"dataset_count", "sim_run_count", "last_forecast_at", "avg_mape"}


def test_recent_forecast_dataclass_fields() -> None:
    """RecentForecast has the required 6 fields."""
    from core.db.queries import RecentForecast

    fields = set(RecentForecast.__dataclass_fields__)
    assert fields == {"forecast_id", "dataset_name", "domain", "model_type", "created_at", "mape"}


def test_dataset_has_created_at_field() -> None:
    """Dataset dataclass includes created_at as the last field."""
    from core.db.queries import Dataset

    assert "created_at" in Dataset.__dataclass_fields__


def test_home_kpis_returns_zeros_on_empty_db(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """get_home_kpis on an empty DB returns zero counts and None timestamps."""
    import duckdb

    from core.db.connection import init_schema
    from core.db.queries import get_home_kpis

    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    init_schema(conn)
    kpis = get_home_kpis(conn)
    assert kpis.dataset_count == 0
    assert kpis.sim_run_count == 0
    assert kpis.last_forecast_at is None
    assert kpis.avg_mape is None
    conn.close()


def test_list_recent_forecasts_returns_empty_on_empty_db(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """list_recent_forecasts on an empty DB returns an empty list."""
    import duckdb

    from core.db.connection import init_schema
    from core.db.queries import list_recent_forecasts

    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    init_schema(conn)
    results = list_recent_forecasts(conn)
    assert results == []
    conn.close()
