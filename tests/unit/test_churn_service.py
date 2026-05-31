"""Unit test stubs for domains/churn/service.py and app/components/sankey_flow.py.

Wave 0 — tests are importorskip-guarded until Plan 02 implements the service.
Once domains/churn/service.py exposes the full API, all guards activate.
"""

from __future__ import annotations

import numpy as np
import pytest


def test_compute_avg_lifetime() -> None:
    """CH-01: compute_avg_lifetime returns expected value for 5-state reference P.

    5-state design reference P (Active/At-Risk/Inactive/Reactivated/Churned):
    - P[4,4] = 0.98  (Churned is near-absorbing, not at 1.0 exactly)
    - All rows sum to 1.0
    - Expected result: float in [15.0, 35.0] (reference ≈ 20.68)
    """
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service, "compute_avg_lifetime"):
        pytest.skip("compute_avg_lifetime not yet implemented (Plan 02)")

    # 5-state reference P matrix:
    # States: Active(0), At-Risk(1), Inactive(2), Reactivated(3), Churned(4)
    # P[4,4] = 0.98 (near-absorbing but not strictly absorbing -> ABSORBING_THRESHOLD=0.95)
    P = np.array(
        [
            # Active   At-Risk  Inactive  Reactivated  Churned
            [0.80,    0.12,    0.03,     0.02,        0.03],   # Active (row 0)
            [0.10,    0.60,    0.15,     0.05,        0.10],   # At-Risk (row 1)
            [0.05,    0.10,    0.65,     0.10,        0.10],   # Inactive (row 2)
            [0.15,    0.10,    0.05,     0.65,        0.05],   # Reactivated (row 3)
            [0.01,    0.00,    0.00,     0.01,        0.98],   # Churned (row 4)
        ],
        dtype=np.float64,
    )
    # Verify all rows sum to 1.0
    np.testing.assert_allclose(P.sum(axis=1), np.ones(5), atol=1e-9)

    result = service.compute_avg_lifetime(P, active_state_idx=0)

    assert result is not None, "Expected float, got None"
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    assert 15.0 < result < 35.0, f"Expected result in (15, 35), got {result}"


def test_compute_avg_lifetime_all_absorbed() -> None:
    """CH-01: compute_avg_lifetime returns None when all states are absorbing.

    np.eye(3) means all diagonal entries are 1.0, so all are absorbing states.
    No transient submatrix -> fundamental matrix cannot be computed -> return None.
    """
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service, "compute_avg_lifetime"):
        pytest.skip("compute_avg_lifetime not yet implemented (Plan 02)")

    result = service.compute_avg_lifetime(np.eye(3, dtype=np.float64), active_state_idx=0)

    assert result is None, f"Expected None for identity matrix (all absorbing), got {result}"


def test_simulate_scenario_renormalizes() -> None:
    """CH-01: _apply_overrides renormalizes the modified row to sum to 1.0."""
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service, "_apply_overrides"):
        pytest.skip("_apply_overrides not yet implemented (Plan 02)")

    # 3x3 row-stochastic baseline P
    P = np.array(
        [
            [0.70, 0.20, 0.10],   # row 0 — will be modified
            [0.30, 0.50, 0.20],   # row 1 — untouched
            [0.00, 0.05, 0.95],   # row 2 — untouched
        ],
        dtype=np.float64,
    )
    original_p01 = float(P[0, 1])

    # Override cell (0,1): set active->atrisk to 0.5 (was 0.20)
    overrides = {(0, 1): 0.5}
    P_mod = service._apply_overrides(P, overrides)

    # Modified row must still sum to 1.0
    np.testing.assert_allclose(P_mod[0].sum(), 1.0, atol=1e-9)

    # The overridden cell increased relative to original
    assert P_mod[0, 1] > original_p01, (
        f"Expected P_mod[0,1] > {original_p01}, got {P_mod[0, 1]}"
    )

    # Untouched rows are unchanged
    np.testing.assert_allclose(P_mod[1], P[1], atol=1e-12)
    np.testing.assert_allclose(P_mod[2], P[2], atol=1e-12)


