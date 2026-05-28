# Phase 01: Markov Engine — Research

**Researched:** 2026-05-29
**Domain:** Markov chain mathematics + NumPy vectorization + DuckDB data layer
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Data sources:**
- D-01: Brand share uses synthetic FMCG DGP — 5 brands, ~24 periods, documented parameters
- D-02: Churn uses IBM Telco CSV at `data/seed/telco_churn.csv` (committed to repo)
- D-03: `.gitignore` amended: `data/seed/*.csv` tracked; `data/raw/` and `data/*.duckdb` gitignored
- D-04: `data/SOURCES.md` must document dataset origin and license context
- D-05: README attributes IBM Telco source with Kaggle link

**M2/M3 extrapolation:**
- D-06: `M2TimeVarying.forecast()` — hold last `P_t` constant when `horizon > len(P_t_sequence)`
- D-07: `M3Extended.forecast()` — hold last `P_t` AND last `G` constant beyond training window

**P_t / G storage:**
- D-08: `P_t_sequence` stored as `np.ndarray` shape `(n_periods, n_states, n_states)`, NOT `list[np.ndarray]`
- D-09: `G` stored as `np.ndarray` — scalar shape `(n_states,)` or time-varying `(n_periods, n_states)`
- D-10: Constructor must validate shape consistency: `P_t_sequence.shape[1] == P_t_sequence.shape[2]` and `G.shape[-1] == P_t_sequence.shape[1]`

**Monte Carlo:**
- D-11: Vectorized cumsum + inverse-CDF algorithm; target ~50ms for 10k×12 steps
- D-12: `cum_matrix[:, -1] = 1.0` after cumsum — mandatory float boundary fix
- D-13: `start_state` accepts `Union[int, np.ndarray]` — int for single state, ndarray (n_states,) for distribution
- D-14: Return `np.ndarray` dtype `int64`, shape `(n_simulations, n_steps+1)` — full paths
- D-15: `rng = np.random.default_rng(seed)` only — never legacy `np.random.seed()`
- D-16: No threading/multiprocessing — Streamlit Cloud is 1 CPU; vectorized NumPy only

**Calibration:**
- D-17: `calibrate_probability()` uses `np.interp()` on sorted `LONGSHOT_CALIBRATION` keys
- D-18: Calibration applied AFTER simulation, never inside the loop; `SimulationResult` exposes both `raw_probability` and `calibrated_probability`

**Test strategy:**
- D-19: Regression-first — un-skip 4 existing tests, add Chan (2015) Table 3 regression, achieve >80% `core/` coverage
- D-20: DuckDB integration tests written in Phase 01 (not deferred); `temp_duckdb_path` fixture already in `tests/conftest.py`

**DuckDB:**
- D-21: JSON columns confirmed — no migration to native arrays
- D-22: `transitions` table is append-only log; no composite PK
- D-23: Seed idempotency via `DELETE WHERE dataset_id` + `INSERT`
- D-24: Serialization helpers in `core/db/serialization.py`; NaN/Inf rejected at boundary

### Claude's Discretion

- Exact column/period count for synthetic FMCG DGP (use 5 brands × 24 periods)
- ID generation strategy for DB PKs (UUID v4 via `uuid.uuid4()`)
- MAPE edge-case when `actual == 0` (skip zero-actual rows with warning)
- Split `tests/unit/` into per-module files vs. consolidated
- Whether `build_transition_matrix()` returns a sparsity mask alongside matrix + counts

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 01 scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENG-01 | `validate_transition_matrix()` raises `InvalidTransitionMatrixError` for non-square, negative, or row-sum≠1; enforces dtype float64 | Implementation pattern in `markov-patterns.md`; `InvalidTransitionMatrixError` already in `core/exceptions.py` |
| ENG-02 | `M1Homogeneous.forecast()` — Y_{t+1} = Y_t · P, verified against Chan (2015) Table 3 | Regression target values already in `test_models.py`; `sample_4x4_chan_matrix` in conftest |
| ENG-03 | `M2TimeVarying.forecast()` — Y_{t+1} = Y_t · P_t, hold-last extrapolation | D-06/D-08 specify exact behavior and storage format |
| ENG-04 | `M3Extended.forecast()` — Q_{t+1} = G ⊙ Q_t · P_t with growth multiplier | D-07/D-09 specify G shape; chan 2015 Tables 4-5 give reference values |
| ENG-05 | `monte_carlo_simulate()` — 10k vectorized paths, `default_rng`, reproducible | `docs/MONTE-CARLO.md` has authoritative pseudo-code; D-11..D-16 are locked |
| ENG-06 | `calibrate_probability()` — LONGSHOT_CALIBRATION interpolation | `np.interp()` 1-liner; D-17/D-18 locked |
| ENG-07 | `compute_quantile_bands()` — 10/50/90th percentile paths with `target_extractor` guard | Pattern: apply extractor first, then `np.percentile(..., axis=0)` |
| ENG-08 | Sparsity detection — warn on cells < `MIN_OBSERVATIONS_PER_CELL=20` | Already defined in `core/models.py`; `validate_transition_matrix()` accepts `transition_counts` param |
| ENG-09 | `walk_forward_backtest()` — re-fit at each step, no future leakage | `docs/MONTE-CARLO.md` has reference implementation |
| ENG-10 | `core/metrics.py` — MAPE, Brier score, log-loss | Stubs with docstrings and examples already present |
| DATA-01 | `core/io/loaders.py` — `validate_transitions_df()` helper for Phase 01 seed script | Full loaders deferred to Phase 02; Phase 01 needs only the validation helper |
| DATA-02 | `scripts/seed_data.py` — synthetic FMCG DGP + IBM Telco processing, 5+ reference forecasts | Telco CSV at `data/seed/telco_churn.csv`; DGP parameters at planner's discretion |
| DATA-03 | `build_transition_matrix()` in `core/db/queries.py` — DuckDB GROUP BY → normalized matrix + counts | SQL pattern in `docs/DATABASE.md`; pivot logic needed |
</phase_requirements>

