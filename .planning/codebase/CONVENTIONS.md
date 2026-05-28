# Coding Conventions

## Language & Tooling

- **Python 3.12+** — modern syntax features used throughout
- **ruff** — linting + formatting (replaces black/isort/flake8); 100-char line length
- **mypy** — strict type checking enforced on `core/` and `domains/`
- **uv** — dependency management (never `pip install` directly)

## Type Hints

- Type hints on all public functions — non-negotiable
- Type aliases defined at module level: `TransitionMatrix: TypeAlias = np.ndarray`
- Pydantic `BaseModel` / `BaseSettings` for config and structured return types
- `@dataclass(frozen=True)` for immutable value objects (e.g. `SimulationResult`)

```python
def build_transition_matrix(
    transitions: np.ndarray,
    n_states: int,
    *,
    smoothing: float = 0.0,
) -> np.ndarray: ...
```

## Naming

| Item | Convention | Example |
|---|---|---|
| Modules/files | `snake_case` | `transition_matrix.py` |
| Classes | `PascalCase` | `MarkovModel`, `SimulationRunner` |
| Functions | `snake_case` | `build_transition_matrix` |
| Constants | `UPPER_SNAKE` | `DEFAULT_N_SIMULATIONS` |
| Private helpers | leading `_` | `_compute_quantile_bands` |
| DB tables | `snake_case` plural | `transition_matrices` |
| Streamlit pages | `N_PascalCase.py` | `1_Brand_Share.py` |

## Error Handling

- Validate at boundaries only (user input, file I/O, DB queries)
- Trust internal contracts — no defensive null-checks within `core/`
- Raise specific exceptions: `ValueError`, `KeyError`, custom domain exceptions from `core/exceptions.py`
- Silent `except Exception: pass` is forbidden
- User-facing error messages are actionable (tell user what to do, not internal jargon)

## Layer Separation

- `core/` and `domains/` are **pure** — no `import streamlit` allowed
  - Verify: `grep -r "import streamlit" core/ domains/` must return empty
- All SQL wrapped in `core/db/queries.py` — never inline SQL strings in `app/`
- Pages call domain services; services call core (no layer skipping)

## Numerical Code

- Vectorized NumPy operations — never loop over arrays in pure Python
- `np.float64` for probabilities (avoid float32 accumulation errors)
- `np.random.default_rng(seed)` — never legacy `np.random.seed()`
- Validate matrix invariants: rows sum to 1.0, no negatives

## Constants

- No magic numbers — extract to module-level `UPPER_SNAKE` constants
- Reference: `core/simulation.py` holds `LONGSHOT_CALIBRATION`, `DEFAULT_N_SIMULATIONS`, etc.

## Comments

- Default: **no comments** — naming self-documents
- Comment only for: paper references (`# Chan 2015 Eq.(3)`), workarounds, non-obvious invariants
- Never restate what the code does

## Imports

Auto-sorted by ruff. Order: stdlib → third-party → local. No wildcards, no relative cross-package imports.

## Docstrings

NumPy style on public functions: Parameters / Returns / Notes / Examples sections.
Private helpers: one-line docstring is sufficient.
