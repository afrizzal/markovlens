"""Shared pytest fixtures."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def sample_2x2_matrix() -> np.ndarray:
    """A valid 2x2 transition matrix for trivial tests."""
    return np.array([[0.7, 0.3], [0.4, 0.6]])


@pytest.fixture
def sample_4x4_chan_matrix() -> np.ndarray:
    """The 4-provider matrix from Chan 2015 numerical example."""
    return np.array([
        [0.98230, 0.00753, 0.00464, 0.00552],
        [0.01158, 0.96161, 0.02489, 0.00192],
        [0.01442, 0.01105, 0.95721, 0.01732],
        [0.01978, 0.01122, 0.01364, 0.95536],
    ])


@pytest.fixture
def temp_duckdb_path(tmp_path: Path) -> Path:
    """Per-test isolated DuckDB file."""
    return tmp_path / "test.duckdb"
