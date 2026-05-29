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
            if (1.0 + tol < P).any():
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
            raise ValueError(f"P_t_sequence inner shape must be square; got {P_t_sequence.shape}")
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
            raise ValueError(f"P_t_sequence inner shape must be square; got {P_t_sequence.shape}")
        for t in range(P_t_sequence.shape[0]):
            validate_transition_matrix(P_t_sequence[t])
        n_states = P_t_sequence.shape[1]
        if G.ndim not in (1, 2):
            raise ValueError(
                f"G must be 1D (shape (n_states,)) or 2D (shape (n_periods, n_states)); got ndim={G.ndim}"
            )
        if G.shape[-1] != n_states:
            raise ValueError(f"G last dim must equal n_states={n_states}; got G.shape={G.shape}")
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
