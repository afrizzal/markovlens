"""Query helpers — all SQL wrapped here, never inline in app/ or domains/."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd

from core.exceptions import DatasetNotFoundError
from core.io.loaders import validate_transitions_df
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
    conn: duckdb.DuckDBPyConnection,
    domain: str,
    name: str,
    source_path: str,
    row_count: int,
    n_states: int,
    *,
    dataset_id: str | None = None,
    metadata: dict | None = None,
) -> str:
    """Insert a new dataset row and return its id.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection.
    domain : str
        Dataset domain, e.g. 'brand_share' or 'churn'.
    name : str
        Human-readable dataset name.
    source_path : str
        Relative path to the source file.
    row_count : int
        Number of transition rows.
    n_states : int
        Number of distinct states.
    dataset_id : str | None
        Optional fixed id (e.g. for idempotent seed scripts). Auto-generated if None.
    metadata : dict | None
        Optional metadata dict, stored as JSON.

    Returns
    -------
    str
        The dataset id.
    """
    ds_id = dataset_id or str(uuid.uuid4())
    meta_json = json.dumps(metadata) if metadata else None
    conn.execute(
        "INSERT INTO datasets (id, domain, name, source_path, row_count, n_states, metadata_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [ds_id, domain, name, source_path, row_count, n_states, meta_json],
    )
    return ds_id


def list_datasets(
    conn: duckdb.DuckDBPyConnection,
    domain: str | None = None,
) -> list[Dataset]:
    """List registered datasets, optionally filtered by domain.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection.
    domain : str | None
        Optional domain filter.

    Returns
    -------
    list[Dataset]
        All matching datasets, ordered by created_at descending.
    """
    if domain is None:
        df = conn.execute(
            "SELECT id, domain, name, source_path, row_count, n_states "
            "FROM datasets ORDER BY created_at DESC"
        ).df()
    else:
        df = conn.execute(
            "SELECT id, domain, name, source_path, row_count, n_states "
            "FROM datasets WHERE domain = ? ORDER BY created_at DESC",
            [domain],
        ).df()

    return [
        Dataset(
            id=row["id"],
            domain=row["domain"],
            name=row["name"],
            source_path=row["source_path"],
            row_count=int(row["row_count"] or 0),
            n_states=int(row["n_states"] or 0),
        )
        for _, row in df.iterrows()
    ]


def get_dataset(conn: duckdb.DuckDBPyConnection, dataset_id: str) -> Dataset:
    """Fetch a single dataset by id.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection.
    dataset_id : str
        Dataset identifier.

    Returns
    -------
    Dataset
        The matching dataset.

    Raises
    ------
    DatasetNotFoundError
        If no dataset with the given id exists.
    """
    df = conn.execute(
        "SELECT id, domain, name, source_path, row_count, n_states FROM datasets WHERE id = ?",
        [dataset_id],
    ).df()
    if df.empty:
        raise DatasetNotFoundError(
            f"Dataset '{dataset_id}' not found. "
            "Register it first via register_dataset() or scripts/seed_data.py."
        )
    row = df.iloc[0]
    return Dataset(
        id=row["id"],
        domain=row["domain"],
        name=row["name"],
        source_path=row["source_path"],
        row_count=int(row["row_count"] or 0),
        n_states=int(row["n_states"] or 0),
    )


def load_transitions(
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    period_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Load raw transitions for a dataset, optionally filtered by period range.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection.
    dataset_id : str
        Dataset identifier.
    period_range : tuple[int, int] | None
        Inclusive (min_period, max_period) filter. None = all periods.

    Returns
    -------
    pd.DataFrame
        Columns: entity_id, period, from_state, to_state, weight.
    """
    if period_range is None:
        return conn.execute(
            "SELECT entity_id, period, from_state, to_state, weight "
            "FROM transitions WHERE dataset_id = ? ORDER BY period",
            [dataset_id],
        ).df()
    min_p, max_p = period_range
    return conn.execute(
        "SELECT entity_id, period, from_state, to_state, weight "
        "FROM transitions WHERE dataset_id = ? AND period BETWEEN ? AND ? ORDER BY period",
        [dataset_id, min_p, max_p],
    ).df()


def bulk_insert_transitions(
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    df: pd.DataFrame,
) -> int:
    """Bulk insert transitions for a dataset. Returns row count inserted.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection.
    dataset_id : str
        Dataset identifier (must already exist in datasets table).
    df : pd.DataFrame
        Long-format transitions. Required columns: entity_id, period, from_state, to_state.
        Optional: weight (defaults to 1.0 per schema).

    Returns
    -------
    int
        Number of rows inserted.

    Raises
    ------
    ValueError
        If required columns are missing or contain NaN.
    """
    validate_transitions_df(df)
    insert_df = df.assign(dataset_id=dataset_id)[
        ["dataset_id", "entity_id", "period", "from_state", "to_state"]
        + (["weight"] if "weight" in df.columns else [])
    ]
    conn.register("_bulk_insert_tmp", insert_df)
    try:
        conn.execute("INSERT INTO transitions SELECT * FROM _bulk_insert_tmp")
    finally:
        conn.unregister("_bulk_insert_tmp")
    return len(insert_df)


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
        counts[i, j] = round(float(row["n"]))

    row_sums = counts.sum(axis=1, keepdims=True)
    safe_row_sums = np.where(row_sums == 0, 1, row_sums)
    matrix = (counts / safe_row_sums).astype(np.float64)

    # States with no observed outgoing transitions become absorbing self-loops,
    # preserving the row-stochastic invariant (every row must sum to 1.0).
    zero_rows = np.flatnonzero(row_sums.ravel() == 0)
    matrix[zero_rows, zero_rows] = 1.0

    validate_transition_matrix(matrix, transition_counts=counts)
    return matrix, counts
