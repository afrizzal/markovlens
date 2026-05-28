"""Churn service — orchestrates core engine for the churn UI page."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChurnAnalysisResult:
    """Output of run_analysis — chart-ready data for Streamlit page."""

    sankey_chart_json: dict
    state_distribution_per_period: list[dict[str, float]]
    kpis: dict[str, float]


def list_cohorts() -> list[dict]:
    """List available customer cohorts."""
    # TODO(phase04)
    raise NotImplementedError("list_cohorts — implement in Phase 04")


def run_analysis(cohort_id: str, horizon: int) -> ChurnAnalysisResult:
    """Compute state distribution evolution + Sankey flows."""
    # TODO(phase04)
    raise NotImplementedError("run_analysis — implement in Phase 04")


def simulate_scenario(cohort_id: str, transition_overrides: dict) -> ChurnAnalysisResult:
    """What-if: override specific transition probabilities, compute new forecast."""
    # TODO(phase04)
    raise NotImplementedError("simulate_scenario — implement in Phase 04")
