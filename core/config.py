"""Application settings — read from environment via pydantic-settings."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from env vars and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    duckdb_path: Path = Field(default=Path("data/markovlens.duckdb"))

    # App
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Reproducibility
    default_random_seed: int = Field(default=42)

    # Simulation
    default_n_simulations: int = Field(default=10_000, ge=100, le=100_000)
    default_n_steps: int = Field(default=12, ge=1, le=120)


settings = Settings()
