"""Monte Carlo simulation + longshot-bias calibration (Becker 2026)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np

TransitionMatrix: TypeAlias = np.ndarray
SimulationPaths: TypeAlias = np.ndarray

CONFIDENCE_LEVELS: tuple[float, ...] = (0.10, 0.50, 0.90)

# Empirical longshot-bias calibration table from Becker (2026) — 72.1M Polymarket trades.
# Maps naive model probability -> real-world resolution rate.
# DO NOT modify without updating docs/MONTE-CARLO.md citation + rerunning backtests.
LONGSHOT_CALIBRATION: dict[float, float] = {
    0.01: 0.0043,
    0.05: 0.0418,
    0.10: 0.087,
    0.20: 0.181,
    0.30: 0.285,
    0.50: 0.500,
    0.70: 0.715,
    0.80: 0.819,
    0.90: 0.913,
    0.95: 0.958,
}


@dataclass(frozen=True)
class SimulationResult:
    """Output of a Monte Carlo run."""

    final_distribution: np.ndarray  # shape (n_states,) probabilities
    quantile_paths: dict[float, np.ndarray]  # percentile -> shape (n_steps+1,)
    raw_probability: float
    calibrated_probability: float
    n_simulations: int
    n_steps: int
    seed: int | None


def monte_carlo_simulate(
    matrix: TransitionMatrix,
    start_state: int,
    n_steps: int = 12,
    n_simulations: int = 10_000,
    seed: int | None = 42,
) -> SimulationPaths:
    """Run Monte Carlo simulation over a transition matrix.

    Returns
    -------
    np.ndarray
        Shape (n_simulations, n_steps+1) of state-index sequences.
    """
    # TODO(phase01): vectorized impl using rng.random + cumsum inverse-CDF sampling
    raise NotImplementedError("monte_carlo_simulate — implement in Phase 01")


def calibrate_probability(raw_prob: float) -> float:
    """Apply Becker (2026) longshot-bias calibration to a raw probability.

    Linear-interpolates between LONGSHOT_CALIBRATION anchor points.

    Examples
    --------
    >>> calibrate_probability(0.05)
    0.0418
    >>> calibrate_probability(0.50)
    0.5
    """
    # TODO(phase01): linear interp per docs/MONTE-CARLO.md
    raise NotImplementedError("calibrate_probability — implement in Phase 01")


def compute_quantile_bands(
    paths: SimulationPaths,
    target_extractor: callable,
    quantiles: tuple[float, ...] = CONFIDENCE_LEVELS,
) -> dict[float, np.ndarray]:
    """Compute percentile bands across simulation paths for a target metric.

    Parameters
    ----------
    paths : np.ndarray
        Output of monte_carlo_simulate, shape (n_sims, n_steps+1).
    target_extractor : callable
        Function (path -> scalar series) for the metric to band.
    quantiles : tuple of float
        Quantile levels in [0, 1].
    """
    # TODO(phase01)
    raise NotImplementedError("compute_quantile_bands — implement in Phase 01")
