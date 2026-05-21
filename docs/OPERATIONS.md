# Operations Runbook

Day-to-day operating the pipeline. Use the table-of-contents below as a triage tool when something looks wrong.

## Healthy state

- Weekly cron runs every Monday ~13:00 UTC
- New files appear in `outputs/memos/`, `outputs/copy/`, `outputs/seo/`, `outputs/influencer/`, `outputs/strengths/` with the run date
- Streamlit Cloud dashboard auto-redeploys after the cron commits, reflecting the latest data
- Total runtime ~10–30 min depending on classify queue depth

If you see all of that, nothing needs your attention.

## Triage table

| Symptom | Likely cause | Fix |
|---|---|---|
| Weekly cron didn't run | Workflow disabled or secret missing | GitHub repo → Actions → "Weekly refresh" → check status; verify `GEMINI_API_KEY` secret exists in Settings → Secrets |
| Cron ran but failed | Look at the failed step in the workflow logs | See specific symptoms below |
| Scrape step took >30 min | App store rate-limiting | Normal; retries with backoff. If consistent, lower `--cap` in workflow file |
| Classify step failed with 429 | Gemini quota exhausted for the day | Wait 24h or re-run manually; or set `REQUESTS_PER_MINUTE=4` env var to pace harder |
| Classify step failed with 401/403 | API key invalid or revoked | Regenerate key at https://aistudio.google.com/apikey → update GitHub secret + Streamlit Cloud secret |
| Synthesize step produced empty memo | No opportunities cleared the `volume >= 3` threshold | Either too little data (run more scrape cycles) or too narrow a window (`--since`) |
| Dashboard says "no database found" | Streamlit Cloud doesn't have the DuckDB committed | `git add -f data/reviews.duckdb && git commit && git push` |
| Dashboard says "no reviews in window" | The `Reviews since` filter is too narrow | Widen the date filter in the sidebar |
| Dashboard shows old data | DuckDB on the Streamlit Cloud side is stale | The weekly cron should auto-commit. If not, manually push the local DB; or trigger the workflow manually |
| Outputs missing for the latest week | `python -m src.synthesize` failed silently | Re-run manually from a local clone or trigger the workflow |
| Reviews from a specific app are zero | App ID is wrong or app was removed from the store | Run `python -m scripts.resolve_app_ids --only "App Name"` and verify the resolved IDs |

## Common tasks

### Trigger the pipeline manually
GitHub repo → Actions tab → "Weekly refresh" → "Run workflow" → main → Run.
Takes 10–30 min. Output appears in `outputs/` directories on success.

### Re-run after a config change
After editing `config/apps.yaml`, `config/markets.yaml`, or `config/taxonomy.yaml`:
1. Commit and push the change
2. Trigger the workflow manually (above)
3. If you renamed a taxonomy key, also delete old classifications first: `DELETE FROM classifications` then re-classify

### Add a new app
1. Append a block to `config/apps.yaml` (name + category, IDs as null)
2. `python -m scripts.resolve_app_ids --only "App Name"` locally
3. Review the resolved IDs in `config/apps.yaml`, commit and push
4. Trigger the workflow

### Rotate the Gemini API key
1. Generate a new key at https://aistudio.google.com/apikey
2. GitHub repo → Settings → Secrets and variables → Actions → update `GEMINI_API_KEY`
3. Streamlit Cloud app → Settings → Secrets → update `GEMINI_API_KEY`
4. (Optional) Update local `.env` if you develop locally
5. Old key can be revoked in Google AI Studio

### Force a dashboard refresh on Streamlit Cloud
Streamlit Cloud → app → ... menu → "Reboot app." Takes ~30 seconds.

### Clear all classifications and re-classify
```python
python -c "from src.db import connect; connect().execute('DELETE FROM classifications')"
python -m src.classify
```
Useful after a taxonomy change.

### Purge demo seed data once real classifications exist
```bash
python -m scripts.seed_demo_data --purge
```
Removes all `demo:*` rows from both `reviews` and `classifications` tables.

## What costs money

Nothing on the default configuration:
- Gemini 2.5 Flash: free tier
- Public GitHub repo: free Actions minutes
- Streamlit Community Cloud: free for public repos
- App store scraping: free public APIs

If you ever see a bill, something was changed. Check `.env` and `requirements.txt` for added paid services.

## Storage growth

`data/reviews.duckdb` grows over time as more reviews are scraped. Expected size after 6 months: 100–300 MB. If it crosses 500 MB:
- Trim old reviews: `DELETE FROM reviews WHERE review_date < CURRENT_DATE - INTERVAL '6 months'`
- Or move to a hosted DuckDB / Postgres if it ever becomes the bottleneck

## What you should NOT do

- Don't commit `.env` (the `.gitignore` already protects you)
- Don't push the GitHub repo secret value anywhere
- Don't run `python -m src.scrape` and `python -m src.classify` simultaneously — they both write to the DuckDB and will hit a lock. Stop Streamlit too if it's running locally during a scrape.
- Don't change the prompt templates without diffing the before/after outputs — small wording changes can drift the tone significantly
- Don't disable the GitHub Actions cron unless you're intentionally pausing the project

## When to escalate / rebuild

You should rewrite or restructure if:
- Defector becomes the primary source of strategic input for >5 teams and Streamlit's read-mostly UI feels limiting → execute `docs/PHASE_2_VERCEL.md`
- A regulatory issue arises with scraping a specific store → drop that source from `config/`
- You need historical reviews older than ~500 most-recent (Apple RSS cap) → consider a paid scraper provider

Otherwise: the pipeline is intentionally boring. Boring is the goal.
