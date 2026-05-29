"""Stubs for core/io/loaders.py validate_transitions_df."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def test_validate_transitions_df_missing_col():
    from core.io.loaders import validate_transitions_df
    df = pd.DataFrame({"entity_id": ["a"], "period": [1], "from_state": ["x"]})
    # missing 'to_state'
    with pytest.raises(ValueError, match="to_state"):
        validate_transitions_df(df)


def test_validate_transitions_df_accepts_valid():
    from core.io.loaders import validate_transitions_df
    df = pd.DataFrame({
        "entity_id": ["a", "b"],
        "period":    [1, 1],
        "from_state":["x", "y"],
        "to_state":  ["y", "x"],
    })
    validate_transitions_df(df)  # should not raise


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
