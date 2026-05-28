"""Forecast accuracy metrics — MAPE, Brier, log-loss."""
from __future__ import annotations

import numpy as np


def mape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Mean Absolute Percentage Error.

    Returns percentage (0-100+). Lower is better.

    Examples
    --------
    >>> mape(np.array([100, 200]), np.array([110, 190]))
    7.5
    """
    # TODO(phase01)
    raise NotImplementedError("mape — implement in Phase 01")


def brier_score(forecast_prob: np.ndarray, actual: np.ndarray) -> float:
    """Brier score for probabilistic forecasts.

    Range [0, 1]. 0 = perfect, 0.25 = random guess on binary outcomes.
    """
    # TODO(phase01)
    raise NotImplementedError("brier_score — implement in Phase 01")


def log_loss(forecast_prob: np.ndarray, actual: np.ndarray, eps: float = 1e-15) -> float:
    """Log loss (cross-entropy)."""
    # TODO(phase01)
    raise NotImplementedError("log_loss — implement in Phase 01")
