# Deployment Guide

> Single source of truth for deploying MarkovLens.

## Target: Streamlit Community Cloud (Free Tier)

| Resource | Limit | MarkovLens needs |
|---|---|---|
| RAM | 1 GB | ✅ < 500 MB |
| CPU | 1 vCPU | ✅ Adequate |
| Disk | Ephemeral (resets on reboot) | ⚠️ See "Data Strategy" |
| Public URL | yes (`*.streamlit.app`) | ✅ |
| Custom domain | possible (CNAME) | ✅ Future enhancement |
| Always-on | yes (no cold start delays for active apps) | ✅ |
| Cost | $0 | ✅ |

## Pre-Deploy Checklist

- [ ] All tests pass: `uv run pytest`
- [ ] No lint errors: `uv run ruff check .`
- [ ] No type errors: `uv run mypy core/ domains/`
- [ ] App runs locally: `uv run streamlit run app/Home.py`
- [ ] DuckDB file is under 500 MB (or use Parquet-only architecture for raw data)
- [ ] `.streamlit/secrets.toml` template documented (NOT committed)
- [ ] `README.md` has live URL placeholder updated
- [ ] All datasets either bundled or auto-downloadable from public source

## Deployment Steps

### 1. Push to GitHub

```bash
rtk git add .
rtk git commit -m "chore: prepare for deploy"
rtk git push origin master
```

### 2. Streamlit Cloud Setup

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `afrizzal/markovlens`
5. Branch: `master`
6. Main file: `app/Home.py`
7. Advanced settings:
   - Python version: 3.12
   - Custom requirements: leave blank (uses `pyproject.toml` via uv automatically)
8. Click "Deploy"

First deploy takes ~3-5 minutes (installing uv + deps).

### 3. Secrets Configuration (if any)

In Streamlit Cloud app settings → Secrets, paste TOML:

```toml
DEFAULT_RANDOM_SEED = 42
LOG_LEVEL = "INFO"
# Add any other secret env vars here
```

### 4. Verify

Visit the assigned URL (e.g., `https://markovlens.streamlit.app`):

- [ ] Home page loads
- [ ] Sidebar nav works
- [ ] Each page (Brand Share, Churn, Reports, Settings) renders
- [ ] At least one forecast runs successfully
- [ ] Charts display correctly
- [ ] No console errors

### 5. Update README

Add live URL to `README.md` badges section and roadmap.

## Data Strategy

Streamlit Cloud disk is ephemeral — the `.duckdb` file resets when the container restarts.

**Strategy A — Bundle datasets (RECOMMENDED for v0.1):**
- Commit small public datasets to `data/raw/` (override .gitignore for these specific files)
- On app cold-start, run `scripts/seed_data.py` to populate DuckDB
- Caches via `@st.cache_resource` so subsequent requests are fast

**Strategy B — Download from public source on cold-start:**
- Use Kaggle API or public GitHub raw URL
- Slower cold-start but smaller repo
- Requires Kaggle API token in Streamlit secrets

**Strategy C — External Postgres (NOT for free tier):**
- Use Neon/Supabase free Postgres for persistent storage
- More complex, breaks "single-file portable" simplicity
- Reserve for v0.3 if scaling matters

## Custom Domain (Optional)

If purchasing a domain (e.g., `markovlens.app`):

1. Add CNAME: `www → <your-app>.streamlit.app`
2. Configure in Streamlit Cloud → Settings → Custom subdomain
3. Wait for DNS propagation (~30 min)
4. Update README + LinkedIn with custom URL

## Rollback

1. In Streamlit Cloud → app → "Reboot app" if minor issue
2. For code issue: `git revert <bad-commit>` + `git push` → auto-redeploys
3. For data issue: rerun `scripts/seed_data.py` to reset DuckDB

## Monitoring

Free tier lacks built-in observability. Workarounds:

- Add `st.sidebar.caption(f"Build: {os.getenv('GIT_COMMIT_SHA', 'dev')}")` to see deployed version
- Log to stderr (visible in Streamlit Cloud logs UI)
- Optional: add Sentry SDK for error tracking (free tier 5k events/month)

## Cost Monitoring

Streamlit Community Cloud is free for public apps. If usage grows:

- Streamlit Cloud paid tier — $20/mo for private apps + more resources
- Self-host on Cloud Run / Fly.io / Railway — $5-20/mo, more control

## Known Issues

- [ ] _None yet — will populate as encountered_

## Future Enhancements

- [ ] GitHub Actions CI: run tests before merge
- [ ] Automated screenshot generation for README
- [ ] Sentry error tracking
- [ ] Sitemap + SEO meta tags
- [ ] Analytics (Plausible / Umami)
