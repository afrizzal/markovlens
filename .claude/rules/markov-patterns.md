# Markov Chain Implementation Rules

## Reference

All Markov model implementations must follow [docs/MARKOV-MODELS.md](../../docs/MARKOV-MODELS.md), which derives from:

- **Chan, K. C. (2015)** — *Market Share Modelling and Forecasting Using Markov Chains and Alternative Models*. International Journal of Innovative Computing, Information and Control, Vol. 11, No. 4.
- **Becker (2026)** — empirical longshot-bias calibration from 72.1M Polymarket trades.

## Model Naming

| Code | Paper | Description |
|---|---|---|
| `m1` | Homogeneous | Constant transition matrix `P` |
| `m2` | Time-varying | `P_t` changes per time step |
| `m3` | Extended time-varying | `P_t` + growth multiplier `G` for market size |
| `m4` | Non-Markov | Category-based, no transition matrix (deferred to v0.2) |

Use these codes consistently in function names, DB columns, UI labels.

## Mandatory Validations

Every transition matrix MUST pass these checks before being used:

```python
def validate_transition_matrix(P: np.ndarray) -> None:
    """Raise AssertionError if P is not a valid transition matrix."""
    # 1. Shape
    assert P.ndim == 2, f"P must be 2D, got {P.ndim}D"
    assert P.shape[0] == P.shape[1], f"P must be square, got {P.shape}"

    # 2. Non-negative
    assert (P >= 0).all(), "P must have no negative probabilities"

    # 3. Bounded
    assert (P <= 1.0 + 1e-9).all(), "P must have no probabilities > 1"

    # 4. Rows sum to 1.0 (within float tolerance)
    row_sums = P.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-9), (
        f"rows must sum to 1.0, got {row_sums}"
    )
```

Run this validation:
- After building a matrix from data
- After any matrix modification (e.g., what-if adjustments)
- At the start of any simulation that uses it

## Minimum Observations Rule

Every cell `P[i, j]` must be estimated from **at least 20-30 observed transitions**. If a row has too-sparse data:

- **Warn** the user with a UI flag on the heatmap cell
- **Suggest** merging sparse states or gathering more data
- **NEVER silently** use noise as signal

```python
def check_sparsity(transition_counts: np.ndarray, min_obs: int = 20) -> np.ndarray:
    """Return boolean mask of cells with insufficient observations."""
    return transition_counts < min_obs
```

## Monte Carlo Defaults

```python
DEFAULT_N_SIMULATIONS = 10_000   # Becker's default; balance speed vs precision
DEFAULT_RANDOM_SEED = 42         # Reproducibility (configurable via env)
CONFIDENCE_LEVELS = (0.10, 0.50, 0.90)  # 80% band + median
```

Always expose `seed` parameter for reproducibility. Always return both raw and calibrated probabilities.

## Calibration Table

Hardcoded in `core/simulation.py` from Becker (2026). DO NOT modify without updating the source citation and rerunning all backtests.

```python
LONGSHOT_CALIBRATION = {
    0.01: 0.0043,
    0.05: 0.0418,
    0.10: 0.087,
    0.20: 0.181,
    0.30: 0.285,
    0.50: 0.500,
    0.70: 0.715,
    0.80: 0.819,
    0.90: 0.913,
    0.95: 0.958,
}
```

## Walk-Forward Validation

Backtests MUST use walk-forward validation — never let future data leak into past matrix estimates:

```python
def walk_forward_backtest(df: pd.DataFrame, window: int = 12) -> list[ForecastResult]:
    """Re-fit at each step using only data available at that time."""
    results = []
    for t in range(window, len(df) - 1):
        train = df.iloc[:t]            # Only past data
        truth = df.iloc[t]              # Hold out
        P = build_matrix(train)
        forecast = run_forecast(P, ...)
        results.append(compare(forecast, truth))
    return results
```

## Caching

Transition matrices and simulation runs are expensive. Cache in DuckDB:

```python
# ✅ Cache-key includes dataset version + model_type + period
cache_key = f"{dataset_id}::{model_type}::{period}"

# Look up first, compute if miss, persist on success
```

Invalidate cache when:
- Underlying dataset rows change
- Calibration table changes
- Model implementation changes (bump model version in code)

## State Discretization

For continuous data (e.g., price in cents), discretize into states with consistent rules:

```python
DEFAULT_N_STATES = 10   # Chan 2015 + Becker convention
# State i contains values in [i/n, (i+1)/n) for normalized values
```

Document any deviation in the dataset's `metadata_json`.

## Forbidden Practices

1. ❌ Using `pandas.crosstab` to build matrices without normalization — easy to forget rows must sum to 1
2. ❌ Using `np.random.seed()` (legacy) — use `np.random.default_rng(seed)`
3. ❌ Computing matrices on user-provided data without sparsity warnings
4. ❌ Using floats from sliders directly as probabilities without renormalizing the row
5. ❌ Conflating "market share" (proportion, m1/m2) with "customer count" (absolute, m3/m4)
