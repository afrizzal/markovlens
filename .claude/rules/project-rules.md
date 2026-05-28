# Project Rules — MarkovLens

## Planning & Documentation Rules

### 1. Do NOT create new planning folders outside designated locations

- ❌ Do not create: `plan/`, `plans/`, alternative `.planning/` directories
- ✅ All new planning notes go to: `docs/planning/`
- ✅ Temporary/uncertain notes: `docs/planning/archive/temp-review/`
- ✅ GSD-managed artifacts (`STATE.md`, `PROJECT.md`, `ROADMAP.md`, `phases/`) — never edit manually

### 2. After every coding session, update these files

- `docs/planning/task-progress.md` — move task to Done + commit hash
- `docs/planning/decisions.md` — if new technical decision was made
- `CLAUDE.md` — if new feature/page/module
- `README.md` — if user-visible change
- `manual-book.md` — if user workflow changed (both English + Indonesian sections)

### 3. Documentation hierarchy

| Tier | Files | Update frequency |
|---|---|---|
| Public-facing | README, manual-book, CONTRIBUTING | Per release |
| Claude config | CLAUDE.md, .claude/rules/* | When conventions change |
| Planning (live) | docs/planning/* | Per task |
| Technical reference | docs/MARKOV-MODELS.md, docs/DATABASE.md, etc. | When architecture/schema changes |
| GSD (auto) | .planning/* | Auto by GSD commands |

## Data Layer Rules

### 4. All persistent data via DuckDB

- File: `data/markovlens.duckdb`
- Connection: `core/db/connection.py` singleton
- Queries wrapped in `core/db/queries.py`
- No raw SQL strings scattered across `app/` files
- See [data-storage.md](data-storage.md)

### 5. Datasets are gitignored

- Raw files in `data/raw/` regenerable from sources (Kaggle)
- DuckDB file (`*.duckdb`) is binary, gitignored
- Provide seed script: `scripts/seed_data.py` that downloads + processes raw data

### 6. Never query the DB without a scope filter

When relevant — always filter by `dataset_id` (or appropriate scope):

```python
# ✅
conn.execute("SELECT * FROM transitions WHERE dataset_id = ?", [dataset_id])

# ❌
conn.execute("SELECT * FROM transitions")
```

## Markov Engine Rules

### 7. Every transition matrix must be validated

Use `validate_transition_matrix()` from `core/models.py` after building or modifying any matrix. See [markov-patterns.md](markov-patterns.md).

### 8. Calibration table is sacrosanct

`LONGSHOT_CALIBRATION` in `core/simulation.py` is derived from Becker (2026). Do not modify without:
- Updating source citation in [docs/MONTE-CARLO.md](../../docs/MONTE-CARLO.md)
- Rerunning all backtests
- Logging the change in `docs/planning/decisions.md`

### 9. Walk-forward validation only

Backtests must never let future data leak into past matrix estimates. Use `walk_forward_backtest()` helper. See [markov-patterns.md](markov-patterns.md).

## Security Rules

### 10. No secrets in code

- Read from `os.environ` via `core/config.py` (pydantic-settings)
- `.env` is gitignored; `.env.example` is committed (template)
- Never commit API keys, even in commit messages

### 11. No PII in datasets

If a dataset contains PII (e.g., real customer IDs), anonymize at ingestion:
- Hash identifiers (SHA-256, store as `entity_id`)
- Strip names, emails, phone numbers
- Document anonymization in dataset metadata

## API Rules

### 12. Core engine is pure (no Streamlit imports)

- `core/` and `domains/` must NOT import `streamlit`
- Test this: `grep -r "import streamlit" core/ domains/` should return empty
- Streamlit lives only in `app/`

### 13. Domain services wrap core

```
app/pages/1_Brand_Share.py        →  domains/brand_share/service.py  →  core/models.py
```

Pages call services; services call core. No skipping layers.

### 14. Function return types

- Multi-value returns: use `@dataclass(frozen=True)` or Pydantic model
- Never return tuples with > 2 elements (positional ambiguity)
- Never return dicts as "ad-hoc structs" — use a proper type

## UI Rules

### 15. UI strings: English

App UI is English (portfolio piece for international recruiters). Indonesian only in `manual-book.md` and any optional user-facing forms.

### 16. Use the design system

- Colors: CSS variables from `app/styles/theme.css`
- Typography: scale defined in theme.css
- Components: reuse from `app/components/`
- Plotly: theme template from `app/styles/plotly_theme.py`

### 17. No emojis as functional icons

Use Lucide-style SVG icons (via `streamlit-shadcn-ui` or custom HTML). Emojis only in headers/page icons where unavoidable.

## Git Rules

### 18. Atomic commits, conventional style

- One logical change per commit
- Format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Subject < 70 chars, body if needed

### 19. Always use `rtk` prefix for bash/git

Token optimization per user's global CLAUDE.md. Even in chained commands:

```bash
# ✅
rtk git add core/models.py && rtk git commit -m "feat: add m3 model"

# ❌
git add . && git commit -m "msg"
```

### 20. Never commit datasets or DB files

- `data/*.duckdb`, `data/raw/*`, `data/processed/*` — all gitignored
- If accidentally committed, use `git rm --cached <file>` + add to `.gitignore`

## Testing Rules

### 21. Pure functions in core/ must have unit tests

- Coverage target: > 80% for `core/`
- Use `pytest` fixtures for shared setup
- Mark slow tests with `@pytest.mark.slow`

### 22. Integration tests use real DuckDB

- Use temporary file per test (`tmp_path` fixture)
- Mark with `@pytest.mark.integration`
- Run separately: `pytest -m integration`

## Deployment Rules

### 23. Deployment target: Streamlit Cloud (free tier)

- App must work on Streamlit Cloud's resource limits (1GB RAM, 1 CPU)
- DuckDB file size < 500MB
- No long-running background processes (Streamlit Cloud kills them)
- See [docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md)
