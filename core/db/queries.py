"""Query helpers — all SQL wrapped here, never inline in app/ or domains/."""
from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd

from core.models import validate_transition_matrix


@dataclass(frozen=True)
class Dataset:
    """Domain object representing a registered dataset."""

    id: str
    domain: str
    name: str
    source_path: str
    row_count: int
    n_states: int


def register_dataset(
    domain: str,
    name: str,
    source_path: str,
    row_count: int,
    n_states: int,
    metadata: dict | None = None,
) -> str:
    """Insert a new dataset row, return its id."""
    # TODO(phase02)
    raise NotImplementedError("register_dataset — implement in Phase 02")


def list_datasets(domain: str | None = None) -> list[Dataset]:
    """List registered datasets, optionally filtered by domain."""
    # TODO(phase02)
    raise NotImplementedError("list_datasets — implement in Phase 02")


def get_dataset(dataset_id: str) -> Dataset:
    """Fetch a single dataset by id. Raises DatasetNotFoundError if missing."""
    # TODO(phase02)
    raise NotImplementedError("get_dataset — implement in Phase 02")


def load_transitions(dataset_id: str, period_range: tuple[int, int] | None = None) -> pd.DataFrame:
    """Load raw transitions for a dataset, optionally filtered by period range."""
    # TODO(phase02)
    raise NotImplementedError("load_transitions — implement in Phase 02")


def bulk_insert_transitions(dataset_id: str, df: pd.DataFrame) -> int:
    """Bulk insert transitions for a dataset. Returns row count inserted."""
    # TODO(phase02)
    raise NotImplementedError("bulk_insert_transitions — implement in Phase 02")


def build_transition_matrix(
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    *,
    period: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Aggregate transitions for a dataset into a row-stochastic matrix + counts.

    Per docs/DATABASE.md "Build m1 transition matrix in pure SQL" pattern + DATA-03.

    Uses parameterized query (no SQL injection risk). Discovers states by sorting the
    union of from_state and to_state values present in the data. Normalizes each row
    by its row sum (rows with zero observations stay zero-filled, division by 1).

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection (caller-managed). Tests should pass a per-test
        connection, NOT the singleton (Pitfall 6).
    dataset_id : str
        Dataset identifier in the datasets table.
    period : int | None
        Optional period filter — if None, aggregates across all periods (m1 style).

    Returns
    -------
    matrix : np.ndarray
        Shape (n_states, n_states), dtype float64, row-stochastic.
    counts : np.ndarray
        Shape (n_states, n_states), dtype int64, raw observation counts (after
        weight summation, rounded to int).
    """
    if period is None:
        df = conn.execute(
            """
            SELECT from_state, to_state, SUM(weight) AS n
            FROM transitions
            WHERE dataset_id = ?
            GROUP BY from_state, to_state
            """,
            [dataset_id],
        ).df()
    else:
        df = conn.execute(
            """
            SELECT from_state, to_state, SUM(weight) AS n
            FROM transitions
            WHERE dataset_id = ? AND period = ?
            GROUP BY from_state, to_state
            """,
            [dataset_id, period],
        ).df()

    if df.empty:
        raise ValueError(
            f"No transitions found for dataset_id={dataset_id!r}"
            + (f", period={period}" if period is not None else "")
        )

    states = sorted(set(df["from_state"]) | set(df["to_state"]))
    n_states = len(states)
    state_idx = {s: i for i, s in enumerate(states)}

    counts = np.zeros((n_states, n_states), dtype=np.int64)
    for _, row in df.iterrows():
        i = state_idx[row["from_state"]]
        j = state_idx[row["to_state"]]
        counts[i, j] = int(round(float(row["n"])))

    row_sums = counts.sum(axis=1, keepdims=True)
    safe_row_sums = np.where(row_sums == 0, 1, row_sums)
    matrix = (counts / safe_row_sums).astype(np.float64)

    # States with no observed outgoing transitions become absorbing self-loops,
    # preserving the row-stochastic invariant (every row must sum to 1.0).
    zero_rows = np.flatnonzero(row_sums.ravel() == 0)
    matrix[zero_rows, zero_rows] = 1.0

    validate_transition_matrix(matrix, transition_counts=counts)
    return matrix, counts