def test_churn_analysis_result_fields() -> None:
    """CH-01: ChurnAnalysisResult has exactly the required dataclass fields (D-09)."""
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service.ChurnAnalysisResult, "__dataclass_fields__"):
        pytest.skip("ChurnAnalysisResult not yet a proper dataclass (Plan 02)")

    expected_fields = {
        "transition_matrix",
        "observation_counts",
        "state_distribution_over_time",
        "baseline_forecast",
        "kpis",
        "state_labels",
        "dataset_name",
        "n_customers",
        "n_periods",
    }
    actual_fields = set(service.ChurnAnalysisResult.__dataclass_fields__)

    # Skip if old stub fields present (pre-Plan-02 stub has wrong field names)
    if "sankey_chart_json" in actual_fields or "state_distribution_per_period" in actual_fields:
        pytest.skip("ChurnAnalysisResult is still the old stub (Plan 02 will rewrite)")

    assert actual_fields == expected_fields, (
        f"Field mismatch.\nExpected: {sorted(expected_fields)}\nGot:      {sorted(actual_fields)}"
    )


def test_kpi_keys_and_revenue_constant() -> None:
    """CH-01/D-05: KPI_KEYS tuple and DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER constant."""
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service, "KPI_KEYS"):
        pytest.skip("KPI_KEYS not yet defined (Plan 02)")

    assert service.KPI_KEYS == ("retention_rate", "avg_lifetime", "expected_churn", "revenue_at_risk"), (
        f"KPI_KEYS mismatch: {service.KPI_KEYS}"
    )
    assert service.DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER == 50_000, (
        f"Expected 50_000, got {service.DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER}"
    )


def test_build_sankey_figure() -> None:
    """CH-02: build_sankey_figure returns a go.Figure with at least one shape (ribbons)."""
    pytest.importorskip("app.components.sankey_flow")
    import plotly.graph_objects as go
    from app.components.sankey_flow import build_sankey_figure

    n_cols = 8
    n_states = 3

    # Synthetic state_distribution_over_time shape (n_cols, n_states), rows sum to 1.0
    rng = np.random.default_rng(42)
    raw = rng.dirichlet(alpha=np.ones(n_states), size=n_cols)
    state_dist = raw.astype(np.float64)

    # 3x3 row-stochastic transition matrix
    P = np.array(
        [
            [0.70, 0.20, 0.10],
            [0.30, 0.50, 0.20],
            [0.00, 0.05, 0.95],
        ],
        dtype=np.float64,
    )

    state_labels = ["active", "atrisk", "churned"]
    state_colors = {
        "active":  "rgba(5,150,105,",
        "atrisk":  "rgba(217,119,6,",
        "churned": "rgba(220,38,38,",
    }

    fig = build_sankey_figure(
        state_dist,
        P,
        state_labels,
        state_colors,
        n_cols=n_cols,
    )

    assert isinstance(fig, go.Figure), f"Expected go.Figure, got {type(fig)}"
    assert len(fig.layout.shapes) >= 1, (
        f"Expected at least 1 shape (ribbon/node), got {len(fig.layout.shapes)}"
    )


def test_build_whatif_chart_has_two_stackgroups() -> None:
    """CH-03: build_whatif_chart returns a stacked-area figure with baseline and modified groups."""
    from app.components.sankey_flow import build_whatif_chart

    base = np.tile([0.6, 0.2, 0.2], (13, 1)).astype(float)
    mod = np.tile([0.5, 0.2, 0.3], (13, 1)).astype(float)
    fig = build_whatif_chart(base, mod, ["active", "atrisk", "churned"])
    groups = {getattr(t, "stackgroup", None) for t in fig.data}
    assert "baseline" in groups and "modified" in groups
    assert len(fig.data) >= 2


def test_impact_narrative_largest_delta() -> None:
    """CH-03: impact_narrative produces correct sentence for the largest delta transition."""
    from app.components.sankey_flow import impact_narrative

    P = np.array([[0.6, 0.2, 0.2], [0.1, 0.7, 0.2], [0.0, 0.0, 1.0]])
    base = np.tile([0.6, 0.2, 0.2], (13, 1)).astype(float)
    mod = np.tile([0.4, 0.2, 0.4], (13, 1)).astype(float)
    text = impact_narrative({(0, 2): 0.4}, P, base, mod, ["active", "atrisk", "churned"], 1000)
    assert "pp" in text
    assert text.startswith("Increasing") or text.startswith("Reducing")


def test_impact_narrative_empty_overrides() -> None:
    """CH-03: impact_narrative returns prompt string when no overrides are set."""
    from app.components.sankey_flow import impact_narrative

    P = np.eye(3)
    z = np.tile([0.33, 0.34, 0.33], (13, 1)).astype(float)
    assert (
        impact_narrative({}, P, z, z, ["active", "atrisk", "churned"], 100)
        == "Adjust a slider to model a retention scenario."
    )
