"""Monte Carlo simulation + longshot-bias calibration (Becker 2026)."""
from __future__ import annotations

from collections.abc import Callable
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

_CALIBRATION_KEYS = np.array(sorted(LONGSHOT_CALIBRATION.keys()), dtype=np.float64)
_CALIBRATION_VALUES = np.array(
    [LONGSHOT_CALIBRATION[k] for k in sorted(LONGSHOT_CALIBRATION)],
    dtype=np.float64,
)


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
    start_state: int | np.ndarray,
    n_steps: int = 12,
    n_simulations: int = 10_000,
    seed: int | None = 42,
) -> SimulationPaths:
    """Run vectorized Monte Carlo over a transition matrix.

    Per D-11..D-16:
    - Cumsum + inverse-CDF vectorized sampling (~50ms target for 10k x 12 steps).
    - rng = np.random.default_rng(seed) — never legacy np.random.seed().
    - Return dtype int64, shape (n_simulations, n_steps + 1) — full paths.
    - start_state may be int (single state) or ndarray (probability distribution).
    - cum_matrix[:, -1] = 1.0 mandatory float boundary fix (D-12).

    Parameters
    ----------
    matrix : np.ndarray
        Validated transition matrix, shape (n_states, n_states).
    start_state : int | np.ndarray
        Initial state index or probability distribution over states.
    n_steps : int
        Number of forward steps.
    n_simulations : int
        Number of independent paths.
    seed : int | None
        RNG seed for reproducibility.

    Returns
    -------
    np.ndarray
        Shape (n_simulations, n_steps + 1), dtype int64.
    """
    rng = np.random.default_rng(seed)  # D-15
    n_states = matrix.shape[0]

    # D-13: normalize start_state to probability distribution
    if isinstance(start_state, (int, np.integer)):
        init_dist = np.zeros(n_states, dtype=np.float64)
        init_dist[int(start_state)] = 1.0
    else:
        init_dist = np.asarray(start_state, dtype=np.float64)
        init_dist = init_dist / init_dist.sum()

    paths = np.zeros((n_simulations, n_steps + 1), dtype=np.int64)  # D-14
    paths[:, 0] = rng.choice(n_states, size=n_simulations, p=init_dist)

    cum_matrix = matrix.cumsum(axis=1)
    cum_matrix[:, -1] = 1.0  # D-12 mandatory float boundary fix

    for t in range(n_steps):
        u = rng.random(n_simulations)
        current_states = paths[:, t]
        cum_probs = cum_matrix[current_states]
        paths[:, t + 1] = (u[:, None] < cum_probs).argmax(axis=1)

    return paths


def calibrate_probability(raw_prob: float) -> float:
    """Apply Becker (2026) longshot-bias calibration via linear interpolation.

    Per D-17: np.interp() over sorted LONGSHOT_CALIBRATION keys.
    np.interp clamps to value range at boundaries (returns values[0] for x < xp[0],
    values[-1] for x > xp[-1]).

    Examples
    --------
    >>> calibrate_probability(0.05)
    0.0418
    >>> calibrate_probability(0.50)
    0.5
    """
    return float(np.interp(raw_prob, _CALIBRATION_KEYS, _CALIBRATION_VALUES))


def compute_quantile_bands(
    paths: SimulationPaths,
    target_extractor: Callable[[np.ndarray], np.ndarray],
    quantiles: tuple[float, ...] = CONFIDENCE_LEVELS,
) -> dict[float, np.ndarray]:
    """Compute percentile bands across simulation paths for a target metric.

    Per ENG-07: target_extractor is applied to each path BEFORE percentile is taken,
    not after — never compute percentile of raw state indices (would be meaningless
    for ordinal state numbering).

    Parameters
    ----------
    paths : np.ndarray
        Output of monte_carlo_simulate, shape (n_sims, n_steps + 1).
    target_extractor : Callable[[np.ndarray], np.ndarray]
        Function (path_array -> per-sim/per-step values). Applied to the entire
        (n_sims, n_steps+1) block; must broadcast or operate elementwise to
        return a 2-D ndarray with the same number of columns (one value per step).
    quantiles : tuple of float
        Quantile levels in [0, 1].

    Returns
    -------
    dict[float, np.ndarray]
        Map of quantile -> per-step series of shape (n_steps + 1,).

    Raises
    ------
    ValueError
        If `target_extractor(paths)` returns a 1-D array — quantile bands require
        a per-simulation distribution per time step.
    """
    extracted = target_extractor(paths)
    if extracted.ndim != 2:
        raise ValueError(
            f"target_extractor must return a 2-D ndarray (n_sims, n_steps+1); "
            f"got ndim={extracted.ndim}. Reduce within the extractor only if it "
            f"preserves the time axis."
        )
    return {
        float(q): np.percentile(extracted, q * 100, axis=0)
        for q in quantiles
    }
