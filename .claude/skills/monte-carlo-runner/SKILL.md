---
name: monte-carlo-runner
description: Run a standardized Monte Carlo simulation over a transition matrix with reproducible seed, percentile confidence bands, and longshot-bias calibration applied. Use whenever the user asks for forecast probabilities, simulation results, or what-if scenarios.
allowed-tools: Read, Edit, Bash
---

# Monte Carlo Simulation Runner

Run a reproducible Monte Carlo simulation over a Markov transition matrix, producing both raw and calibrated probability estimates with confidence bands.

## When to Use

- User asks "what's the probability of X happening in N steps?"
- Generating fan charts for forecast pages
- Computing what-if scenario outcomes
- Backtesting model accuracy

## Standard Parameters

```python
DEFAULT_N_SIMULATIONS = 10_000
DEFAULT_N_STEPS = 12        # 1 year of monthly steps
CONFIDENCE_LEVELS = (0.10, 0.50, 0.90)   # 80% band + median
DEFAULT_SEED = 42           # from env DEFAULT_RANDOM_SEED
```

## Procedure

1. **Validate inputs:**
   - Run `markov-validator` skill on the matrix first
   - Verify `start_state` is in valid range [0, n_states)
   - Verify `n_steps >= 1` and `n_simulations in [100, 100_000]`

2. **Run the simulation:**
   ```python
   from core.simulation import monte_carlo_simulate, calibrate_probability
   
   raw_paths = monte_carlo_simulate(
       matrix=P,
       start_state=start,
       n_steps=n_steps,
       n_simulations=n_simulations,
       seed=seed,  # for reproducibility
   )
   ```

3. **Compute percentile bands:**
   ```python
   import numpy as np
   p10 = np.percentile(raw_paths, 10, axis=0)
   p50 = np.percentile(raw_paths, 50, axis=0)
   p90 = np.percentile(raw_paths, 90, axis=0)
   ```

4. **Calibrate raw probability** (per Becker 2026 longshot-bias table):
   ```python
   raw_prob = (raw_paths[:, -1] >= threshold).mean()
   calibrated_prob = calibrate_probability(raw_prob)
   ```

5. **Cache the result** in `simulation_runs` table for future re-use.

6. **Return** a `SimulationResult` dataclass with all artifacts.

## Output Format

```
## Monte Carlo Run

**Inputs:**
- Matrix: shape (10, 10)
- Start state: 4 (40-50 range)
- Horizon: 12 steps
- Simulations: 10,000
- Seed: 42

**Results:**
- Raw probability (YES at horizon): 0.582
- Calibrated probability: 0.547 (-0.035 from longshot calibration)
- Percentile bands at horizon: p10=0.32, p50=0.54, p90=0.78

**Edge analysis:**
- Market price: 0.45
- Edge: +0.097 (calibrated prob - market price)
- Quarter-Kelly position: 4.8% of bankroll

**Cached at:** simulation_runs.id = "sim_a8f3..."
```

## DO NOT

- ❌ Skip calibration — raw probs are systematically biased for extreme values
- ❌ Re-run a simulation with same inputs without checking cache first
- ❌ Use legacy `np.random.seed()` — use `np.random.default_rng(seed)`
- ❌ Return paths without percentile aggregation for charts (would explode memory)
