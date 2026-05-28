# Getting Started — Manual Steps Checklist

> **What this is:** Step-by-step manual commands for you (afrizzal) to run after the scaffold.
>
> **When to delete this file:** After you've completed all 6 steps and the app is running locally.

---

## ✅ Already Done (by Claude in scaffold session)

- Project structure created (82 files across `core/`, `domains/`, `app/`, `tests/`, `docs/`, `.claude/`)
- All documentation written (README, CLAUDE.md, manual-book, 6 technical docs, 4 planning docs)
- All `.claude/` config (8 rules, 3 commands, 4 skills, memory index, settings.local.json)
- Code skeleton with TODO stubs for Phase 01-04 implementation
- `git init` executed (branch: `master`)

---

## 🔧 Manual Steps For You (in order)

### Step 1 — Install `uv` (Python package manager)

Open **PowerShell as Administrator** and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation finishes, **close and reopen PowerShell**, then verify:

```powershell
uv --version
```

You should see something like `uv 0.5.x`. If you get "command not found", restart PowerShell again.

---

### Step 2 — Install Python 3.12 + Dependencies

In PowerShell, navigate to the project:

```powershell
cd D:\Aff\proj\markovlens
```

Then sync dependencies (this will also install Python 3.12 if you don't have it):

```powershell
uv sync
```

This downloads and installs:
- Python 3.12 (if needed)
- Streamlit, NumPy, Pandas, SciPy, DuckDB, Plotly, and ~30 other packages
- Dev tools: pytest, ruff, mypy, jupyter

First run takes 2-3 minutes. You'll see a `.venv/` folder created — that's your isolated Python environment, managed by uv.

**Verify:**

```powershell
uv run python --version
# Should print: Python 3.12.x
```

---

### Step 3 — Test the App Runs

Launch the Streamlit app:

```powershell
uv run streamlit run app/Home.py
```

This will:
- Open your browser to `http://localhost:8501`
- Show the MarkovLens Home page
- Sidebar will show "Home" (other pages added in Phase 03+)

**Press Ctrl+C in the terminal to stop the app.**

If you see errors, check:
- Did `uv sync` complete without errors?
- Is port 8501 already in use? Try `uv run streamlit run app/Home.py --server.port 8502`

---

### Step 4 — Initialize GSD Planning System

In a **NEW PowerShell window** (so Streamlit can keep running if you want), open Claude Code in your **Sonnet executor terminal** (your usual workflow):

```powershell
cd D:\Aff\proj\markovlens
claude
```

Then in Claude Code, run:

```
/gsd:new-project
```

When GSD asks questions, use these answers (already aligned with our planning):

| Question | Answer |
|---|---|
| Project name | `MarkovLens` |
| Description | `Multi-domain forecasting workbench applying Markov chain models (m1/m2/m3 from Chan 2015) to brand share and customer churn forecasting. Portfolio piece for BA/BI role.` |
| Tech stack | `Python 3.12, uv, Streamlit, streamlit-shadcn-ui, Plotly, NumPy, Pandas, SciPy, scikit-learn, DuckDB, pytest, ruff, mypy` |
| Timeline | `4 weeks (target v0.1 by 2026-06-25)` |
| Constraints | `Solo developer, must deploy to Streamlit Cloud free tier (1GB RAM), BA/BI portfolio focus, English UI strings, Indonesian + English docs` |
| First milestone | `v0.1 — Core engine + Brand Share domain + Customer Churn domain + UI polish + deploy` |

GSD will populate `.planning/PROJECT.md`, `.planning/ROADMAP.md`, and `.planning/STATE.md`.

---

### Step 5 — First Commit

Back in PowerShell:

```powershell
cd D:\Aff\proj\markovlens
rtk git add .
rtk git commit -m "chore: initial scaffold with full documentation and planning"
```

Verify:

```powershell
rtk git log --oneline
```

---

### Step 6 — Submit to Claude Design (for UI mockup)

1. Open https://claude.ai in your browser
2. Start a new conversation
3. **Attach these 3 files** from your project:
   - `docs/planning/master-plan.md`
   - `docs/MARKOV-MODELS.md`
   - `docs/MONTE-CARLO.md`
4. **Paste the prompt** I gave you earlier in our brainstorming session (the "PROMPT untuk CLAUDE DESIGN" section starting with `# Role`)
5. Claude Design will produce a React + Tailwind artifact with 11 page mockups
6. Save the output — we'll use it in **Phase 05 (UI Polish)** to extract design tokens

---

## 🚀 What's Next (After Manual Steps)

Once Steps 1-6 are done, you're ready to start **Phase 01: Markov Engine Core**. In your Sonnet terminal, run:

```
/gsd:plan-phase 01
```

This will create `.planning/phases/01-markov-engine-core/PLAN.md`. Once approved, run `/gsd:execute-phase 01` and Sonnet will implement:
- `core/models.py` — m1, m2, m3 with all validators
- `core/simulation.py` — Monte Carlo + calibration
- `core/metrics.py` — MAPE, Brier, log-loss
- `core/validation.py` — walk-forward backtester
- `tests/unit/*` — unit tests for all of above

Expected duration: **2-3 days of work** for Phase 01.

---

## 📞 If You Get Stuck

| Problem | Solution |
|---|---|
| `uv: command not found` after install | Close + reopen PowerShell. If still fails, check `$env:Path` includes `%USERPROFILE%\.cargo\bin` |
| `uv sync` fails with network error | Check internet; behind corporate proxy may need `UV_HTTP_PROXY` env var |
| `streamlit run` says port in use | Use `--server.port 8502` flag |
| `/gsd:new-project` not found | Make sure you're in the markovlens folder; GSD is per-directory |
| Browser doesn't open automatically | Manually open `http://localhost:8501` |

For anything else: come back to the Opus terminal (this conversation) and ask.

---

## ✅ Verification Checklist

Before deleting this file, confirm:

- [ ] `uv --version` works
- [ ] `uv sync` completed without errors
- [ ] `uv run streamlit run app/Home.py` opens the Home page in browser
- [ ] `/gsd:new-project` populated `.planning/` files
- [ ] First commit exists (`git log --oneline` shows it)
- [ ] Claude Design output saved somewhere accessible

Once all 6 checkboxes are ✅, you can delete this file with:

```powershell
rtk git rm GETTING-STARTED.md
rtk git commit -m "docs: remove getting-started after onboarding"
```

Then go directly to running `/gsd:plan-phase 01` in your Sonnet terminal.

---

**Project ready.** ✨
