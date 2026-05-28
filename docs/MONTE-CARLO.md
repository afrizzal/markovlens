# Monte Carlo Simulation & Calibration

> Methodology: 10,000-path simulation + Becker (2026) longshot-bias calibration + walk-forward validation.

## Overview

Monte Carlo simulation answers the question:

> "Given the current state and the transition matrix, what's the **full distribution** of possible outcomes N steps ahead?"

Instead of computing analytically, we sample 10,000 random walks through the Markov chain and observe where they end up. The frequency of each terminal state estimates the true probability.

## Why Monte Carlo (vs. Analytical)

For small horizons and small state spaces, analytical computation via matrix powers (`Y_{t+1} = Y_t · P^t`) gives the **expected** distribution. But Monte Carlo also gives:

- **Confidence bands** (p10, p50, p90 across simulations)
- **Tail risk** estimates (probability of extreme outcomes)
- **Path-dependent metrics** (e.g., "what's the probability we ever cross 50% share?")
- **What-if injection** at intermediate steps

The same method physicists used for the first nuclear reactors. The downside: noisy, requires N → ∞ for convergence. With N=10,000 the Monte Carlo error on a probability estimate is ~0.5% standard deviation — usually acceptable.

## Implementation

### Pseudo-code

```python
def monte_carlo_simulate(
    matrix: np.ndarray,
    start_state: int,
    n_steps: int = 12,
    n_simulations: int = 10_000,
    seed: int = 42,
) -> np.ndarray:
    """Returns shape (n_simulations, n_steps+1) array of state sequences."""
    rng = np.random.default_rng(seed)
    n_states = matrix.shape[0]
    paths = np.zeros((n_simulations, n_steps + 1), dtype=int)
    paths[:, 0] = start_state
    for t in range(n_steps):
        for sim in range(n_simulations):
            current = paths[sim, t]
            paths[sim, t + 1] = rng.choice(n_states, p=matrix[current])
    return paths
```

**Vectorized version (much faster):**

```python
def monte_carlo_simulate_vectorized(
    matrix: np.ndarray,
    start_state: int,
    n_steps: int = 12,
    n_simulations: int = 10_000,
    seed: int = 42,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n_states = matrix.shape[0]
    paths = np.zeros((n_simulations, n_steps + 1), dtype=np.int32)
    paths[:, 0] = start_state
    
    # Pre-compute cumulative probabilities for each row (for inverse-CDF sampling)
    cum_matrix = matrix.cumsum(axis=1)
    
    for t in range(n_steps):
        u = rng.random(n_simulations)  # Uniform random
        current_states = paths[:, t]
        cum_probs = cum_matrix[current_states]  # shape (n_simulations, n_states)
        paths[:, t + 1] = (u[:, None] < cum_probs).argmax(axis=1)
    return paths
```

The vectorized version runs 10,000 sims × 12 steps in ~50ms.

## Aggregation

After simulation, aggregate to user-friendly outputs:

```python
# Final state distribution (counts per state)
final_states = paths[:, -1]
distribution = np.bincount(final_states, minlength=n_states) / n_simulations

# Confidence bands at each time step (for fan chart)
# Convert paths (state indices) to a target metric, e.g., "P(state >= threshold)"
target_probs = (paths >= threshold).astype(float)  # shape (n_sims, n_steps+1)
p10 = np.percentile(target_probs, 10, axis=0)
p50 = np.percentile(target_probs, 50, axis=0)
p90 = np.percentile(target_probs, 90, axis=0)

# Raw probability of resolution = YES at horizon
raw_prob_yes = (paths[:, -1] >= threshold).mean()
```

## Calibration: The Longshot Bias Problem

**Empirical observation (Becker 2026, 72.1M Polymarket trades):**
Raw probability estimates from naive models systematically OVERESTIMATE extreme events.

| Market price | Actual win rate |
|---|---|
| 1¢ | 0.43% (predicted 1.0%) |
| 5¢ | 4.18% (predicted 5.0%) |
| 50¢ | ~50% (predicted ~50%, fair) |
| 95¢ | 95.8% (predicted 95.0%) |

