---
phase: 01-markov-engine
plan: 02
type: execute
wave: 2
depends_on:
  - 01
files_modified:
  - core/models.py
  - tests/unit/test_models.py
autonomous: true
requirements:
  - ENG-01
  - ENG-02
  - ENG-03
  - ENG-04
  - ENG-08
must_haves:
  truths:
    - "validate_transition_matrix() raises InvalidTransitionMatrixError on non-square / negative / unnormalized / non-float64 matrices"
    - "validate_transition_matrix() logs a sparsity warning (not an exception) when transition_counts contains cells below MIN_OBSERVATIONS_PER_CELL"
    - "M1Homogeneous.forecast() reproduces Chan 2015 Table 3 row at t=2 within atol=1e-3"
    - "M2TimeVarying constructor accepts np.ndarray of shape (n_periods, n_states, n_states) — NOT list[np.ndarray]"
    - "M2TimeVarying.forecast() holds last P_t constant when horizon exceeds n_periods (D-06)"
    - "M3Extended constructor accepts np.ndarray of shape (n_periods, n_states, n_states) for P_t and np.ndarray for G (D-08/D-09)"
    - "M3Extended.forecast() applies Q_{t+1} = (G ⊙ Q_t) · P_t with hold-last-P_t fallback (D-07)"
  artifacts:
    - path: "core/models.py"
      provides: "validate_transition_matrix, M1Homogeneous, M2TimeVarying, M3Extended"
      contains: "raise InvalidTransitionMatrixError"
    - path: "tests/unit/test_models.py"
      provides: "All 11 tests pass (4 existing + 7 previously skip-annotated)"
      contains: "test_m1_forecast_replicates_chan_2015_table3"
  key_links:
    - from: "core/models.py M1Homogeneous.__init__"
      to: "validate_transition_matrix"
      via: "validate_transition_matrix(P) call before assignment"
      pattern: "validate_transition_matrix\\(P"
    - from: "core/models.py M2TimeVarying.__init__"
      to: "np.ndarray shape (n_periods, n_states, n_states)"
      via: "shape validation in constructor"
      pattern: "P_t_sequence\\.shape"
    - from: "core/models.py validate_transition_matrix"
      to: "core.exceptions.InvalidTransitionMatrixError"
      via: "raise statement"
      pattern: "raise InvalidTransitionMatrixError"
---

<objective>
Implement matrix validation and all three Markov model classes per Chan (2015).

Purpose: validate_transition_matrix() is a prerequisite for every downstream model. Without it, no simulation, no forecast, no seed script can run. M1/M2/M3 forecasts are the mathematical core of the portfolio piece — incorrect math invalidates the entire project narrative.

Output:
- Working `core/models.py` with all stubs replaced by tested implementations
- All 11 tests in `tests/unit/test_models.py` pass (4 originals + 7 stubs un-skipped)
- Chan (2015) Table 3 regression test green within atol=1e-3
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-markov-engine/01-CONTEXT.md
@.planning/phases/01-markov-engine/01-RESEARCH.md
@.planning/phases/01-markov-engine/01-VALIDATION.md
@core/models.py
@core/exceptions.py
@tests/unit/test_models.py
@tests/conftest.py
@.claude/rules/markov-patterns.md
@.claude/rules/python-conventions.md
@.claude/skills/markov-validator/SKILL.md

<interfaces>
Existing stable contracts (do NOT change):

```python
# core/exceptions.py — already exists
class InvalidTransitionMatrixError(MarkovLensError): ...

# core/models.py — these stay, only fill in NotImplementedError bodies + update constructors
TransitionMatrix: TypeAlias = np.ndarray
StateVector: TypeAlias = np.ndarray
PopulationVector: TypeAlias = np.ndarray
MIN_OBSERVATIONS_PER_CELL: int = 20
PROBABILITY_TOLERANCE: float = 1e-9

@dataclass(frozen=True)
class ForecastResult:
    forecast_array: np.ndarray
    confidence_bands: dict[float, np.ndarray] | None
    model_type: str
    horizon: int
    accuracy_metrics: dict[str, float] | None = None
```

