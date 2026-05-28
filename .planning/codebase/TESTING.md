# Testing

## Framework & Config

- **pytest 8.3.0+** configured in `pyproject.toml`
- **pytest-cov** for coverage reporting
- **pytest-mock** for mocking

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast, pure function tests (no I/O)
│   └── test_*.py
└── integration/         # Tests hitting real DuckDB (tmp_path fixture)
    └── test_*.py
```

One test file per module: `core/models.py` → `tests/unit/test_models.py`

## Markers

- `@pytest.mark.slow` — deselect with `-m "not slow"`
- `@pytest.mark.integration` — run separately with `-m integration`

## Shared Fixtures (conftest.py)

```python
sample_2x2_matrix       # Simple 2-state transition matrix
sample_4x4_chan_matrix   # 4-state matrix from Chan (2015)
temp_duckdb_path        # Temporary DuckDB file (cleaned up per test)
```

## Test Pattern (AAA)

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

## Mocking Policy

- **Integration tests use real DuckDB** — no mocking the database
- Mock only external APIs and filesystem boundaries
- `tmp_path` fixture provides isolated DB per test

## Current State

- Framework is scaffolded and ready
- Tests are currently skipped (Phase 01 implementation pending)
- Coverage target: > 80% for `core/`
- Pure functions in `core/` must have unit tests

## Run Commands

```bash
uv run pytest                      # All tests
uv run pytest -m "not slow"        # Skip slow tests
uv run pytest -m integration       # Integration only
uv run pytest --cov=core           # With coverage
```
