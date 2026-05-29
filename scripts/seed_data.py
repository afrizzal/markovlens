"""Seed local DuckDB with brand-share + churn datasets.

Per CONTEXT.md decisions:
- D-01: Brand share uses a synthetic FMCG data-generating process (5 brands x 24 periods).
- D-02: Churn uses the IBM Telco CSV committed at data/seed/telco_churn.csv with tenure
  discretized into ['new', 'growing', 'mature', 'loyal'] + absorbing 'churned' state.
- D-23: Idempotency via DELETE-WHERE-dataset_id before INSERT for every table.
- DATA-02 Roadmap SC 5: forecasts table must contain >= 5 reference rows after seed.

Synthetic FMCG DGP parameters (Claude's Discretion):
- Brands: Alpha, Beta, Gamma, Delta, Epsilon (n=5)
- Periods: 24 (monthly, simulating ~2 years)
- Initial share: [0.35, 0.25, 0.20, 0.12, 0.08]
- Base P matrix: hand-crafted plausible m1-like row-stochastic 5x5 (see P_BASE_FMCG)
- Per-period variation: small Dirichlet noise around P_BASE (drives M2/M3 interest)
- Aggregate transitions = (share_t[i] * P_BASE[i,j]) scaled to integer 'weight' units

Run with (after Task 3b lands):
    uv run python scripts/seed_data.py
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.db.connection import get_connection, init_schema  # noqa: E402
from core.db.queries import build_transition_matrix  # noqa: E402
from core.db.serialization import ndarray_to_json  # noqa: E402
from core.io.loaders import validate_transitions_df  # noqa: E402
from core.models import M1Homogeneous, M2TimeVarying  # noqa: E402

BRAND_SHARE_DATASET_ID: str = "ds_brand_share_synthetic"
CHURN_DATASET_ID: str = "ds_churn_telco"

FMCG_BRANDS: list[str] = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
FMCG_N_PERIODS: int = 24
FMCG_INITIAL_SHARE: np.ndarray = np.array([0.35, 0.25, 0.20, 0.12, 0.08])
FMCG_TOTAL_MARKET_UNITS: int = 100_000
FMCG_DIRICHLET_CONCENTRATION: float = 200.0  # higher = less noise per period

P_BASE_FMCG: np.ndarray = np.array(
    [
        [0.90, 0.04, 0.03, 0.02, 0.01],
        [0.05, 0.85, 0.05, 0.03, 0.02],
        [0.04, 0.06, 0.82, 0.05, 0.03],
        [0.03, 0.05, 0.06, 0.80, 0.06],
        [0.02, 0.03, 0.05, 0.07, 0.83],
    ],
    dtype=np.float64,
)

TENURE_STATE_BINS: list[tuple[str, int, int | None]] = [
    ("new", 0, 12),
    ("growing", 12, 24),
    ("mature", 24, 48),
    ("loyal", 48, None),
]
CHURNED_STATE: str = "churned"

REFERENCE_FORECAST_HORIZON: int = 12
RNG_SEED: int = 42


def _tenure_to_state(tenure: float) -> str:
    """Map a tenure-in-months value to an ordinal state name."""
    for state, lo, hi in TENURE_STATE_BINS:
        if hi is None and tenure >= lo:
            return state
        if hi is not None and lo <= tenure < hi:
            return state
    return TENURE_STATE_BINS[0][0]


def _delete_dataset_rows(conn, dataset_id: str) -> None:
    """D-23 idempotency: remove every row tied to a dataset_id across all tables."""
    conn.execute("DELETE FROM forecasts WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM transition_matrices WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM simulation_runs WHERE matrix_id IN (SELECT id FROM transition_matrices WHERE dataset_id = ?)", [dataset_id])
    conn.execute("DELETE FROM scenarios WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM transitions WHERE dataset_id = ?", [dataset_id])
    conn.execute("DELETE FROM datasets WHERE id = ?", [dataset_id])


def _generate_synthetic_fmcg(rng: np.random.Generator) -> tuple[pd.DataFrame, list[np.ndarray]]:
    """Generate synthetic FMCG transitions (long format) + per-period matrices.

    Returns
    -------
    transitions_df : pd.DataFrame
        Columns: entity_id, period, from_state, to_state, weight.
        entity_id is a synthetic aggregate id (one per brand) — weight encodes flow magnitude.
    P_t_list : list[np.ndarray]
        Per-period transition matrices (length FMCG_N_PERIODS), each shape (5, 5).
    """
    P_t_list: list[np.ndarray] = []
    rows: list[dict] = []
    share = FMCG_INITIAL_SHARE.copy()

    for period in range(1, FMCG_N_PERIODS + 1):
        P_t = np.array(
            [rng.dirichlet(P_BASE_FMCG[i] * FMCG_DIRICHLET_CONCENTRATION) for i in range(5)],
            dtype=np.float64,
        )
        P_t_list.append(P_t)

        for i, from_brand in enumerate(FMCG_BRANDS):
            for j, to_brand in enumerate(FMCG_BRANDS):
                flow = share[i] * P_t[i, j] * FMCG_TOTAL_MARKET_UNITS
                if flow >= 1:
                    rows.append(
                        {
                            "entity_id": f"fmcg_agg_{from_brand}",
                            "period": period,
                            "from_state": from_brand,
                            "to_state": to_brand,
                            "weight": float(round(flow)),
                        }
                    )
        share = share @ P_t
        share = share / share.sum()

    return pd.DataFrame(rows), P_t_list


def _load_telco_transitions(csv_path: Path) -> pd.DataFrame:
    """Parse data/seed/telco_churn.csv into long-format transitions.

    IBM Telco CSV has one row per customer with `tenure` (months) and `Churn` (Yes/No).
    For Phase 01 we treat this as a single-period transition: the customer's state
    AT END of period (tenure-discretized OR 'churned') vs an inferred PRIOR state
    (one tenure bracket below their current bracket — a plausible approximation).
    Customers with tenure=0 are excluded (no prior state to infer).
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"data/seed/telco_churn.csv not found at {csv_path}. "
            f"Place the IBM Watson Sample Data CSV at that path. See data/SOURCES.md."
        )
    raw = pd.read_csv(csv_path)
    raw = raw[raw["tenure"] > 0].copy()

    def _prior_state(tenure: float) -> str:
        prior = max(tenure - 1.0, 0.0)
        return _tenure_to_state(prior)

    raw["from_state"] = raw["tenure"].apply(_prior_state)
    raw["to_state"] = np.where(
        raw["Churn"] == "Yes",
        CHURNED_STATE,
        raw["tenure"].apply(_tenure_to_state),
    )
    transitions = pd.DataFrame(
        {
            "entity_id": raw["customerID"].astype(str),
            "period": 1,
            "from_state": raw["from_state"],
            "to_state": raw["to_state"],
            "weight": 1.0,
        }
    )
    return transitions


def _bulk_insert_transitions(conn, dataset_id: str, df: pd.DataFrame) -> int:
    """Insert long-format transitions for a dataset. Uses DuckDB native df param binding."""
    validate_transitions_df(df)
    df = df.assign(dataset_id=dataset_id)[
        ["dataset_id", "entity_id", "period", "from_state", "to_state", "weight"]
    ]
    conn.register("transitions_df", df)
    try:
        conn.execute("INSERT INTO transitions SELECT * FROM transitions_df")
    finally:
        conn.unregister("transitions_df")
    return len(df)


def _persist_reference_forecast(
    conn,
    dataset_id: str,
    model_type: str,
    horizon: int,
    forecast_array: np.ndarray,
) -> None:
    """Insert one row into the forecasts table with serialized forecast_json."""
    conn.execute(
        "INSERT INTO forecasts (id, dataset_id, model_type, horizon_steps, forecast_json) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            str(uuid.uuid4()),
            dataset_id,
            model_type,
            horizon,
            ndarray_to_json(forecast_array),
        ],
    )
