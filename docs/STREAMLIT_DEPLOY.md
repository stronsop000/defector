# Deploying the Parent Feedback dashboard to Streamlit Community Cloud

Goal: a public URL like `defector.streamlit.app` that anyone (your leader,
the judges, future employers) can open and see the live dashboard.

Streamlit Community Cloud is free for public repos. The deploy takes ~5 minutes.

## Prerequisites

- The repo is pushed to public GitHub (see `GITHUB_SETUP.md`)
- `data/reviews.duckdb` has been committed (see "Data for the public dashboard"
  below — by default it's gitignored, but you'll want a snapshot in the repo
  so the public dashboard isn't empty)

## Data for the public dashboard

The default `.gitignore` excludes `data/reviews.duckdb` because it's
regeneratable and can be large. But for a public dashboard demo, you want
the DB to be available so the page isn't empty.

Two options:

**Option A — commit a snapshot (simplest, recommended for the prize):**

```bash
# Force-add despite .gitignore
git add -f data/reviews.duckdb
git commit -m "Snapshot reviews.duckdb for public dashboard"
git push
```

This is fine for the prize submission. The file is probably 10-50 MB which
GitHub handles. The snapshot will go stale unless you re-commit, which is
acceptable for the May 31 deadline.

**Option B — let Streamlit Cloud regenerate it (overkill for the prize):**

You'd need to configure Streamlit Cloud secrets with `GEMINI_API_KEY`, run
scrape + classify on deploy via a startup script, and accept ~5-10 min cold
boots. Skip this for the prize unless we have spare time post-deploy.

## Deploy

1. Go to https://share.streamlit.io and sign in with your GitHub account
2. Click "Create app" → "Deploy from existing repo"
3. Fill in:
   - **Repository:** `<your-handle>/defector`
   - **Branch:** `main`
   - **Main file path:** `dashboard/app.py`
   - **App URL (custom subdomain):** `defector` (or `defector-kinedu`, whatever's available)
4. Click "Advanced settings":
   - **Python version:** 3.13
   - **Secrets:** add this block (paste from your local `.env`):
     ```toml
     GEMINI_API_KEY = "AIza..."
     ```
     (Only needed if you want the dashboard to do live LLM calls. For
     read-only dashboard viewing, you can skip this entirely.)
5. Click "Deploy"

First build takes ~3-5 min (installing requirements). Subsequent reboots are
~30 seconds.

## After deploy

Open the URL. You should see the Parent Feedback header, KPI cards populated, and
the four tabs.

Things to verify:
- ✓ Overview heatmap renders
- ✓ Switching Opportunities tab shows real quotes
- ✓ Generated outputs tab loads memo + copy markdown
- ✓ Sidebar filters work

If the dashboard shows "No database found" it means `data/reviews.duckdb`
isn't committed — go back to "Data for the public dashboard" above.

## Add the URL to the repo

Once deployed, paste the URL into:

1. **GitHub repo About → Website field** (right sidebar of the repo page)
2. **README.md** — add a badge at the top:
   ```markdown
   [![Live dashboard](https://img.shields.io/badge/dashboard-live-success?style=flat&logo=streamlit)](https://defector.streamlit.app)
   ```
3. **My Kinedu submission** as the tool link (see `SUBMISSION.md`)

## Troubleshooting

**"ModuleNotFoundError" on deploy:** Streamlit Cloud reads `requirements.txt`
from the repo root. Make sure the path is exactly `requirements.txt` and not
nested.

**"App is over the resource limits":** Community Cloud caps each app at
~1 GB RAM. DuckDB is efficient and the dashboard is read-only — you should
be well under. If not, downsample by filtering older reviews out of the
committed `reviews.duckdb` before pushing.

**"Database is locked":** OneDrive locking your `.duckdb` file before push.
Pause OneDrive sync, push, resume sync. Or move the project out of OneDrive
before pushing.
