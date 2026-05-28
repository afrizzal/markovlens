# Markov Models — Mathematical Reference

> Based on Chan, K. C. (2015). *Market Share Modelling and Forecasting Using Markov Chains and Alternative Models*. International Journal of Innovative Computing, Information and Control, Vol. 11, No. 4, pp. 1205-1218. ISSN 1349-4198.

This document derives the four model formulations and provides worked numerical examples.

## Notation

Throughout this document:

| Symbol | Meaning |
|---|---|
| `M` | Number of providers/states (e.g., 4 brands) |
| `s_i` | State i (e.g., provider/brand i), where i ∈ {1, ..., M} |
| `T` | Set of time steps {1, 2, ..., t_max} |
| `X_t` | Random variable: state at time t |
| `p_{i,j}` | Probability of moving from state i to state j |
| `P` | Transition probability matrix, shape (M, M), where `P[i,j] = p_{i,j}` |
| `P_t` | Time-varying transition matrix at time t |
| `Y_t` | Market share vector at time t, shape (1, M), where Σ y_t(s_k) = 1 |
| `Q_t` | Population (customer count) vector at time t, shape (1, M) |
| `G` | Growth multiplier vector, shape (1, M), `G[i] = g_i` |
| `M_t` | Total market size at time t (sum of Q_t components) |

## Properties of Transition Matrix

A valid `P` (or `P_t`) must satisfy:

1. **Non-negative:** `0 ≤ p_{i,j} ≤ 1` for all (i, j)
2. **Row-stochastic:** `Σ_j p_{i,j} = 1` for all i (each row is a probability distribution)
3. **Square:** shape (M, M) where M = number of states

These must be checked programmatically — see `core/models.py::validate_transition_matrix()`.

## Markov Property

The defining assumption:

```
P{X_{t+1} = j | X_t = i, X_{t-1} = i_{t-1}, ..., X_1 = i_1} = P{X_{t+1} = j | X_t = i}
```

In plain English: the probability of next state depends ONLY on current state, not history. This is what makes the math tractable.

Models m1, m2, m3 all satisfy this. Model m4 does NOT — it's a non-Markov alternative.

---

## Model m1 — Homogeneous Markov

**Assumption:** Transition matrix `P` is **constant** over time.

**Formulation:**

```
P{X_{t+1} = j | X_t = i} = p_{i,j}    (independent of t)
```

**Market share forecast:**

```
Y_{t+1} = Y_t · P
```

Iterating from initial state:

```
Y_2 = Y_1 · P
Y_3 = Y_2 · P = Y_1 · P²
Y_{t+1} = Y_1 · P^t                    ...(Equation 1 in paper)
```

**Customer count:**

```
Q_t = M_t · Y_t
```

where `M_t` is total market size (assumed constant under m1).

**Suitable for:** Stable markets, fixed total market size, switching patterns that don't drift over time.

**Limitations:**
- Cannot model market growth/shrinkage
- Cannot model changes in switching dynamics (e.g., new competitor disrupting)

---

## Model m2 — Time-Varying Markov

**Assumption:** Transition matrix `P_t` **varies** at each time step. Total market size still constant.

**Formulation:**

```
Y_2 = Y_1 · P_1
Y_3 = Y_2 · P_2 = Y_1 · P_1 · P_2
Y_{t+1} = Y_1 · ∏_{n=1}^{t} P_n         ...(Equation 2 in paper)
```

**Suitable for:** Dynamic markets where competitive intensity, marketing spend, or external shocks shift transition probabilities over time.

**Estimation:** Requires `P_t` per time step from data. Either:
- Use raw observed transitions at each step (high variance for short windows)
- Assume `P_{t+1} = P_t + ΔP` linear drift (smoother)
- Bayesian smoothing (more advanced; not in v1)

**Limitations:**
- Still cannot model total market growth/shrinkage
- More parameters to estimate; needs more data per time step

---

## Model m3 — Extended Time-Varying Markov (with Growth Multiplier)

**Assumption:** Like m2 (time-varying `P_t`) PLUS individual provider market size can grow/shrink via multiplier `G`.

**Formulation:**

```
Q_{t+1} = G ⊙ Q_t · P_t
        = [g_1 · q_t(s_1), g_2 · q_t(s_2), ..., g_M · q_t(s_M)] · P_t       ...(Equation 3 in paper)
```

where `⊙` is element-wise multiplication.

**The growth multiplier `G`** captures:
- New customers entering the market (joining)
- Existing customers permanently leaving
- `g_i > 1` → provider i is gaining; `g_i < 1` → shrinking

**Suitable for:** Markets in growth or contraction phase, product lifecycle modeling, scenarios where some competitors are gaining while overall market shifts.

**Two-step interpretation of Equation 3:**
1. Adjust each provider's customer count by its growth multiplier: `Q_t' = G ⊙ Q_t`
2. Apply transition probabilities to redistribute: `Q_{t+1} = Q_t' · P_t`

**Estimation of G:**
```
g_i = Q_{t+1}(s_i) / Q_t(s_i)    (ratio of provider's customer counts across periods)
```

**Limitations:**
- `G` is assumed constant (can be extended to time-varying `G_t` for product lifecycle phases)
- Assumes the "natural" customer movement (Markov part) is separable from "market size" movement (G part)

---

## Model m4 — Non-Markov (Deferred to v0.2)

