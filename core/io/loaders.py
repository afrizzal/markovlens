"""Dataset loaders — Kaggle CSV → MarkovLens canonical format."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_brand_share_csv(path: Path) -> pd.DataFrame:
    """Load a brand-share dataset from Kaggle format and convert to long transitions."""
    # TODO(phase02): see .claude/skills/dataset-prepper/SKILL.md
    raise NotImplementedError("load_brand_share_csv — implement in Phase 02")


def load_churn_csv(path: Path) -> pd.DataFrame:
    """Load a churn dataset from Kaggle format and convert to state transitions."""
    # TODO(phase02): see .claude/skills/dataset-prepper/SKILL.md
    raise NotImplementedError("load_churn_csv — implement in Phase 02")


REQUIRED_TRANSITION_COLUMNS: frozenset[str] = frozenset(
    {"entity_id", "period", "from_state", "to_state"}
)


def validate_transitions_df(df: pd.DataFrame) -> None:
    """Validate a long-format transitions DataFrame before DuckDB insertion.

    Phase 01 minimal scope (per RESEARCH.md Open Question 1):
    - Required columns: entity_id, period, from_state, to_state
    - No NaN in identifier or state columns (would corrupt transition matrix)
    - 'weight' is optional (defaults to 1.0 at INSERT time per schema)

    Parameters
    ----------
    df : pd.DataFrame
        Long-format transitions to validate.

    Raises
    ------
    ValueError
        If a required column is missing or NaN appears in entity_id/from_state/to_state.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "entity_id": ["a"], "period": [1], "from_state": ["x"], "to_state": ["y"],
    ... })
    >>> validate_transitions_df(df)  # silent on valid input
    """
    missing = REQUIRED_TRANSITION_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}. "
            f"Required: {sorted(REQUIRED_TRANSITION_COLUMNS)}"
        )
    for col in ("entity_id", "from_state", "to_state"):
        if df[col].isna().any():
            n_na = int(df[col].isna().sum())
            raise ValueError(
                f"Column '{col}' contains {n_na} NaN value(s); cannot build transitions."
            )
