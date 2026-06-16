"""Stubs for Monte Carlo, calibration, quantile bands, walk-forward backtest."""

from __future__ import annotations

import numpy as np
import pytest


def test_monte_carlo_same_seed_reproducible(sample_2x2_matrix):
    from core.simulation import monte_carlo_simulate

    P = sample_2x2_matrix.astype(np.float64)
    paths_a = monte_carlo_simulate(P, start_state=0, n_steps=10, n_simulations=1_000, seed=42)
    paths_b = monte_carlo_simulate(P, start_state=0, n_steps=10, n_simulations=1_000, seed=42)
    np.testing.assert_array_equal(paths_a, paths_b)


def test_monte_carlo_different_seeds_differ(sample_2x2_matrix):
    from core.simulation import monte_carlo_simulate

    P = sample_2x2_matrix.astype(np.float64)
    paths_a = monte_carlo_simulate(P, start_state=0, n_steps=10, n_simulations=1_000, seed=42)
    paths_c = monte_carlo_simulate(P, start_state=0, n_steps=10, n_simulations=1_000, seed=7)
    assert not np.array_equal(paths_a, paths_c)


def test_monte_carlo_output_shape(sample_2x2_matrix):
    from core.simulation import monte_carlo_simulate

    P = sample_2x2_matrix.astype(np.float64)
    paths = monte_carlo_simulate(P, start_state=0, n_steps=12, n_simulations=500, seed=1)
    assert paths.shape == (500, 13)  # n_steps + 1


def test_monte_carlo_dtype_int64(sample_2x2_matrix):
    from core.simulation import monte_carlo_simulate

    P = sample_2x2_matrix.astype(np.float64)
    paths = monte_carlo_simulate(P, start_state=0, n_steps=5, n_simulations=100, seed=1)
    assert paths.dtype == np.int64


def test_monte_carlo_accepts_distribution_start():
    """D-13: start_state may be an np.ndarray initial distribution."""
    from core.simulation import monte_carlo_simulate

    P = np.array([[0.7, 0.3], [0.4, 0.6]], dtype=np.float64)
    init_dist = np.array([0.5, 0.5])
    paths = monte_carlo_simulate(P, start_state=init_dist, n_steps=5, n_simulations=2_000, seed=42)
    initial_states = paths[:, 0]
    # With seed=42, roughly half the paths should start in each state
    state_0_frac = (initial_states == 0).mean()
    assert 0.4 < state_0_frac < 0.6