**Assumption:** NO Markov property. Each *category* of customer (group with same from-state/to-state pattern) follows its own trend independently.

**Definition:** Category `n_{t|i,j}` = number of customers moving from state i to state j at time t.

**Formulation (Equation 5 in paper):**

```
N_{t+1} = [max(0, n_{t|i,j} + q_t(s_i) · n'_{i,j}) for all (i, j)]
```

where `N'` is a constant matrix of *relative changes* in customer counts (estimated from history).

**Conceptually:** Instead of asking "where will customer in state i go?", asks "how many customers will be in the i→j category at the next period?" — each category has its own growth.

**Why deferred:** Different conceptual model, different UI/visualization needed. v0.1 focus is on the 3 Markov variants for model comparison.

---

## Worked Numerical Example (from Chan 2015, Tables 1-2)

Telecommunications industry, 4 providers: `Incumbent`, `NextGen`, `CowBoy`, `Others`.

### Initial data (2010 → 2011 subscriber counts)

| From \ To | Incumbent | NextGen | CowBoy | Others | Total |
|---|---|---|---|---|---|
| Incumbent | 1,600,000 | 12,000 | 7,000 | 8,300 | 1,627,300 |
| NextGen | 8,900 | 750,000 | 20,000 | 1,400 | 780,300 |
| CowBoy | 1,800 | 1,200 | 125,000 | 2,776 | 130,000 |
| Others | 3,200 | 1,750 | 2,250 | 166,000 | 173,200 |

### m1 transition matrix `P` (averaged across periods)

```
P = [[0.98230  0.00753  0.00464  0.00552]
     [0.01158  0.96161  0.02489  0.00192]
     [0.01442  0.01105  0.95721  0.01732]
     [0.01978  0.01122  0.01364  0.95536]]
```

**Verify:** each row sums to 1.0. ✅

### m1 forecast (next 5 years), starting from Y_1 = [0.5878, 0.2830, 0.0585, 0.0708]

| t | Incumbent | NextGen | CowBoy | Others |
|---|---|---|---|---|
| 1 | 0.5878 | 0.2830 | 0.0585 | 0.0708 |
| 2 | 0.5829 | 0.2780 | 0.0667 | 0.0724 |
| 3 | 0.5782 | 0.2733 | 0.0745 | 0.0741 |
| 4 | 0.5737 | 0.2688 | 0.0818 | 0.0758 |
| 5 | 0.5693 | 0.2645 | 0.0887 | 0.0775 |
| 6 | 0.5651 | 0.2605 | 0.0951 | 0.0792 |

CowBoy is growing — consistent with their observed gains.

### m3 forecast (with growth multiplier G)

```
G = [1.0315, 1.0561, 0.9029, 1.0897]
```

| t | Incumbent | NextGen | CowBoy | Others | Q_t (total) |
|---|---|---|---|---|---|
| 1 | 0.5878 | 0.2830 | 0.0585 | 0.0708 | 2,806,396 |
| 2 | 0.5799 | 0.2847 | 0.0603 | 0.0751 | 2,904,830 |
| 3 | 0.5716 | 0.2871 | 0.0618 | 0.0795 | 3,006,878 |
| 4 | 0.5630 | 0.2904 | 0.0629 | 0.0838 | 3,112,896 |
| 5 | 0.5540 | 0.2944 | 0.0636 | 0.0879 | 3,223,242 |
| 6 | 0.5448 | 0.2991 | 0.0642 | 0.0919 | 3,338,269 |

Note: m3 captures absolute customer counts AND market growth, unlike m1.

---

## Model Selection Guide

| Market characteristic | Best model |
|---|---|
| Stable, mature market, fixed size | m1 |
| Dynamic, changing competitive intensity | m2 |
| Growing/shrinking market with shifting dynamics | m3 |
| Need to model heterogeneous customer journeys | m4 (future) |

In MarkovLens, we expose all three to the user as **a model comparison panel** — let them see which fits their data best by MAPE/Brier score.

---

## Implementation in `core/models.py`

```python
class M1Homogeneous:
    """Constant transition matrix P. Y_{t+1} = Y_t · P."""
    def __init__(self, P: np.ndarray): ...
    def forecast(self, Y_1: np.ndarray, horizon: int) -> np.ndarray: ...

class M2TimeVarying:
    """Time-varying P_t. Y_{t+1} = Y_t · P_t."""
    def __init__(self, P_t_sequence: list[np.ndarray]): ...
    def forecast(self, Y_1: np.ndarray, horizon: int) -> np.ndarray: ...

class M3Extended:
    """With growth multiplier G. Q_{t+1} = (G ⊙ Q_t) · P_t."""
    def __init__(self, P_t_sequence: list[np.ndarray], G: np.ndarray): ...
    def forecast(self, Q_1: np.ndarray, horizon: int) -> np.ndarray: ...
```

See [.claude/rules/markov-patterns.md](../.claude/rules/markov-patterns.md) for validation requirements.

## References

1. Chan, K. C. (2015). *Market Share Modelling and Forecasting Using Markov Chains and Alternative Models*. IJICIC 11(4), 1205-1218.
2. Armstrong & Farley (1969). *A note on the use of Markov chains in forecasting store choice*. Management Science 16(4).
3. Ehrenberg (1965). *An appraisal of Markov brand-switching models*. Journal of Marketing Research 2(4).

See the `References` section of Chan 2015 (paper pages 1217-1218) for the full citation list.
