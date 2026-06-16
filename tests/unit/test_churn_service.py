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
            [0.80, 0.12, 0.03, 0.02, 0.03],  # Active (row 0)
            [0.10, 0.60, 0.15, 0.05, 0.10],  # At-Risk (row 1)
            [0.05, 0.10, 0.65, 0.10, 0.10],  # Inactive (row 2)
            [0.15, 0.10, 0.05, 0.65, 0.05],  # Reactivated (row 3)
            [0.01, 0.00, 0.00, 0.01, 0.98],  # Churned (row 4)
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
            [0.70, 0.20, 0.10],  # row 0 — will be modified
            [0.30, 0.50, 0.20],  # row 1 — untouched
            [0.00, 0.05, 0.95],  # row 2 — untouched
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
    assert P_mod[0, 1] > original_p01, f"Expected P_mod[0,1] > {original_p01}, got {P_mod[0, 1]}"

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

    assert service.KPI_KEYS == (
        "retention_rate",
        "avg_lifetime",
        "expected_churn",
        "revenue_at_risk",
    ), f"KPI_KEYS mismatch: {service.KPI_KEYS}"
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
        "active": "rgba(5,150,105,",
        "atrisk": "rgba(217,119,6,",
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
    assert "baseline" in groups
    assert "modified" in groups
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


def test_apply_overrides_locks_modified_cell_exactly() -> None:
    """_apply_overrides must lock the modified cell at the exact target value (not renormalized away).

    Regression test for iteration #3 bug: old code divided by row_sum after setting the
    override, which changed active->active from 0.50 back to ~0.877 on telco-like data.
    """
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service, "_apply_overrides"):
        pytest.skip("_apply_overrides not yet implemented")

    # Telco-like baseline: active row = [0.93, 0.00, 0.07, 0.00]
    P = np.array(
        [
            [0.93, 0.00, 0.07, 0.00],  # Active
            [0.10, 0.70, 0.15, 0.05],  # At-Risk
            [0.05, 0.05, 0.80, 0.10],  # Inactive
            [0.00, 0.00, 0.02, 0.98],  # Churned
        ],
        dtype=np.float64,
    )

    # User moves active->active slider from 0.93 to 0.50
    P_mod = service._apply_overrides(P, {(0, 0): 0.50})

    # The modified cell must be EXACTLY 0.50 — not 0.877 (old renormalize bug)
    np.testing.assert_allclose(
        P_mod[0, 0],
        0.50,
        atol=1e-9,
        err_msg="Modified cell must be locked at target value, not renormalized away",
    )

    # Row must still sum to 1.0
    np.testing.assert_allclose(P_mod[0].sum(), 1.0, atol=1e-9)

    # Result matches the hand-trace: remaining 0.50 goes entirely to cell (0,2) = 0.07/0.07
    np.testing.assert_allclose(P_mod[0], [0.50, 0.00, 0.50, 0.00], atol=1e-9)

    # Untouched rows are unchanged
    np.testing.assert_allclose(P_mod[1:], P[1:], atol=1e-12)


def test_apply_overrides_redistributes_remaining_proportionally() -> None:
    """Unmodified cells receive remaining mass proportional to their baseline weights."""
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service, "_apply_overrides"):
        pytest.skip("_apply_overrides not yet implemented")

    # Baseline P[0] = [0.70, 0.20, 0.10]; set cell (0,2) = 0.30
    P = np.array(
        [[0.70, 0.20, 0.10], [0.30, 0.50, 0.20], [0.00, 0.05, 0.95]],
        dtype=np.float64,
    )
    P_mod = service._apply_overrides(P, {(0, 2): 0.30})

    # Cell (0,2) locked at 0.30
    np.testing.assert_allclose(P_mod[0, 2], 0.30, atol=1e-9)

    # Remaining = 0.70 is redistributed to cells (0,0) and (0,1) proportional to 0.70:0.20
    remaining = 0.70
    unmod_sum = 0.70 + 0.20  # baseline mass of unmodified cells
    expected_00 = 0.70 * remaining / unmod_sum  # 0.70 * 0.70 / 0.90 ≈ 0.5444
    expected_01 = 0.20 * remaining / unmod_sum  # 0.20 * 0.70 / 0.90 ≈ 0.1556
    np.testing.assert_allclose(P_mod[0, 0], expected_00, atol=1e-9)
    np.testing.assert_allclose(P_mod[0, 1], expected_01, atol=1e-9)
    np.testing.assert_allclose(P_mod[0].sum(), 1.0, atol=1e-9)


def test_apply_overrides_clamp_sum_exceeds_one() -> None:
    """When sum of modified cells > 1.0, result row still sums to 1.0."""
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service, "_apply_overrides"):
        pytest.skip("_apply_overrides not yet implemented")

    P = np.array([[0.70, 0.20, 0.10], [0.30, 0.50, 0.20]], dtype=np.float64)
    # Two modified cells that together sum to 1.5
    P_mod = service._apply_overrides(P, {(0, 0): 0.80, (0, 1): 0.70})

    np.testing.assert_allclose(P_mod[0].sum(), 1.0, atol=1e-9)
    assert (P_mod[0] >= 0).all(), "No negative probabilities after clamp"


