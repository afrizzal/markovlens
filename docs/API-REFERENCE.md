# API Reference

> Public Python API of the MarkovLens engine. Auto-generated stubs — fill from docstrings as modules are implemented.

This document mirrors the public API of `core/` and `domains/`. Generated semi-manually for now; future versions may use `pdoc` or `sphinx`.

## `core/models.py`

### `validate_transition_matrix(P, transition_counts=None, *, tol=1e-9, min_obs=20)`

Validate a Markov transition matrix against project invariants.

- **Parameters:**
  - `P` (np.ndarray) — Matrix to validate
  - `transition_counts` (np.ndarray | None) — Per-cell observation counts for sparsity check
  - `tol` (float) — Tolerance for row-sum check
  - `min_obs` (int) — Minimum observations per cell
- **Raises:** `AssertionError` if any invariant fails
- **Returns:** `None`

### `class M1Homogeneous`

Constant transition matrix. Eq. (1) in Chan 2015.

```python
model = M1Homogeneous(P=transition_matrix)
forecast = model.forecast(Y_1=initial_shares, horizon=12)
```

### `class M2TimeVarying`

Time-varying transition matrices. Eq. (2) in Chan 2015.

```python
model = M2TimeVarying(P_t_sequence=[P_1, P_2, ..., P_t])
forecast = model.forecast(Y_1=initial_shares, horizon=12)
```

### `class M3Extended`

Time-varying P + growth multiplier G. Eq. (3) in Chan 2015.

```python
model = M3Extended(P_t_sequence=[...], G=growth_multiplier)
forecast = model.forecast(Q_1=initial_population, horizon=12)
```

---

## `core/simulation.py`

### `monte_carlo_simulate(matrix, start_state, n_steps=12, n_simulations=10_000, seed=42)`

Run Monte Carlo simulation over a transition matrix.

- **Returns:** `np.ndarray` shape `(n_simulations, n_steps+1)` of state sequences

### `calibrate_probability(raw_prob: float) -> float`

Apply Becker (2026) longshot-bias calibration to a raw probability.

### `LONGSHOT_CALIBRATION: dict[float, float]`

Hard-coded calibration table. See [MONTE-CARLO.md](MONTE-CARLO.md).

### `CONFIDENCE_LEVELS: tuple[float, ...]`

Default = `(0.10, 0.50, 0.90)` — 80% band + median.

---

## `core/metrics.py`

### `mape(actual: np.ndarray, forecast: np.ndarray) -> float`

Mean Absolute Percentage Error.

### `brier_score(forecast_prob: np.ndarray, actual: np.ndarray) -> float`

Brier score for probabilistic forecasts.

### `log_loss(forecast_prob: np.ndarray, actual: np.ndarray) -> float`

Log loss (cross-entropy).

---

## `core/validation.py`

### `walk_forward_backtest(df, build_fn, forecast_fn, min_window=12)`

Walk-forward validation — re-fit at each step using only past data.

- **Parameters:**
  - `df` (pd.DataFrame) — Historical observations
  - `build_fn` (Callable) — Function to build matrix from training subset
  - `forecast_fn` (Callable) — Function to produce forecast from matrix
  - `min_window` (int) — Minimum training periods before first backtest
- **Returns:** `list[ForecastResult]`

---

## `core/db/connection.py`

### `get_connection() -> duckdb.DuckDBPyConnection`

Returns the singleton DuckDB connection.

### `init_schema(conn) -> None`

Apply `schema.sql` to a connection (idempotent).

---

## `core/db/queries.py`

### Datasets

- `register_dataset(domain, name, source_path, row_count, n_states) -> str` — Returns dataset id
- `list_datasets(domain=None) -> list[Dataset]`
- `get_dataset(dataset_id) -> Dataset`

### Transitions

- `load_transitions(dataset_id, period_range=None) -> pd.DataFrame`
- `bulk_insert_transitions(dataset_id, df) -> int` — Returns row count inserted

### Matrices

- `get_cached_matrix(dataset_id, model_type, period=None) -> np.ndarray | None`
- `save_matrix(dataset_id, model_type, matrix, n_observations, period=None) -> str` — Returns matrix id

### Simulations

- `get_cached_simulation(matrix_id, start_state, n_steps, n_simulations, seed) -> SimulationResult | None`
- `save_simulation(matrix_id, result) -> str`

---

## `domains/brand_share/service.py`

### `list_datasets() -> list[Dataset]`

List all `brand_share` domain datasets.

### `run_forecast(dataset_id, model_type, horizon) -> BrandShareForecastResult`

End-to-end: load → build matrix → forecast → return chart-ready data.

### `get_transition_matrix(dataset_id, model_type) -> TransitionMatrixResult`

Just the matrix (for explorer view).

### `compare_models(dataset_id, models, horizon) -> ModelComparisonResult`

Run all 3 models, return side-by-side accuracy.

---

## `domains/churn/service.py`

### `list_cohorts() -> list[Cohort]`

List available customer cohorts.

### `run_analysis(cohort_id, horizon) -> ChurnAnalysisResult`

Compute state distribution evolution + Sankey flows.

### `simulate_scenario(cohort_id, transition_overrides) -> ScenarioResult`

What-if: override specific transition probabilities, compute new forecast.

---

## Exceptions

### `core.exceptions.DatasetNotFoundError`

Dataset id not in DB.

### `core.exceptions.DatasetTooSparseError`

Dataset has too few observations for valid matrix estimation.

### `core.exceptions.InvalidTransitionMatrixError`

Matrix failed `validate_transition_matrix()`.

### `core.exceptions.UnsupportedModelError`

Requested model type not implemented.

---

## Type Aliases

```python
from typing import TypeAlias
import numpy as np

TransitionMatrix: TypeAlias = np.ndarray  # shape (n_states, n_states)
StateVector: TypeAlias = np.ndarray       # shape (n_states,)
PopulationVector: TypeAlias = np.ndarray  # shape (n_states,) of customer counts
SimulationPaths: TypeAlias = np.ndarray   # shape (n_simulations, n_steps+1)
```

---

## Dataclasses

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Dataset:
    id: str
    domain: str
    name: str
    n_states: int
    row_count: int
    metadata: dict

@dataclass(frozen=True)
class SimulationResult:
    final_distribution: np.ndarray
    quantile_paths: dict[float, np.ndarray]
    raw_probability: float
    calibrated_probability: float
    n_simulations: int
    seed: int | None

@dataclass(frozen=True)
class ForecastResult:
    forecast_array: np.ndarray  # shape (horizon, n_states)
    confidence_bands: dict[float, np.ndarray]
    model_type: str
    horizon: int
    accuracy_metrics: dict[str, float] | None
```

---

> _This document will be updated as the engine matures. For now, treat each section as a contract — implementations must match these signatures._
