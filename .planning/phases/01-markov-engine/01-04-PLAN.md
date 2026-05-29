---
phase: 01-markov-engine
plan: 04
type: execute
wave: 3
depends_on:
  - 02
files_modified:
  - core/db/serialization.py
  - core/db/queries.py
  - core/io/loaders.py
  - tests/unit/test_serialization.py
  - tests/unit/test_loaders.py
  - tests/integration/test_queries.py
autonomous: true
requirements:
  - DATA-01
  - DATA-03
must_haves:
  truths:
    - "core/db/serialization.py exists with ndarray_to_json and json_to_ndarray functions (D-24)"
    - "Serialization rejects NaN and Inf at boundary by raising ValueError (D-24)"
    - "ndarray to JSON to ndarray round-trips with bit-identity for float64 1D, 2D, and 3D arrays"
    - "build_transition_matrix queries DuckDB via GROUP BY and returns (matrix: float64, counts: int64) tuple"
    - "build_transition_matrix matrix has rows summing to 1.0 within PROBABILITY_TOLERANCE"
    - "build_transition_matrix uses parameterized query — never f-string SQL injection"
    - "validate_transitions_df raises ValueError when required columns missing (DATA-01)"
  artifacts:
    - path: "core/db/serialization.py"
      provides: "ndarray_to_json, json_to_ndarray"
      contains: "def ndarray_to_json"
    - path: "core/db/queries.py"
      provides: "build_transition_matrix (added to existing file)"
      contains: "def build_transition_matrix"
    - path: "core/io/loaders.py"
      provides: "validate_transitions_df (added to existing file)"
      contains: "def validate_transitions_df"
  key_links:
    - from: "core/db/queries.py build_transition_matrix"
      to: "core.models.validate_transition_matrix"
      via: "validate after building"
      pattern: "validate_transition_matrix\\(matrix"
    - from: "core/db/queries.py build_transition_matrix"
      to: "duckdb GROUP BY query"
      via: "conn.execute parameterized query"
      pattern: "GROUP BY from_state, to_state"
    - from: "core/db/serialization.py ndarray_to_json"
      to: "ValueError for NaN/Inf"
      via: "np.isfinite check before json.dumps"
      pattern: "raise ValueError"
---

<objective>
Implement the DuckDB data layer: serialization helpers, build_transition_matrix() query, and validate_transitions_df() helper.

Purpose: Phase 02 (Brand Share UI) will read matrices and forecasts from DuckDB. Without serialization + build_transition_matrix, no cached matrices can round-trip and the seed script has nowhere to write reference forecasts. validate_transitions_df is needed by the seed script and Phase 02 loaders.

Output:
- New `core/db/serialization.py` module (D-24)
- `build_transition_matrix()` added to `core/db/queries.py` (DATA-03)
- `validate_transitions_df()` added to `core/io/loaders.py` (DATA-01)
- Unit tests for serialization round-trip and DATA-01 pass green
- Integration tests for DATA-03 build_transition_matrix paths pass green
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-markov-engine/01-CONTEXT.md
@.planning/phases/01-markov-engine/01-RESEARCH.md
@.planning/phases/01-markov-engine/01-VALIDATION.md
@.planning/phases/01-markov-engine/01-02-SUMMARY.md
@core/db/connection.py
@core/db/queries.py
@core/db/schema.sql
@core/io/loaders.py
@core/models.py
@tests/unit/test_serialization.py
@tests/unit/test_loaders.py
@tests/integration/test_queries.py
@.claude/rules/data-storage.md

<interfaces>
Existing contracts (do NOT change):

```python
# core/db/connection.py — singleton pattern
def get_connection() -> duckdb.DuckDBPyConnection: ...
def init_schema(conn) -> None: ...
def close_connection() -> None: ...

# core/db/queries.py — existing Dataset dataclass + Phase 02 stubs that stay
@dataclass(frozen=True)
class Dataset:
    id: str
    domain: str
    name: str
    source_path: str
    row_count: int
    n_states: int

# Phase 02 functions (DO NOT IMPLEMENT in Phase 01): register_dataset, list_datasets,
# get_dataset, load_transitions, bulk_insert_transitions — leave their NotImplementedError stubs alone.

# core/models.py — already implemented in Plan 02
from core.models import validate_transition_matrix
```

