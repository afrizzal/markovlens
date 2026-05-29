"""Stubs for core/db/serialization.py ndarray↔JSON helpers."""
from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_ndarray_json_roundtrip():
    from core.db.serialization import ndarray_to_json, json_to_ndarray
    arr = np.array([[0.1, 0.9], [0.5, 0.5]], dtype=np.float64)
    s = ndarray_to_json(arr)
    arr_back = json_to_ndarray(s)
    np.testing.assert_array_equal(arr, arr_back)
    assert arr_back.dtype == np.float64


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_ndarray_json_roundtrip_3d():
    from core.db.serialization import ndarray_to_json, json_to_ndarray
    arr = np.random.default_rng(42).random((4, 3, 3))
    s = ndarray_to_json(arr)
    arr_back = json_to_ndarray(s)
    np.testing.assert_allclose(arr, arr_back)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_serializer_rejects_nan():
    from core.db.serialization import ndarray_to_json
    arr = np.array([0.5, np.nan, 0.5])
    with pytest.raises(ValueError, match="NaN|Inf"):
        ndarray_to_json(arr)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_serializer_rejects_inf():
    from core.db.serialization import ndarray_to_json
    arr = np.array([0.5, np.inf, 0.5])
    with pytest.raises(ValueError, match="NaN|Inf"):
        ndarray_to_json(arr)
