"""Integration tests for domains/brand_share/service.py — BS-01, BS-04."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Fixture: seeded_conn
# ---------------------------------------------------------------------------

@pytest.fixture
def seeded_conn(temp_duckdb_path: Path):
    """Open a temp DuckDB, run the schema, seed a brand_share dataset.

    States: ["A", "B", "C"] — 3 states, 5 periods, >= 20 obs per active cell
    to avoid sparsity errors.
    """
    from core.db.connection import init_schema
    from core.db.queries import bulk_insert_transitions, register_dataset

    conn = duckdb.connect(str(temp_duckdb_path))
    init_schema(conn)

    dataset_id = "ds_brand_test"
    register_dataset(
        conn,
        domain="brand_share",
        name="Test Brand Share",
        source_path="test.csv",
        row_count=300,
        n_states=3,
        dataset_id=dataset_id,
    )

    # Build a deterministic long-format transitions frame.
    # 3 states: A, B, C; 5 periods (1..5); 30 transitions per (from_state, period).
    # Transition pattern per from_state (sum to 30 per period):
    #   A -> A: 20, A -> B: 7, A -> C: 3
    #   B -> A: 4, B -> B: 22, B -> C: 4
    #   C -> A: 3, C -> B: 5, C -> C: 22
    records = []
    entity_counter = 0
    pattern = {
        "A": [("A", 20), ("B", 7), ("C", 3)],
        "B": [("A", 4), ("B", 22), ("C", 4)],
        "C": [("A", 3), ("B", 5), ("C", 22)],
    }
    for period in range(1, 6):  # periods 1..5
        for from_s, transitions in pattern.items():
            for to_s, count in transitions:
                for _ in range(count):
                    records.append(
                        {
                            "entity_id": f"e{entity_counter}",
                            "period": period,
                            "from_state": from_s,
                            "to_state": to_s,
                            "weight": 1.0,
                        }
                    )
                    entity_counter += 1

    df = pd.DataFrame(records)
    bulk_insert_transitions(conn, dataset_id, df)

    yield conn, dataset_id

    conn.close()


# ---------------------------------------------------------------------------
# Task 1: Structural test — BS-01
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_run_forecast_returns_numpy_only(seeded_conn):
    """BS-01: run_forecast returns BrandShareForecastResult with no Plotly objects.

    Verifies:
    - Return type is BrandShareForecastResult
    - transition_matrix shape == (3, 3)
    - state_labels length == 3 and == ["A", "B", "C"]
    - All forecast arrays are np.ndarray
    - No field contains a plotly object
    """
    from domains.brand_share.service import BrandShareForecastResult, run_forecast

    conn, dataset_id = seeded_conn
    result = run_forecast(conn, dataset_id, "m1", horizon=6)

    assert isinstance(result, BrandShareForecastResult)
    assert result.transition_matrix.shape == (3, 3)
    assert len(result.state_labels) == 3
    assert result.state_labels == ["A", "B", "C"]

    # All forecast arrays must be np.ndarray
    for key, arr in result.forecasts.items():
        assert isinstance(arr, np.ndarray), f"forecasts[{key!r}] is not ndarray"

    # No field may be a Plotly object
    for field in dataclasses.fields(result):
        val = getattr(result, field.name)
        module = type(val).__module__ or ""
        assert not module.startswith("plotly"), (
            f"Field {field.name!r} is a Plotly object: {type(val)}"
        )


@pytest.mark.integration
def test_list_datasets_filters_brand_share(seeded_conn):
    """BS-01: list_datasets returns only brand_share-domain datasets."""
    from core.db.queries import register_dataset
    from domains.brand_share.service import list_datasets

    conn, dataset_id = seeded_conn

    # Register an extra dataset with a different domain — should not appear
    register_dataset(
        conn,
        domain="churn",
        name="Churn Dataset",
        source_path="churn.csv",
        row_count=100,
        n_states=3,
        dataset_id="ds_churn_test",
    )

    datasets = list_datasets(conn)
    domains = {ds.domain for ds in datasets}
    assert domains == {"brand_share"}, f"Expected only brand_share, got {domains}"
    assert any(ds.id == dataset_id for ds in datasets)
    assert not any(ds.id == "ds_churn_test" for ds in datasets)


# ---------------------------------------------------------------------------
# Task 2: Full pipeline tests — BS-04
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_model_comparison(seeded_conn):
    """BS-04: accuracy_metrics has all three models + computed winner."""
    from domains.brand_share.service import run_forecast

    conn, dataset_id = seeded_conn
    result = run_forecast(conn, dataset_id, "m1", horizon=6)

    # All three models present
    assert set(result.accuracy_metrics.keys()) == {"m1", "m2", "m3"}, (
        f"Expected m1/m2/m3 keys, got {set(result.accuracy_metrics.keys())}"
    )

    # Each model has mape, brier, log_loss as floats
    for model_key in ("m1", "m2", "m3"):
        metrics = result.accuracy_metrics[model_key]
        assert set(metrics.keys()) == {"mape", "brier", "log_loss"}, (
            f"Model {model_key} missing metric keys: {set(metrics.keys())}"
        )
        for metric_name, value in metrics.items():
            assert isinstance(value, float), (
                f"accuracy_metrics[{model_key!r}][{metric_name!r}] is not float: {type(value)}"
            )

    # best_model is in the valid set
    assert result.best_model in {"m1", "m2", "m3"}, (
        f"best_model={result.best_model!r} not in expected set"
    )

    # best_model is derived from computed metrics, not hardcoded
    computed_winner = min(("m1", "m2", "m3"), key=lambda m: result.accuracy_metrics[m]["mape"])
    assert result.best_model == computed_winner, (
        f"best_model={result.best_model!r} != computed winner {computed_winner!r}"
    )


@pytest.mark.integration
def test_confidence_bands_monotonic(seeded_conn):
    """BS-03: confidence bands present, monotonic, and correct length."""
    from domains.brand_share.service import run_forecast

    conn, dataset_id = seeded_conn
    horizon = 6
    result = run_forecast(conn, dataset_id, "m1", horizon=horizon)

    assert set(result.confidence_bands.keys()) == {0.10, 0.50, 0.90}, (
        f"Expected keys {{0.10, 0.50, 0.90}}, got {set(result.confidence_bands.keys())}"
    )

    p10 = result.confidence_bands[0.10]
    p50 = result.confidence_bands[0.50]
    p90 = result.confidence_bands[0.90]

    # Each band must be a 1-D array of length horizon+1
    for quantile, band in [(0.10, p10), (0.50, p50), (0.90, p90)]:
        assert isinstance(band, np.ndarray), f"Band {quantile} is not ndarray"
        assert band.ndim == 1, f"Band {quantile} ndim={band.ndim}, expected 1"
        assert len(band) == horizon + 1, (
            f"Band {quantile} length={len(band)}, expected {horizon + 1}"
        )

    # Monotonicity: p10 <= p50 + epsilon, p50 <= p90 + epsilon
    assert (p10 <= p50 + 1e-9).all(), "p10 > p50 violated"
    assert (p50 <= p90 + 1e-9).all(), "p50 > p90 violated"


@pytest.mark.integration
def test_stationary_present(seeded_conn):
    """BS-05: stationary_distribution is None or sums to 1.0."""
    from domains.brand_share.service import run_forecast

    conn, dataset_id = seeded_conn
    result = run_forecast(conn, dataset_id, "m1", horizon=6)

    if result.stationary_distribution is not None:
        assert isinstance(result.stationary_distribution, np.ndarray)
        total = float(result.stationary_distribution.sum())
        assert abs(total - 1.0) < 1e-6, (
            f"stationary_distribution sums to {total}, expected ~1.0"
        )
