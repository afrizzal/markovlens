"""Query helpers — all SQL wrapped here, never inline in app/ or domains/."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Dataset:
    """Domain object representing a registered dataset."""

    id: str
    domain: str
    name: str
    source_path: str
    row_count: int
    n_states: int


def register_dataset(
    domain: str,
    name: str,
    source_path: str,
    row_count: int,
    n_states: int,
    metadata: dict | None = None,
) -> str:
    """Insert a new dataset row, return its id."""
    # TODO(phase02)
    raise NotImplementedError("register_dataset — implement in Phase 02")


def list_datasets(domain: str | None = None) -> list[Dataset]:
    """List registered datasets, optionally filtered by domain."""
    # TODO(phase02)
    raise NotImplementedError("list_datasets — implement in Phase 02")


def get_dataset(dataset_id: str) -> Dataset:
    """Fetch a single dataset by id. Raises DatasetNotFoundError if missing."""
    # TODO(phase02)
    raise NotImplementedError("get_dataset — implement in Phase 02")


def load_transitions(dataset_id: str, period_range: tuple[int, int] | None = None) -> pd.DataFrame:
    """Load raw transitions for a dataset, optionally filtered by period range."""
    # TODO(phase02)
    raise NotImplementedError("load_transitions — implement in Phase 02")


def bulk_insert_transitions(dataset_id: str, df: pd.DataFrame) -> int:
    """Bulk insert transitions for a dataset. Returns row count inserted."""
    # TODO(phase02)
    raise NotImplementedError("bulk_insert_transitions — implement in Phase 02")