NEW MODULE in this plan: `core/db/serialization.py` (per D-24)

NEW FUNCTION (added to existing file): `build_transition_matrix(conn, dataset_id, *, period=None) -> tuple[np.ndarray, np.ndarray]` in `core/db/queries.py`

NEW FUNCTION (added to existing file): `validate_transitions_df(df) -> None` in `core/io/loaders.py` (DATA-01 minimal scope for Phase 01 per Open Question 1)
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Create core/db/serialization.py module (D-24)</name>
  <read_first>
    - core/db/queries.py (existing patterns — sibling module style)
    - tests/unit/test_serialization.py (read all 4 stubs — exact function signatures expected)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (section "Pattern 8: Serialization Helpers")
    - .planning/phases/01-markov-engine/01-CONTEXT.md (D-24)
  </read_first>
  <behavior>
    - ndarray_to_json(np.array([[0.1, 0.9], [0.5, 0.5]])) returns a JSON string that, parsed back via json_to_ndarray with dtype=float64, equals the original array bit-identically.
    - ndarray_to_json handles 3D arrays (e.g. (4, 3, 3)) — round-trips cleanly.
    - ndarray_to_json(arr containing np.nan) raises ValueError with message containing "NaN" or "Inf".
    - ndarray_to_json(arr containing np.inf) raises ValueError with message containing "NaN" or "Inf".
    - json_to_ndarray accepts optional dtype kwarg (default np.float64).
  </behavior>
  <action>
Create new file `core/db/serialization.py` with this content:

```python
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
```

Un-skip all 4 tests in `tests/unit/test_serialization.py` (remove `@pytest.mark.skip(reason="Wave 0 stub...")` from each).

Run: `uv run pytest tests/unit/test_serialization.py -x -q` — all 4 tests must pass.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_serialization.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - File `core/db/serialization.py` exists.
    - `grep -n "def ndarray_to_json" core/db/serialization.py` returns 1 match.
    - `grep -n "def json_to_ndarray" core/db/serialization.py` returns 1 match.
    - `grep -n "np\\.isfinite" core/db/serialization.py` returns 1 match (NaN/Inf guard present).
    - `grep -n "raise ValueError" core/db/serialization.py` returns at least 1 match.
    - `uv run pytest tests/unit/test_serialization.py -x -q` exits 0 with `4 passed`.
    - `grep -c "@pytest.mark.skip" tests/unit/test_serialization.py` returns 0.
  </acceptance_criteria>
  <done>
    Serialization module created and round-trip verified for 1D, 2D, and 3D arrays. NaN/Inf rejected at boundary.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement validate_transitions_df() in core/io/loaders.py (DATA-01)</name>
  <read_first>
    - core/io/loaders.py (current Phase 02 stubs — leave them, add validate_transitions_df)
    - tests/unit/test_loaders.py (read all 3 stub assertions exactly)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (Open Question 1 — recommended minimal Phase 01 scope)
    - .claude/skills/dataset-prepper/SKILL.md (canonical format — entity_id, period, from_state, to_state, weight)
  </read_first>
  <behavior>
    - validate_transitions_df(df) returns None silently if df has required columns and no NaN in entity_id/from_state/to_state.
    - Missing column 'to_state' raises ValueError with "to_state" in message.
    - NaN in entity_id raises ValueError.
    - The required columns are: entity_id, period, from_state, to_state.
  </behavior>
  <action>
Add this function to `core/io/loaders.py` BELOW the existing Phase 02 stubs (DO NOT modify or remove `load_brand_share_csv` or `load_churn_csv`). Ensure both `import numpy as np` AND `import pandas as pd` are present at the top of the file (the function signature uses `pd.DataFrame` and the body calls `df[col].isna()` — without pandas imported, the module will fail at import time with NameError on pd):