---

## Summary

Phase 01 implements every `NotImplementedError` stub in `core/`. The work divides into four groups: (1) matrix validation and model mathematics, (2) Monte Carlo simulation engine, (3) DuckDB data layer, and (4) seed script + tests. All groups have strict internal dependencies but groups 3 and 4 can be parallelized once group 1 is complete.

The mathematical reference is fully documented in `docs/MARKOV-MODELS.md` and `docs/MONTE-CARLO.md` — no external research is needed for the math. The codebase already has the correct type aliases, dataclasses (`ForecastResult`, `SimulationResult`), exception hierarchy, DB schema, and test fixtures. Phase 01 is almost entirely fill-in-the-blank implementation, not greenfield design.

**Primary recommendation:** Build in strict dependency order: `validate_transition_matrix` (unblocks everything) → M1 (regression test must pass) → M2/M3 → Monte Carlo → calibration/quantiles → serialization helpers → `build_transition_matrix()` → seed script → metrics. Do not start later steps until earlier ones have green tests.

**Critical version note:** Installed packages are significantly newer than pyproject.toml minimums — NumPy 2.4.6, DuckDB 1.5.3, Pandas 3.0.3, scipy 1.17.1. The implementation must target these actual installed versions, not the minimums.

---

## Standard Stack

### Core (already installed and locked)

| Library | Installed Version | Purpose | Notes |
|---------|-------------------|---------|-------|
| NumPy | 2.4.6 | Matrix ops, vectorized simulation, RNG | Use `np.random.default_rng()` — NEP 50 is active in 2.x |
| Pandas | 3.0.3 | Transition DataFrame construction | `Copy-on-Write` is default in Pandas 3.x — do not rely on in-place mutations |
| DuckDB | 1.5.3 | Embedded DB for transitions and cache | API stable; `conn.execute().df()` still the primary pattern |
| Pydantic | 2.13.4 | Config/settings | Already used in `core/config.py` |
| pytest | 9.0.3 | Test runner | `--strict-markers` already set in `pyproject.toml` |
| pytest-cov | installed | Coverage reporting | `uv run pytest --cov=core tests/` |

### Stdlib Used

| Module | Use |
|--------|-----|
| `uuid` | UUID v4 for DB PKs |
| `json` | ndarray ↔ JSON in serialization helpers |
| `math` | Edge cases in metrics (log-loss clipping) |
| `pathlib.Path` | File paths for seed script |

### Version Risks

**NumPy 2.x:** Type promotion rules changed (NEP 50). `np.float64` must be declared explicitly for probability arrays — do not rely on implicit upcasting. The `default_rng()` API is stable and preferred.

**Pandas 3.x:** Copy-on-Write is the default. Chained assignments (`df["col"][mask] = val`) silently fail. Use `.loc[]` exclusively for mutations.

**DuckDB 1.5.3 vs. schema written for 1.1.0:** JSON column type is stable. `conn.execute().df()` pattern is stable. No breaking changes for the operations Phase 01 needs.

---

## Architecture Patterns

### Recommended Project Structure (Phase 01 additions)

```
core/
├── models.py              # Fill in validate_transition_matrix, M1, M2, M3
├── simulation.py          # Fill in monte_carlo_simulate, calibrate, quantile_bands
├── metrics.py             # Fill in mape, brier_score, log_loss
├── db/
│   ├── serialization.py   # NEW — ndarray <-> JSON helpers
│   └── queries.py         # Add build_transition_matrix() here
└── io/
    └── loaders.py         # Add validate_transitions_df() helper

data/
└── seed/
    └── telco_churn.csv    # NEW — IBM Telco CSV (committed)

scripts/
└── seed_data.py           # Rewrite with actual DGP + telco processing

tests/
├── conftest.py            # Existing fixtures — do not modify
├── unit/
│   ├── test_models.py     # Un-skip 4 tests, add new tests
│   ├── test_simulation.py # NEW — Monte Carlo, calibration, quantile bands
│   └── test_metrics.py    # NEW — MAPE, Brier, log-loss
└── integration/
    └── test_queries.py    # NEW — build_transition_matrix, seed script paths

docs/
└── SOURCES.md             # NEW — dataset attribution
```

### Pattern 1: Strict Build Order (Dependency Chain)

The validator is a dependency of every model constructor. The models are dependencies of the seed script. The seed script is a dependency of integration tests. The chain is:

```
Wave A (foundation):
  validate_transition_matrix()    ← no dependencies
  InvalidTransitionMatrixError    ← already exists

Wave B (models, depend on Wave A):
  M1Homogeneous.forecast()        ← depends on validate
  M2TimeVarying.forecast()        ← depends on validate
  M3Extended.forecast()           ← depends on validate

Wave C (simulation, depends on Wave A):
  monte_carlo_simulate()          ← depends on validate (caller validates before passing)
  calibrate_probability()         ← depends on LONGSHOT_CALIBRATION dict (already defined)
  compute_quantile_bands()        ← depends on monte_carlo_simulate output shape

Wave D (data layer, depends on Wave A):
  core/db/serialization.py        ← depends on numpy (no model deps)
  build_transition_matrix()       ← depends on serialization, DuckDB connection

Wave E (seed + metrics, depends on all):
  validate_transitions_df()       ← depends on pandas
  scripts/seed_data.py            ← depends on D and B (needs matrices + forecasts)
  core/metrics.py functions       ← depends on numpy only
  walk_forward_backtest()         ← depends on B + D

Wave F (tests only):
  Un-skip test_models.py          ← depends on Wave B
  tests/unit/test_simulation.py   ← depends on Wave C
  tests/unit/test_metrics.py      ← depends on Wave E
  tests/integration/test_queries  ← depends on Wave D
```