Without calibration, a Markov-based forecasting tool would lie to users about tail risk.

### Calibration Table

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

### Calibration Function

```python
def calibrate_probability(raw_prob: float) -> float:
    """Linear-interpolate raw probability against Becker (2026) longshot table."""
    keys = sorted(LONGSHOT_CALIBRATION.keys())
    if raw_prob <= keys[0]:
        return LONGSHOT_CALIBRATION[keys[0]]
    if raw_prob >= keys[-1]:
        return LONGSHOT_CALIBRATION[keys[-1]]
    for i in range(len(keys) - 1):
        lo, hi = keys[i], keys[i + 1]
        if lo <= raw_prob <= hi:
            frac = (raw_prob - lo) / (hi - lo)
            return LONGSHOT_CALIBRATION[lo] + frac * (LONGSHOT_CALIBRATION[hi] - LONGSHOT_CALIBRATION[lo])
    return raw_prob  # unreachable
```

### When NOT to Apply Calibration

The Becker calibration was derived from **prediction market** data (binary YES/NO contracts). It applies cleanly to:

- ✅ Probability of a single discrete event (e.g., "P(brand A market leader at horizon)")
- ✅ Tail probabilities in a categorical forecast

It does NOT cleanly apply to:

- ⚠️ Continuous-valued forecasts (e.g., "expected revenue") — use prediction intervals from the Monte Carlo distribution directly
- ⚠️ Calibration for non-binary categories — the table assumes binary YES/NO

For MarkovLens, we apply calibration when the user asks for `P(state in target set)`. We do NOT apply it to forecasted shares directly (those are means, not probabilities).

## Walk-Forward Validation

**Critical rule:** never let future data leak into past matrix estimates during backtests.

```python
def walk_forward_backtest(df: pd.DataFrame, min_window: int = 12) -> list[ForecastResult]:
    """Re-fit at each step using only past data."""
    results = []
    for t in range(min_window, len(df) - 1):
        train = df.iloc[:t]              # Past only
        truth = df.iloc[t]                # Held out
        P = build_transition_matrix(train)
        forecast = monte_carlo_simulate(P, ...)
        results.append(compare_forecast_to_truth(forecast, truth))
    return results
```

**Common bug:** computing P from all data, then "testing" on points already in training. This gives misleadingly good results because the test set leaked into the model.

## Metrics

We report two metrics per backtest:

### MAPE (Mean Absolute Percentage Error)

```python
mape = np.mean(np.abs((actual - forecast) / actual)) * 100
```

- For market share forecasts (continuous values)
- Lower is better; <10% is "good", <5% is "excellent"

### Brier Score

```python
brier = np.mean((forecast_prob - actual_outcome) ** 2)
```

- For probabilistic forecasts (binary outcomes)
- Lower is better; 0 = perfect, 0.25 = random guess

## Reproducibility

**Always pass a seed** for reproducible runs:

```python
result = monte_carlo_simulate(matrix, start, n_steps, n_simulations, seed=42)
```

- Default seed: 42 (configurable via env `DEFAULT_RANDOM_SEED`)
- Cache key includes seed — same inputs → cache hit
- Different seeds give different paths but converge to same distribution as N → ∞

## Performance Targets

| Operation | Target | Notes |
|---|---|---|
| 10,000 sims × 12 steps × 10 states | < 100ms | Vectorized impl |
| 50,000 sims × 24 steps × 20 states | < 1s | For deep what-if |
| Cache lookup | < 5ms | DuckDB indexed |

## References

- Becker (2026). *72.1M Polymarket Trade Analysis* — empirical longshot calibration source
- Metropolis, N. (1949). *The Monte Carlo Method*. Journal of the American Statistical Association 44(247). [original Monte Carlo paper]
- Chan, K. C. (2015) — Section 3, Numerical Example, uses analytical (not Monte Carlo) computation. MarkovLens adds the Monte Carlo layer for confidence bands.
