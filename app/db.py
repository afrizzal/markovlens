"""Shared Streamlit DB accessor with cold-start auto-seeding (DEPLOY-01).

All page entry points import get_db() from here so the seed sentinel runs once
per cold start regardless of which page loads first (D-05). The spinner fires
only on cache miss (cold start) and is silent on warm reruns (D-05/D-06).
"""

from __future__ import annotations

import logging

import duckdb
import streamlit as st

from core.config import settings
from core.db.connection import get_connection
from core.db.init import ensure_seeded

log = logging.getLogger(__name__)


@st.cache_resource(show_spinner="Preparing demo data…")
def get_db() -> duckdb.DuckDBPyConnection:
    """Return the singleton DuckDB connection, auto-seeding on cold start.

    The env-aware guard (D-08) ensures a seed failure never blocks the app:
    dev surfaces the error, prod shows a soft warning, and the page still renders.
    """
    conn = get_connection()
    try:
        ensure_seeded(conn)
    except Exception as e:  # top-level guard; app must not crash on seed failure
        log.exception("Auto-seed failed")
        if settings.app_env == "development":
            st.error(f"Seed failed: {e}")
            st.exception(e)
        else:
            st.warning("Demo data not available yet — KPIs may show dashes.")
    return conn
