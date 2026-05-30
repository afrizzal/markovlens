"""Structural tests for app/components (UI-02, BS-02, BS-03).

Tests target the private ``_build_*_figure`` helpers which return ``go.Figure``
objects — no Streamlit runtime is needed.  Each test module imports Streamlit
first (RESEARCH Pitfall 1) so the ``"streamlit"`` template is registered before
``register_theme()`` runs.
"""
from __future__ import annotations

import inspect
import pathlib

import numpy as np
import plotly.graph_objects as go
import pytest
import streamlit  # noqa: F401 — must import before register_theme

from app.styles.plotly_theme import register_theme

# Register the Plotly theme once at module scope so it's available for all tests.
register_theme()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def matrix_3x3() -> np.ndarray:
    """Valid 3x3 transition matrix (rows sum to 1)."""
    P = np.array([
        [0.70, 0.20, 0.10],
        [0.15, 0.65, 0.20],
        [0.05, 0.25, 0.70],
    ])
    return P


@pytest.fixture
def obs_counts_dense() -> np.ndarray:
    """Observation counts — all cells well above sparsity threshold."""
    return np.full((3, 3), 50, dtype=int)


@pytest.fixture
def obs_counts_sparse() -> np.ndarray:
    """Observation counts — one cell below the 20-observation threshold."""
    counts = np.full((3, 3), 50, dtype=int)
    counts[0, 1] = 5  # sparse cell
    return counts


@pytest.fixture
def state_labels_3() -> list[str]:
    return ["Alpha", "Beta", "Gamma"]


@pytest.fixture
def fan_arrays():
    """Monotone P10/P50/P90 arrays and a short history."""
    n = 12
    p10 = np.linspace(0.10, 0.20, n)
    p50 = np.linspace(0.30, 0.40, n)
    p90 = np.linspace(0.50, 0.60, n)
    history = np.linspace(0.25, 0.30, 6)
    return p10, p50, p90, history


# ---------------------------------------------------------------------------
# transition_heatmap tests (BS-02)
# ---------------------------------------------------------------------------


class TestTransitionHeatmap:
    def test_transition_heatmap_fixed_scale(
        self,
        matrix_3x3: np.ndarray,
        obs_counts_dense: np.ndarray,
        state_labels_3: list[str],
    ) -> None:
        """BS-02: heatmap must have a fixed [0, 1] color axis, never auto-range."""
        from app.components.transition_heatmap import _build_heatmap_figure

        fig = _build_heatmap_figure(
            matrix_3x3,
            obs_counts_dense,
            state_labels_3,
        )
        assert isinstance(fig, go.Figure)
        heatmap_trace = next(t for t in fig.data if isinstance(t, go.Heatmap))
        assert heatmap_trace.zmin == 0, "zmin must be 0 (fixed scale)"
        assert heatmap_trace.zmax == 1, "zmax must be 1 (fixed scale)"

    def test_transition_heatmap_sparsity(
        self,
        matrix_3x3: np.ndarray,
        obs_counts_sparse: np.ndarray,
        state_labels_3: list[str],
    ) -> None:
        """BS-02: sparsity marker must appear in warning color; all cells annotated."""
        from app.components.transition_heatmap import _build_heatmap_figure

        n = len(state_labels_3)
        fig = _build_heatmap_figure(
            matrix_3x3,
            obs_counts_sparse,
            state_labels_3,
        )
        annotations = fig.layout.annotations
        assert annotations is not None
        assert len(annotations) > 0

        # Count percent-value annotations (one per cell = n*n)
        value_annotations = [a for a in annotations if "%" in str(a.text)]
        assert len(value_annotations) == n * n, (
            f"Expected {n * n} percent annotations, got {len(value_annotations)}"
        )

        # At least one warning marker in warning color
        warning_annotations = [
            a for a in annotations
            if str(a.text).strip() == "⚠"  # ⚠
        ]
        assert len(warning_annotations) >= 1, "At least one sparsity marker expected"
        for wa in warning_annotations:
            assert wa.font.color == "#D97706", (
                f"Sparsity marker must use #D97706, got {wa.font.color}"
            )


