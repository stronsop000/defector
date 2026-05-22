<h1 align="center">Defector</h1>

<p align="center">
  <b>Multilingual marketing intelligence + copy generation for parenting and baby-product apps across the Americas.</b><br>
  Built for the Kinedu AI Challenge · May 2026
</p>

<p align="center">
  <a href="#"><img alt="Python" src="https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white"></a>
  <a href="#"><img alt="LLM" src="https://img.shields.io/badge/LLM-Gemini%202.5%20Flash%20%7C%20Claude-6366f1"></a>
  <a href="#"><img alt="Streamlit" src="https://img.shields.io/badge/dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white"></a>
  <a href="#"><img alt="DuckDB" src="https://img.shields.io/badge/storage-DuckDB-FFF000?logo=duckdb&logoColor=black"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green"></a>
  <a href="https://defector.streamlit.app/"><img alt="Live dashboard" src="https://img.shields.io/badge/dashboard-live-success?logo=streamlit&logoColor=white"></a>
</p>

---

## The 30-second pitch

Every week, thousands of parents publicly post **why** they're leaving Lovevery, BabyCenter, BabySparks, Pampers Rewards, Huggies, Wonder Weeks, and every other brand competing for parent attention. It's all in their App Store reviews. **Nobody at Kinedu reads it systematically.**

Defector does. In **3 languages**, across **30 apps**, across **7 markets**, every week — and turns it into ad copy, SEO briefs, and influencer talking points the Kinedu growth team can ship on Monday morning.

> 🔗 **Live dashboard:** **https://defector.streamlit.app/**
> 📊 **What it produces this week:** see `outputs/memos/`, `outputs/copy/`, `outputs/seo/`, `outputs/influencer/`, `outputs/strengths/`

---

## What it produces

Four artifacts per weekly refresh, all reproducible from this repo, all in the parents' own language:

| # | Artifact | Used by | What it does |
|---|---|---|---|
| 1 | **Switching Opportunities memo** | Leadership / growth | Top 5 places this week where parents are publicly leaving a competitor, with verbatim quotes and a recommended message angle. |
| 2 | **Meta/Google ad copy variants** | In-house creative team | 3 headlines + 3 primary-text variants + 1 landing hero + 2 push notifications, per opportunity, in the market's language. |
| 3 | **SEO comparison-page briefs** | Content / SEO team | H1, meta description, hook, outline, target keyword, verbatim pull-quotes — ready for a writer to flesh out in 30 min. |
| 4 | **Influencer / partner briefs** | Influencer marketing / partnerships | 4-6 talking points an influencer can riff on in a Reel, plus a hook line, plus what NOT to say (legal). |

Plus a Streamlit dashboard the marketing, content, product, and partnership teams can open to explore, filter, and pull individual quotes.

---

## Architecture

```
                      ┌─────────────────────────┐
                      │  config/apps.yaml       │  ~30 apps × 7 markets × 2 stores
                      │  config/markets.yaml    │
                      │  config/taxonomy.yaml   │  11 defection-reason categories
                      └────────────┬────────────┘
                                   │
            ┌──────────────────────┴──────────────────────┐
            ▼                                              ▼
   src/scrapers/play_store.py                   src/scrapers/app_store.py
   (google-play-scraper)                        (iTunes RSS feed)
            │                                              │
            └──────────────────────┬──────────────────────┘
                                   ▼
                       data/reviews.duckdb
                                   │
                                   ▼
                       src/classify.py
                       (Gemini 2.5 Flash → JSON-schema-forced classification)
                                   │
                                   ▼
                       src/synthesize.py
                       (memo + ad copy + SEO brief + influencer brief
                        — one prompt template per artifact type)
                                   │
                                   ▼
                       dashboard/app.py
                       (Streamlit + Plotly)
```

**Public data only.** No Kinedu internal data is used. Everything is reproducible from this repo with a free Gemini API key.

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get a free Gemini API key at https://aistudio.google.com/apikey
#    (no credit card, generous free quota).
python -m scripts.set_api_key
# Paste your key when prompted. It's written to .env (gitignored) and verified
# with a tiny test call. To use Claude instead: --provider anthropic.

# 3. (Optional) Seed the DB with demo data so the dashboard isn't empty
python -m scripts.seed_demo_data
# Inserts ~56 synthetic but realistic classified reviews. Purge any time
# with `python -m scripts.seed_demo_data --purge`.

# 4. Scrape real reviews
python -m src.scrape                    # ~30 apps × 7 markets × 2 stores, idempotent

# 5. Verify classifier accuracy on the labeled eval (50 hand-labeled rows)
python -m src.classify --eval           # prints accuracy + per-category mismatches

# 6. Classify the real reviews (only 1-2★)
python -m src.classify                  # idempotent — only touches unclassified rows

