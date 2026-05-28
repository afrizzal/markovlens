# Coding Style — MarkovLens

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Modules | snake_case | `transition_matrix.py`, `monte_carlo.py` |
| Classes | PascalCase | `MarkovModel`, `SimulationRunner` |
| Functions | snake_case | `build_transition_matrix`, `run_simulation` |
| Constants | UPPER_SNAKE | `DEFAULT_N_SIMULATIONS`, `MIN_OBSERVATIONS` |
| Private (module) | leading `_` | `_compute_quantile_bands` |
| Type aliases | PascalCase | `TransitionMatrix`, `StateVector` |
| DB tables | snake_case plural | `transitions`, `simulation_runs` |
| DB columns | snake_case | `entity_id`, `from_state`, `created_at` |
| Streamlit pages | `N_PascalCase.py` | `1_Brand_Share.py` |
| CSS classes | kebab-case | `kpi-card`, `accent-bar` |

## File Organization

```
core/                        # Domain-agnostic engine
├── __init__.py
├── config.py                # Settings via pydantic-settings
├── db/
│   ├── connection.py
│   ├── schema.sql
│   └── queries.py           # All SQL wrapped here
├── io/
│   ├── loaders.py
│   └── exporters.py
├── models.py                # m1, m2, m3 implementations
├── simulation.py            # Monte Carlo + calibration
└── metrics.py               # MAPE, Brier, log-loss

domains/                     # Domain-specific logic
├── brand_share/
│   ├── __init__.py
│   ├── service.py           # Orchestration (calls core/)
│   ├── transforms.py        # Domain-specific data shaping
│   └── presets.py           # Default configs for this domain
└── churn/
    └── (same structure)

app/                         # Streamlit (UI only)
├── Home.py
├── pages/
├── components/
└── styles/
```

## Function Design

- **Single responsibility** — function name tells you exactly what it does
- **< 50 lines** — split if larger
- **Keyword-only arguments after positional core**:
  ```python
  def run_simulation(
      matrix: np.ndarray,
      start_state: int,
      *,
      n_steps: int = 12,
      n_simulations: int = 10_000,
      seed: int | None = None,
  ) -> SimulationResult: ...
  ```
- **Return dataclass/Pydantic for multi-value returns** — not tuples

## Class Design

Prefer composition over inheritance:

```python
# ✅ Composition
class MarkovModel:
    def __init__(self, matrix: np.ndarray, validator: Validator):
        self.matrix = matrix
        self.validator = validator

# ❌ Deep inheritance
class M1Model(BaseModel):
    class TimeVaryingM1Model(M1Model):
        class ExtendedTimeVaryingM1Model(TimeVaryingM1Model): ...
```

Use `@dataclass(frozen=True)` for value objects:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SimulationResult:
    final_distribution: np.ndarray
    quantile_paths: dict[float, np.ndarray]
    raw_probability: float
    calibrated_probability: float
    n_simulations: int
    seed: int | None
```

## Constants

No magic numbers. Extract to module-level constants:

```python
# ✅ Top of module
DEFAULT_N_SIMULATIONS: int = 10_000
DEFAULT_N_STATES: int = 10
MIN_OBSERVATIONS_PER_CELL: int = 20
CONFIDENCE_LEVELS: tuple[float, ...] = (0.10, 0.50, 0.90)
PROBABILITY_TOLERANCE: float = 1e-9

# ✅ Use them
if n_obs < MIN_OBSERVATIONS_PER_CELL:
    warn_sparsity(...)

# ❌ Magic numbers
if n_obs < 20:  # what does 20 mean?
    ...
```

## Comments

**Default: no comments.** Code should self-document via naming.

**Write a comment ONLY for:**
1. Reference to a paper/external source: `# Chan 2015 Eq.(3)`
2. Workaround for a specific bug: `# Workaround: DuckDB 1.1 returns wrong type for JSON in older API`
3. Non-obvious invariant: `# matrix is already validated by caller — skip re-check for hot path`
4. Counter-intuitive choice: `# Using float32 here intentionally — precision tradeoff for speed in batch sim`

**Never:**
- ❌ Restate what the code does: `# multiply matrix by vector`
- ❌ Reference current task/ticket: `# fix for issue #42`
- ❌ TODO without owner+date: `# TODO: fix this`  → use `# TODO(afrizzal, 2026-06-15): ...`

## Imports

Auto-sorted by ruff. Order:

```python
"""Module docstring."""
from __future__ import annotations  # if needed for older type syntax

# stdlib
import json
import logging
from pathlib import Path
from typing import TypeAlias

# third-party
import duckdb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# local
from core.config import settings
from core.db.connection import get_connection
from core.models import MarkovModel
```

No wildcard imports (`from x import *`). No relative imports across packages.

## Error Messages

User-facing messages: actionable, no jargon.

```python
# ✅ Tells user what to do
raise ValueError(
    "Dataset 'foo' has only 5 transitions in state 'Bronze' — "
    "need at least 20. Try merging Bronze and Silver states."
)

# ❌ Internal-only
raise ValueError(f"sparsity {n_obs}<{MIN_OBSERVATIONS_PER_CELL} for state {state}")
```

## Logging

Use `logging`, not `print`. Configured centrally in `core/config.py`.

```python
import logging
log = logging.getLogger(__name__)

log.info("Building transition matrix for dataset=%s, model=%s", dataset_id, model_type)
log.warning("Sparsity detected: %d cells below threshold", n_sparse)
log.error("Failed to load dataset", exc_info=True)
```

In Streamlit: use `log` for diagnostics, `st.warning`/`st.error` for user-visible messages.

## Tests

- One test file per module: `core/models.py` → `tests/unit/test_models.py`
- Test names describe the contract: `test_transition_matrix_rows_sum_to_one`
- AAA pattern: Arrange, Act, Assert
- Use fixtures for shared setup (`conftest.py`)
- Mark slow tests: `@pytest.mark.slow` (deselect with `-m "not slow"`)

```python
def test_monte_carlo_with_fixed_seed_is_reproducible():
    # Arrange
    matrix = np.array([[0.7, 0.3], [0.4, 0.6]])
    
    # Act
    result1 = run_monte_carlo(matrix, start=0, n_steps=10, n_simulations=1000, seed=42)
    result2 = run_monte_carlo(matrix, start=0, n_steps=10, n_simulations=1000, seed=42)
    
    # Assert
    assert result1.calibrated_probability == result2.calibrated_probability
```
