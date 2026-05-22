# Pushing Parent Feedback to a public GitHub repo

Goal: a clean, public, portfolio-grade repo at `github.com/<your-handle>/defector`
without ever exposing your API key.

## Step 1 — Verify nothing sensitive is staged

```bash
cd C:\Users\sophi\OneDrive\Kinedu\defector
git status                              # should show "Not a git repository" the first time
```

Before initializing git, sanity-check that the `.gitignore` we shipped catches `.env`:

```bash
type .gitignore
```

You should see `.env` near the top. Don't proceed if you don't.

## Step 2 — Initialize and make the first commit

```bash
git init -b main
git add .
git status                              # CRITICAL: scan the list. .env must NOT appear.
git commit -m "Initial commit: Parent Feedback — competitor switching intelligence"
```

If `.env` shows up in `git status` before the commit, STOP and add it to `.gitignore`:
```bash
echo .env >> .gitignore
git rm --cached .env                    # if it was already staged
git add .gitignore
git commit -m "Ignore .env"
```

## Step 3 — Create the empty repo on GitHub

Option A — via gh CLI (fastest):
```bash
gh repo create defector --public --source=. --description "Multilingual marketing intelligence + copy generation engine for parenting and baby-product apps across the Americas. Built for the Kinedu AI Challenge." --push
```

Option B — via the GitHub web UI:
1. Go to https://github.com/new
2. Repository name: `defector`
3. Description: *Multilingual marketing intelligence + copy generation engine for parenting and baby-product apps across the Americas. Built for the Kinedu AI Challenge.*
4. Public
5. Do NOT initialize with README, .gitignore, or license (we already have them)
6. Click "Create repository"
7. Copy the SSH or HTTPS URL it shows you, then:
   ```bash
   git remote add origin https://github.com/<your-handle>/defector.git
   git push -u origin main
   ```

## Step 4 — Add repo topics + social preview (for portfolio polish)

On the GitHub repo page → click the gear next to "About" (top right):
- Description: as above
- Website: paste the Streamlit Cloud URL once it's deployed (see `STREAMLIT_DEPLOY.md`)
- Topics: `claude`, `gemini`, `multilingual-nlp`, `competitive-intelligence`,
  `parenting`, `duckdb`, `streamlit`, `firecrawl`, `kinedu`

Settings → General → Social preview → upload a screenshot of the dashboard.
(One screenshot of the heatmap or the Opportunities tab does the job.)

## Step 5 — Verify the public view looks right

Open `https://github.com/<your-handle>/defector` in an incognito window. Confirm:
- ✓ README renders with the architecture diagram and the four-artifact table
- ✓ No `.env`, no `data/reviews.duckdb`, no `outputs/memos/*.md` in the tree
- ✓ The `.github/workflows/weekly_refresh.yml` workflow is visible
- ✓ The repo is **public**

## Step 6 (optional, recommended) — wire the GitHub Actions weekly cron

For the cron in `.github/workflows/weekly_refresh.yml` to work in CI you'd
need to add `GEMINI_API_KEY` as a repo secret. This is NOT required for
submission, but it makes the "this is a real running pipeline" story
demonstrable.

Settings → Secrets and variables → Actions → New repository secret:
- Name: `GEMINI_API_KEY`
- Value: paste your key (different from `.env` — this lives only on GitHub's side)

Trigger one run manually from the Actions tab to confirm it works.

## If you accidentally pushed your `.env`

This is unlikely if you followed Step 2, but if it happens:

1. Rotate the key IMMEDIATELY at https://aistudio.google.com/apikey (revoke + create new)
2. Update your local `.env` with the new key
3. Force-rewrite history to remove the leaked file:
   ```bash
   git rm --cached .env
   git commit -m "Remove leaked .env"
   git push --force origin main
   ```
4. Note: forcing isn't quite enough to scrub it from GitHub's caches.
   Use `git filter-repo` or BFG Repo Cleaner if you need a guaranteed wipe.