# 7. Generate the weekly memo, ad copy, SEO briefs, influencer briefs
python -m src.synthesize                # writes to outputs/

# 8. Launch the dashboard
streamlit run dashboard/app.py
```

---

## Key features

- 🌎 **7 markets, 3 languages** — US + Mexico + Brazil + Argentina + Colombia + Chile + Peru. EN/ES/PT classified natively, no English-only blind spots.
- 🆓 **Runs on free LLM tiers** — Gemini 2.5 Flash by default; Anthropic Claude via env-var switch. Total cost to operate: **$0**.
- 🏗️ **Pluggable LLM layer** — `src/llm.py` exposes `call_tool` / `call_text` with provider-agnostic interface.
- 🗂️ **Config-driven** — add an app, a market, or a defection category by editing YAML, not code.
- ✅ **JSON-schema-forced classifier output** — no flaky regex parsing of LLM responses.
- 📊 **Hand-labeled evaluation set** — 50 reviews spanning EN/ES/PT and all 11 categories, with `python -m src.classify --eval` reporting accuracy.
- 🤖 **Idempotent end-to-end** — Ctrl-C and resume at any stage. Scrape, classify, synthesize all skip already-done work.
- 🔄 **Weekly cron** — GitHub Actions workflow refreshes the data + memo + copy every Monday.
- 📦 **Single embedded DB** — DuckDB in one file, no server, no infrastructure to manage.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.13 | universally readable, fastest path to handoff |
| LLM | Gemini 2.5 Flash (default) / Claude (optional) | free tier; pluggable for upgrade |
| Storage | DuckDB | single embedded file, perfect for analytical workloads, ships with the repo |
| Dashboard | Streamlit + Plotly | 5-minute deploy to Streamlit Cloud, no separate front-end build |
| Scraping | google-play-scraper + Apple iTunes RSS | public, free, no API keys |
| Scheduling | GitHub Actions cron (weekly) + Windows Task Scheduler (local) | both wired up |
| Config | YAML | non-engineers can extend the universe |

---

## File map

| File | Purpose |
|---|---|
| `config/apps.yaml` | Apps to track. Edit to add/remove. |
| `config/markets.yaml` | Country + language pairs to scrape. |
| `config/taxonomy.yaml` | The 11 defection-reason categories the classifier uses. |
| `data/reviews.duckdb` | Single embedded DB. Tables: `reviews`, `classifications`. |
| `data/eval/labeled_sample.csv` | 50 hand-labeled reviews for classifier accuracy. |
| `scripts/set_api_key.py` | Securely write LLM API key to `.env` (hidden input + test call). |
| `scripts/resolve_app_ids.py` | One-time helper: fill in missing Play / App Store IDs. |
| `scripts/seed_demo_data.py` | Insert synthetic demo data for empty-dashboard previews. |
| `src/scrape.py` | CLI: scrape (app × market × store) pairs into DuckDB. |
| `src/scrapers/play_store.py` | Google Play Store scraper. |
| `src/scrapers/app_store.py` | Apple App Store scraper (iTunes RSS). |
| `src/classify.py` | CLI: classify reviews with Gemini/Claude. |
| `src/synthesize.py` | CLI: generate memo + ad copy + SEO + influencer briefs. |
| `src/llm.py` | Pluggable LLM client wrapper (Gemini + Anthropic). |
| `src/db.py` | DuckDB schema + helpers. |
| `src/config.py` | YAML loader. |
| `dashboard/app.py` | Streamlit dashboard. |
| `docs/GITHUB_SETUP.md` | Push to public repo without leaking `.env`. |
| `docs/STREAMLIT_DEPLOY.md` | Deploy dashboard to Streamlit Cloud. |
| `docs/DEMO_SCRIPT.md` | 5-min spoken demo for the submission. |
| `docs/SUBMISSION.md` | Pre-written My Kinedu form text. |
| `docs/PHASE_2_VERCEL.md` | Post-prize roadmap: Next.js + Vercel rebuild. |
| `LEADER_PITCH.md` | Internal Kinedu approval doc. |
| `run_weekly.bat` | Windows Task Scheduler wrapper for weekly refresh. |
| `.github/workflows/weekly_refresh.yml` | GitHub Actions weekly cron. |

---

## Command reference

### `src.scrape`
```bash
python -m src.scrape                            # full run
python -m src.scrape --app Kinedu               # one app, all markets
python -m src.scrape --country br               # all apps, Brazil
python -m src.scrape --category brand_product   # only baby-product brand apps
python -m src.scrape --cap 200                  # cap reviews per (app, market, store)
python -m src.scrape --dry-run                  # don't write to DB, just count
```
Idempotent — re-runs only insert genuinely new reviews. The Apple RSS feed caps at ~500 most-recent reviews per market; Play Store has no such cap (we cap at 1000 by default).

### `src.classify`
```bash
python -m src.classify                          # classify all unclassified 1-2★ reviews
python -m src.classify --limit 50               # smoke test
python -m src.classify --max-stars 3            # also include 3★ reviews
python -m src.classify --eval                   # accuracy report against eval set
python -m src.classify --dry-run                # classify but don't write
```

### `src.synthesize`
```bash
python -m src.synthesize                        # all four output types
python -m src.synthesize --top 3                # only top 3 opportunities
python -m src.synthesize --memo-only            # skip ad/SEO/influencer
python -m src.synthesize --since 2026-01-01     # window for the analysis
```

---

## Extending it

### Add a new app

1. Append a block to `config/apps.yaml` (`name`, `category`, leave the store IDs as `null`)
2. Resolve its IDs: `python -m scripts.resolve_app_ids --only "App Name"`
3. Verify the developer name in the script output matches the brand (store search is noisy)
4. Scrape it: `python -m src.scrape --app "App Name"`

### Add a new market

Add a row to `config/markets.yaml` with the country code (ISO 3166-1 alpha-2) and language (ISO 639-1). Re-run scrape for that country: `python -m src.scrape --country <code>`.

### Change the taxonomy

Edit `config/taxonomy.yaml`. Then re-classify everything:

```bash
# Wipe and reclassify (DB is local, no risk of remote damage)
python -c "from src.db import connect; connect().execute('DELETE FROM classifications')"
python -m src.classify
```

---

## Evaluation

`data/eval/labeled_sample.csv` has 50 hand-labeled reviews covering all 11 categories and three languages.

```bash
python -m src.classify --eval
```

Sample output:
```
Eval accuracy: 44/50 = 88.0%
Mismatches:
  gold=missing_features    pred=ux_friction         n=1
  gold=notifications_spam  pred=ux_friction         n=1
  ...
