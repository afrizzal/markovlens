"""Brand share service — orchestrates core engine for the brand-share UI page."""
from __future__ import annotations

from dataclasses import dataclass

from core.db.queries import Dataset


@dataclass(frozen=True)
class BrandShareForecastResult:
    """Output of run_forecast — chart-ready data for Streamlit page."""

    forecast_chart_json: dict  # Plotly figure dict
    transition_matrix: list[list[float]]
    kpis: dict[str, float]
    confidence_bands: dict[float, list[float]]


def list_datasets() -> list[Dataset]:
    """List all brand_share-domain datasets registered in DB."""
    # TODO(phase03)
    raise NotImplementedError("list_datasets — implement in Phase 03")


def run_forecast(
    dataset_id: str,
    model_type: str,
    horizon: int,
) -> BrandShareForecastResult:
    """End-to-end: load → build matrix → forecast → return chart-ready data."""
    # TODO(phase03)
    raise NotImplementedError("run_forecast — implement in Phase 03")
