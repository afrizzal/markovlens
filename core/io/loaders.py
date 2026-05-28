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
