"""Unit tests for core.models — validators and m1/m2/m3 forecast."""
from __future__ import annotations

import numpy as np
import pytest


def test_validate_transition_matrix_accepts_valid(sample_2x2_matrix):
    from core.models import validate_transition_matrix

    validate_transition_matrix(sample_2x2_matrix)  # should not raise


def test_validate_transition_matrix_rejects_non_square():
    from core.exceptions import InvalidTransitionMatrixError
    from core.models import validate_transition_matrix

    with pytest.raises(InvalidTransitionMatrixError):
        validate_transition_matrix(np.array([[0.5, 0.5, 0.0]]))


def test_validate_transition_matrix_rejects_unnormalized():
    from core.exceptions import InvalidTransitionMatrixError
    from core.models import validate_transition_matrix

    with pytest.raises(InvalidTransitionMatrixError):
        validate_transition_matrix(np.array([[0.5, 0.5], [0.3, 0.3]]))


def test_m1_forecast_replicates_chan_2015_table3(sample_4x4_chan_matrix):
    """Verify m1 forecast matches Chan 2015 Table 3 within 1e-3."""
    from core.models import M1Homogeneous

    Y_1 = np.array([0.5878, 0.2830, 0.0585, 0.0708])
    model = M1Homogeneous(P=sample_4x4_chan_matrix)
    result = model.forecast(Y_1=Y_1, horizon=5)

    # Expected from Chan 2015 Table 3, row t=2
    expected_t2 = np.array([0.5829, 0.2780, 0.0667, 0.0724])
    np.testing.assert_allclose(result.forecast_array[1], expected_t2, atol=1e-3)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_rejects_negative():
    from core.exceptions import InvalidTransitionMatrixError
    from core.models import validate_transition_matrix
    with pytest.raises(InvalidTransitionMatrixError):
        validate_transition_matrix(np.array([[1.5, -0.5], [0.5, 0.5]]))


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_rejects_wrong_dtype():
    from core.exceptions import InvalidTransitionMatrixError
    from core.models import validate_transition_matrix
    P = np.array([[0.7, 0.3], [0.4, 0.6]], dtype=np.float32)
    with pytest.raises(InvalidTransitionMatrixError):
        validate_transition_matrix(P)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_warns_sparse_cells(caplog):
    from core.models import validate_transition_matrix
    P = np.array([[0.7, 0.3], [0.4, 0.6]])
    counts = np.array([[100, 100], [5, 5]])  # row 1 sparse
    with caplog.at_level("WARNING"):
        validate_transition_matrix(P, transition_counts=counts)
    assert any("sparsity" in r.message.lower() or "sparse" in r.message.lower() for r in caplog.records)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_m1_forecast_shape(sample_2x2_matrix):
    from core.models import M1Homogeneous
    model = M1Homogeneous(P=sample_2x2_matrix)
    Y_1 = np.array([0.6, 0.4])
    result = model.forecast(Y_1=Y_1, horizon=5)
    assert result.forecast_array.shape == (5, 2)
    assert result.model_type == "m1"
    assert result.horizon == 5


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_m2_forecast_shape():
    from core.models import M2TimeVarying
    P_t = np.array([
        [[0.7, 0.3], [0.4, 0.6]],
        [[0.6, 0.4], [0.5, 0.5]],
        [[0.8, 0.2], [0.3, 0.7]],
    ], dtype=np.float64)
    model = M2TimeVarying(P_t_sequence=P_t)
    Y_1 = np.array([0.6, 0.4])
    result = model.forecast(Y_1=Y_1, horizon=3)
    assert result.forecast_array.shape == (3, 2)
    assert result.model_type == "m2"


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_m2_holds_last_pt_at_horizon():
    from core.models import M2TimeVarying
    P_t = np.array([
        [[0.7, 0.3], [0.4, 0.6]],
        [[0.6, 0.4], [0.5, 0.5]],
    ], dtype=np.float64)
    model = M2TimeVarying(P_t_sequence=P_t)
    Y_1 = np.array([0.6, 0.4])
    result_4 = model.forecast(Y_1=Y_1, horizon=4)
    # After step 2, P_t[-1] must be reused — verify by manually computing
    Y2 = Y_1 @ P_t[0]
    Y3 = Y2 @ P_t[1]
    Y4 = Y3 @ P_t[1]  # held last
    Y5 = Y4 @ P_t[1]  # held last
    np.testing.assert_allclose(result_4.forecast_array[3], Y5, atol=1e-9)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_m3_forecast_replicates_chan_2015(sample_4x4_chan_matrix):
    """Verify M3 forecast matches Chan 2015 m3 table within reasonable tolerance.

    From RESEARCH.md Code Examples:
    G = [1.0315, 1.0561, 0.9029, 1.0897]
    Q_1 = [0.5878, 0.2830, 0.0585, 0.0708]
    Expected at t=2: [0.5799, 0.2847, 0.0603, 0.0751] (per docs/MARKOV-MODELS.md m3 table)
    """
    from core.models import M3Extended
    P_t = np.tile(sample_4x4_chan_matrix[None, :, :], (5, 1, 1))  # repeat 5 times
    G = np.array([1.0315, 1.0561, 0.9029, 1.0897])
    Q_1 = np.array([0.5878, 0.2830, 0.0585, 0.0708])
    model = M3Extended(P_t_sequence=P_t, G=G)
    result = model.forecast(Q_1=Q_1, horizon=5)
    expected_t2 = np.array([0.5799, 0.2847, 0.0603, 0.0751])
    np.testing.assert_allclose(result.forecast_array[0], expected_t2, atol=1e-2)