### Pattern 2: validate_transition_matrix() Implementation

The validator in `core/models.py` must check in this order (collect all failures, raise once):

```python
# Source: .claude/rules/markov-patterns.md + core/exceptions.py
from core.exceptions import InvalidTransitionMatrixError

def validate_transition_matrix(
    P: TransitionMatrix,
    transition_counts: np.ndarray | None = None,
    *,
    tol: float = PROBABILITY_TOLERANCE,
    min_obs: int = MIN_OBSERVATIONS_PER_CELL,
) -> None:
    errors: list[str] = []

    # Check 1: 2D
    if P.ndim != 2:
        errors.append(f"P must be 2D, got {P.ndim}D")
    # Check 2: square
    elif P.shape[0] != P.shape[1]:
        errors.append(f"P must be square, got {P.shape}")
    else:
        # Check 3: no NaN/Inf
        if not np.isfinite(P).all():
            errors.append("P contains NaN or Inf values")
        # Check 4: non-negative
        if (P < 0).any():
            errors.append(f"P has negative values; min={P.min()}")
        # Check 5: bounded
        if (P > 1.0 + tol).any():
            errors.append(f"P has values > 1; max={P.max()}")
        # Check 6: rows sum to 1
        row_sums = P.sum(axis=1)
        if not np.allclose(row_sums, 1.0, atol=tol):
            bad = np.where(~np.isclose(row_sums, 1.0, atol=tol))[0]
            errors.append(f"Rows {bad.tolist()} do not sum to 1.0; sums={row_sums[bad]}")
        # Check 7: dtype
        if P.dtype != np.float64:
            errors.append(f"P must be float64, got {P.dtype}")

    if errors:
        raise InvalidTransitionMatrixError("; ".join(errors))

    # Sparsity warning (non-raising)
    if transition_counts is not None:
        sparse_mask = transition_counts < min_obs
        if sparse_mask.any():
            sparse_cells = list(zip(*np.where(sparse_mask)))
            # Return warning via logging, not exception — UI layer decides how to display
            import logging
            logging.getLogger(__name__).warning(
                "Sparsity: %d cells below min_obs=%d: %s",
                sparse_mask.sum(), min_obs, sparse_cells[:5]
            )
```

**IMPORTANT NOTE on existing stub:** The current `M2TimeVarying.__init__` and `M3Extended.__init__` accept `list[TransitionMatrix]` but D-08 locks storage as `np.ndarray` shape `(n_periods, n_states, n_states)`. The constructor signatures **must be updated** to accept `np.ndarray` — this is a breaking stub change.

### Pattern 3: M1 Forecast

```python
# Source: docs/MARKOV-MODELS.md Equation 1
# Y_{t+1} = Y_1 · P^t
def forecast(self, Y_1: StateVector, horizon: int) -> ForecastResult:
    validate_transition_matrix(self.P)  # re-validate on use
    forecast_array = np.zeros((horizon, self.n_states), dtype=np.float64)
    Y_t = Y_1.copy()
    for t in range(horizon):
        Y_t = Y_t @ self.P
        forecast_array[t] = Y_t
    return ForecastResult(
        forecast_array=forecast_array,
        confidence_bands=None,
        model_type="m1",
        horizon=horizon,
    )
```

The `forecast_array` shape is `(horizon, n_states)`. Row 0 is t=2 (first predicted step). The Chan (2015) Table 3 regression test checks `result.forecast_array[1]` (t=2 → index 1) against `[0.5829, 0.2780, 0.0667, 0.0724]` with `atol=1e-3`.

**Correctness check:** `Y_1 @ self.P` gives `Y_2`. `Y_1 @ np.linalg.matrix_power(self.P, 2)` gives `Y_3`. Both are equivalent. The iterative approach (`Y_t = Y_t @ self.P`) is simpler and correct for sequential forecasting.

### Pattern 4: M2 Time-Varying Forecast

```python
# Source: docs/MARKOV-MODELS.md Equation 2
# Y_{t+1} = Y_1 · P_1 · P_2 · ... · P_t  (hold last P_t if horizon > n_periods)
def forecast(self, Y_1: StateVector, horizon: int) -> ForecastResult:
    n_periods = self.P_t.shape[0]  # P_t is ndarray (n_periods, n_states, n_states)
    forecast_array = np.zeros((horizon, self.n_states), dtype=np.float64)
    Y_t = Y_1.copy()
    for t in range(horizon):
        P_at_t = self.P_t[t] if t < n_periods else self.P_t[-1]  # D-06: hold last
        Y_t = Y_t @ P_at_t
        forecast_array[t] = Y_t
    return ForecastResult(
        forecast_array=forecast_array,
        confidence_bands=None,
        model_type="m2",
        horizon=horizon,
    )
```

### Pattern 5: M3 Extended Forecast

