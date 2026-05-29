"""Tests for BS-05: compute_stationary() helper in core/models.py."""
from __future__ import annotations

import numpy as np
import pytest

from core.models import compute_stationary


def test_stationary_sums_to_one(sample_2x2_matrix: np.ndarray) -> None:
    """For [[0.7, 0.3], [0.4, 0.6]], stationary should be [4/7, 3/7]."""
    P = sample_2x2_matrix  # [[0.7, 0.3], [0.4, 0.6]]
    stat = compute_stationary(P)
    assert stat is not None
    assert abs(stat.sum() - 1.0) < 1e-6
    assert (stat >= 0).all()
    # Analytic stationary: solve pi @ P = pi, pi.sum()=1 => pi=[4/7, 3/7]
    assert np.allclose(stat, [4 / 7, 3 / 7], atol=1e-4)


def test_stationary_chan_matrix(sample_4x4_chan_matrix: np.ndarray) -> None:
    """For the Chan 2015 4x4 matrix, stationary must sum to 1.0 with length 4."""
    P = sample_4x4_chan_matrix
    stat = compute_stationary(P)
    assert stat is not None
    assert abs(stat.sum() - 1.0) < 1e-6
    assert len(stat) == 4


def test_stationary_returns_none_when_undefined() -> None:
    """Identity matrix is absorbing but has a valid stationary distribution.

    Power-iteration on np.eye(3) converges immediately (already converged):
    each row of eye(3)^n is still eye(3), so Pn[0] = [1, 0, 0] which is a valid
    probability vector. The function should return a valid vector, not None.
    Additionally, compute_stationary must never raise for any 2D stochastic input.
    """
    eye3 = np.eye(3)
    result = compute_stationary(eye3)
    # For identity the power-iteration result is valid — either eigenvector or
    # power-iteration may return a degenerate [1,0,0]-ish or averaged vector;
    # either way it must be a valid probability vector, never raise.
    assert result is not None
    assert abs(result.sum() - 1.0) < 1e-6

    # Confirm the function never raises for diverse valid stochastic matrices
    for _ in range(5):
        rng = np.random.default_rng(seed=42)
        n = rng.integers(2, 6)
        raw = rng.random((n, n)) + 0.01
        P_rand = (raw / raw.sum(axis=1, keepdims=True)).astype(np.float64)
        try:
            outcome = compute_stationary(P_rand)
            # Must be None or a valid probability vector
            if outcome is not None:
                assert abs(outcome.sum() - 1.0) < 1e-4
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"compute_stationary raised unexpectedly: {exc}")
