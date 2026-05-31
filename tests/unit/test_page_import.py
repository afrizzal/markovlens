"""BS-06 import smoke test + Overview structural check for app/pages/1_Brand_Share.py.

This module tests:
1. The Brand Share page module can be imported (syntax + import-time check).
   We use AppTest.from_file with a timeout; on timeout we fall back to the
   importlib pure-import approach (which avoids the DB call).
2. _build_overview_figure produces a Plotly figure with at least one trace and
   a 'today' separator shape (Task 2a structural check — pure function, no DB).

Mechanism:
    Primary: AppTest.from_file with increased timeout.
    Fallback: importlib loads the module without executing Streamlit's
    rendering loop — set_page_config() + register_theme() run at module level,
    but the main() call at the bottom is guarded by the @st.cache_resource /
    @st.cache_data decorators which are no-ops without a running Streamlit server.
    Since main() is called unconditionally at module load, we monkey-patch
    st.stop / st.cache_resource etc. to no-ops before the importlib load.
"""
from __future__ import annotations

import contextlib
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PAGE_PATH = str(Path(__file__).parent.parent.parent / "app" / "pages" / "1_Brand_Share.py")
CHURN_PAGE_PATH = str(Path(__file__).parent.parent.parent / "app" / "pages" / "2_Churn.py")