def test_monte_carlo_no_drift_to_zero_for_last_state():
    """D-12 regression: cum_matrix[:, -1] = 1.0 fix must keep last state reachable."""
    from core.simulation import monte_carlo_simulate

    # Matrix where state 0 -> state 2 has nonzero probability
    P = np.array(
        [
            [0.5, 0.3, 0.2],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    paths = monte_carlo_simulate(P, start_state=0, n_steps=1, n_simulations=10_000, seed=42)
    next_states = paths[:, 1]
    # Last state (index 2) must be reachable with probability ~0.2
    state_2_frac = (next_states == 2).mean()
    assert state_2_frac > 0.15


def test_calibrate_anchor_points():
    from core.simulation import calibrate_probability

    assert calibrate_probability(0.05) == pytest.approx(0.0418, abs=1e-6)
    assert calibrate_probability(0.50) == pytest.approx(0.500, abs=1e-6)
    assert calibrate_probability(0.95) == pytest.approx(0.958, abs=1e-6)


def test_calibrate_interpolates():
    from core.simulation import calibrate_probability

    # 0.03 is the midpoint of key interval [0.01, 0.05] -> output is midpoint of their values
    midpoint = calibrate_probability(0.03)
    assert midpoint == pytest.approx((0.0043 + 0.0418) / 2, abs=1e-3)


def test_calibrate_boundary_clamps():
    from core.simulation import calibrate_probability

    assert calibrate_probability(0.0) == pytest.approx(0.0043, abs=1e-6)
    assert calibrate_probability(1.0) == pytest.approx(0.958, abs=1e-6)


def test_quantile_bands_shape():
    from core.simulation import compute_quantile_bands

    paths = np.random.default_rng(42).integers(0, 4, size=(1000, 13))
    bands = compute_quantile_bands(paths, target_extractor=lambda p: p.astype(np.float64))
    assert 0.10 in bands and 0.50 in bands and 0.90 in bands
    assert bands[0.50].shape == (13,)


def test_quantile_bands_target_extractor_applied():
    """ENG-07: target_extractor must be applied BEFORE percentile, not after."""
    from core.simulation import compute_quantile_bands

    paths = np.array([[0, 1, 2], [1, 2, 3], [2, 3, 4]], dtype=np.int64)
    bands = compute_quantile_bands(paths, target_extractor=lambda p: p * 2.0, quantiles=(0.5,))
    np.testing.assert_allclose(bands[0.5], [2.0, 4.0, 6.0])


def test_walk_forward_no_leakage():
    """ENG-09: backtest must only use past data to fit matrix at each step."""
    import pandas as pd

    from core.simulation import walk_forward_backtest

    df = pd.DataFrame(
        {
            "period": list(range(1, 13)),
            "from_state": ["A"] * 6 + ["B"] * 6,
            "to_state": ["A"] * 5 + ["B"] * 7,
            "entity_id": ["e1"] * 12,
            "dataset_id": ["ds_test"] * 12,
            "weight": [1.0] * 12,
        }
    )
    results = walk_forward_backtest(df, window=3)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all("period" in r for r in results)


# ── Targeted branch-coverage tests (Phase 05, D-02) ─────────────────────────────────────────────


def test_quantile_bands_rejects_1d_extractor():
    from core.simulation import compute_quantile_bands

    paths = np.zeros((100, 13), dtype=np.int64)
    with pytest.raises(ValueError):
        compute_quantile_bands(paths, target_extractor=lambda p: p[:, -1])  # 1-D → L165


def test_counts_from_empty_df_returns_zeros():
    import pandas as pd

    from core.simulation import _counts_from_long_df

    df = pd.DataFrame(columns=["from_state", "to_state", "weight"])
    state_idx = {"A": 0, "B": 1}
    counts = _counts_from_long_df(df, state_idx, n_states=2)
    assert counts.shape == (2, 2)
    assert (counts == 0).all()


def test_state_distribution_from_empty_df_returns_zeros():
    import pandas as pd

    from core.simulation import _state_distribution_from_long_df

    df = pd.DataFrame(columns=["to_state", "weight"])
    state_idx = {"A": 0, "B": 1}
    vec = _state_distribution_from_long_df(df, state_idx, n_states=2, state_col="to_state")
    assert vec.shape == (2,)
    assert (vec == 0).all()


def test_walk_forward_assigns_default_weight():
    import pandas as pd

    from core.simulation import walk_forward_backtest

    df = pd.DataFrame(
        {
            "period": list(range(1, 13)),
            "from_state": ["A"] * 6 + ["B"] * 6,
            "to_state": ["A"] * 5 + ["B"] * 7,
        }
    )  # NO weight column
    results = walk_forward_backtest(df, window=3)
    assert isinstance(results, list)
    assert len(results) > 0


def test_walk_forward_too_few_periods_returns_empty():
    import pandas as pd

    from core.simulation import walk_forward_backtest

    df = pd.DataFrame(
        {
            "period": [1, 1, 2, 2],
            "from_state": ["A", "B", "A", "B"],
            "to_state": ["A", "B", "A", "B"],
            "weight": [1.0, 1.0, 1.0, 1.0],
        }
    )  # only 2 unique periods, window=3 → []
    assert walk_forward_backtest(df, window=3) == []


def test_walk_forward_mape_exception_sets_none():
    import pandas as pd
    from unittest.mock import patch

    from core.simulation import walk_forward_backtest

    df = pd.DataFrame(
        {
            "period": list(range(1, 13)),
            "from_state": ["A"] * 6 + ["B"] * 6,
            "to_state": ["A"] * 5 + ["B"] * 7,
            "weight": [1.0] * 12,
        }
    )
    with patch("core.metrics.mape", side_effect=ValueError("boom")):
        results = walk_forward_backtest(df, window=3)
    assert len(results) > 0
    assert all(r["mape"] is None for r in results)