```python
# Source: docs/MARKOV-MODELS.md Equation 3
# Q_{t+1} = (G ⊙ Q_t) · P_t
def forecast(self, Q_1: PopulationVector, horizon: int) -> ForecastResult:
    n_periods = self.P_t.shape[0]
    forecast_array = np.zeros((horizon, self.n_states), dtype=np.float64)
    Q_t = Q_1.copy()
    for t in range(horizon):
        P_at_t = self.P_t[t] if t < n_periods else self.P_t[-1]  # D-07
        Q_t = (self.G * Q_t) @ P_at_t  # G ⊙ Q_t, then matrix multiply
        forecast_array[t] = Q_t
    return ForecastResult(
        forecast_array=forecast_array,
        confidence_bands=None,
        model_type="m3",
        horizon=horizon,
    )
```

**Note on G shape:** `self.G` is shape `(n_states,)` for standard case. `self.G * Q_t` is element-wise multiplication — NumPy broadcasting handles this correctly when both are 1D arrays.

### Pattern 6: Vectorized Monte Carlo

```python
# Source: docs/MONTE-CARLO.md (authoritative pseudo-code — use directly)
def monte_carlo_simulate(
    matrix: TransitionMatrix,
    start_state: int | np.ndarray,
    n_steps: int = 12,
    n_simulations: int = 10_000,
    seed: int | None = 42,
) -> SimulationPaths:
    rng = np.random.default_rng(seed)  # D-15
    n_states = matrix.shape[0]

    # Normalize start_state to probability distribution (D-13)
    if isinstance(start_state, int):
        init_dist = np.zeros(n_states, dtype=np.float64)
        init_dist[start_state] = 1.0
    else:
        init_dist = np.asarray(start_state, dtype=np.float64)
        init_dist = init_dist / init_dist.sum()  # normalize

    paths = np.zeros((n_simulations, n_steps + 1), dtype=np.int64)  # D-14: int64

    # Sample initial states from distribution
    paths[:, 0] = rng.choice(n_states, size=n_simulations, p=init_dist)

    # D-12: mandatory float boundary fix
    cum_matrix = matrix.cumsum(axis=1)
    cum_matrix[:, -1] = 1.0

    for t in range(n_steps):
        u = rng.random(n_simulations)
        current_states = paths[:, t]
        cum_probs = cum_matrix[current_states]         # (n_simulations, n_states)
        paths[:, t + 1] = (u[:, None] < cum_probs).argmax(axis=1)

    return paths
```

**Confidence:** HIGH — this is the verbatim algorithm from `docs/MONTE-CARLO.md` with D-12/D-13/D-14/D-15 applied.

### Pattern 7: Calibration (1-liner)

```python
# Source: docs/MONTE-CARLO.md + D-17
def calibrate_probability(raw_prob: float) -> float:
    keys = np.array(sorted(LONGSHOT_CALIBRATION.keys()), dtype=np.float64)
    values = np.array([LONGSHOT_CALIBRATION[k] for k in sorted(LONGSHOT_CALIBRATION)], dtype=np.float64)
    return float(np.interp(raw_prob, keys, values))
```

`np.interp()` handles boundary clamping automatically (returns `values[0]` for `x < xp[0]` and `values[-1]` for `x > xp[-1]`).

### Pattern 8: Serialization Helpers

```python
# core/db/serialization.py (new file)
def ndarray_to_json(arr: np.ndarray) -> str:
    if not np.isfinite(arr).all():
        raise ValueError("Array contains NaN or Inf — cannot serialize")
    return json.dumps(arr.tolist())

def json_to_ndarray(s: str, dtype: np.dtype = np.float64) -> np.ndarray:
    return np.array(json.loads(s), dtype=dtype)
```

### Pattern 9: build_transition_matrix()

```python
# core/db/queries.py (add to existing file)
# Source: docs/DATABASE.md "Build m1 transition matrix in pure SQL"
def build_transition_matrix(
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    *,
    period: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (matrix: float64 ndarray, counts: int ndarray), both shape (n_states, n_states)."""
    period_filter = "AND period = ?" if period is not None else ""
    params = [dataset_id] + ([period] if period is not None else [])
    df = conn.execute(f"""
        SELECT from_state, to_state, SUM(weight) AS n
        FROM transitions
        WHERE dataset_id = ? {period_filter}
        GROUP BY from_state, to_state
    """, params).df()

    states = sorted(set(df["from_state"]) | set(df["to_state"]))
    n = len(states)
    state_idx = {s: i for i, s in enumerate(states)}

    counts = np.zeros((n, n), dtype=np.int64)
    for _, row in df.iterrows():
        i, j = state_idx[row["from_state"]], state_idx[row["to_state"]]
        counts[i, j] = int(row["n"])

    row_sums = counts.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)  # avoid div-by-zero
    matrix = (counts / row_sums).astype(np.float64)
    validate_transition_matrix(matrix, transition_counts=counts)
    return matrix, counts
```

### Anti-Patterns to Avoid