**BREAKING CHANGE in this plan (D-08, D-09):**
- `M2TimeVarying.__init__(self, P_t_sequence: list[TransitionMatrix])` → `M2TimeVarying.__init__(self, P_t_sequence: np.ndarray)` where shape is `(n_periods, n_states, n_states)`.
- `M3Extended.__init__(self, P_t_sequence: list[TransitionMatrix], G: np.ndarray)` → `M3Extended.__init__(self, P_t_sequence: np.ndarray, G: np.ndarray)` where `P_t_sequence` shape is `(n_periods, n_states, n_states)` and `G` shape is `(n_states,)` or `(n_periods, n_states)`.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement validate_transition_matrix() (ENG-01, ENG-08)</name>
  <read_first>
    - core/models.py (current stub — preserve type aliases, dataclasses, constants)
    - core/exceptions.py (InvalidTransitionMatrixError definition)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (section "Pattern 2: validate_transition_matrix() Implementation")
    - .claude/rules/markov-patterns.md (Mandatory Validations section)
    - .claude/skills/markov-validator/SKILL.md (7-check procedure)
    - tests/unit/test_models.py (verify what the 5 validation tests assert)
  </read_first>
  <behavior>
    - Valid 2x2 matrix [[0.7, 0.3], [0.4, 0.6]] dtype float64 passes silently (returns None).
    - Non-square matrix [[0.5, 0.5, 0.0]] (1x3) raises InvalidTransitionMatrixError.
    - Unnormalized matrix [[0.5, 0.5], [0.3, 0.3]] raises InvalidTransitionMatrixError.
    - Matrix with negative cell [[1.5, -0.5], [0.5, 0.5]] raises InvalidTransitionMatrixError.
    - Matrix with dtype float32 raises InvalidTransitionMatrixError.
    - Matrix containing NaN or Inf raises InvalidTransitionMatrixError.
    - Valid matrix with `transition_counts` array having any cell < MIN_OBSERVATIONS_PER_CELL (20) emits a logging.WARNING (does NOT raise).
    - All collected error messages joined into ONE exception (do not stop at first failure).
  </behavior>
  <action>
Replace the body of `validate_transition_matrix()` in `core/models.py` (line ~19-46) with the exact implementation below. KEEP the function signature, docstring, and the existing imports unchanged. Add `import logging` at the top of the module (after `import numpy as np`).

```python
def validate_transition_matrix(
    P: TransitionMatrix,
    transition_counts: np.ndarray | None = None,
    *,
    tol: float = PROBABILITY_TOLERANCE,
    min_obs: int = MIN_OBSERVATIONS_PER_CELL,
) -> None:
    """Validate matrix against MarkovLens invariants.

    Per `.claude/rules/markov-patterns.md` — collect ALL failures, raise once.

    Parameters
    ----------
    P : np.ndarray
        Transition matrix to validate, shape (M, M).
    transition_counts : np.ndarray | None
        Per-cell observation counts for sparsity check (logged, not raised).
    tol : float
        Tolerance for row-sum check.
    min_obs : int
        Minimum observations per cell.

    Raises
    ------
    InvalidTransitionMatrixError
        If any structural invariant fails (shape, dtype, NaN/Inf, sign, row-sum).
    """
    errors: list[str] = []

    if P.ndim != 2:
        errors.append(f"P must be 2D, got {P.ndim}D")
    elif P.shape[0] != P.shape[1]:
        errors.append(f"P must be square, got {P.shape}")
    else:
        if P.dtype != np.float64:
            errors.append(f"P must be float64, got {P.dtype}")
        if not np.isfinite(P).all():
            errors.append("P contains NaN or Inf values")
        else:
            if (P < 0).any():
                errors.append(f"P has negative values; min={P.min()}")
            if (P > 1.0 + tol).any():
                errors.append(f"P has values > 1; max={P.max()}")
            row_sums = P.sum(axis=1)
            if not np.allclose(row_sums, 1.0, atol=tol):
                bad = np.where(~np.isclose(row_sums, 1.0, atol=tol))[0]
                errors.append(
                    f"Rows {bad.tolist()} do not sum to 1.0; sums={row_sums[bad].tolist()}"
                )

    if errors:
        raise InvalidTransitionMatrixError("; ".join(errors))

    if transition_counts is not None:
        sparse_mask = transition_counts < min_obs
        if sparse_mask.any():
            sparse_cells = list(zip(*np.where(sparse_mask)))
            logging.getLogger(__name__).warning(
                "Sparsity detected: %d cells below min_obs=%d: first_five=%s",
                int(sparse_mask.sum()),
                min_obs,
                sparse_cells[:5],
            )
```

