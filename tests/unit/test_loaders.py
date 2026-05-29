"""Stubs for core/io/loaders.py validate_transitions_df."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_transitions_df_missing_col():
    from core.io.loaders import validate_transitions_df
    df = pd.DataFrame({"entity_id": ["a"], "period": [1], "from_state": ["x"]})
    # missing 'to_state'
    with pytest.raises(ValueError, match="to_state"):
        validate_transitions_df(df)


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_transitions_df_accepts_valid():
    from core.io.loaders import validate_transitions_df
    df = pd.DataFrame({
        "entity_id": ["a", "b"],
        "period":    [1, 1],
        "from_state":["x", "y"],
        "to_state":  ["y", "x"],
    })
    validate_transitions_df(df)  # should not raise


@pytest.mark.skip(reason="Wave 0 stub — implementation in later wave")
def test_validate_transitions_df_rejects_nan_entity():
    from core.io.loaders import validate_transitions_df
    df = pd.DataFrame({
        "entity_id": [np.nan, "b"],
        "period":    [1, 1],
        "from_state":["x", "y"],
        "to_state":  ["y", "x"],
    })
    with pytest.raises(ValueError):
        validate_transitions_df(df)