def test_apply_overrides_all_baseline_mass_on_modified_cells() -> None:
    """When all baseline mass is on modified cells, remaining distributes equally."""
    service = pytest.importorskip("domains.churn.service")
    if not hasattr(service, "_apply_overrides"):
        pytest.skip("_apply_overrides not yet implemented")

    # Row with zero baseline on unmodified cell (0,2)
    P = np.array([[0.60, 0.40, 0.00], [0.30, 0.50, 0.20]], dtype=np.float64)
    # Modify cells (0,0) and (0,1) — all baseline mass is on modified cells
    P_mod = service._apply_overrides(P, {(0, 0): 0.30, (0, 1): 0.30})

    # Modified cells locked; remaining = 0.40 distributed equally to 1 unmodified cell
    np.testing.assert_allclose(P_mod[0, 0], 0.30, atol=1e-9)
    np.testing.assert_allclose(P_mod[0, 1], 0.30, atol=1e-9)
    np.testing.assert_allclose(P_mod[0, 2], 0.40, atol=1e-9)  # equal share
    np.testing.assert_allclose(P_mod[0].sum(), 1.0, atol=1e-9)


def test_impact_narrative_empty_overrides() -> None:
    """CH-03: impact_narrative returns prompt string when no overrides are set."""
    from app.components.sankey_flow import impact_narrative

    P = np.eye(3)
    z = np.tile([0.33, 0.34, 0.33], (13, 1)).astype(float)
    assert (
        impact_narrative({}, P, z, z, ["active", "atrisk", "churned"], 100)
        == "Adjust a slider to model a retention scenario."
    )


# ---------------------------------------------------------------------------
# Tests for new helpers: ImpactSummary, impact_summary, state_legend_html
# ---------------------------------------------------------------------------


def test_impact_summary_empty_overrides_is_neutral() -> None:
    """Test 1 (empty): impact_summary with empty overrides -> applied=False, neutral."""
    from app.components.sankey_flow import ImpactSummary, impact_summary

    P = np.eye(3, dtype=np.float64)
    z = np.tile([0.33, 0.34, 0.33], (13, 1)).astype(np.float64)
    result = impact_summary({}, P, z, z, ["active", "atrisk", "churned"], 100)

    assert isinstance(result, ImpactSummary)
    assert result.applied is False
    assert result.direction == "neutral"
    assert result.accent_token == "var(--color-text-tertiary)"
    assert "Adjust a slider" in result.html


def test_impact_summary_improving_scenario() -> None:
    """Test 2 (improving): override that reduces churn -> direction='improving'."""
    from app.components.sankey_flow import impact_summary

    P = np.array([[0.6, 0.2, 0.2], [0.1, 0.7, 0.2], [0.0, 0.0, 1.0]], dtype=np.float64)
    # Baseline: churned column at 0.2; modified: churned at 0.1 => improvement
    base = np.tile([0.6, 0.2, 0.2], (13, 1)).astype(np.float64)
    mod = np.tile([0.7, 0.2, 0.1], (13, 1)).astype(np.float64)

    result = impact_summary(
        {(0, 2): 0.1},  # reduce active->churned from 0.2 to 0.1
        P,
        base,
        mod,
        ["active", "atrisk", "churned"],
        1000,
    )

    assert result.applied is True
    assert result.direction == "improving"
    assert result.accent_token == "var(--color-success)"
    assert "t-h2" in result.html
    assert "saves" in result.html


def test_impact_summary_worsening_scenario() -> None:
    """Test 3 (worsening): override that raises churn -> direction='worsening'."""
    from app.components.sankey_flow import impact_summary

    P = np.array([[0.6, 0.2, 0.2], [0.1, 0.7, 0.2], [0.0, 0.0, 1.0]], dtype=np.float64)
    # Baseline: churned at 0.2; modified: churned at 0.4 => worsening
    base = np.tile([0.6, 0.2, 0.2], (13, 1)).astype(np.float64)
    mod = np.tile([0.4, 0.2, 0.4], (13, 1)).astype(np.float64)

    result = impact_summary(
        {(0, 2): 0.4},  # increase active->churned from 0.2 to 0.4
        P,
        base,
        mod,
        ["active", "atrisk", "churned"],
        1000,
    )

    assert result.applied is True
    assert result.direction == "worsening"
    assert result.accent_token == "var(--color-warning)"
    assert "costs" in result.html


def test_state_legend_html_swatch_count() -> None:
    """Test 4 (legend): state_legend_html returns correct swatch count."""
    from app.components.sankey_flow import state_legend_html

    html = state_legend_html(["Active", "At-Risk", "Churned"])

    assert "Active" in html
    assert "At-Risk" in html
    assert "Churned" in html
    # Each swatch is a circle div — assert exactly 3 swatch elements
    assert html.count("border-radius:50%") == 3
