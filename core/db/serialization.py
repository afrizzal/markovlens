"""ndarray to JSON helpers for DuckDB persistence.

Per D-24: NaN and Inf are rejected at the boundary — silent NaN persistence
would corrupt downstream forecasts and validation.
"""
from __future__ import annotations

import json

import numpy as np


def ndarray_to_json(arr: np.ndarray) -> str:
    """Serialize an ndarray to a JSON string for DuckDB JSON columns.

    Parameters
    ----------
    arr : np.ndarray
        Array to serialize. Must contain no NaN or Inf values.

    Returns
    -------
    str
        JSON string representation (nested list).

    Raises
    ------
    ValueError
        If arr contains NaN or Inf values.

    Examples
    --------
    >>> ndarray_to_json(np.array([0.5, 0.5]))
    '[0.5, 0.5]'
    """
    if not np.isfinite(arr).all():
        raise ValueError(
            "Array contains NaN or Inf values — cannot serialize to JSON. "
            "Validate upstream computation."
        )
    return json.dumps(arr.tolist())


def json_to_ndarray(s: str, dtype: np.dtype | type = np.float64) -> np.ndarray:
    """Deserialize a JSON string (nested list) back to an ndarray.

    Parameters
    ----------
    s : str
        JSON string produced by ndarray_to_json.
    dtype : np.dtype | type
        Target NumPy dtype. Defaults to np.float64 to match LONGSHOT_CALIBRATION
        and validate_transition_matrix expectations.

    Returns
    -------
    np.ndarray
        Reconstructed array.

    Examples
    --------
    >>> json_to_ndarray('[0.5, 0.5]')
    array([0.5, 0.5])
    """
    return np.array(json.loads(s), dtype=dtype)
