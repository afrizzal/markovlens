"""Churn domain service — orchestrates Phase 01 core engine for churn analysis.

Implements CH-01: ChurnAnalysisResult with NumPy-only fields (no Plotly coupling),
full churn pipeline (run_analysis, simulate_scenario, list_datasets), absorbing Markov
chain fundamental matrix KPIs, and what-if scenario support.

Domain layer is pure — no Streamlit imports. Mirrors domains/brand_share/service.py structure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd

import core.db.queries as queries
from core.db.queries import Dataset, build_transition_matrix, get_dataset, load_transitions
from core.exceptions import DatasetTooSparseError
from core.models import M1Homogeneous, validate_transition_matrix

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module constants — NO magic numbers in function bodies
# ---------------------------------------------------------------------------

CHURN_DOMAIN: str = "churn"
DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER: int = 50_000  # Rp (D-05; UI tooltip; future Settings v2 makes this configurable)
ABSORBING_THRESHOLD: float = 0.95                   # P[i,i] >= this => state treated as absorbing (RESEARCH Pitfall 1)
CONDITION_NUMBER_LIMIT: float = 1e10                # switch inv -> pinv above this (RESEARCH Pattern 3)
ACTIVE_STATE_KEY: str = "active"
CHURNED_STATE_KEY: str = "churned"
KPI_KEYS: tuple[str, ...] = ("retention_rate", "avg_lifetime", "expected_churn", "revenue_at_risk")


# ---------------------------------------------------------------------------
# Result type — NumPy-only, frozen dataclass (D-09)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChurnAnalysisResult:
    """Output of run_analysis — structured NumPy arrays only (D-09). No Plotly coupling.

    Fields
    ------
    transition_matrix : np.ndarray
        Row-stochastic transition matrix, shape (n_states, n_states).
    observation_counts : np.ndarray
        Raw observation counts, shape (n_states, n_states).
    state_distribution_over_time : np.ndarray
        State proportions over historical periods, shape (n_periods+1, n_states).
        Row 0 = Y_1 (initial distribution); rows 1..n_periods = iterated forecasts.
        INCLUDES period 0 to avoid Sankey column-0 gap (Pitfall 2).
    baseline_forecast : np.ndarray
        Forward forecast from Y_1, shape (horizon+1, n_states). Row 0 = Y_1.
    kpis : dict[str, float]
        KPI values; keys == KPI_KEYS.
    state_labels : list[str]
        Ordered state labels; state_labels[i] is row/col i of transition_matrix.
    dataset_name : str
        Human-readable dataset name from the datasets table.
    n_customers : int
        Distinct entity_id count in the transitions table.
    n_periods : int
        Number of observed distinct periods in the dataset.
    """

    transition_matrix: np.ndarray              # (n_states, n_states), row-stochastic
    observation_counts: np.ndarray             # (n_states, n_states), raw counts
    state_distribution_over_time: np.ndarray   # (n_periods+1, n_states) — INCLUDES period 0 (Pitfall 2)
    baseline_forecast: np.ndarray              # (horizon+1, n_states) — INCLUDES period 0
    kpis: dict[str, float]                     # keys == KPI_KEYS
    state_labels: list[str]                    # ordered; state_labels[i] is row/col i
    dataset_name: str
    n_customers: int                           # distinct entity_id count
    n_periods: int                             # number of observed periods


# ---------------------------------------------------------------------------
# Absorbing Markov chain — fundamental matrix helpers
# ---------------------------------------------------------------------------

def compute_fundamental_matrix(
    P: np.ndarray,
    *,
    absorbing_threshold: float = ABSORBING_THRESHOLD,
) -> tuple[np.ndarray | None, list[int]]:
    """Compute the fundamental matrix N = (I - Q)^{-1} for transient states.

    Parameters
    ----------
    P : np.ndarray
        Square row-stochastic transition matrix, shape (n, n).
    absorbing_threshold : float
        States with P[i,i] >= this are treated as absorbing. Default = ABSORBING_THRESHOLD.

    Returns
    -------
    tuple[np.ndarray | None, list[int]]
        (N, transient_indices) where N is the fundamental matrix over transient states,
        or (None, []) if all states are absorbing or computation fails.

    Notes
    -----
    Uses pinv instead of inv when condition number of (I - Q) exceeds CONDITION_NUMBER_LIMIT.
    This handles near-singular cases from near-absorbing states (Pitfall 1).
    """
    n = len(P)
    transient_idx = [i for i in range(n) if P[i, i] < absorbing_threshold]
    if not transient_idx:
        return None, []
    Q = P[np.ix_(transient_idx, transient_idx)]
    I_Q = np.eye(len(transient_idx), dtype=np.float64) - Q
    try:
        cond = np.linalg.cond(I_Q)
        N = np.linalg.pinv(I_Q) if cond > CONDITION_NUMBER_LIMIT else np.linalg.inv(I_Q)
        return N, transient_idx
    except np.linalg.LinAlgError:
        return None, transient_idx


def compute_avg_lifetime(P: np.ndarray, active_state_idx: int) -> float | None:
    """Expected periods in any transient state for customers starting in the active state.

    Parameters
    ----------
    P : np.ndarray
        Square row-stochastic transition matrix, shape (n, n).
    active_state_idx : int
        Row index of the "active" state in P.

    Returns
    -------
    float | None
        Expected periods until absorption. None if computation fails (all states absorbing,
        active_state_idx not in transient set, or near-singular matrix).

    Notes
    -----
    Computed from the fundamental matrix N = (I - Q)^{-1} (Chan 2015). Row sums of N
    give the expected periods spent in any transient state before absorption.
    """
    N, transient_idx = compute_fundamental_matrix(P)
    if N is None or active_state_idx not in transient_idx:
        return None
    row = transient_idx.index(active_state_idx)
    return float(N.sum(axis=1)[row])


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _compute_share_vector(
    df: pd.DataFrame,
    state_idx: dict[str, int],
    n_states: int,
) -> np.ndarray:
    """Compute normalized share vector from a period slice (to_state distribution).

    Parameters
    ----------
    df : pd.DataFrame
        Transitions slice for one period; must have 'to_state' and 'weight' columns.
    state_idx : dict[str, int]
        Maps state label to matrix row/col index.
    n_states : int
        Total number of states (dimension of output vector).

    Returns
    -------
    np.ndarray
        Shape (n_states,), sums to 1.0. If empty, puts all mass on index 0.
    """
    vec = np.zeros(n_states, dtype=np.float64)
    if df.empty:
        vec[0] = 1.0
        return vec
    grouped = df.groupby("to_state")["weight"].sum()
    for state, count in grouped.items():
        if state in state_idx:
            vec[state_idx[state]] = float(count)
    total = vec.sum()
    if total > 1e-12:
        normalized: np.ndarray = vec / total
        return normalized.astype(np.float64)
    vec[0] = 1.0
    return vec


def _initial_distribution(
    df: pd.DataFrame,
    state_labels: list[str],
    state_idx: dict[str, int],
    n_states: int,
) -> np.ndarray:
    """Compute Y_1 from the earliest period's from_state distribution.

    Parameters
    ----------
    df : pd.DataFrame
        All transitions; must have 'period', 'from_state', 'weight' columns.
    state_labels : list[str]
        Ordered state labels (unused directly; state_idx carries the mapping).
    state_idx : dict[str, int]
        Maps state label to matrix row/col index.
    n_states : int
        Total number of states.

    Returns
    -------
    np.ndarray
        Shape (n_states,), sums to 1.0. Represents the cohort's starting composition.
        If the earliest period slice is empty, puts all mass on index 0.
    """
    if df.empty:
        vec = np.zeros(n_states, dtype=np.float64)
        vec[0] = 1.0
        return vec
    earliest_period = df["period"].min()
    earliest_df = df[df["period"] == earliest_period]
    vec = np.zeros(n_states, dtype=np.float64)
    grouped = earliest_df.groupby("from_state")["weight"].sum()
    for state, count in grouped.items():
        if state in state_idx:
            vec[state_idx[state]] = float(count)
    total = vec.sum()
    if total > 1e-12:
        normalized: np.ndarray = vec / total
        return normalized.astype(np.float64)
    vec[0] = 1.0
    return vec


def _state_distribution_over_time(
    Y_1: np.ndarray,
    P: np.ndarray,
    n_periods: int,
) -> np.ndarray:
    """Iterate Y_t = Y_{t-1} @ P for n_periods steps, prepending Y_1 as row 0.

    Parameters
    ----------
    Y_1 : np.ndarray
        Initial distribution, shape (n_states,).
    P : np.ndarray
        Row-stochastic transition matrix, shape (n_states, n_states).
    n_periods : int
        Number of observed periods; produces shape (n_periods+1, n_states).

    Returns
    -------
    np.ndarray
        Shape (n_periods+1, n_states). Row 0 = Y_1 (Pitfall 2 guard — includes period 0
        so the Sankey column 0 has source coordinates).
    """
    n_states = len(Y_1)
    dist = np.zeros((n_periods + 1, n_states), dtype=np.float64)
    dist[0] = Y_1
    Y_t = Y_1.copy()
    for t in range(n_periods):
        Y_t = Y_t @ P
        dist[t + 1] = Y_t
    return dist


def _apply_overrides(
    P: np.ndarray,
    transition_overrides: dict[tuple[int, int], float],
) -> np.ndarray:
    """Copy P, apply cell overrides, renormalize each touched row.

    Parameters
    ----------
    P : np.ndarray
        Row-stochastic baseline matrix, shape (n, n).
    transition_overrides : dict[tuple[int, int], float]
        Keys are (from_state_idx, to_state_idx); values are new probabilities.
        Each affected row is renormalized after all overrides for that row are applied.

    Returns
    -------
    np.ndarray
        Modified copy of P with all touched rows renormalized to sum to 1.0.
    """
    P_mod = P.copy()
    rows_to_fix: dict[int, dict[int, float]] = {}
    for (i, j), val in transition_overrides.items():
        rows_to_fix.setdefault(i, {})[j] = val
    for i, changes in rows_to_fix.items():
        for j, val in changes.items():
            P_mod[i, j] = float(np.clip(val, 0.0, 1.0))
        row_sum = P_mod[i].sum()
        if row_sum > 1e-12:
            P_mod[i] /= row_sum
    return P_mod


def _compute_kpis(
    P: np.ndarray,
    state_distribution_over_time: np.ndarray,
    baseline_forecast: np.ndarray,
    state_labels: list[str],
    n_customers: int,
    horizon: int,
) -> dict[str, float]:
    """Compute the four churn KPIs from the transition matrix and forecast arrays.

    Parameters
    ----------
    P : np.ndarray
        Row-stochastic transition matrix, shape (n_states, n_states).
    state_distribution_over_time : np.ndarray
        Shape (n_periods+1, n_states).
    baseline_forecast : np.ndarray
        Shape (horizon+1, n_states). Row 0 = initial distribution Y_1.
    state_labels : list[str]
        Ordered state labels; index-aligned with P rows/cols.
    n_customers : int
        Total distinct customer count.
    horizon : int
        Number of forecast steps.

    Returns
    -------
    dict[str, float]
        Keys == KPI_KEYS: retention_rate, avg_lifetime, expected_churn, revenue_at_risk.
    """
    active_idx = next((i for i, s in enumerate(state_labels) if s.lower() == ACTIVE_STATE_KEY), 0)
    churned_idx = next((i for i, s in enumerate(state_labels) if s.lower() == CHURNED_STATE_KEY), -1)

    # KPI 1: Retention Rate = Active share at horizon / initial Active share
    initial_active = baseline_forecast[0, active_idx]
    final_active = baseline_forecast[horizon, active_idx]
    retention_rate = float(final_active / initial_active) if initial_active > 1e-12 else 0.0

    # KPI 2: Avg Customer Lifetime from fundamental matrix
    avg_lifetime = compute_avg_lifetime(P, active_idx) or float("nan")

    # KPI 3: Expected Churn = Active customers * P(active -> churned)
    initial_active_count = n_customers * initial_active
    p_churn_one_step = float(P[active_idx, churned_idx]) if churned_idx >= 0 else 0.0
    expected_churn = initial_active_count * p_churn_one_step

    # KPI 4: Revenue at Risk
    revenue_at_risk = expected_churn * DEFAULT_MONTHLY_REVENUE_PER_CUSTOMER

    return {
        "retention_rate": retention_rate,
        "avg_lifetime": avg_lifetime,
        "expected_churn": expected_churn,
        "revenue_at_risk": revenue_at_risk,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_datasets(conn: duckdb.DuckDBPyConnection, *, domain: str = CHURN_DOMAIN) -> list[Dataset]:
    """Return churn-domain datasets registered in the DB.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection (caller-managed).
    domain : str
        Domain filter; defaults to "churn" (D-10).

    Returns
    -------
    list[Dataset]
        All datasets with domain == "churn".
    """
    return queries.list_datasets(conn, domain=domain)


def run_analysis(
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    horizon: int,
) -> ChurnAnalysisResult:
    """Orchestrate the m1 Markov churn pipeline for a registered dataset.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection (caller-managed; page uses @st.cache_resource).
    dataset_id : str
        Dataset identifier in the datasets table.
    horizon : int
        Number of forward forecast steps.

    Returns
    -------
    ChurnAnalysisResult
        All fields are NumPy arrays, scalars, or plain Python collections —
        no Plotly objects (D-09).

    Raises
    ------
    DatasetTooSparseError
        If the dataset has no valid transitions for matrix construction.
    DatasetNotFoundError
        If dataset_id is not registered.
    """
    # ── 1. Load dataset metadata ───────────────────────────────────────────
    ds = get_dataset(conn, dataset_id)

    # ── 2. Load raw transitions ────────────────────────────────────────────
    df = load_transitions(conn, dataset_id)

    # ── 3. Derive state labels — MUST match build_transition_matrix sort ───
    # sorted union of from/to states so index aligns with matrix (Pitfall 2)
    state_labels: list[str] = sorted(set(df["from_state"]) | set(df["to_state"]))
    n_states = len(state_labels)
    state_idx = {s: i for i, s in enumerate(state_labels)}

    # ── 4. Build m1 constant transition matrix ─────────────────────────────
    try:
        P, counts = build_transition_matrix(conn, dataset_id)
    except ValueError as exc:
        raise DatasetTooSparseError(
            "Churn dataset is too sparse to build a reliable transition matrix. "
            "Merge states with fewer than 20 observations or load a longer history."
        ) from exc

    periods = sorted(int(p) for p in df["period"].unique())
    n_periods = len(periods)
    n_customers = int(df["entity_id"].nunique())  # Open Question 2

    # ── 5. Initial distribution + historical state evolution ───────────────
    Y_1 = _initial_distribution(df, state_labels, state_idx, n_states)
    state_distribution_over_time = _state_distribution_over_time(Y_1, P, n_periods)  # (n_periods+1, n_states)

    # ── 6. Baseline forecast (horizon+1, n_states), prepend Y_1 as period 0 ─
    fc = M1Homogeneous(P).forecast(Y_1, horizon)                         # forecast_array shape (horizon, n_states)
    baseline_forecast = np.vstack([Y_1.reshape(1, -1), fc.forecast_array])  # (horizon+1, n_states), incl period 0

    # ── 7. KPI computation ─────────────────────────────────────────────────
    kpis = _compute_kpis(P, state_distribution_over_time, baseline_forecast, state_labels, n_customers, horizon)

    return ChurnAnalysisResult(
        transition_matrix=P,
        observation_counts=counts,
        state_distribution_over_time=state_distribution_over_time,
        baseline_forecast=baseline_forecast,
        kpis=kpis,
        state_labels=state_labels,
        dataset_name=ds.name,
        n_customers=n_customers,
        n_periods=n_periods,
    )


def simulate_scenario(
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    horizon: int,
    transition_overrides: dict[tuple[int, int], float],
    *,
    baseline_P: np.ndarray | None = None,
) -> np.ndarray:
    """Apply partial transition overrides, renormalize touched rows, return forecast distribution.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection (caller-managed).
    dataset_id : str
        Dataset identifier in the datasets table.
    horizon : int
        Number of forward forecast steps.
    transition_overrides : dict[tuple[int, int], float]
        Keys are (from_state_idx, to_state_idx); values are new probabilities.
        Each affected row is renormalized after all overrides for that row are applied.
    baseline_P : np.ndarray | None
        Optional pre-loaded baseline matrix. If provided, skips the DB query for
        the baseline (Pitfall 5 performance optimization — caller can pass result.transition_matrix).

    Returns
    -------
    np.ndarray
        state_distribution_over_time, shape (horizon+1, n_states). Includes period 0.

    Raises
    ------
    InvalidTransitionMatrixError
        If the modified matrix fails row-stochastic validation.
    """
    if baseline_P is None:
        baseline_P, _ = build_transition_matrix(conn, dataset_id)
    P_mod = _apply_overrides(baseline_P, transition_overrides)
    validate_transition_matrix(P_mod)  # raises if broken

    df = load_transitions(conn, dataset_id)
    state_labels: list[str] = sorted(set(df["from_state"]) | set(df["to_state"]))
    n_states = len(state_labels)
    state_idx = {s: i for i, s in enumerate(state_labels)}
    Y_1 = _initial_distribution(df, state_labels, state_idx, n_states)

    fc = M1Homogeneous(P_mod).forecast(Y_1, horizon)
    return np.vstack([Y_1.reshape(1, -1), fc.forecast_array]).astype(np.float64)  # (horizon+1, n_states)