- **`list[np.ndarray]` for P_t_sequence** — D-08 locks this as `np.ndarray` shape `(n_periods, n_states, n_states)`. The existing stub uses `list` — it must be changed.
- **`np.random.seed()`** — forbidden (legacy, not reproducible across NumPy 2.x). Only `np.random.default_rng(seed)`.
- **Missing `cum_matrix[:, -1] = 1.0`** — silent correctness bug where float drift causes last state to never be selected.
- **Calibration inside simulation loop** — D-18 locks this: calibrate after, not during.
- **Raw SQL in scripts/seed_data.py** — all queries must use `core/db/queries.py` or `core/db/connection.py` patterns.
- **`pandas.crosstab()` for transition matrix** — easy to produce unnormalized rows. Use DuckDB SQL + explicit normalization.
- **`df.groupby().sum()` instead of DuckDB SQL** — for `build_transition_matrix()`, use the DuckDB query path.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Linear interpolation for calibration | Custom loop over LONGSHOT table | `np.interp()` | Boundary clamping, monotonicity, 1 line |
| JSON serialization of ndarrays | Custom encoder | `.tolist()` + `json.dumps()` | Correct for nested lists; round-trips cleanly |
| Random walk sampling | `rng.choice()` in a loop | Vectorized cumsum + `argmax` | 100-1000x faster for 10k sims |
| Matrix row normalization | Manual loop | `counts / counts.sum(axis=1, keepdims=True)` | NumPy broadcasting |
| DB pivot for transition matrix | `pd.pivot_table` | DuckDB GROUP BY + Python pivot | DuckDB is faster for large datasets |
| Unique IDs | Sequential ints or timestamps | `str(uuid.uuid4())` | Collision-free, sortable |

**Key insight:** The hardest part of this phase is correctness (matching Chan 2015 numerics and ensuring no float drift), not algorithmic complexity. Every computational primitive needed is already available in NumPy.

---

## Common Pitfalls

### Pitfall 1: M2/M3 Constructor Signature Mismatch

**What goes wrong:** The existing stub defines `M2TimeVarying.__init__(self, P_t_sequence: list[TransitionMatrix])` but D-08 requires `np.ndarray` shape `(n_periods, n_states, n_states)`. If the constructor is not changed, the type annotation and internal indexing will be wrong.

**Why it happens:** The stub was written before the CONTEXT.md decision.

**How to avoid:** Update both `M2TimeVarying.__init__` and `M3Extended.__init__` signatures in the same commit as implementation. Update the `list[ndarray]` validation loop to array shape checks.

**Warning signs:** `P_t_sequence[0]` still works with a list, so the bug is silent until Phase 02 tries to serialize to DuckDB JSON.

### Pitfall 2: Chan 2015 Table 3 Index Off-By-One

**What goes wrong:** The test asserts `result.forecast_array[1]` (index 1) matches t=2 values. A naive implementation that stores Y_1 in `forecast_array[0]` would shift the results and cause the regression test to fail with wrong values.

**Why it happens:** Confusion between "the initial state is Y_1" and "forecast_array[0] should be Y_2, not Y_1."

**How to avoid:** `forecast_array` contains ONLY the forecast steps, not the initial vector. `forecast_array[0]` = Y_2, `forecast_array[1]` = Y_3, etc.

**Warning signs:** Test fails with values close to but not equal to expected — off by exactly one matrix multiply.

### Pitfall 3: Float Boundary Drift in Monte Carlo

**What goes wrong:** After `matrix.cumsum(axis=1)`, the last column may be `0.9999999...` due to float64 precision. When a uniform sample `u` is `> 0.999999`, `(u[:, None] < cum_probs).argmax(axis=1)` returns 0 (the argmax of all-False is 0, not the last state).

**Why it happens:** Floating-point accumulation in cumsum.

**How to avoid:** `cum_matrix[:, -1] = 1.0` immediately after cumsum. D-12 is mandatory.

**Warning signs:** Monte Carlo produces zero probability for the last state even when the matrix has non-zero entries in that column.

### Pitfall 4: np.int32 vs. int64 dtype for paths

**What goes wrong:** `docs/MONTE-CARLO.md` pseudo-code uses `np.int32`. D-14 locks the return dtype to `int64`. If `int32` is used, `compute_quantile_bands()` in Phase 02 may produce incorrect percentile calculations for large state spaces.

**Why it happens:** The pseudo-code predates the CONTEXT.md decision.

**How to avoid:** Always declare `dtype=np.int64` in `np.zeros(...)` for the paths array. The `argmax()` call returns int, which auto-promotes.

### Pitfall 5: Pandas 3.x Copy-on-Write in build_transition_matrix()

**What goes wrong:** If `build_transition_matrix()` uses chained indexing to fill the matrix (e.g., `matrix_df["col"]["row"] = value`), it will silently not write in Pandas 3.x with Copy-on-Write enabled.

**Why it happens:** Pandas 3.0 made CoW the default.

**How to avoid:** Build the matrix as a NumPy array directly (preferred) or use `.loc[]` for any Pandas mutations.

### Pitfall 6: DuckDB Connection Re-use in Integration Tests

**What goes wrong:** `core/db/connection.py` uses a module-level singleton `_connection`. Integration tests that use `temp_duckdb_path` but do NOT call `close_connection()` will leave the connection pointing at the wrong file in subsequent tests.

**Why it happens:** The singleton persists across test function calls.

**How to avoid:** Each integration test must either (1) open a direct `duckdb.connect(str(temp_duckdb_path))` without using the singleton, or (2) call `close_connection()` in a fixture teardown. Do NOT rely on the singleton in integration tests.

### Pitfall 7: MAPE Division by Zero

**What goes wrong:** `mape()` formula is `|actual - forecast| / actual * 100`. When `actual == 0`, this is division by zero.

**Why it happens:** Brand share states can hit 0% legitimately.

**How to avoid:** Per Claude's Discretion (D-82), skip rows where `actual == 0` with a `logging.warning`. Return the mean over non-zero rows only. Document this in the function docstring.

### Pitfall 8: Seed Script Idempotency

**What goes wrong:** Running `seed_data.py` twice leaves duplicate rows in the `transitions` table, which doubles all counts and corrupts transition matrices.

**Why it happens:** Append-only table with no PK.