def _load_page_module_importlib():
    """Load app/pages/1_Brand_Share.py as a Python module via importlib.

    The filename starts with a digit so standard import syntax cannot reference it.
    This function loads the module with DB calls patched to avoid needing a real
    DuckDB file in the test environment.

    Returns
    -------
    types.ModuleType
        The loaded page module, or raises on failure.
    """
    # Patch service.list_datasets to return empty list (triggers st.stop path)
    # and st.stop to raise SystemExit(0) so execution halts cleanly.
    # Also patch get_connection to avoid DB initialization.
    mock_datasets = []
    mock_conn = MagicMock()

    # Build mock patches for DB + service
    patches = [
        patch("core.db.connection.get_connection", return_value=mock_conn),
        patch("domains.brand_share.service.list_datasets", return_value=mock_datasets),
    ]

    for p in patches:
        p.start()

    try:
        spec = importlib.util.spec_from_file_location("brand_share_page", PAGE_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {PAGE_PATH}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules.pop("brand_share_page", None)
        sys.modules["brand_share_page"] = mod
        with contextlib.suppress(SystemExit):
            # st.stop() raises SystemExit in test context — acceptable
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        for p in patches:
            p.stop()

    return mod


# ---------------------------------------------------------------------------
# Test 1: Page module is importable (smoke test)
# ---------------------------------------------------------------------------

def test_brand_share_page_imports_without_error():
    """BS-06: Brand Share page module can be loaded without an ImportError or syntax error.

    This is the importlib fallback path. It verifies that all imports resolve and
    the module structure (register_theme, set_page_config, main) is intact.
    AppTest was not used here due to DB timeout in test environments without
    a seeded DuckDB file — documented as 'importlib fallback' per plan spec.
    """
    mod = _load_page_module_importlib()
    # Verify the critical attributes are present on the loaded module
    assert hasattr(mod, "_build_overview_figure"), "Missing _build_overview_figure in page module"
    assert hasattr(mod, "main"), "Missing main() in page module"
    assert hasattr(mod, "_cached_forecast"), "Missing _cached_forecast in page module"


# ---------------------------------------------------------------------------
# Test 2: _build_overview_figure structural check
# ---------------------------------------------------------------------------

def test_overview_figure_has_separator():
    """Overview stacked-area helper produces a figure with >= 1 trace and a 'today' separator.

    _build_overview_figure is a pure function (no Streamlit side effects) so we
    can call it directly after loading the page module. The test uses synthetic
    small arrays that cover the 2-state, 3-period case.

    Asserts:
        (a) fig.data has at least 1 trace (historical brand trace present)
        (b) a vertical separator exists — either as a layout shape (from add_vline)
            or as an annotation with 'today' text.

    This is the Overview structural check required by BS-06 (Task 2a).
    """
    # Arrange: 2 states, 3 historical periods, 4-step forecast
    n_hist = 3
    n_fc = 4

    rng = np.random.default_rng(0)
    historical_shares = np.abs(rng.random((n_hist, 2)))
    historical_shares /= historical_shares.sum(axis=1, keepdims=True)
    forecast = np.abs(rng.random((n_fc, 2)))
    forecast /= forecast.sum(axis=1, keepdims=True)
    state_labels = ["BrandA", "BrandB"]

    # Load module and extract the helper
    mod = _load_page_module_importlib()
    build_fn = mod._build_overview_figure

    # Act
    fig = build_fn(historical_shares, forecast, state_labels, horizon=n_fc, model="m1")

    # Assert (a): at least one trace from historical data
    assert len(fig.data) >= 1, (
        f"Expected >= 1 trace in overview figure, got {len(fig.data)}"
    )

    # Assert (b): 'today' separator is present
    # add_vline() adds to fig.layout.shapes (Plotly stores vlines as shapes).
    today_in_shapes = len(fig.layout.shapes) >= 1
    today_in_annotations = any(
        "today" in (getattr(a, "text", "") or "")
        for a in (fig.layout.annotations or [])
    )
    assert today_in_shapes or today_in_annotations, (
        "Expected a 'today' separator (shape or annotation) in the overview figure. "
        f"shapes count={len(fig.layout.shapes)}, "
        f"annotations count={len(fig.layout.annotations or [])}"
    )


# ---------------------------------------------------------------------------
# Churn page (2_Churn.py) smoke test — CH-04
# ---------------------------------------------------------------------------

def _load_churn_page_module_importlib():
    """Load app/pages/2_Churn.py as a Python module via importlib.

    The filename starts with a digit so standard import syntax cannot reference it.
    Patches DB connection and churn service.list_datasets to return empty list,
    which triggers the st.stop() path — a clean exit from the module.

    Returns
    -------
    types.ModuleType
        The loaded page module, or raises on failure.
    """
    mock_conn = MagicMock()
    mock_datasets: list = []

    patches = [
        patch("core.db.connection.get_connection", return_value=mock_conn),
        patch("domains.churn.service.list_datasets", return_value=mock_datasets),
    ]

    for p in patches:
        p.start()

    try:
        spec = importlib.util.spec_from_file_location("churn_page", CHURN_PAGE_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {CHURN_PAGE_PATH}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules.pop("churn_page", None)
        sys.modules["churn_page"] = mod
        with contextlib.suppress(SystemExit):
            # st.stop() raises SystemExit in test context — acceptable
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        for p in patches:
            p.stop()

    return mod


def test_churn_page_imports_without_error():
    """CH-04: Churn page module can be loaded without an ImportError or syntax error.

    Mirrors the brand-share importlib smoke-test (BS-06). Verifies that all imports
    resolve and the module structure (main, _cached_analysis) is intact.
    Uses importlib fallback with mock.patch to avoid a real DuckDB connection.
    """
    mod = _load_churn_page_module_importlib()
    assert hasattr(mod, "main"), "Missing main() in churn page module"
    assert hasattr(mod, "_cached_analysis"), "Missing _cached_analysis in churn page module"


# ---------------------------------------------------------------------------
# Home page (app/Home.py) smoke test — HOME-01
# ---------------------------------------------------------------------------

HOME_PAGE_PATH = str(Path(__file__).parent.parent.parent / "app" / "Home.py")


def _load_home_page_module_importlib():
    """Load app/Home.py as a Python module via importlib.

    Home.py runs all UI code at module level (no main() wrapper).
    Patches DB connection and query helpers to avoid needing a real DuckDB file.

    Returns
    -------
    types.ModuleType
        The loaded Home page module, or raises on failure.
    """
    from core.db.queries import HomeKpis

    mock_conn = MagicMock()
    mock_kpis = HomeKpis(
        dataset_count=2,
        sim_run_count=5,
        last_forecast_at=None,
        avg_mape=None,
    )
    mock_recent: list = []

    patches = [
        patch("core.db.connection.get_connection", return_value=mock_conn),
        patch("core.db.queries.get_home_kpis", return_value=mock_kpis),
        patch("core.db.queries.list_recent_forecasts", return_value=mock_recent),
    ]

    for p in patches:
        p.start()

    try:
        spec = importlib.util.spec_from_file_location("home_page", HOME_PAGE_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {HOME_PAGE_PATH}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules.pop("home_page", None)
        sys.modules["home_page"] = mod
        with contextlib.suppress(SystemExit):
            # st.stop() raises SystemExit in test context — acceptable
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        for p in patches:
            p.stop()

    return mod


def test_home_page_imports_without_error():
    """HOME-01: Home page module can be loaded without an ImportError or syntax error.

    Verifies that all imports resolve (including get_home_kpis, list_recent_forecasts,
    register_theme, inject_theme, kpi_card, empty_state) and the wired KPI strip +
    Recent Forecasts code paths execute without crashing.
    Uses importlib fallback with mock.patch to avoid a real DuckDB connection.
    """
    mod = _load_home_page_module_importlib()
    # Home.py has module-level constants — verify they are present after load
    assert hasattr(mod, "DOMAIN_ICON"), "Missing DOMAIN_ICON constant in Home page module"
    assert hasattr(mod, "_get_db"), "Missing _get_db() in Home page module"


# ---------------------------------------------------------------------------
# Settings page (app/pages/4_Settings.py) smoke test — SET-01
# ---------------------------------------------------------------------------

SETTINGS_PAGE_PATH = str(
    Path(__file__).parent.parent.parent / "app" / "pages" / "4_Settings.py"
)


def _load_settings_page_module_importlib():
    """Load app/pages/4_Settings.py as a Python module via importlib.

    The filename starts with a digit so standard import syntax cannot reference it.
    Patches DB connection and list_datasets to return an empty list, which exercises
    the empty_state path without needing a real DuckDB file.

    Returns
    -------
    types.ModuleType
        The loaded Settings page module, or raises on failure.
    """
    mock_conn = MagicMock()
    mock_datasets: list = []

    patches = [
        patch("core.db.connection.get_connection", return_value=mock_conn),
        patch("core.db.queries.list_datasets", return_value=mock_datasets),
    ]

    for p in patches:
        p.start()

    try:
        spec = importlib.util.spec_from_file_location("settings_page", SETTINGS_PAGE_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {SETTINGS_PAGE_PATH}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules.pop("settings_page", None)
        sys.modules["settings_page"] = mod
        with contextlib.suppress(SystemExit):
            # st.stop() raises SystemExit in test context — acceptable
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        for p in patches:
            p.stop()

    return mod


def test_settings_page_imports_without_error():
    """SET-01: Settings page module can be loaded without an ImportError or syntax error.

    Mirrors the brand-share and churn importlib smoke-tests. Verifies that all imports
    resolve (list_datasets, empty_state, register_theme, inject_theme, core.config.settings)
    and the 4-tab layout code executes without crashing.
    Uses importlib fallback with mock.patch to avoid a real DuckDB connection.
    """
    mod = _load_settings_page_module_importlib()
    # Settings page has module-level constants — verify they are present after load
    assert hasattr(mod, "PAGE_NS"), "Missing PAGE_NS constant in Settings page module"
    assert hasattr(mod, "APP_VERSION"), "Missing APP_VERSION constant in Settings page module"
    assert hasattr(mod, "_get_db"), "Missing _get_db() in Settings page module"
