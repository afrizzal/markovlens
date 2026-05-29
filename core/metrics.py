"""Forecast accuracy metrics — MAPE, Brier, log-loss."""

from __future__ import annotations

import logging

import numpy as np


def mape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Mean Absolute Percentage Error.

    Per Claude's Discretion (CONTEXT.md Pitfall 7): rows where actual == 0 are
    SKIPPED with a logging.WARNING — division by zero would be undefined.

    Parameters
    ----------
    actual : np.ndarray
        Ground-truth values.
    forecast : np.ndarray
        Predicted values, same shape as actual.

    Returns
    -------
    float
        Mean absolute percentage error in 0-100+ range. Lower is better.
        Returns 0.0 if every actual is zero.

    Examples
    --------
    >>> mape(np.array([100, 200]), np.array([110, 190]))
    7.5
    """
    actual = np.asarray(actual, dtype=np.float64)
    forecast = np.asarray(forecast, dtype=np.float64)
    mask = actual != 0
    if (~mask).any():
        logging.getLogger(__name__).warning(
            "MAPE: skipping %d zero-actual rows out of %d total",
            int((~mask).sum()),
            int(actual.size),
        )
    if not mask.any():
        return 0.0
    pct_err = np.abs((actual[mask] - forecast[mask]) / actual[mask])
    return float(pct_err.mean() * 100)


def brier_score(forecast_prob: np.ndarray, actual: np.ndarray) -> float:
    """Brier score for probabilistic forecasts.

    Per docs/MONTE-CARLO.md: mean squared error between probability vector
    and one-hot actual vector. Range [0, 1] for 2-class; range [0, 2] in
    multi-class formulation (this implementation uses mean-per-row).

    Parameters
    ----------
    forecast_prob : np.ndarray
        Predicted probabilities, shape (n_samples, n_classes).
    actual : np.ndarray
        One-hot true labels, shape (n_samples, n_classes).

    Returns
    -------
    float
        Mean Brier score across rows. 0 = perfect.
    """
    forecast_prob = np.asarray(forecast_prob, dtype=np.float64)
    actual = np.asarray(actual, dtype=np.float64)
    squared_err = (forecast_prob - actual) ** 2
    return float(squared_err.mean())


def log_loss(forecast_prob: np.ndarray, actual: np.ndarray, eps: float = 1e-15) -> float:
    """Log loss (cross-entropy).

    Clips probabilities to [eps, 1-eps] before log() to avoid -inf when
    forecast_prob has zeros (Pitfall 7-adjacent — same eps technique as sklearn).

    Parameters
    ----------
    forecast_prob : np.ndarray
        Predicted probabilities, shape (n_samples, n_classes).
    actual : np.ndarray
        One-hot true labels, shape (n_samples, n_classes).
    eps : float
        Clipping epsilon to avoid log(0).

    Returns
    -------
    float
        Mean negative log-likelihood across rows.
    """
    forecast_prob = np.asarray(forecast_prob, dtype=np.float64)
    actual = np.asarray(actual, dtype=np.float64)
    clipped = np.clip(forecast_prob, eps, 1.0 - eps)
    per_row = -(actual * np.log(clipped)).sum(axis=1)
    return float(per_row.mean())