After replacing the function body, **un-skip the 4 validation tests** in `tests/unit/test_models.py`:
- `test_validate_transition_matrix_accepts_valid` (existing — skip already removed in Plan 01)
- `test_validate_transition_matrix_rejects_non_square` (existing — skip already removed in Plan 01)
- `test_validate_transition_matrix_rejects_unnormalized` (existing — skip already removed in Plan 01)
- `test_validate_rejects_negative` (new stub — REMOVE its `@pytest.mark.skip(reason="Wave 0 stub...")` decorator now)
- `test_validate_rejects_wrong_dtype` (new stub — REMOVE skip decorator)
- `test_validate_warns_sparse_cells` (new stub — REMOVE skip decorator)

Also update the conftest `sample_2x2_matrix` fixture indirectly: it currently returns a float64 array (numpy default). The existing test `test_validate_transition_matrix_accepts_valid` passes the raw fixture, but `np.array([[0.7, 0.3], [0.4, 0.6]])` defaults to `float64` on this NumPy version — verify with: `python -c "import numpy as np; print(np.array([[0.7, 0.3], [0.4, 0.6]]).dtype)"`. If it returns `float64` (it should on NumPy 2.x), no fixture change is needed. If not, edit `tests/conftest.py` to add `dtype=np.float64` explicitly.

Run: `uv run pytest tests/unit/test_models.py -k "validate" -x -q` — all 6 validation tests must pass green.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_models.py -k "validate" -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `core/models.py` contains the literal string `raise InvalidTransitionMatrixError(` (no longer just `raise NotImplementedError`).
    - `core/models.py` contains `import logging` at the module top.
    - `grep -c "@pytest.mark.skip" tests/unit/test_models.py` decreases by 6 from Plan 01 baseline (3 validation existing skip strings already gone; 3 of the new "Wave 0 stub" markers — `test_validate_rejects_negative`, `test_validate_rejects_wrong_dtype`, `test_validate_warns_sparse_cells` — must be removed in this task).
    - `uv run pytest tests/unit/test_models.py -k "validate" -x -q` exits 0 with `6 passed`.
    - `uv run pytest tests/unit/test_models.py::test_validate_warns_sparse_cells -x -q` exits 0 (proves logging works, not exception).
  </acceptance_criteria>
  <done>
    All 6 validation tests pass green. Function raises InvalidTransitionMatrixError with descriptive multi-error messages on bad input. Sparsity is logged at WARNING level, never raised.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement M1Homogeneous.forecast() (ENG-02)</name>
  <read_first>
    - core/models.py (after Task 1 — validate_transition_matrix is now implemented)
    - tests/unit/test_models.py (read the exact assertion in `test_m1_forecast_replicates_chan_2015_table3` — Y_1 vector, expected_t2 vector, atol)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (section "Pattern 3: M1 Forecast" and "Pitfall 2: Chan 2015 Table 3 Index Off-By-One")
    - docs/MARKOV-MODELS.md (Chan 2015 Equation 1)
    - tests/conftest.py (sample_4x4_chan_matrix fixture for Chan Table 1 P)
  </read_first>
  <behavior>
    - Valid 2x2 matrix + Y_1=[0.6, 0.4] + horizon=5 returns ForecastResult with forecast_array shape (5, 2), model_type "m1", horizon 5.
    - Chan 2015 P (from sample_4x4_chan_matrix) + Y_1=[0.5878, 0.2830, 0.0585, 0.0708] + horizon=5: `result.forecast_array[1]` (i.e. t=2) equals `[0.5829, 0.2780, 0.0667, 0.0724]` within atol=1e-3.
    - `forecast_array[0]` is Y_2 (one matmul applied), NOT Y_1 (per Pitfall 2).
  </behavior>
  <action>
Replace `M1Homogeneous.forecast()` body in `core/models.py` (line ~67-69):

```python
    def forecast(self, Y_1: StateVector, horizon: int) -> ForecastResult:
        """Forecast Y_{t+1} = Y_t · P per Chan 2015 Eq.(1).

        forecast_array[0] is Y_2 (one matmul applied to Y_1).
        forecast_array[h-1] is Y_{h+1}.
        """
        validate_transition_matrix(self.P)
        forecast_array = np.zeros((horizon, self.n_states), dtype=np.float64)
        Y_t = Y_1.astype(np.float64, copy=True)
        for t in range(horizon):
            Y_t = Y_t @ self.P  # Chan 2015 Eq.(1)
            forecast_array[t] = Y_t
        return ForecastResult(
            forecast_array=forecast_array,
            confidence_bands=None,
            model_type="m1",
            horizon=horizon,
        )
```