**How to avoid:** D-23 locks the pattern: `DELETE FROM transitions WHERE dataset_id = ?` before every `INSERT`. Same for `forecasts`, `transition_matrices`, `simulation_runs`, and `datasets`. Test this by running the seed script twice and asserting row counts are identical.

---

## Code Examples

### Chan 2015 Table 3 Regression Values (HIGH confidence)

```python
# Source: docs/MARKOV-MODELS.md — Tables 1 and 3
# P matrix (Table 1) — already in tests/conftest.py as sample_4x4_chan_matrix
P = np.array([
    [0.98230, 0.00753, 0.00464, 0.00552],
    [0.01158, 0.96161, 0.02489, 0.00192],
    [0.01442, 0.01105, 0.95721, 0.01732],
    [0.01978, 0.01122, 0.01364, 0.95536],
])

Y_1 = np.array([0.5878, 0.2830, 0.0585, 0.0708])

# Table 3 forecast values:
# t=2: [0.5829, 0.2780, 0.0667, 0.0724]   ← result.forecast_array[1] (index 1)
# t=3: [0.5782, 0.2733, 0.0745, 0.0741]
# t=4: [0.5737, 0.2688, 0.0818, 0.0758]
# t=5: [0.5693, 0.2645, 0.0887, 0.0775]
# t=6: [0.5651, 0.2605, 0.0951, 0.0792]
```

### M3 Reference Values (Chan 2015 Tables 4-5)

```python
# Source: docs/MARKOV-MODELS.md — m3 forecast table
G = np.array([1.0315, 1.0561, 0.9029, 1.0897])
Q_1 = np.array([0.5878, 0.2830, 0.0585, 0.0708])  # normalized shares as starting point
# t=2: Q = [0.5799, 0.2847, 0.0603, 0.0751], total=2,904,830
```

### calibrate_probability() Expected Values

```python
# Source: LONGSHOT_CALIBRATION dict (already in core/simulation.py)
# Direct anchor points (exact):
assert calibrate_probability(0.05) == pytest.approx(0.0418)
assert calibrate_probability(0.50) == pytest.approx(0.500)
# Interpolated (approximate):
assert calibrate_probability(0.025) == pytest.approx((0.0043 + 0.0418) / 2, abs=0.001)
```

### Synthetic FMCG DGP Design

```python
# Claude's discretion — suggested parameters for planner
BRANDS = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
N_PERIODS = 24   # 24 months = 2 years
INITIAL_SHARE = np.array([0.35, 0.25, 0.20, 0.12, 0.08])  # sum=1.0

# Plausible m1-like base transition matrix (rows must sum to 1):
P_base = np.array([
    [0.90, 0.04, 0.03, 0.02, 0.01],  # Alpha: dominant, low churn
    [0.05, 0.85, 0.05, 0.03, 0.02],  # Beta
    [0.04, 0.06, 0.82, 0.05, 0.03],  # Gamma
    [0.03, 0.05, 0.06, 0.80, 0.06],  # Delta
    [0.02, 0.03, 0.05, 0.07, 0.83],  # Epsilon
])
# Small random drift per period to make m2/m3 interesting
```

### Telco Churn State Discretization

```python
# Source: CONTEXT.md specifics section + dataset-prepper SKILL.md
# IBM Telco CSV columns: customerID, tenure (months), Churn (Yes/No)
# Discretize tenure into 4 states:
TENURE_STATES = {
    "new":      (0, 12),
    "growing":  (12, 24),
    "mature":   (24, 48),
    "loyal":    (48, None),   # 48+ months
}
# Churned customers → absorbing state "churned"
# Transition: at each period, track state before/after any tenure change or churn event
```

---

## Runtime State Inventory

This is a greenfield phase — no existing runtime state to migrate. Phase 01 creates new state:

| Category | Items | Action |
|----------|-------|--------|
| Stored data | DuckDB file will be created by seed script | No migration — new |
| Live service config | None | None |
| OS-registered state | None | None |
| Secrets/env vars | `.env` with `DUCKDB_PATH` (from `.env.example`) | Copy `.env.example` to `.env` if not done |
| Build artifacts | `.venv` exists; all deps installed | No reinstall needed |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All code | Yes | 3.12.10 | — |
| uv | Dependency management | Yes | (installed, `.venv` present) | — |
| NumPy | Core math | Yes | 2.4.6 | — |
| Pandas | Data manipulation | Yes | 3.0.3 | — |
| DuckDB | Data layer | Yes | 1.5.3 | — |
| SciPy | (not used in Phase 01) | Yes | 1.17.1 | — |
| pytest | Test runner | Yes | 9.0.3 | — |
| pytest-cov | Coverage | Yes | installed | — |
| `data/seed/telco_churn.csv` | Seed script | **NOT YET** | — | Must be committed before seed_data.py runs |

