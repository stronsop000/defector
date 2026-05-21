# Phase 2 — Next.js + Vercel platform

**Status:** Post-prize scope. Do not start before May 31 submission. Notes
captured now so the work is shovel-ready the moment the prize is in.

## Why this exists

Streamlit Cloud is the right deploy target for the prize submission — free,
fast, public URL in 5 minutes. But Streamlit looks like a Python notebook
with a CSS skin. If we want Kinedu's marketing, SEO, product, and
partnerships teams to actually open and use Defector as a recurring tool,
it needs to look and feel like a product, not a dashboard.

The Phase 2 goal: a Vercel-hosted Next.js app at `defector.kinedu.com` (or
similar) that:

- Anyone on the Kinedu team can open without installing anything
- Shows the same Switching Opportunities, ad copy, SEO briefs, influencer
  briefs as the current Streamlit dashboard, but in a polished UI
- Has named ownership (the marketing team can subscribe to the weekly memo
  via email/Slack from the app)
- Could eventually accept manual annotations ("we shipped this ad — here's
  the CTR result") to close the loop

## Architecture

The Python pipeline (scrape → classify → synthesize) stays exactly as-is.
We add a thin data export step that publishes the classifications and
outputs to a format Next.js can consume.

```
[Python pipeline — unchanged]
    ↓
[data/reviews.duckdb]
    ↓ src/export.py (new)
    ↓
[data/exports/snapshot.json]  ← committed to repo OR pushed to Vercel Blob / Supabase
    ↓
[Next.js app on Vercel]
    ├── reads snapshot.json at build time (ISR) or runtime
    ├── shows: Overview heatmap, Opportunities feed, Outputs library
    └── auth: NextAuth with Google → restrict to @kinedu.com domain
```

## Why Next.js + Vercel specifically

- Vercel free tier is generous; production-ready hosting at no cost
- Next.js App Router + Server Components match the read-mostly workload
  perfectly — no client-side fetching round trips
- `@vercel/analytics` gives us a free metric on whether anyone is using it
- Native support for incremental static regeneration — rebuild the page
  every Monday after the weekly cron writes a fresh snapshot
- The Python pipeline runs as a GitHub Actions cron (already wired up),
  exports the JSON, commits to the repo, Vercel auto-deploys

## Build plan (after May 31)

| Day | Work |
|---|---|
| 1 | Scaffold `web/` directory with Next.js 15 + Tailwind + shadcn/ui. Read snapshot.json from `data/exports/`. Render Overview heatmap with recharts. |
| 2 | Opportunities feed page (mirror of current Streamlit tab). Filters in URL params. |
| 3 | Outputs library page — markdown rendering of memo + ad copy + SEO + influencer briefs. |
| 4 | NextAuth Google login restricted to a Kinedu domain. |
| 5 | Wire up the GitHub Actions cron to also run `python -m src.export` and commit the snapshot. Vercel auto-deploys on push. |
| 6 | Polish: empty states, loading skeletons, mobile layout. |
| 7 | Hand off to a named owner in marketing. |

Roughly one focused week. Keep the existing Streamlit app alive as a
fallback during the transition.

## What we need from Kinedu before starting

- A subdomain (`defector.kinedu.com` or similar) — DNS CNAME to Vercel
- A named owner on the marketing or growth team who'll consume the weekly memo
- Confirmation that the data we surface is OK to display to all employees
  (it's all public review data, so this should be a quick yes)

## What stays in the Python repo

Everything. The Python pipeline is the source of truth. The Next.js app is
strictly a read-only viewer on top of the JSON snapshot the pipeline
produces. This keeps the system reproducible and easy to hand off.

## Don't do these (anti-scope)

- Don't rebuild the classifier or synthesizer in TypeScript. Python is fine,
  it runs on cron, leave it alone.
- Don't put the LLM API key in the Next.js app. Snapshots are static; no
  live LLM calls needed in the web tier.
- Don't add a database. The snapshot.json approach is simpler and survives
  forever without any infrastructure.