Then un-skip `test_m1_forecast_shape` in `tests/unit/test_models.py` (remove its `@pytest.mark.skip(reason="Wave 0 stub...")` decorator).

The Chan regression test `test_m1_forecast_replicates_chan_2015_table3` was already un-skipped in Plan 01 — verify it now passes.

Run: `uv run pytest tests/unit/test_models.py -k "m1" -x -q` — both M1 tests must pass.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_models.py::test_m1_forecast_replicates_chan_2015_table3 tests/unit/test_models.py::test_m1_forecast_shape -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `core/models.py` `M1Homogeneous.forecast` body contains `Y_t = Y_t @ self.P` (iterative matmul, not matrix_power).
    - `core/models.py` `M1Homogeneous.forecast` returns ForecastResult with `model_type="m1"` literal string.
    - `uv run pytest tests/unit/test_models.py::test_m1_forecast_replicates_chan_2015_table3 -x -q` exits 0 (Chan 2015 Table 3 regression passes within atol=1e-3).
    - `uv run pytest tests/unit/test_models.py::test_m1_forecast_shape -x -q` exits 0.
    - Manual REPL check (run in shell): `uv run python -c "import numpy as np; from core.models import M1Homogeneous; P=np.array([[0.98230,0.00753,0.00464,0.00552],[0.01158,0.96161,0.02489,0.00192],[0.01442,0.01105,0.95721,0.01732],[0.01978,0.01122,0.01364,0.95536]]); Y=np.array([0.5878,0.2830,0.0585,0.0708]); r=M1Homogeneous(P).forecast(Y,5); print(np.round(r.forecast_array[1],4))"` prints values approximately `[0.5829 0.2780 0.0667 0.0724]`.
  </acceptance_criteria>
  <done>
    M1 forecast matches Chan (2015) Table 3 to 1e-3 precision. Both M1 tests pass green. Roadmap Phase 01 Success Criterion 1 partially satisfied (M1 portion).
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Implement M2TimeVarying + M3Extended (constructor signature breaking change, ENG-03, ENG-04)</name>
  <read_first>
    - core/models.py (current stubs — note constructor signatures will CHANGE from list to ndarray)
    - .planning/phases/01-markov-engine/01-RESEARCH.md (section "Pattern 4: M2 Time-Varying Forecast", "Pattern 5: M3 Extended Forecast", "Pitfall 1: M2/M3 Constructor Signature Mismatch")
    - .planning/phases/01-markov-engine/01-CONTEXT.md (decisions D-06, D-07, D-08, D-09, D-10)
    - tests/unit/test_models.py (read `test_m2_forecast_shape`, `test_m2_holds_last_pt_at_horizon`, `test_m3_forecast_replicates_chan_2015` for the exact expected behavior)
  </read_first>
  <behavior>
    - M2 constructor accepts `P_t_sequence: np.ndarray` of shape (n_periods, n_states, n_states); validates each slice with validate_transition_matrix.
    - M2 constructor on a 2D ndarray or list raises ValueError or InvalidTransitionMatrixError.
    - M2.forecast(Y_1, horizon=3) with P_t.shape=(3,2,2) returns ForecastResult.forecast_array.shape == (3, 2).
    - M2.forecast(Y_1, horizon=4) with P_t.shape=(2,2,2) holds P_t[-1] constant at steps 3 and 4 (D-06).
    - M3 constructor accepts P_t as ndarray shape (n_periods, n_states, n_states) AND G as ndarray of shape (n_states,) or (n_periods, n_states).
    - M3 constructor validates shape compatibility (D-10): `P_t.shape[1] == P_t.shape[2]` and `G.shape[-1] == P_t.shape[1]`.
    - M3.forecast: Q_{t+1} = (G ⊙ Q_t) · P_t with P_t and G held last past training window (D-07).
    - M3 forecast Chan 2015 test: with G=[1.0315, 1.0561, 0.9029, 1.0897], Q_1=[0.5878, 0.2830, 0.0585, 0.0708], P_t = Chan Table 1 P repeated 5 times — `result.forecast_array[0]` (t=2) approximately equals `[0.5799, 0.2847, 0.0603, 0.0751]` within atol=1e-2.
  </behavior>
  <action>
Replace `M2TimeVarying` class in `core/models.py` (lines ~72-83) with this exact implementation (note the breaking signature change per D-08):