**Missing dependencies with no fallback:**
- `data/seed/telco_churn.csv` — must be obtained and committed before seed script can run. Source: IBM Watson Sample Data via Kaggle `blastchar/telco-customer-churn`. The CONTEXT.md (D-02) confirms this file will be committed to the repo; it just doesn't exist yet.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/unit/ -m "not slow" --cov=core --cov-report=term-missing -q` |
| Full suite command | `uv run pytest --cov=core --cov-report=term-missing` |
| Integration only | `uv run pytest -m integration` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENG-01 | validator accepts valid 2x2 matrix | unit | `uv run pytest tests/unit/test_models.py::test_validate_transition_matrix_accepts_valid -x` | Yes (skipped) |
| ENG-01 | validator rejects non-square matrix | unit | `uv run pytest tests/unit/test_models.py::test_validate_transition_matrix_rejects_non_square -x` | Yes (skipped) |
| ENG-01 | validator rejects unnormalized rows | unit | `uv run pytest tests/unit/test_models.py::test_validate_transition_matrix_rejects_unnormalized -x` | Yes (skipped) |
| ENG-01 | validator rejects negative values | unit | `uv run pytest tests/unit/test_models.py::test_validate_rejects_negative -x` | No — Wave 0 |
| ENG-01 | validator rejects non-float64 dtype | unit | `uv run pytest tests/unit/test_models.py::test_validate_rejects_wrong_dtype -x` | No — Wave 0 |
| ENG-02 | M1 forecast matches Chan 2015 Table 3 | unit/regression | `uv run pytest tests/unit/test_models.py::test_m1_forecast_replicates_chan_2015_table3 -x` | Yes (skipped) |
| ENG-02 | M1 forecast returns correct shape | unit | `uv run pytest tests/unit/test_models.py::test_m1_forecast_shape -x` | No — Wave 0 |
| ENG-03 | M2 forecast returns correct shape and type | unit | `uv run pytest tests/unit/test_models.py::test_m2_forecast_shape -x` | No — Wave 0 |
| ENG-03 | M2 extrapolation holds last P_t | unit | `uv run pytest tests/unit/test_models.py::test_m2_holds_last_pt_at_horizon -x` | No — Wave 0 |
| ENG-04 | M3 forecast matches Chan 2015 m3 table | unit/regression | `uv run pytest tests/unit/test_models.py::test_m3_forecast_replicates_chan_2015 -x` | No — Wave 0 |
| ENG-05 | Same seed → bit-identical paths | unit | `uv run pytest tests/unit/test_simulation.py::test_monte_carlo_same_seed_reproducible -x` | No — Wave 0 |
| ENG-05 | Different seed → different paths | unit | `uv run pytest tests/unit/test_simulation.py::test_monte_carlo_different_seeds_differ -x` | No — Wave 0 |
| ENG-05 | paths shape is (n_sims, n_steps+1) | unit | `uv run pytest tests/unit/test_simulation.py::test_monte_carlo_output_shape -x` | No — Wave 0 |
| ENG-05 | paths dtype is int64 | unit | `uv run pytest tests/unit/test_simulation.py::test_monte_carlo_dtype_int64 -x` | No — Wave 0 |
| ENG-06 | calibrate anchor points match table | unit | `uv run pytest tests/unit/test_simulation.py::test_calibrate_anchor_points -x` | No — Wave 0 |
| ENG-06 | calibrate interpolates between anchors | unit | `uv run pytest tests/unit/test_simulation.py::test_calibrate_interpolates -x` | No — Wave 0 |
| ENG-07 | quantile bands shape is (n_steps+1,) per quantile | unit | `uv run pytest tests/unit/test_simulation.py::test_quantile_bands_shape -x` | No — Wave 0 |
| ENG-08 | sparsity warning logged when counts below threshold | unit | `uv run pytest tests/unit/test_models.py::test_validate_warns_sparse_cells -x` | No — Wave 0 |
| ENG-09 | walk_forward_backtest uses only past data | unit | `uv run pytest tests/unit/test_simulation.py::test_walk_forward_no_leakage -x` | No — Wave 0 |
| ENG-10 | mape matches known value | unit | `uv run pytest tests/unit/test_metrics.py::test_mape_known_value -x` | No — Wave 0 |
| ENG-10 | mape skips zero-actual rows | unit | `uv run pytest tests/unit/test_metrics.py::test_mape_skips_zero_actual -x` | No — Wave 0 |
| ENG-10 | brier_score known value | unit | `uv run pytest tests/unit/test_metrics.py::test_brier_known_value -x` | No — Wave 0 |
| ENG-10 | log_loss known value | unit | `uv run pytest tests/unit/test_metrics.py::test_log_loss_known_value -x` | No — Wave 0 |
| DATA-01 | validate_transitions_df rejects missing columns | unit | `uv run pytest tests/unit/test_loaders.py::test_validate_transitions_df_missing_col -x` | No — Wave 0 |
| DATA-03 | build_transition_matrix returns normalized matrix | integration | `uv run pytest -m integration tests/integration/test_queries.py::test_build_transition_matrix_normalized -x` | No — Wave 0 |
| DATA-03 | build_transition_matrix returns counts array | integration | `uv run pytest -m integration tests/integration/test_queries.py::test_build_transition_matrix_counts -x` | No — Wave 0 |
| DATA-02 | seed_data.py runs twice and produces identical counts | integration | `uv run pytest -m integration tests/integration/test_queries.py::test_seed_idempotency -x` | No — Wave 0 |
| DATA-02 | forecasts table has >= 5 rows after seed | integration | `uv run pytest -m integration tests/integration/test_queries.py::test_seed_produces_reference_forecasts -x` | No — Wave 0 |
| Serialize | ndarray round-trips through JSON cleanly | unit | `uv run pytest tests/unit/test_serialization.py::test_ndarray_json_roundtrip -x` | No — Wave 0 |
| Serialize | serializer rejects NaN/Inf | unit | `uv run pytest tests/unit/test_serialization.py::test_serializer_rejects_nan -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/ -m "not slow" -q`
- **Per wave merge:** `uv run pytest --cov=core --cov-report=term-missing -q`
- **Phase gate:** Full suite green + `core/` coverage >= 80% before marking Phase 01 complete

### Wave 0 Gaps (files to create before implementation tasks)

These test files do not yet exist and must be created in the first task of Phase 01:

