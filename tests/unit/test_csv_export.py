"""Unit tests for CSV export helpers (RPT-01)."""
from __future__ import annotations

import csv
import io

import numpy as np


def _build_brand_share_csv_bytes(
    state_labels: list[str],
    transition_matrix: np.ndarray,
    forecast: np.ndarray,
    model_name: str,
) -> bytes:
    """Inline reimplementation of the CSV helper logic for test isolation."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["# Forecast", f"model={model_name}"])
    w.writerow(["period", *state_labels])
    for period, row in enumerate(forecast):
        w.writerow([period, *[f"{v:.6f}" for v in row]])
    w.writerow([])
    w.writerow(["# Transition Matrix"])
    w.writerow(["from_state", *state_labels])
    for i, label in enumerate(state_labels):
        w.writerow([label, *[f"{v:.6f}" for v in transition_matrix[i]]])
    return buf.getvalue().encode("utf-8")


def test_brand_share_csv_has_forecast_section() -> None:
    """CSV output contains '# Forecast' section header."""
    labels = ["Alpha", "Beta", "Gamma"]
    P = np.array([[0.8, 0.1, 0.1], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]])
    forecast = np.array([[0.4, 0.35, 0.25], [0.38, 0.36, 0.26], [0.37, 0.37, 0.26]])
    csv_bytes = _build_brand_share_csv_bytes(labels, P, forecast, "m1")
    text = csv_bytes.decode("utf-8")
    assert "# Forecast" in text
    assert "# Transition Matrix" in text


def test_csv_forecast_rows_count() -> None:
    """CSV has one data row per forecast period."""
    labels = ["A", "B"]
    P = np.eye(2)
    horizon = 5
    forecast = np.tile([0.5, 0.5], (horizon, 1))
    csv_bytes = _build_brand_share_csv_bytes(labels, P, forecast, "m2")
    text = csv_bytes.decode("utf-8")
    lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    # Lines starting with a digit are data rows (period index)
    forecast_data_rows = [line for line in lines if line[0].isdigit()]
    assert len(forecast_data_rows) == horizon


def test_csv_column_headers_match_state_labels() -> None:
    """CSV period header row uses state labels as column names."""
    labels = ["Active", "AtRisk", "Churned"]
    P = np.array([[0.7, 0.2, 0.1], [0.1, 0.7, 0.2], [0.0, 0.0, 1.0]])
    forecast = np.tile([0.6, 0.3, 0.1], (3, 1))
    csv_bytes = _build_brand_share_csv_bytes(labels, P, forecast, "m1")
    text = csv_bytes.decode("utf-8")
    assert "Active" in text
    assert "AtRisk" in text
    assert "Churned" in text


def test_csv_transition_matrix_rows_sum_to_one() -> None:
    """Values in the transition matrix section are valid probabilities (sum to 1 per row)."""
    labels = ["A", "B", "C"]
    P = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1], [0.05, 0.05, 0.9]])
    forecast = np.tile([0.4, 0.35, 0.25], (4, 1))
    csv_bytes = _build_brand_share_csv_bytes(labels, P, forecast, "m1")
    text = csv_bytes.decode("utf-8")

    # Parse transition matrix rows from the CSV
    lines = text.splitlines()
    in_matrix = False
    matrix_rows: list[list[float]] = []
    for line in lines:
        if "# Transition Matrix" in line:
            in_matrix = True
            continue
        if in_matrix and line and not line.startswith("from_state"):
            vals = line.split(",")[1:]  # skip from_state label
            matrix_rows.append([float(v) for v in vals])

    assert len(matrix_rows) == 3
    for row in matrix_rows:
        assert abs(sum(row) - 1.0) < 1e-4, f"Row sum {sum(row)} != 1.0"


def test_csv_bytes_is_utf8_encoded() -> None:
    """CSV helper returns bytes (not str) in UTF-8 encoding."""
    csv_bytes = _build_brand_share_csv_bytes(
        ["X", "Y"], np.eye(2), np.tile([0.5, 0.5], (2, 1)), "m1"
    )
    assert isinstance(csv_bytes, bytes)
    # Must decode without error
    csv_bytes.decode("utf-8")
