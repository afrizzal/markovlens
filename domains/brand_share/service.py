"""Brand share domain service — orchestrates the Phase 01 core engine.

Implements BS-01 (run_forecast returning NumPy-only BrandShareForecastResult)
and BS-04 (per-model accuracy comparison). Domain layer is pure (no Streamlit imports).
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
from core.metrics import brier_score, log_loss, mape
from core.models import M1Homogeneous, M2TimeVarying, M3Extended, compute_stationary
from core.simulation import compute_quantile_bands, monte_carlo_simulate, walk_forward_backtest

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module constants — NO magic numbers in function bodies
# ---------------------------------------------------------------------------

BRAND_SHARE_DOMAIN: str = "brand_share"
DEFAULT_N_SIMULATIONS: int = 10_000
DEFAULT_SEED: int = 42
BACKTEST_WINDOW: int = 3
MODEL_KEYS: tuple[str, ...] = ("m1", "m2", "m3")


# ---------------------------------------------------------------------------
# Result type — NumPy-only, frozen dataclass (D-18)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrandShareForecastResult:
    """Output of run_forecast — structured NumPy arrays only.

    No Plotly coupling. All chart construction happens in app/components.

    Fields
    ------
    forecasts : dict[str, np.ndarray]
        Per-model forecast arrays keyed by model id ("m1"/"m2"/"m3").
        Each array is shape (horizon, n_states).
    historical_shares : np.ndarray
        Share matrix shape (n_hist_periods, n_states) index-aligned to state_labels.
    transition_matrix : np.ndarray
        m1 constant transition matrix, shape (n_states, n_states).
    recent_transition_matrix : np.ndarray
        Most recent per-period P_t, shape (n_states, n_states).
    observation_counts : np.ndarray
        Raw observation counts, shape (n_states, n_states).
    confidence_bands : dict[float, np.ndarray]
        Monte Carlo quantile bands {0.10, 0.50, 0.90 -> shape (horizon+1,)}.
    stationary_distribution : np.ndarray | None
        Stationary distribution from m1 matrix, or None if not computable.
    accuracy_metrics : dict[str, dict[str, float]]
        Per-model accuracy: {"m1": {"mape": .., "brier": .., "log_loss": ..}, ...}.
    backtest_results : list[dict]
        Walk-forward backtest results from core.simulation.walk_forward_backtest.
    state_labels : list[str]
        Ordered state labels; state_labels[i] is row/col i of transition_matrix.
    dataset_name : str
        Human-readable dataset name.
    n_transitions : int
        Total transition row count.
    n_periods : int
        Number of distinct periods in the dataset.
    best_model : str
        Model with the lowest MAPE among m1/m2/m3 (computed, never hardcoded).
    """

    forecasts: dict[str, np.ndarray]
    historical_shares: np.ndarray
    transition_matrix: np.ndarray
    recent_transition_matrix: np.ndarray
    observation_counts: np.ndarray
    confidence_bands: dict[float, np.ndarray]
    stationary_distribution: np.ndarray | None
    accuracy_metrics: dict[str, dict[str, float]]
    backtest_results: list[dict]
    state_labels: list[str]
    dataset_name: str
    n_transitions: int
    n_periods: int
    best_model: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_datasets(conn: duckdb.DuckDBPyConnection) -> list[Dataset]:
    """Return brand_share-domain datasets registered in the DB.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection (caller-managed).

    Returns
    -------
    list[Dataset]
        All datasets with domain == "brand_share".
    """
    return queries.list_datasets(conn, domain=BRAND_SHARE_DOMAIN)


def run_forecast(
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    model_type: str,
    horizon: int,
    *,
    n_simulations: int = DEFAULT_N_SIMULATIONS,
    seed: int = DEFAULT_SEED,
) -> BrandShareForecastResult:
    """Orchestrate the full m1/m2/m3 Markov pipeline for brand share forecasting.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
        Open DuckDB connection (caller-managed; page uses @st.cache_resource).
    dataset_id : str
        Dataset identifier in the datasets table.
    model_type : str
        Primary model driving Monte Carlo bands ("m1", "m2", or "m3").
    horizon : int
        Number of forward forecast steps.
    n_simulations : int
        Monte Carlo path count.
    seed : int
        RNG seed for reproducible simulations.

    Returns
    -------
    BrandShareForecastResult
        All fields are NumPy arrays, scalars, or plain Python collections —
        no Plotly objects (D-18).

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
    # sorted union of from/to states so index aligns with matrix (RESEARCH Pitfall 2)
    state_labels: list[str] = sorted(set(df["from_state"]) | set(df["to_state"]))
    n_states = len(state_labels)
    state_idx = {s: i for i, s in enumerate(state_labels)}

    # ── 4. Build m1 constant transition matrix ─────────────────────────────
    try:
        matrix, counts = build_transition_matrix(conn, dataset_id)
    except ValueError as exc:
        raise DatasetTooSparseError(
            "Dataset is too sparse to build a reliable transition matrix. "
            "Try selecting a longer date range or merging states with fewer "
            "than 20 observations."
        ) from exc

    # ── 5. Build per-period P_t sequence for m2/m3 ────────────────────────
    # Cast to Python int — DuckDB cannot accept numpy.int32/int64 as query params
    periods = [int(p) for p in sorted(df["period"].unique())]
    n_periods = len(periods)

    P_t_list: list[np.ndarray] = []
    for p in periods:
        try:
            P_t_raw, _ = build_transition_matrix(conn, dataset_id, period=p)
        except ValueError:
            P_t_raw = np.eye(n_states, dtype=np.float64)

        # Guard per Open Question 1: re-embed smaller matrices into (n, n)
        if P_t_raw.shape[0] < n_states:
            P_t_raw = _embed_matrix(P_t_raw, conn, dataset_id, p, state_idx, n_states)

        P_t_list.append(P_t_raw)

    P_t_sequence = np.stack(P_t_list, axis=0)  # shape (n_periods, n_states, n_states)
    recent_transition_matrix = P_t_sequence[-1]

    # ── 6. Derive initial share vector Y_1 (last observed period) ─────────
    max_period = periods[-1]
    last_df = df[df["period"] == max_period]
    Y_1 = _compute_share_vector(last_df, state_idx, n_states)

    # ── 7. Derive M3 initial count vector Q_1 (absolute, not normalized) ──
    # markov-patterns forbidden #5: M3 needs absolute counts, NOT normalized shares
    Q_1 = _compute_count_vector(last_df, state_idx, n_states)

    # G = neutral growth multiplier — no market size growth data available in this domain
    G = np.ones(n_states, dtype=np.float64)

    # ── 8. Forecast all three models ───────────────────────────────────────
    fc_m1 = M1Homogeneous(matrix).forecast(Y_1, horizon)
    fc_m2 = M2TimeVarying(P_t_sequence).forecast(Y_1, horizon)
    fc_m3 = M3Extended(P_t_sequence, G).forecast(Q_1, horizon)

    forecasts: dict[str, np.ndarray] = {
        "m1": fc_m1.forecast_array,
        "m2": fc_m2.forecast_array,
        "m3": fc_m3.forecast_array,
    }

    # ── 9. Historical shares (n_hist_periods, n_states) ───────────────────
    historical_shares = _compute_historical_shares(df, periods, state_idx, n_states)

    # ── 10. Stationary distribution from m1 constant matrix (D-13) ────────
    stationary_distribution = compute_stationary(matrix)

    # ── 11. Monte Carlo confidence bands for the selected model ───────────
    P_mc = matrix if model_type == "m1" else recent_transition_matrix
    confidence_bands = _compute_confidence_bands(P_mc, Y_1, horizon, n_simulations, seed)

    # ── 12. Walk-forward backtest ──────────────────────────────────────────
    backtest_results = walk_forward_backtest(df, window=BACKTEST_WINDOW)

    # ── 13. Per-model accuracy metrics (BS-04) ────────────────────────────
    prev_period = periods[-2] if n_periods >= 2 else periods[-1]
    prev_df = df[df["period"] == prev_period]

    accuracy_metrics = _compute_accuracy_metrics(
        Y_1=Y_1,
        last_df=last_df,
        prev_df=prev_df,
        state_idx=state_idx,
        n_states=n_states,
        matrix=matrix,
        P_t_sequence=P_t_sequence,
        Q_1=Q_1,
        G=G,
    )

    # ── 14. Computed winner — lowest MAPE (D-12) ──────────────────────────
    best_model = min(MODEL_KEYS, key=lambda m: accuracy_metrics[m]["mape"])

    return BrandShareForecastResult(
        forecasts=forecasts,
        historical_shares=historical_shares,
        transition_matrix=matrix,
        recent_transition_matrix=recent_transition_matrix,
        observation_counts=counts,
        confidence_bands=confidence_bands,
        stationary_distribution=stationary_distribution,
        accuracy_metrics=accuracy_metrics,
        backtest_results=backtest_results,
        state_labels=state_labels,
        dataset_name=ds.name,
        n_transitions=len(df),
        n_periods=n_periods,
        best_model=best_model,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _embed_matrix(
    small_P: np.ndarray,
    conn: duckdb.DuckDBPyConnection,
    dataset_id: str,
    period: int,
    state_idx: dict[str, int],
    n_states: int,
) -> np.ndarray:
    """Re-embed a smaller period matrix into the full (n_states, n_states) space.

    Rows missing from a sparse period become absorbing self-loops.
    """
    period_df = conn.execute(
        "SELECT DISTINCT from_state, to_state FROM transitions "
        "WHERE dataset_id = ? AND period = ?",
        [dataset_id, period],
    ).df()

    if period_df.empty:
        return np.eye(n_states, dtype=np.float64)

    partial_states = sorted(set(period_df["from_state"]) | set(period_df["to_state"]))
    partial_idx = {s: i for i, s in enumerate(partial_states)}

    full_P = np.eye(n_states, dtype=np.float64)
    for s_from, i_partial in partial_idx.items():
        if s_from not in state_idx:
            continue
        i_full = state_idx[s_from]
        row = np.zeros(n_states, dtype=np.float64)
        for s_to, j_partial in partial_idx.items():
            if s_to in state_idx:
                row[state_idx[s_to]] = small_P[i_partial, j_partial]
        row_sum = row.sum()
        if row_sum > 1e-12:
            full_P[i_full] = row / row_sum

    return full_P


def _compute_share_vector(
    df: pd.DataFrame,
    state_idx: dict[str, int],
    n_states: int,
) -> np.ndarray:
    """Compute normalized share vector from a period slice (to_state distribution)."""
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
        return vec / total
    vec[0] = 1.0
    return vec


def _compute_count_vector(
    df: pd.DataFrame,
    state_idx: dict[str, int],
    n_states: int,
) -> np.ndarray:
    """Compute absolute count vector from a period slice (to_state counts).

    Used for M3Extended Q_1 — absolute counts per markov-patterns forbidden #5.
    """
    vec = np.zeros(n_states, dtype=np.float64)
    if df.empty:
        return vec
    grouped = df.groupby("to_state")["weight"].sum()
    for state, count in grouped.items():
        if state in state_idx:
            vec[state_idx[state]] = float(count)
    return vec


def _compute_historical_shares(
    df: pd.DataFrame,
    periods: list,
    state_idx: dict[str, int],
    n_states: int,
) -> np.ndarray:
    """Build historical share matrix (n_periods, n_states) index-aligned to state_idx.

    Each row is the normalized from_state distribution for one period.
    """
    n_hist = len(periods)
    shares = np.zeros((n_hist, n_states), dtype=np.float64)

    for t, period in enumerate(periods):
        period_df = df[df["period"] == period]
        if period_df.empty:
            continue
        grouped = period_df.groupby("from_state")["weight"].sum()
        total = grouped.sum()
        if total > 1e-12:
            for state, count in grouped.items():
                if state in state_idx:
                    shares[t, state_idx[state]] = float(count) / float(total)

    return shares


def _compute_confidence_bands(
    P: np.ndarray,
    Y_1: np.ndarray,
    horizon: int,
    n_simulations: int,
    seed: int,
) -> dict[float, np.ndarray]:
    """Run Monte Carlo and return P10/P50/P90 bands for the leading brand.

    The extractor returns a 2-D boolean indicator (n_sims, n_steps+1) per Pitfall 4.
    """
    paths = monte_carlo_simulate(
        P,
        start_state=Y_1,
        n_steps=horizon,
        n_simulations=n_simulations,
        seed=seed,
    )
    b = int(np.argmax(Y_1))
    # 2-D extractor per Pitfall 4 — must return (n_sims, n_steps+1)
    target_extractor = lambda p, b=b: (p == b).astype(float)  # noqa: E731
    return compute_quantile_bands(paths, target_extractor)


def _compute_accuracy_metrics(
    Y_1: np.ndarray,
    last_df: pd.DataFrame,
    prev_df: pd.DataFrame,
    state_idx: dict[str, int],
    n_states: int,
    matrix: np.ndarray,
    P_t_sequence: np.ndarray,
    Q_1: np.ndarray,
    G: np.ndarray,
) -> dict[str, dict[str, float]]:
    """Compute per-model MAPE / Brier / log-loss against last-period actual.

    One-step-ahead in-sample comparison from the second-to-last period.
    """
    actual_vec = _compute_share_vector(last_df, state_idx, n_states)
    prev_share = _compute_share_vector(prev_df, state_idx, n_states)
    prev_Q = _compute_count_vector(prev_df, state_idx, n_states)
    last_P_t = P_t_sequence[-1]

    one_step: dict[str, np.ndarray] = {
        "m1": prev_share @ matrix,
        "m2": prev_share @ last_P_t,
        "m3": _m3_one_step_share(prev_Q, G, last_P_t),
    }

    result: dict[str, dict[str, float]] = {}
    for model_key in MODEL_KEYS:
        fc_vec = one_step[model_key]
        fc_2d = fc_vec.reshape(1, -1)
        actual_2d = actual_vec.reshape(1, -1)

        result[model_key] = {
            "mape": float(mape(actual_vec, fc_vec)),
            "brier": float(brier_score(fc_2d, actual_2d)),
            "log_loss": float(log_loss(fc_2d, actual_2d)),
        }

    return result


def _m3_one_step_share(
    Q: np.ndarray,
    G: np.ndarray,
    P_t: np.ndarray,
) -> np.ndarray:
    """Compute one-step M3 forecast normalized to a share vector.

    Q_{t+1} = (G ⊙ Q_t) · P_t — Chan (2015) Eq.(3). Normalizes to shares
    for metric comparison with m1/m2.
    """
    Q_next = (G * Q) @ P_t  # Chan 2015 Eq.(3)
    total = Q_next.sum()
    if total > 1e-12:
        return Q_next / total
    return Q_next
