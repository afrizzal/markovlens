"""Unit tests for core.models — validators and m1/m2/m3 forecast."""
from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.skip(reason="TODO Phase 01 — implementation pending")
def test_validate_transition_matrix_accepts_valid(sample_2x2_matrix):
    from core.models import validate_transition_matrix

    validate_transition_matrix(sample_2x2_matrix)  # should not raise


@pytest.mark.skip(reason="TODO Phase 01 — implementation pending")
def test_validate_transition_matrix_rejects_non_square():
    from core.exceptions import InvalidTransitionMatrixError
    from core.models import validate_transition_matrix

    with pytest.raises(InvalidTransitionMatrixError):
        validate_transition_matrix(np.array([[0.5, 0.5, 0.0]]))


@pytest.mark.skip(reason="TODO Phase 01 — implementation pending")
def test_validate_transition_matrix_rejects_unnormalized():
    from core.exceptions import InvalidTransitionMatrixError
    from core.models import validate_transition_matrix

    with pytest.raises(InvalidTransitionMatrixError):
        validate_transition_matrix(np.array([[0.5, 0.5], [0.3, 0.3]]))


@pytest.mark.skip(reason="TODO Phase 01 — implementation pending")
def test_m1_forecast_replicates_chan_2015_table3(sample_4x4_chan_matrix):
    """Verify m1 forecast matches Chan 2015 Table 3 within 1e-3."""
    from core.models import M1Homogeneous

    Y_1 = np.array([0.5878, 0.2830, 0.0585, 0.0708])
    model = M1Homogeneous(P=sample_4x4_chan_matrix)
    result = model.forecast(Y_1=Y_1, horizon=5)

    # Expected from Chan 2015 Table 3, row t=2
    expected_t2 = np.array([0.5829, 0.2780, 0.0667, 0.0724])
    np.testing.assert_allclose(result.forecast_array[1], expected_t2, atol=1e-3)
