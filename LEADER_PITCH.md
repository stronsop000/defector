# Parent Feedback — AI Challenge Proposal

**Owner:** Sophia Strong • Partnerships
**Status:** Working prototype already running. Submitting full deliverable by May 31.
**One-line:** A multilingual marketing-intelligence and copy-generation engine that mines public reviews of 30 parenting and baby-product apps across 7 markets in EN / ES / PT to brief Kinedu's marketing, SEO, product, and partnerships teams every week.

## The problem

Every week, thousands of parents publicly post why they're frustrated with parenting apps and baby-product brands — Lovevery, BabySparks, BabyCenter, Pampers, Huggies, Enfamil, and every other player Kinedu competes with for parent attention. The signal is rich, multilingual, and free. Nobody at Kinedu reads it systematically.

That leaves four teams writing into the dark:

1. **Performance marketing** writes ad copy weekly from gut or internal opinions instead of from parents' actual language.
2. **Content / SEO** could be ranking on high-intent comparison queries ("Lovevery alternative," "best Kinedu vs. BabySparks") with copy grounded in real complaints — but those articles aren't getting written, or are getting written without the right hooks.
3. **Product** has to choose between roadmap candidates without a cheap way to see which feature gaps are bleeding parents from competitors.
4. **Partnerships** (my team) walks into pitches without market-specific data about what parents in Brazil, Mexico, and Argentina actually care about.

Off-the-shelf competitive-intel tools mostly read English. For a LatAm-focused company that's the gap.

## What I'm building

**Parent Feedback** — a four-step pipeline, all from public data:

1. **Scrape** App Store + Play Store reviews for ~30 apps across 7 markets (US, MX, BR, AR, CO, CL, PE), 3 languages (EN / ES / PT). Public, idempotent, refreshes weekly via cron.
2. **Classify** each 1★/2★ review with Claude into one of 11 defection-reason categories (price, content quality, bugs, UX friction, missing features, notifications, trust, privacy, localization, support, other). Forced-JSON tool output for reliability. Accuracy measured against a hand-labeled eval set.
3. **Synthesize** four artifacts a week:
   - Ranked "switching opportunities" memo
   - Meta / Google ad copy variants per opportunity, in the parents' language
   - SEO comparison-page briefs (H1, meta, hook, subhead outline, target keyword, verbatim callouts)
   - Influencer / partner talking points
4. **Dashboard** (Streamlit) — searchable, filterable, demo-ready.

## What this is realistically expected to move

I'm being honest about the value chain — judges will probe.

| Team | Artifact they use | KPI it moves |
|---|---|---|
| Performance marketing | Ad copy variants in EN/ES/PT, grounded in verbatim parent language | Creative-test hit rate; CPM × CTR on Parent Feedback-briefed variants vs. baseline. Realistic lift: 10-30% on creative tests, which compounds over a quarter. |
| Content / SEO | Weekly comparison-page briefs ("Lovevery alternative — what parents say") | New comparison articles shipped per month; organic traffic to those URLs. Realistic: 2-3 new articles/month, compounding organic. |
| Product | Quarterly competitor feature-gap memo | Roadmap input; we measure usage, not ship. Cheaper than running user interviews. |
| Partnerships | Market-specific intelligence in the dashboard | Pitch evidence — "in Brazil parents talk about X 3× more than in the US" lands better than a generic deck. |

I'm not promising direct CAC attribution in two weeks. The realistic story is **marketing efficiency**: the same teams making the same number of decisions every week, with continuously refreshed evidence to back them up.

## Why this and not something closer to my role

I considered building further automation on top of my partnership outreach pipeline, but most of the easy wins there are already captured by my Airtable + Claude setup. Parent Feedback is a bigger lever on breakeven because it touches three high-leverage acquisition channels (paid creative, SEO, influencer) plus product and partnerships. It's also fully cross-functional, so the artifact has natural owners beyond me, which strengthens the adoption story.

## What's already done (as of May 18)

- Project scaffold + config-driven pipeline at `C:\Users\sophi\OneDrive\Kinedu\defector\` (will be a public GitHub repo on submission)
- Play Store + Apple App Store scrapers tested end-to-end (550 Kinedu reviews already in the database)
- DuckDB schema + idempotent ingestion
- 11-category defection taxonomy with examples and a hand-labeled eval set spanning EN / ES / PT
- Claude classifier with forced-JSON tool output and prompt caching for cost control
- Memo synthesizer + ad-copy generator (SEO + influencer outputs in progress this week)
- Streamlit dashboard
- Weekly automation (Windows Task Scheduler + GitHub Actions)
- README + full handoff documentation so anyone on the team can pick this up

## Remaining timeline

- **May 18-19:** Full scrape + classification across all apps & markets, generate first weekly artifacts, add SEO + influencer outputs.
- **May 20-21:** Share early outputs with marketing and SEO for feedback. Iterate.
- **May 22-26:** Public GitHub repo + Streamlit Cloud deploy + demo recording.
- **May 31:** Submit.

## AI tools used

- **Gemini 2.5 Flash** (Google AI Studio free tier) for classification + synthesis
- Pluggable LLM layer also supports Claude (Anthropic) by env-var switch
- Forced JSON-schema output for reliable structured classification
- Public data only — no internal Kinedu data required

## Cost to run

**Zero on Gemini's free tier** for the full prototype (1500 requests/day quota
is enough for the demo). If we ever move to Claude for higher throughput,
prompt caching keeps it at ~$0.001 per review (~$5 for 5000 reviews).

## Public artifacts at submission

- GitHub repo (public) — link in submission
- Live Streamlit dashboard — link in submission
- 5-min recorded demo — link in submission
