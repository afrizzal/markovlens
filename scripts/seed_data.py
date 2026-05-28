"""Seed local DuckDB with brand-share + churn datasets.

Run with:
    uv run python scripts/seed_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path when run as script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.db.connection import get_connection, init_schema  # noqa: E402


def main() -> None:
    """Initialize schema + load sample datasets."""
    print("Connecting to DuckDB...")
    conn = get_connection()
    init_schema(conn)
    print(f"Schema initialized. Tables:")
    tables = conn.execute("SHOW TABLES").fetchall()
    for (name,) in tables:
        print(f"  - {name}")

    # TODO(phase02): Load brand_share + churn datasets
    print("\n[TODO] Dataset ingestion — implement in Phase 02.")
    print("       See .claude/skills/dataset-prepper/SKILL.md for the procedure.")


if __name__ == "__main__":
    main()