# ---------------------------------------------------------------------------
# monte_carlo_fan tests (BS-03)
# ---------------------------------------------------------------------------


class TestMonteCarlFan:
    def test_monte_carlo_fan_traces(
        self,
        fan_arrays: tuple,
    ) -> None:
        """BS-03: fan chart must have >= 5 traces + vline shape + named legend entries."""
        from app.components.monte_carlo_fan import _build_fan_figure

        p10, p50, p90, history = fan_arrays
        fig = _build_fan_figure(p10, p50, p90, history=history, brand_label="TestBrand")

        assert isinstance(fig, go.Figure)

        # At least 5 data traces
        assert len(fig.data) >= 5, (
            f"Expected >= 5 traces, got {len(fig.data)}: {[t.name for t in fig.data]}"
        )

        # Separator shape (vline produces a shape in fig.layout.shapes)
        assert len(fig.layout.shapes) >= 1, (
            "Expected at least one vertical separator shape from add_vline"
        )

        # Named legend entries must include Median (P50), P10, P90, Historical
        trace_names = {str(t.name) for t in fig.data}
        required_names = {"Median (P50)", "P10", "P90", "Historical"}
        for name in required_names:
            assert name in trace_names, (
                f"Legend entry '{name}' not found. Got: {trace_names}"
            )

    def test_monte_carlo_fan_fill_present(
        self,
        fan_arrays: tuple,
    ) -> None:
        """BS-03: at least one trace must have fill set (band area)."""
        from app.components.monte_carlo_fan import _build_fan_figure

        p10, p50, p90, history = fan_arrays
        fig = _build_fan_figure(p10, p50, p90, history=history)

        fill_traces = [t for t in fig.data if getattr(t, "fill", None)]
        assert len(fill_traces) >= 1, "Expected at least one filled band trace"


# ---------------------------------------------------------------------------
# kpi_card tests (D-06/D-07)
# ---------------------------------------------------------------------------


class TestKpiCard:
    def test_kpi_card_no_st_metric(self) -> None:
        """D-07: kpi_card must use custom HTML, not st.metric."""
        src = pathlib.Path(__file__).parent.parent.parent / "app" / "components" / "kpi_card.py"
        content = src.read_text(encoding="utf-8")
        assert "st.metric" not in content, "kpi_card must NOT use st.metric"
        assert "TODO(phase05)" not in content, "stale TODO(phase05) comment must be removed"
        assert "phase05" not in content.lower(), "stale phase05 reference must be removed"
        assert "accent-card" in content, "kpi_card must render .accent-card HTML"

    def test_kpi_card_signature(self) -> None:
        """kpi_card must expose keyword-only params: delta_suffix and accent."""
        from app.components.kpi_card import kpi_card

        params = inspect.signature(kpi_card).parameters
        assert "delta_suffix" in params, "delta_suffix param missing"
        assert "accent" in params, "accent param missing"
        assert "unit" in params, "unit param missing"
        assert "sparkline" in params, "sparkline param missing"


# ---------------------------------------------------------------------------
# empty_state tests (D-06)
# ---------------------------------------------------------------------------


class TestEmptyState:
    def test_empty_state_signature(self) -> None:
        """empty_state must accept action_label and action_callback (not old action tuple)."""
        from app.components.empty_state import empty_state

        params = inspect.signature(empty_state).parameters
        assert "action_label" in params, "action_label param missing"
        assert "action_callback" in params, "action_callback param missing"
        assert "action" not in params, "old 'action' tuple param must be removed"

    def test_empty_state_no_old_signature(self) -> None:
        """empty_state source must not use the old action-tuple pattern."""
        src = pathlib.Path(__file__).parent.parent.parent / "app" / "components" / "empty_state.py"
        content = src.read_text(encoding="utf-8")
        assert "action: tuple" not in content, "Old action: tuple signature must be removed"