```python
class M2TimeVarying:
    """Time-varying P_t. Y_{t+1} = Y_t · P_t. Eq. (2) in Chan 2015.

    Per D-06: when horizon > n_periods, holds last P_t constant for remaining steps.
    Per D-08: P_t_sequence stored as np.ndarray of shape (n_periods, n_states, n_states),
    NOT list[np.ndarray] — cleaner indexing, NumPy-broadcasting-friendly, JSON-serializable.
    """

    def __init__(self, P_t_sequence: np.ndarray) -> None:
        if P_t_sequence.ndim != 3:
            raise ValueError(
                f"P_t_sequence must be 3D ndarray (n_periods, n_states, n_states), "
                f"got ndim={P_t_sequence.ndim}"
            )
        if P_t_sequence.shape[1] != P_t_sequence.shape[2]:
            raise ValueError(
                f"P_t_sequence inner shape must be square; got {P_t_sequence.shape}"
            )
        for t in range(P_t_sequence.shape[0]):
            validate_transition_matrix(P_t_sequence[t])
        self.P_t = P_t_sequence
        self.n_periods = P_t_sequence.shape[0]
        self.n_states = P_t_sequence.shape[1]

    def forecast(self, Y_1: StateVector, horizon: int) -> ForecastResult:
        """Forecast Y_{t+1} = Y_t · P_t per Chan 2015 Eq.(2).

        D-06: when t >= n_periods, P_t[-1] is reused for remaining steps.
        """
        forecast_array = np.zeros((horizon, self.n_states), dtype=np.float64)
        Y_t = Y_1.astype(np.float64, copy=True)
        for t in range(horizon):
            P_at_t = self.P_t[t] if t < self.n_periods else self.P_t[-1]
            Y_t = Y_t @ P_at_t
            forecast_array[t] = Y_t
        return ForecastResult(
            forecast_array=forecast_array,
            confidence_bands=None,
            model_type="m2",
            horizon=horizon,
        )
```

Replace `M3Extended` class in `core/models.py` (lines ~86-100) with this exact implementation:

```python
class M3Extended:
    """Extended Markov with growth multiplier G. Q_{t+1} = (G ⊙ Q_t) · P_t. Eq. (3).

    Per D-07: when horizon > n_periods, holds last P_t AND G constant.
    Per D-09: G is np.ndarray of shape (n_states,) for scalar growth per state,
    or (n_periods, n_states) for time-varying growth.
    Per D-10: constructor validates P_t.shape[1] == P_t.shape[2] and G.shape[-1] == P_t.shape[1].
    """

    def __init__(self, P_t_sequence: np.ndarray, G: np.ndarray) -> None:
        if P_t_sequence.ndim != 3:
            raise ValueError(
                f"P_t_sequence must be 3D ndarray (n_periods, n_states, n_states), "
                f"got ndim={P_t_sequence.ndim}"
            )
        if P_t_sequence.shape[1] != P_t_sequence.shape[2]:
            raise ValueError(
                f"P_t_sequence inner shape must be square; got {P_t_sequence.shape}"
            )
        for t in range(P_t_sequence.shape[0]):
            validate_transition_matrix(P_t_sequence[t])
        n_states = P_t_sequence.shape[1]
        if G.ndim not in (1, 2):
            raise ValueError(f"G must be 1D (shape (n_states,)) or 2D (shape (n_periods, n_states)); got ndim={G.ndim}")
        if G.shape[-1] != n_states:
            raise ValueError(
                f"G last dim must equal n_states={n_states}; got G.shape={G.shape}"
            )
        self.P_t = P_t_sequence
        self.G = G
        self.n_periods = P_t_sequence.shape[0]
        self.n_states = n_states

    def forecast(self, Q_1: PopulationVector, horizon: int) -> ForecastResult:
        """Forecast Q_{t+1} = (G ⊙ Q_t) · P_t per Chan 2015 Eq.(3).

        D-07: when t >= n_periods, P_t[-1] and (if 2D) G[-1] are reused.
        """
        forecast_array = np.zeros((horizon, self.n_states), dtype=np.float64)
        Q_t = Q_1.astype(np.float64, copy=True)
        for t in range(horizon):
            P_at_t = self.P_t[t] if t < self.n_periods else self.P_t[-1]
            if self.G.ndim == 1:
                G_at_t = self.G
            else:
                G_at_t = self.G[t] if t < self.G.shape[0] else self.G[-1]
            Q_t = (G_at_t * Q_t) @ P_at_t  # Chan 2015 Eq.(3)
            forecast_array[t] = Q_t
        return ForecastResult(
            forecast_array=forecast_array,
            confidence_bands=None,
            model_type="m3",
            horizon=horizon,
        )
```