- [ ] `tests/unit/test_simulation.py` — covers ENG-05, ENG-06, ENG-07, ENG-09
- [ ] `tests/unit/test_metrics.py` — covers ENG-10
- [ ] `tests/unit/test_serialization.py` — covers DATA-03 serialization path
- [ ] `tests/unit/test_loaders.py` — covers DATA-01
- [ ] `tests/integration/test_queries.py` — covers DATA-02, DATA-03 integration paths

**Existing test file to modify:**
- [ ] `tests/unit/test_models.py` — remove all `@pytest.mark.skip` decorators, add 6 new tests

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `np.random.seed(N)` | `np.random.default_rng(N)` | NumPy 1.17 / NEP 50 in 2.0 | Must use new API; project rules enforce this |
| `pd.DataFrame.groupby().sum()` | DuckDB SQL GROUP BY | Pandas 3.x CoW | SQL path is faster and avoids CoW pitfalls |
| `pd.DataFrame.pivot_table()` | Explicit NumPy array build | Pandas 3.x CoW | More explicit, no hidden copies |
| `list[np.ndarray]` for P_t | `np.ndarray (n,m,m)` | CONTEXT.md D-08 | Better for JSON serialization, NumPy indexing |

---

## Open Questions

1. **validate_transitions_df() scope for Phase 01**
   - What we know: `core/io/loaders.py` has full loaders deferred to Phase 02; Phase 01 seed script needs something to validate a DataFrame before inserting into DuckDB
   - What's unclear: whether a simple inline check in `seed_data.py` is sufficient or whether a reusable `validate_transitions_df()` is worth creating in Phase 01
   - Recommendation: Create a lightweight `validate_transitions_df()` in `core/io/loaders.py` — required columns check + dtype assertion. This is the DATA-01 scope for Phase 01. The full loader functions remain Phase 02.

2. **Synthetic FMCG DGP exact parameters**
   - What we know: 5 brands, ~24 periods, parameters at planner's discretion (Claude's Discretion)
   - What's unclear: whether the DGP should use a fixed seed-generated random walk or a hand-crafted plausible matrix
   - Recommendation: Hand-craft a plausible `P_base` matrix as shown in Code Examples above, then add small Dirichlet noise per period to produce M2-interesting time-variation. Document the parameters in a module-level docstring in `seed_data.py`.

3. **walk_forward_backtest() return type**
   - What we know: the function must return some kind of result list
   - What's unclear: whether it should return `list[ForecastResult]` or a specialized backtest result type
   - Recommendation: Return `list[dict]` with keys `{"period", "forecast", "actual", "mape", "brier"}` for simplicity in Phase 01. Phase 05 QA can refine the type.

---

## Project Constraints (from CLAUDE.md)

- **Python 3.12+** — required; use modern syntax (`match`, `|` unions, `TypeAlias`)
- **uv** — all dependency operations; never `pip install`
- **ruff** — all linting/formatting; run before commit
- **mypy** — strict on `core/` and `domains/`; must pass `uv run mypy core/`
- **No `import streamlit` in `core/` or `domains/`** — enforced
- **All SQL in `core/db/queries.py`** — no raw SQL in `scripts/` or `app/`
- **`rtk git` prefix for all bash git commands** — token optimization
- **`@dataclass(frozen=True)` for result types** — `ForecastResult` and `SimulationResult` are already frozen
- **NumPy docstrings on public functions** — Parameters/Returns/Examples format
- **No magic numbers** — extract to `UPPER_SNAKE` constants at module level
- **Conventional commits** — `feat:`, `fix:`, `refactor:`, `test:` prefixes
- **`.planning/` owned by GSD** — never edit `STATE.md`, `PROJECT.md`, `ROADMAP.md`, `phases/**` manually

---

## Sources

### Primary (HIGH confidence)

- `docs/MARKOV-MODELS.md` — Chan (2015) equations, Table 1/3/4/5 regression values
- `docs/MONTE-CARLO.md` — vectorized pseudo-code, calibration function, walk-forward pattern
- `core/db/schema.sql` — confirmed DB schema, all 6 tables
- `docs/DATABASE.md` — common query patterns, build_transition_matrix SQL pattern
- `tests/conftest.py` — existing fixtures (sample_4x4_chan_matrix, temp_duckdb_path)
- `tests/unit/test_models.py` — 4 existing tests and their assertions
- `.planning/phases/01-markov-engine/01-CONTEXT.md` — 24 locked decisions
- `.claude/rules/markov-patterns.md` — validation checklist, forbidden practices
- `.claude/rules/python-conventions.md` — type hints, NumPy patterns, docstrings
- `.claude/rules/data-storage.py` — DuckDB connection pattern, parameterized queries
- `.claude/skills/markov-validator/SKILL.md` — 7-check validation procedure
- `.claude/skills/monte-carlo-runner/SKILL.md` — standard parameters and aggregation procedure

### Secondary (MEDIUM confidence)

- NumPy 2.4.6 release notes (NEP 50 type promotion) — verified against installed version

### Tertiary (LOW confidence — not needed for this phase)

None — all needed information is in project-local documentation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against installed `.venv` packages
- Architecture: HIGH — derived directly from existing stubs, CONTEXT.md decisions, and project docs
- Math patterns: HIGH — Chan (2015) equations documented in `docs/MARKOV-MODELS.md`; regression values in `tests/conftest.py`
- Pitfalls: HIGH — derived from locked decisions (D-08, D-12, D-14) and code inspection of existing stubs
- Test map: HIGH — based on existing test structure and REQUIREMENTS.md

**Research date:** 2026-05-29
**Valid until:** 2026-06-29 (stable math + locked stack; re-validate if DuckDB or NumPy upgraded)