```python
REQUIRED_TRANSITION_COLUMNS: frozenset[str] = frozenset(
    {"entity_id", "period", "from_state", "to_state"}
)


def validate_transitions_df(df: pd.DataFrame) -> None:
    """Validate a long-format transitions DataFrame before DuckDB insertion.

    Phase 01 minimal scope (per RESEARCH.md Open Question 1):
    - Required columns: entity_id, period, from_state, to_state
    - No NaN in identifier or state columns (would corrupt transition matrix)
    - 'weight' is optional (defaults to 1.0 at INSERT time per schema)

    Parameters
    ----------
    df : pd.DataFrame
        Long-format transitions to validate.

    Raises
    ------
    ValueError
        If a required column is missing or NaN appears in entity_id/from_state/to_state.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "entity_id": ["a"], "period": [1], "from_state": ["x"], "to_state": ["y"],
    ... })
    >>> validate_transitions_df(df)  # silent on valid input
    """
    missing = REQUIRED_TRANSITION_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}. "
            f"Required: {sorted(REQUIRED_TRANSITION_COLUMNS)}"
        )
    for col in ("entity_id", "from_state", "to_state"):
        if df[col].isna().any():
            n_na = int(df[col].isna().sum())
            raise ValueError(
                f"Column '{col}' contains {n_na} NaN value(s); cannot build transitions."
            )
```

Un-skip all 3 tests in `tests/unit/test_loaders.py` (remove `@pytest.mark.skip(reason="Wave 0 stub...")` from each).

Run: `uv run pytest tests/unit/test_loaders.py -x -q` — all 3 tests pass.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_loaders.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "def validate_transitions_df" core/io/loaders.py` returns 1 match.
    - `grep -n "REQUIRED_TRANSITION_COLUMNS" core/io/loaders.py` returns at least 1 match.
    - `grep -E "^import numpy as np|^import pandas as pd" core/io/loaders.py` returns 2 matches (both imports present at module top — required because the new function uses pd.DataFrame in its type hint and pd-style isna() in its body).
    - `grep -c "raise NotImplementedError" core/io/loaders.py` returns 2 (the two Phase 02 stubs are untouched).
    - `uv run pytest tests/unit/test_loaders.py -x -q` exits 0 with `3 passed`.
    - `grep -c "@pytest.mark.skip" tests/unit/test_loaders.py` returns 0.
  </acceptance_criteria>
  <done>
    DATA-01 minimal validator landed alongside Phase 02 loader stubs. Three loader tests pass.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Implement build_transition_matrix() in core/db/queries.py (DATA-03)</name>
  <read_first>
    - core/db/queries.py (existing Dataset dataclass + Phase 02 stubs — leave them, add new function at the bottom)
    - core/db/schema.sql (verify transitions table column names: dataset_id, entity_id, period, from_state, to_state, weight)
    - core/models.py (validate_transition_matrix signature — final argument is min_obs)
    - tests/integration/test_queries.py (read 3 build_transition_matrix integration tests exactly)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (Pattern 9 "build_transition_matrix()" + Pitfall 5 + Pitfall 6)
    - .claude/rules/data-storage.md (parameterized queries, no SQL injection)
  </read_first>
  <behavior>
    - Given a fresh DuckDB with the schema applied + a dataset_id 'ds_test' with 4 rows (A->A w=1, A->B w=1, B->A w=1, B->B w=3), build_transition_matrix returns matrix shape (2,2) where row 0 sums to 1.0 and row 1 sums to 1.0.
    - Returns (matrix: np.ndarray float64, counts: np.ndarray int64) tuple.
    - Filters strictly by dataset_id parameter (rows from other dataset_ids are NOT aggregated).
    - Uses parameterized SQL (`?` placeholders) — no f-string interpolation of dataset_id.
    - Calls validate_transition_matrix on the resulting matrix (re-raise InvalidTransitionMatrixError if invalid).
    - Optional `period: int | None` parameter filters to a specific period when provided.
  </behavior>
  <action>
Add NEW function to `core/db/queries.py` at the bottom of the file (after `bulk_insert_transitions` stub). Add these imports at the top (if not present):

```python
import duckdb
import numpy as np

