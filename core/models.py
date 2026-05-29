"""Markov chain model implementations — m1, m2, m3 from Chan (2015)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TypeAlias

import numpy as np

from core.exceptions import InvalidTransitionMatrixError

TransitionMatrix: TypeAlias = np.ndarray
StateVector: TypeAlias = np.ndarray
PopulationVector: TypeAlias = np.ndarray

MIN_OBSERVATIONS_PER_CELL: int = 20
PROBABILITY_TOLERANCE: float = 1e-9


def validate_transition_matrix(
    P: TransitionMatrix,
    transition_counts: np.ndarray | None = None,
    *,
    tol: float = PROBABILITY_TOLERANCE,
    min_obs: int = MIN_OBSERVATIONS_PER_CELL,
) -> None:
    """Validate matrix against MarkovLens invariants.

    Parameters
    ----------
    P : np.ndarray
        Transition matrix to validate, shape (M, M).
    transition_counts : np.ndarray | None
        Per-cell observation counts for sparsity check.
    tol : float
        Tolerance for row-sum check.
    min_obs : int
        Minimum observations per cell.

    Raises
    ------
    InvalidTransitionMatrixError
        If any invariant fails.
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
            sparse_cells = list(zip(*np.where(sparse_mask), strict=False))
            logging.getLogger(__name__).warning(
                "Sparsity detected: %d cells below min_obs=%d: first_five=%s",
                int(sparse_mask.sum()),
                min_obs,
                sparse_cells[:5],
            )


@dataclass(frozen=True)
class ForecastResult:
    """Output of a Markov forecast."""

    forecast_array: np.ndarray  # shape (horizon, n_states)
    confidence_bands: dict[float, np.ndarray] | None
    model_type: str
    horizon: int
    accuracy_metrics: dict[str, float] | None = None


class M1Homogeneous:
    """Constant transition matrix P. Y_{t+1} = Y_t · P. Eq. (1) in Chan 2015."""

    def __init__(self, P: TransitionMatrix) -> None:
        validate_transition_matrix(P)
        self.P = P
        self.n_states = P.shape[0]

    def forecast(self, Y_1: StateVector, horizon: int) -> ForecastResult:
        # TODO(phase01): Y_{t+1} = Y_1 · P^t per Eq.(1)
        raise NotImplementedError("M1Homogeneous.forecast — implement in Phase 01")


class M2TimeVarying:
    """Time-varying P_t. Y_{t+1} = Y_t · P_t. Eq. (2) in Chan 2015."""

    def __init__(self, P_t_sequence: list[TransitionMatrix]) -> None:
        for P in P_t_sequence:
            validate_transition_matrix(P)
        self.P_t = P_t_sequence
        self.n_states = P_t_sequence[0].shape[0]

    def forecast(self, Y_1: StateVector, horizon: int) -> ForecastResult:
        # TODO(phase01): Y_{t+1} = Y_1 · ∏ P_n per Eq.(2)
        raise NotImplementedError("M2TimeVarying.forecast — implement in Phase 01")


class M3Extended:
    """Extended Markov with growth multiplier G. Q_{t+1} = (G ⊙ Q_t) · P_t. Eq. (3)."""

    def __init__(self, P_t_sequence: list[TransitionMatrix], G: np.ndarray) -> None:
        for P in P_t_sequence:
            validate_transition_matrix(P)
        if G.shape != (P_t_sequence[0].shape[0],):
            raise ValueError(f"G must have shape ({P_t_sequence[0].shape[0]},), got {G.shape}")
        self.P_t = P_t_sequence
        self.G = G
        self.n_states = G.shape[0]

    def forecast(self, Q_1: PopulationVector, horizon: int) -> ForecastResult:
        # TODO(phase01): Q_{t+1} = (G ⊙ Q_t) · P_t per Eq.(3)
        raise NotImplementedError("M3Extended.forecast — implement in Phase 01")
