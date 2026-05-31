"""Integration test stubs for domains/churn/service.py — CH-01, CH-03.

Wave 0 — tests are importorskip-guarded until Plan 02 implements the service.
seeded_churn_conn fixture mirrors the brand_share seeded_conn pattern with
churn states (active/atrisk/churned) and domain="churn".
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Fixture: seeded_churn_conn
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_churn_conn(temp_duckdb_path: Path):
    """Open a temp DuckDB, run the schema, seed a churn dataset.

    States: ["active", "atrisk", "churned"] — 3 states (lowercase, case-insensitive lookup).
    5 periods (1..5); >= 20 obs per active cell to avoid sparsity warnings.
    Churned is near-absorbing so compute_avg_lifetime has a transient set.

    Transition counts per from-state per period (total 30 each):
      active  -> active: 22,  active  -> atrisk:  6,  active  -> churned: 2
      atrisk  -> active:  8,  atrisk  -> atrisk: 14,  atrisk  -> churned: 8
      churned -> churned: 30  (absorbing)
    """
    from core.db.connection import init_schema
    from core.db.queries import bulk_insert_transitions, register_dataset

    conn = duckdb.connect(str(temp_duckdb_path))
    init_schema(conn)

    dataset_id = "ds_churn_test"
    register_dataset(
        conn,
        domain="churn",
        name="Test Churn Dataset",
        source_path="test_churn.csv",
        row_count=450,   # 5 periods x 3 states x 30 transitions
        n_states=3,
        dataset_id=dataset_id,
    )

    # Deterministic long-format transitions frame.
    # 3 states: active, atrisk, churned; 5 periods (1..5); 30 transitions per (from_state, period).
    records = []
    entity_counter = 0
    pattern = {
        "active":  [("active", 22), ("atrisk", 6), ("churned", 2)],
        "atrisk":  [("active", 8),  ("atrisk", 14), ("churned", 8)],
        "churned": [("churned", 30)],
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

    yield conn

    conn.close()


# ---------------------------------------------------------------------------
# Integration tests — CH-01, CH-03
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_run_analysis_returns_result(seeded_churn_conn) -> None:
    """CH-01: run_analysis returns ChurnAnalysisResult with correct shapes."""
    pytest.importorskip("domains.churn.service")
    from domains.churn import service

    if not hasattr(service, "run_analysis") or not hasattr(service, "ChurnAnalysisResult"):
        pytest.skip("run_analysis not yet implemented (Plan 02)")

    import inspect
    sig = inspect.signature(service.run_analysis)
    if "conn" not in sig.parameters:
        pytest.skip("run_analysis has old stub signature without conn param (Plan 02)")

    result = service.run_analysis(seeded_churn_conn, "ds_churn_test", horizon=12)

    assert result.transition_matrix.shape == (3, 3)
    np.testing.assert_allclose(
        result.transition_matrix.sum(axis=1), [1, 1, 1], atol=1e-9
    )
    assert result.state_distribution_over_time.shape[1] == 3
    assert result.state_distribution_over_time.shape[0] >= 2
    assert result.baseline_forecast.shape == (13, 3)   # horizon+1 = 13 rows
    assert set(result.kpis) == {"retention_rate", "avg_lifetime", "expected_churn", "revenue_at_risk"}
    assert result.n_customers > 0


@pytest.mark.integration
def test_state_distribution_includes_period_zero(seeded_churn_conn) -> None:
    """CH-01: state_distribution_over_time shape[0] == n_periods + 1 (period 0 prepended).

    Pitfall 2 guard: slice [0] is Y_1 (initial), slices [1..n_periods] are forecasted.
    """
    pytest.importorskip("domains.churn.service")
    from domains.churn import service

    if not hasattr(service, "run_analysis"):
        pytest.skip("run_analysis not yet implemented (Plan 02)")

    import inspect
    if "conn" not in inspect.signature(service.run_analysis).parameters:
        pytest.skip("run_analysis has old stub signature (Plan 02)")

    result = service.run_analysis(seeded_churn_conn, "ds_churn_test", horizon=12)

    assert result.state_distribution_over_time.shape[0] == result.n_periods + 1, (
        f"Expected shape[0]={result.n_periods + 1}, "
        f"got {result.state_distribution_over_time.shape[0]}"
    )


@pytest.mark.integration
def test_baseline_forecast_rows_sum_to_one(seeded_churn_conn) -> None:
    """CH-01: all rows of baseline_forecast sum to 1.0 (valid probability distribution)."""
    pytest.importorskip("domains.churn.service")
    from domains.churn import service

    if not hasattr(service, "run_analysis"):
        pytest.skip("run_analysis not yet implemented (Plan 02)")

    import inspect
    if "conn" not in inspect.signature(service.run_analysis).parameters:
        pytest.skip("run_analysis has old stub signature (Plan 02)")

    result = service.run_analysis(seeded_churn_conn, "ds_churn_test", horizon=12)

    np.testing.assert_allclose(
        result.baseline_forecast.sum(axis=1),
        np.ones(13),
        atol=1e-6,
    )


@pytest.mark.integration
def test_simulate_scenario_differs(seeded_churn_conn) -> None:
    """CH-03: simulate_scenario with override produces a different distribution than baseline.

    Forces active->churned to 0.30 (vs baseline ~0.067). The churned column at
    the final period must be HIGHER in the scenario than in the baseline.
    """
    pytest.importorskip("domains.churn.service")
    from domains.churn import service

    if not hasattr(service, "run_analysis") or not hasattr(service, "simulate_scenario"):
        pytest.skip("simulate_scenario not yet implemented (Plan 02)")

    import inspect
    if "conn" not in inspect.signature(service.run_analysis).parameters:
        pytest.skip("simulate_scenario has old stub signature (Plan 02)")

    baseline = service.run_analysis(seeded_churn_conn, "ds_churn_test", horizon=12)
    scenario = service.simulate_scenario(
        seeded_churn_conn,
        "ds_churn_test",
        12,
        {(0, 2): 0.30},   # force active->churned to 0.30
    )

    assert scenario.shape == (13, 3)
    assert not np.allclose(scenario, baseline.baseline_forecast, atol=1e-3), (
        "scenario and baseline should differ with large override {(0,2): 0.30}"
    )
    # Churned column (state 2) at final period must be higher in scenario
    churned_idx = 2
    assert scenario[-1, churned_idx] > baseline.baseline_forecast[-1, churned_idx], (
        f"Expected higher churned share in scenario at t=12: "
        f"scenario={scenario[-1, churned_idx]:.4f} vs baseline={baseline.baseline_forecast[-1, churned_idx]:.4f}"
    )


@pytest.mark.integration
def test_simulate_scenario_rows_renormalized(seeded_churn_conn) -> None:
    """CH-03: all rows of simulate_scenario output sum to 1.0."""
    pytest.importorskip("domains.churn.service")
    from domains.churn import service

    if not hasattr(service, "simulate_scenario"):
        pytest.skip("simulate_scenario not yet implemented (Plan 02)")

    import inspect
    if "conn" not in inspect.signature(service.simulate_scenario).parameters:
        pytest.skip("simulate_scenario has old stub signature (Plan 02)")

    scenario = service.simulate_scenario(
        seeded_churn_conn,
        "ds_churn_test",
        12,
        {(0, 1): 0.5},   # force active->atrisk to 0.50
    )

    np.testing.assert_allclose(
        scenario.sum(axis=1),
        np.ones(13),
        atol=1e-6,
    )


@pytest.mark.integration
def test_baseline_forecast_shape_matches_horizon_and_states(seeded_churn_conn) -> None:
    """Scrubber range fix: baseline_forecast.shape must be (horizon+1, n_states).

    Regression guard: snapshot datasets (1 historical period) have
    state_distribution_over_time.shape[0] == 2, which collapsed the scrubber to 0-1.
    The page now uses baseline_forecast.shape[0] == horizon+1 == 13 for horizon=12.
    """
    pytest.importorskip("domains.churn.service")
    from domains.churn import service

    if not hasattr(service, "run_analysis"):
        pytest.skip("run_analysis not yet implemented (Plan 02)")

    import inspect
    if "conn" not in inspect.signature(service.run_analysis).parameters:
        pytest.skip("run_analysis has old stub signature (Plan 02)")

    horizon = 12
    result = service.run_analysis(seeded_churn_conn, "ds_churn_test", horizon=horizon)
    n_states = len(result.state_labels)

    assert result.baseline_forecast.shape == (horizon + 1, n_states), (
        f"Expected baseline_forecast.shape == ({horizon + 1}, {n_states}), "
        f"got {result.baseline_forecast.shape}"
    )


@pytest.mark.integration
def test_list_datasets_churn_domain(seeded_churn_conn) -> None:
    """CH-01: list_datasets returns at least the seeded churn dataset."""
    pytest.importorskip("domains.churn.service")
    from domains.churn import service

    if not hasattr(service, "list_datasets"):
        pytest.skip("list_datasets not yet implemented (Plan 02)")

    import inspect
    if "conn" not in inspect.signature(service.list_datasets).parameters:
        pytest.skip("list_datasets has old stub signature (Plan 02)")

    datasets = service.list_datasets(seeded_churn_conn)

    assert len(datasets) >= 1, "Expected at least 1 dataset"
    ids = [d.id for d in datasets]
    domains = [d.domain for d in datasets]
    assert "ds_churn_test" in ids, f"Expected ds_churn_test in {ids}"
    assert all(dom == "churn" for dom in domains), (
        f"Expected all domains to be 'churn', got {domains}"
    )
