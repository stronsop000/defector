# Onboarding — Taking over Parent Feedback

You're inheriting Parent Feedback. Read this once (~10 min). After that you can run, maintain, and extend it without help from the original author.

## What Parent Feedback is

A weekly-refreshing multilingual marketing-intelligence pipeline for parenting and baby-product apps. It scrapes public app store reviews, classifies why parents praise or leave competitors, and auto-generates marketing copy, SEO briefs, and influencer talking points for Kinedu.

**Audience for outputs:** in-house creative team, SEO/content team, product (roadmap signal), partnerships (pitch evidence).
**Audience for the dashboard:** anyone at Kinedu who wants to browse the raw signal.

## The three things you must know

1. **Everything runs in the cloud.** No part of this project depends on the original author's local machine. The pipeline runs in GitHub Actions on a weekly cron; the dashboard runs on Streamlit Cloud. You don't need to run anything on your own laptop unless you're developing.

2. **The whole stack costs $0 to operate.** The LLM (Gemini 2.5 Flash) runs on Google's free tier. Scraping is free public app store data. DuckDB is a single file. Streamlit Cloud is free for public repos. GitHub Actions is free for public repos. If costs ever appear, something has been changed.

3. **The pipeline is idempotent end-to-end.** Any stage can be Ctrl-C'd and resumed. Already-scraped reviews are skipped. Already-classified reviews are skipped. There is no "broken state" that requires wiping and starting over. If something looks wrong, just re-run the stage.

## 30-minute checklist for a new owner

### Read (10 min)
- This file (`docs/ONBOARDING.md`) ✓
- `docs/OPERATIONS.md` — what to do when something breaks
- `docs/MARKETING_GUIDE.md` — what to do with the outputs (for context on who consumes what)
- `README.md` top half — the value pitch + architecture diagram

### Verify access (5 min)
- You can log into the GitHub repo at https://github.com/stronsop000/defector
- You can log into the Streamlit Cloud account that hosts the dashboard
- You have the `GEMINI_API_KEY` value (stored in GitHub repo secrets + Streamlit Cloud secrets — see Operations doc)

### Set up locally (10 min) — only if you'll develop, not required just to operate
- Clone: `git clone https://github.com/stronsop000/defector.git`
- Install: `pip install -r requirements.txt`
- Set key: `python -m scripts.set_api_key` (paste a Gemini key from https://aistudio.google.com/apikey)
- Test: `python -m streamlit run dashboard/app.py` (you should see the dashboard at http://localhost:8501)

### Trigger one manual refresh (5 min)
- Go to the GitHub repo → Actions tab → "Weekly refresh" workflow → "Run workflow" → main → Run
- Wait ~10 min for it to complete
- Confirm the new outputs land in `outputs/` after the workflow commits them back
- Confirm the Streamlit Cloud dashboard reflects the new data after auto-redeploy

If all four sections above check out, you're operational.

## What to actually do each week

Nothing, unless you want to. The cron runs on Mondays. The memo and copy land in `outputs/`. The dashboard updates automatically.

Your only proactive job is **deciding what the team should do with the outputs**:
- Forward the weekly memo to the marketing leadership distribution list
- Pull 1-2 specific ad-copy briefs and hand them to the creative team for that week's testing
- Pull SEO briefs and hand to content team
- Once a quarter, summarize feature-gap themes for the product team

These are the workflows that turn data into decisions. Without them, Parent Feedback becomes a dashboard nobody opens.

## What to do if you want to change something

| Want to … | Edit this | Re-run this |
|---|---|---|
| Add or remove an app | `config/apps.yaml` | `python -m scripts.resolve_app_ids` (one-time), then weekly cron |
| Add a new country/language | `config/markets.yaml` | weekly cron |
| Rename a defection category | `config/taxonomy.yaml` | `python -m src.classify` (full re-classify) |
| Change the memo tone | `src/synthesize.py` `synthesize_memo` system prompt | `python -m src.synthesize` |
| Generate new artifact type (e.g., a sales-team brief) | Add a new function in `src/synthesize.py` modeled after `generate_seo_brief` | `python -m src.synthesize` |
| Switch from Gemini to Claude (paid) | `.env`: set `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` | normal pipeline runs |

## Cost guardrails

| Resource | Free tier limit | What happens at the boundary |
|---|---|---|
| Gemini 2.5 Flash | ~1500 req/day | Pipeline rate-limits gracefully (`src/llm.py` paces at 8 RPM). For >1500 reviews/day, the next day's cron picks up the rest. |
| GitHub Actions | 2000 min/month free for public repos | Parent Feedback uses ~30 min/week; way under. |
| Streamlit Cloud | 1 GB RAM per app | The DuckDB + dashboard fits comfortably. |
| App store scrapers | No formal limit but informal rate caps | `tenacity` retries with backoff handle the rare 429. |

If you ever upgrade to paid tiers, swap `LLM_PROVIDER=anthropic` in `.env` and budget ~$5 per 5000 classified reviews.

## Who to ask if you're stuck

Everything is in this repo. Specifically:
- Operational issues (cron broken, dashboard down, API errors): `docs/OPERATIONS.md`
- Conceptual questions (why does this exist, what's it for): `LEADER_PITCH.md` + `README.md`
- How non-engineers use the outputs: `docs/MARKETING_GUIDE.md`
- Future product roadmap (Next.js + Vercel): `docs/PHASE_2_VERCEL.md`

If the above doesn't answer it, file a GitHub issue on the repo. The code is documented enough that a Python-comfortable engineer can read `src/` and answer most questions.

## Final inheritance checklist

When you're confident you own this:
- [ ] You have admin access to the GitHub repo
- [ ] You have admin access to the Streamlit Cloud account
- [ ] You have the GEMINI_API_KEY value (either the existing one or your own)
- [ ] You've run one manual `Weekly refresh` workflow successfully
- [ ] You've subscribed to GitHub repo notifications so failed cron runs email you
- [ ] You've identified at least one consumer of the memo at Kinedu (marketing, content, partnerships, or product lead) and forwarded them the first memo

That's the handoff complete. Parent Feedback now operates without the original author.
