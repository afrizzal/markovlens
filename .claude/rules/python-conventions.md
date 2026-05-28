# Python Conventions — MarkovLens

## Version & Tooling

- **Python 3.12+** — required (uses modern syntax features)
- **uv** for all dependency management — never `pip install` directly
- **ruff** for linting + formatting (single tool, replaces black/isort/flake8)
- **mypy** for type checking — strict mode for `core/` and `domains/`

## Type Hints

```python
# ✅ Always type-hint public functions
def build_transition_matrix(
    transitions: np.ndarray,
    n_states: int,
    *,
    smoothing: float = 0.0,
) -> np.ndarray:
    """Build a transition matrix from observed transitions."""
    ...

# ✅ Use type aliases for complex types
from typing import TypeAlias
TransitionMatrix: TypeAlias = np.ndarray  # shape (n_states, n_states)
StateVector: TypeAlias = np.ndarray       # shape (n_states,)

# ✅ Pydantic models for config + DB rows
from pydantic import BaseModel, Field

class SimulationConfig(BaseModel):
    n_simulations: int = Field(default=10_000, ge=100, le=100_000)
    n_steps: int = Field(default=12, ge=1, le=120)
    seed: int | None = None
```

## Imports

```python
# ✅ Standard order (ruff enforces):
# 1. stdlib
import json
from pathlib import Path

# 2. third-party
import numpy as np
import pandas as pd
import streamlit as st

# 3. local
from core.models import MarkovModel
from core.simulation import run_monte_carlo
```

## Error Handling

- **Validate at boundaries only** — user input, file loading, DB queries
- **Trust internal contracts** — no defensive null-checks within `core/`
- **Raise specific exceptions** — `ValueError`, `KeyError`, custom domain exceptions
- **Never silent except** — `except Exception: pass` is forbidden

```python
# ✅ Boundary validation
def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    df = pd.read_csv(path)
    required = {"entity_id", "period", "state"}
    if missing := required - set(df.columns):
        raise ValueError(f"Missing required columns: {missing}")
    return df

# ❌ Defensive paranoia inside core
def compute_share(matrix: np.ndarray) -> float:
    # NO — matrix is internal, trust it
    if matrix is None or len(matrix) == 0:
        return 0.0
    ...
```

## Numerical Code

- **Use NumPy for vectorized ops** — never loop over arrays in pure Python
- **Use `np.float64` for probabilities** — avoid `float32` accumulation errors
- **Set seed via `np.random.default_rng(seed)`** — never use legacy `np.random.seed()`
- **Validate matrix invariants** — rows sum to 1.0 (within tolerance), no negatives

```python
# ✅ Use the new RNG API
def monte_carlo(matrix: np.ndarray, start: int, n_steps: int, seed: int | None = None) -> int:
    rng = np.random.default_rng(seed)
    state = start
    for _ in range(n_steps):
        state = rng.choice(len(matrix), p=matrix[state])
    return state

# ✅ Validate invariants
def assert_transition_matrix(P: np.ndarray, tol: float = 1e-9) -> None:
    assert P.ndim == 2 and P.shape[0] == P.shape[1], "must be square"
    assert (P >= 0).all(), "no negative probabilities"
    row_sums = P.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=tol), f"rows must sum to 1.0, got {row_sums}"
```

## Pure vs Side-Effectful

| Layer | Allowed side effects |
|---|---|
| `core/` | DB writes (only via `core/db/`); logging |
| `domains/` | Same as core |
| `app/` | Streamlit state, file I/O, network calls |
| `tests/` | Anything (tests should be hermetic per test) |

## Docstrings

NumPy style for public API:

```python
def calibrate_probability(raw_prob: float) -> float:
    """Adjust raw model probability against empirical longshot bias.

    Parameters
    ----------
    raw_prob : float
        Raw probability from Monte Carlo simulation, in [0, 1].

    Returns
    -------
    float
        Calibrated probability, in [0, 1].

    Notes
    -----
    Based on Becker (2026) analysis of 72.1M Polymarket trades.
    See docs/MONTE-CARLO.md for the full calibration table.

    Examples
    --------
    >>> calibrate_probability(0.05)
    0.0418
    """
    ...
```

Private helpers (leading `_`): one-line docstring is fine.

## File Size

- Modules: aim for < 300 lines. Split if larger.
- Functions: aim for < 50 lines. Extract helpers if larger.
- Classes: prefer composition over deep inheritance.

## Comments

- **Default: no comments.** Well-named code self-documents.
- **Exception: hidden constraints, workarounds, references to papers.**

```python
# ✅ Good comment — explains a non-obvious constraint
# Chan 2015 Eq.(2): t-fold matrix product for time-varying P
Y_next = Y_initial @ np.linalg.multi_dot([P_t for P_t in transition_history])

# ❌ Bad comment — restates the code
# Multiply Y by P to get next Y
Y_next = Y @ P
```
