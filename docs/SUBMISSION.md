# My Kinedu submission text — pre-filled

The submission form on My Kinedu asks for four things. Drafts below; fill
in the bracketed values after deploy + demo recording.

---

## Project name

> Defector — Multilingual Marketing Intelligence + Copy Engine

---

## Short description (max 200 words)

> Defector is a marketing-intelligence and copy-generation engine that
> mines public 1- and 2-star reviews from 30 parenting and baby-product
> apps across 7 markets in the Americas (US, MX, BR, AR, CO, CL, PE) in
> English, Spanish, and Portuguese. A Gemini-based classifier sorts each
> review into one of 11 defection-reason categories. A synthesizer then
> generates four artifacts per week: (1) a switching-opportunities memo
> ranking the top conversion targets; (2) Meta and Google ad-copy
> packages grounded in real parent verbatim language; (3) SEO
> comparison-page briefs for the content team targeting high-intent
> queries like "Lovevery alternative"; (4) influencer and partner
> talking-point briefs.
>
> The system is fully reproducible from a public GitHub repo, runs on
> free LLM tiers (zero cost), and refreshes weekly via cron. KPI moved:
> marketing efficiency — higher hit rate on creative tests, more SEO
> comparison content shipped, cheaper competitive intel than user
> research. Adoption-ready for performance marketing, content/SEO,
> product (feature-gap roadmap), and partnerships (market-specific pitch
> evidence).

(Word count: ~195. Trim or expand to taste.)

---

## Link to video or slide deck

> {YOUTUBE_URL after demo upload}

---

## Link to tool / document / workflow

> Public GitHub repo: https://github.com/stronsop000/defector
> Live dashboard: https://defector.streamlit.app/

---

## Project category

> Automation + Content + Product (cross-functional — pick "Automation" if
> only one is allowed; the description makes the cross-functional value
> clear)

---

## If there's a free-text "AI tools used" field

> - **Google Gemini 2.5 Flash** (Google AI Studio free tier) — classifier
>   and synthesizer
> - Pluggable LLM layer also supports Anthropic Claude via env-var switch
> - Forced JSON-schema output for reliable structured classification
> - Public data only; no internal Kinedu data
> - Stack: Python 3.13, google-play-scraper, Apple iTunes RSS, DuckDB,
>   Streamlit + Plotly, GitHub Actions cron

---

## If there's a "team members" field

> Solo — Sophia Strong (Partnerships)
