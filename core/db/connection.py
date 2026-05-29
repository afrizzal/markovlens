"""DuckDB connection singleton + schema initialization."""

from __future__ import annotations

from pathlib import Path

import duckdb

from core.config import settings

_connection: duckdb.DuckDBPyConnection | None = None


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return the singleton DuckDB connection (creates if not exists)."""
    global _connection
    if _connection is None:
        settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        _connection = duckdb.connect(str(settings.duckdb_path))
        init_schema(_connection)
    return _connection


def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Apply schema.sql to the connection (idempotent)."""
    schema_path = Path(__file__).parent / "schema.sql"
    conn.execute(schema_path.read_text())


def close_connection() -> None:
    """Close the singleton connection. Useful for tests."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