```

Grow this file with edge cases as you spot them — it's how the taxonomy gets sharper over time.

---

## Cost

- Scraping is **free** (public app store data, no API keys)
- Classifier on **Gemini 2.5 Flash free tier**: **$0**. Quota is the constraint (~1500 requests/day); for >2000 reviews per refresh, run overnight or switch to Flash-Lite.
- Classifier on Claude Sonnet with prompt caching: ~$0.001/review, ~$5 per 5000 reviews
- Synthesizer: a handful of long-context calls per weekly run; trivial on any provider

---

## Automating weekly refresh

### Local (Windows Task Scheduler)
```powershell
$action  = New-ScheduledTaskAction -Execute "C:\Users\sophi\OneDrive\Kinedu\defector\run_weekly.bat"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:00am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Defector-Weekly" -Action $action -Trigger $trigger -Settings $settings
```

### GitHub Actions
`.github/workflows/weekly_refresh.yml` runs the pipeline weekly in CI and uploads the resulting DuckDB + outputs as artifacts. Add `GEMINI_API_KEY` as a repo secret to enable.

---

## Recovery from interruption

- `src.scrape` is idempotent. Ctrl-C and re-run; already-seen reviews are skipped via PRIMARY KEY.
- `src.classify` is idempotent — only reviews without a classification row are touched. Crashes mid-run leave a partial state that the next run picks up.
- DuckDB stores everything in one file. To wipe and start over: delete `data/reviews.duckdb`.

---

## Honest limitations

- Apple iTunes RSS caps at ~500 most-recent reviews per (app, country). Long-tail historical analysis would need a paid scraper.
- Some app names match wrong results in store search. Run `resolve_app_ids --interactive` or hand-edit `config/apps.yaml` after the first resolution.
- The classifier handles EN/ES/PT well. Other languages will work but accuracy is unmeasured.
- This is a marketing-intelligence + copy-generation engine, not a literal ad-targeting system. You can't upload "Lovevery defectors" to Meta — but you *can* run ads on competitor keywords using the language defectors actually use, write SEO comparison pages that match high-intent queries, brief influencers, and re-engage your own at-risk users with that language.
- OneDrive can occasionally lock `data/reviews.duckdb` mid-write. If you see `database is locked`, pause OneDrive sync during runs or move the project outside OneDrive.

---

## Why this exists

Built for the Kinedu AI Challenge. The challenge brief: use AI to move a real KPI on the path to breakeven. Defector targets **marketing efficiency** — higher creative-test hit rate, more SEO comparison content shipped per month, cheaper competitive intel than user research, and weekly-refreshed pitch evidence for partnership conversations.

Public GitHub. Public Streamlit URL. Reproducible from scratch in 20 minutes with a free API key.

—

Made by [Sophia Strong](https://github.com/) · MIT licensed
#   d e f e c t o r  
 #   d e f e c t o r  
 