from core.models import validate_transition_matrix
```

Function implementation:

```python
def build_transition_matrix(
    conn: "duckdb.DuckDBPyConnection",
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

    validate_transition_matrix(matrix, transition_counts=counts)
    return matrix, counts
```

Un-skip the 3 build_transition_matrix tests in `tests/integration/test_queries.py`. Remove `@pytest.mark.skip(reason="Wave 0 stub...")` from:
- `test_build_transition_matrix_normalized`
- `test_build_transition_matrix_counts`
- `test_build_transition_matrix_filters_dataset`

LEAVE `test_seed_idempotency` and `test_seed_produces_reference_forecasts` skipped — they belong to Plan 05.

Run: `uv run pytest tests/integration/test_queries.py -m integration -k "build_transition" -x -q` — all 3 must pass.
  </action>
  <verify>
    <automated>uv run pytest tests/integration/test_queries.py -m integration -k "build_transition" -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "def build_transition_matrix" core/db/queries.py` returns 1 match.
    - `grep -n "GROUP BY from_state, to_state" core/db/queries.py` returns at least 1 match.
    - `grep -n "validate_transition_matrix(matrix" core/db/queries.py` returns 1 match (matrix validated before return).
    - `grep -E "f\".*WHERE dataset_id" core/db/queries.py` returns nothing (no f-string SQL injection — query uses `?` placeholders).
    - `grep -E "\\[dataset_id\\]|\\[dataset_id, period\\]" core/db/queries.py` returns at least 2 matches (parameter binding for both query branches).
    - `uv run pytest tests/integration/test_queries.py -m integration -k "build_transition" -x -q` exits 0 with `3 passed`.
  </acceptance_criteria>
  <done>
    build_transition_matrix queries DuckDB with parameterized GROUP BY, returns (float64 matrix, int64 counts) tuple, validates the result before returning. Integration tests pass.
  </done>
</task>

</tasks>

<verification>
After all tasks:
```bash
uv run pytest tests/unit/test_serialization.py tests/unit/test_loaders.py -x -q
uv run pytest tests/integration/test_queries.py -m integration -k "build_transition" -x -q
```
Expected: 4 + 3 + 3 = 10 passed, 0 failed in covered scope.

```bash
uv run ruff check core/db/serialization.py core/db/queries.py core/io/loaders.py
uv run mypy core/db/serialization.py core/db/queries.py core/io/loaders.py
```
Both pass clean.

Manual end-to-end verification:
```bash
uv run python -c "
import duckdb, numpy as np
from core.db.connection import init_schema
from core.db.queries import build_transition_matrix
from core.db.serialization import ndarray_to_json, json_to_ndarray

conn = duckdb.connect(':memory:')
init_schema(conn)
conn.execute(\"INSERT INTO datasets (id, domain, name, source_path, row_count, n_states) VALUES ('ds_demo', 'churn', 'demo', '-', 4, 2)\")
conn.execute(\"INSERT INTO transitions VALUES ('ds_demo','e1',1,'A','A',7.0), ('ds_demo','e1',1,'A','B',3.0), ('ds_demo','e2',1,'B','A',2.0), ('ds_demo','e2',1,'B','B',8.0)\")
m, c = build_transition_matrix(conn, dataset_id='ds_demo')
print('matrix:', m.tolist())
print('rows sum:', m.sum(axis=1).tolist())
print('counts total:', c.sum())
s = ndarray_to_json(m)
m_back = json_to_ndarray(s)
print('round-trip ok:', np.array_equal(m, m_back))
"
```
Expected: `rows sum: [1.0, 1.0]`, `counts total: 20`, `round-trip ok: True`.
</verification>

<success_criteria>
- `core/db/serialization.py` exists with ndarray_to_json + json_to_ndarray and NaN/Inf rejection.
- `core/io/loaders.py` has validate_transitions_df (Phase 02 stubs untouched).
- `core/db/queries.py` has build_transition_matrix using parameterized SQL + validate.
- All 4 test_serialization.py tests pass.
- All 3 test_loaders.py tests pass.
- 3 build_transition_matrix integration tests pass.
- No raw f-string SQL anywhere in the new code.
</success_criteria>

<output>
After completion, create `.planning/phases/01-markov-engine/01-04-SUMMARY.md` documenting:
- Files created/modified
- DATA-01, DATA-03 marked complete (DATA-02 deferred to Plan 05)
- Confirmation D-24 (NaN/Inf rejection) and parameterized query patterns
- Integration test results
</output>
