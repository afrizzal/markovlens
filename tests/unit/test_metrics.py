"""Stubs for MAPE, Brier score, log-loss."""
from __future__ import annotations

import numpy as np
import pytest


def test_mape_known_value():
    from core.metrics import mape
    actual = np.array([100.0, 200.0])
    forecast = np.array([110.0, 190.0])
    # (|10|/100 + |10|/200) / 2 * 100 = (0.1 + 0.05) / 2 * 100 = 7.5
    assert mape(actual, forecast) == pytest.approx(7.5, abs=1e-9)


def test_mape_skips_zero_actual(caplog):
    from core.metrics import mape
    actual = np.array([0.0, 100.0, 200.0])
    forecast = np.array([5.0, 110.0, 190.0])
    with caplog.at_level("WARNING"):
        result = mape(actual, forecast)
    # only rows 1 and 2 counted: (10/100 + 10/200)/2 * 100 = 7.5
    assert result == pytest.approx(7.5, abs=1e-9)


def test_brier_known_value():
    from core.metrics import brier_score
    forecast_prob = np.array([[0.7, 0.3], [0.4, 0.6]])
    actual = np.array([[1, 0], [0, 1]])
    # ((0.7-1)^2 + (0.3-0)^2)/2 + ((0.4-0)^2 + (0.6-1)^2)/2 — then mean
    # = (0.09 + 0.09)/2 + (0.16 + 0.16)/2 = 0.09 + 0.16 = 0.25 — mean over rows = 0.125
    assert brier_score(forecast_prob, actual) == pytest.approx(0.125, abs=1e-6)


def test_log_loss_known_value():
    from core.metrics import log_loss
    forecast_prob = np.array([[0.9, 0.1], [0.2, 0.8]])
    actual = np.array([[1, 0], [0, 1]])
    # -mean(log(0.9) + log(0.8))
    expected = -(np.log(0.9) + np.log(0.8)) / 2
    assert log_loss(forecast_prob, actual) == pytest.approx(expected, abs=1e-6)


def test_log_loss_clips_zeros():
    from core.metrics import log_loss
    forecast_prob = np.array([[1.0, 0.0]])
    actual = np.array([[0, 1]])  # predicted prob 0 for true class
    result = log_loss(forecast_prob, actual)
    assert np.isfinite(result)  # must not blow up to inf
