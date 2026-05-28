# Context7 MCP Usage

Use Context7 MCP to fetch current documentation whenever the user asks about a library, framework, SDK, API, CLI tool, or cloud service — even well-known ones like Streamlit, NumPy, Plotly, DuckDB, Pandas, Pydantic, scikit-learn. This includes API syntax, configuration, version migration, library-specific debugging, setup instructions, and CLI tool usage. Use even when you think you know the answer — your training data may not reflect recent changes. Prefer this over web search for library docs.

**Do not use for:** refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

## When to Use (Examples)

| Task | Use context7? |
|---|---|
| "How do I do multi-page apps in Streamlit?" | ✅ Yes |
| "What's the new NumPy 2.0 syntax for default_rng?" | ✅ Yes |
| "How to read Parquet with DuckDB?" | ✅ Yes |
| "Pydantic v2 settings pattern" | ✅ Yes |
| "Plotly Sankey diagram setup" | ✅ Yes |
| "Refactor this Streamlit page into components" | ❌ No (it's refactoring) |
| "Why is my Markov simulation returning all zeros?" | ❌ No (business logic bug) |

## Steps

1. **Always start with `resolve-library-id`** using the library name and the user's question, unless the user provides an exact library ID in `/org/project` format
2. **Pick the best match** (ID format: `/org/project`) by: exact name match, description relevance, code snippet count, source reputation (High/Medium preferred), and benchmark score (higher is better). If results don't look right, try alternate names or queries (e.g., "duckdb-py" vs "duckdb"). Use version-specific IDs when the user mentions a version.
3. **`query-docs`** with the selected library ID and the user's full question (not single words)
4. **Answer using the fetched docs** — cite the relevant snippet/section

## Project-Relevant Libraries (Common Lookups)

| Library | Likely ID hint |
|---|---|
| Streamlit | `streamlit/streamlit` |
| streamlit-shadcn-ui | search "shadcn-ui streamlit" |
| Plotly | `plotly/plotly.py` |
| NumPy | `numpy/numpy` |
| Pandas | `pandas-dev/pandas` |
| DuckDB | `duckdb/duckdb` (or `duckdb/duckdb-web` for docs) |
| Pydantic | `pydantic/pydantic` |
| pytest | `pytest-dev/pytest` |
| ReportLab | search "reportlab" |
| uv | `astral-sh/uv` |
| ruff | `astral-sh/ruff` |