After implementations land, **un-skip** the M2 and M3 tests in `tests/unit/test_models.py`:
- `test_m2_forecast_shape` (remove `@pytest.mark.skip(reason="Wave 0 stub...")`)
- `test_m2_holds_last_pt_at_horizon` (remove skip)
- `test_m3_forecast_replicates_chan_2015` (remove skip)

Run: `uv run pytest tests/unit/test_models.py -x -q` — all 11 tests must pass.
  </action>
  <verify>
    <automated>uv run pytest tests/unit/test_models.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "P_t_sequence: np.ndarray" core/models.py` returns at least 2 matches (M2 and M3 constructors signature updated per D-08).
    - `grep -c "list\\[TransitionMatrix\\]" core/models.py` returns 0 (the legacy stub signature is fully replaced — no list type annotations remain for P_t_sequence).
    - `grep -n "self.P_t\\[-1\\]" core/models.py` returns at least 2 matches (D-06 + D-07 hold-last behavior present in both M2.forecast and M3.forecast).
    - `grep -n "(G_at_t \\* Q_t) @ P_at_t\\|self\\.G \\* Q_t" core/models.py` returns at least 1 match (M3 Eq.(3) `G ⊙ Q_t` then matmul).
    - `uv run pytest tests/unit/test_models.py -x -q` exits 0 with `11 passed` (all originally-skipped stubs now activated and passing).
    - `uv run pytest tests/unit/test_models.py::test_m2_holds_last_pt_at_horizon -x -q` exits 0 (D-06 hold-last behavior verified).
    - `uv run pytest tests/unit/test_models.py::test_m3_forecast_replicates_chan_2015 -x -q` exits 0 (Chan 2015 m3 numerics verified within atol=1e-2).
    - `grep -c "@pytest.mark.skip" tests/unit/test_models.py` returns 0 (every stub in test_models.py is now un-skipped at end of Plan 02).
  </acceptance_criteria>
  <done>
    All three Markov model classes implemented per Chan (2015). Constructor signatures match D-08/D-09. All 11 tests in test_models.py pass. Roadmap Phase 01 Success Criterion 1 fully satisfied (Chan Table 3 regression green).
  </done>
</task>

</tasks>

<verification>
After all tasks complete:
```bash
uv run pytest tests/unit/test_models.py -v --tb=short
```
Expected: 11 passed, 0 skipped, 0 failed in test_models.py.

```bash
uv run ruff check core/models.py
uv run mypy core/models.py
```
Both must pass clean. No `NotImplementedError` left in `core/models.py`.

Manual REPL check (Roadmap Success Criterion 1):
```bash
uv run python -c "
import numpy as np
from core.models import M1Homogeneous
P = np.array([[0.98230,0.00753,0.00464,0.00552],[0.01158,0.96161,0.02489,0.00192],[0.01442,0.01105,0.95721,0.01732],[0.01978,0.01122,0.01364,0.95536]])
Y = np.array([0.5878,0.2830,0.0585,0.0708])
result = M1Homogeneous(P).forecast(Y, horizon=5)
print('forecast_array[1] (t=2):', np.round(result.forecast_array[1], 4))
print('Expected (Chan 2015 Table 3): [0.5829 0.2780 0.0667 0.0724]')
"
```
Output line 1 must match output line 2.
</verification>

<success_criteria>
- All 11 tests in `tests/unit/test_models.py` pass (4 existing + 7 stubs un-skipped through Plan 02).
- `grep -n "raise NotImplementedError" core/models.py` returns 0 (no stubs remain in models.py).
- Chan 2015 Table 3 regression test green within atol=1e-3.
- M2 constructor accepts ndarray, NOT list — verified by `test_m2_forecast_shape` passing.
- M3 forecast applies `(G ⊙ Q_t) @ P_t` formula — verified by `test_m3_forecast_replicates_chan_2015` matching within atol=1e-2.
</success_criteria>

<output>
After completion, create `.planning/phases/01-markov-engine/01-02-SUMMARY.md` documenting:
- core/models.py before/after (functions implemented)
- Chan 2015 Table 3 regression result (actual values from test output)
- Confirmation that M2/M3 constructor signatures use ndarray per D-08
- Sparsity warning behavior verified
- ENG-01, ENG-02, ENG-03, ENG-04, ENG-08 marked complete
</output>