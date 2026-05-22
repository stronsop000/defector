# Parent Feedback — Handoff Briefing

Read-aloud talking points for your handoff presentation, plus the maintenance
story to walk through. Optimized to be skimmed before you go on, then
referenced live.

---

## 30-second pitch — open with this

> *"Every week, parents publicly say what they think about every parenting and
> baby-product app — Lovevery, BabyCenter, BabySparks, Pampers, Huggies, Wonder
> Weeks, twenty-five others — in English, Spanish, and Portuguese, across the US
> and Latin America. Parent Feedback reads all of it, sorts it by topic and
> sentiment, and writes ad copy, SEO briefs, and influencer talking points for
> Kinedu — grounded in real parent language, refreshed every Monday, costing
> zero dollars to run."*

---

## What to point at during the demo

Open https://defector.streamlit.app/ and walk through, in this order:

1. **The masthead and reading line at the top.**
   > *"This is the weekly issue. Right now we're reading ~900 reviews across 25
   > apps in 7 markets. About a third are negative — that's our switching
   > opportunities. A fifth are positive — that's what competitors are doing
   > well that we need to match or position around."*

2. **The "Switching Opportunities" tab.**
   > *"Each card is one place where parents are publicly leaving a competitor
   > for a specific reason. Ranked by volume. Click any one to see the parents'
   > actual words and the marketing assets we've already written for that
   > opportunity — ad copy in the right language, an SEO comparison-page brief
   > ready for the content team, an influencer brief with talking points."*

3. **The "Competitor Strengths" tab.**
   > *"Same data, opposite direction. This is what competitors are winning at —
   > Lovevery's research-backed content, Huckleberry's multi-caregiver sync,
   > Bebbo's UNICEF credibility. So we know what to defend and what to copy."*

4. **The "Generated outputs" tab.**
   > *"The team doesn't have to open the dashboard to use this. Every Monday,
   > five artifacts land here: a memo on switching opportunities, a memo on
   > competitor strengths, ad copy packages, SEO briefs, influencer briefs. All
   > downloadable. All in the parents' own language and the target market's
   > language."*

5. **The footer link to GitHub.**
   > *"The whole thing is reproducible from a public GitHub repo. The pipeline
   > runs itself on a weekly cron. No human in the loop unless we want to add
   > new apps or change the questions we're asking."*

---

## Headline bullets (one slide if you make a deck)

- **Reads 30 parenting apps across 7 markets and 3 languages**, every Monday, automatically
- **Classifies the topic and sentiment** of each review — 11 topics × 3 sentiment directions
- **Produces 5 artifacts a week**: switching memo, strengths memo, ad copy, SEO briefs, influencer briefs
- **Used by 4 teams**: performance marketing (copy), content/SEO (comparison pages), product (feature-gap roadmap signal), partnerships (market pitch evidence)
- **Costs $0** — free Gemini tier, free GitHub Actions, free Streamlit Cloud
- **No maintenance burden** — runs itself; the team just consumes the outputs
- **Public, reproducible, portable** — anyone with a Gemini key can clone the repo and stand it up in 20 minutes

---

## KPIs it credibly moves

Be honest — judges and team will probe.

| Team | What they get | What moves |
|---|---|---|
| Performance marketing | Ready-to-test ad copy variants in EN/ES/PT, in real parent language | 10-30% lift on creative-test hit rate vs. gut-written baseline |
| Content / SEO | Weekly comparison-page briefs ("Lovevery alternative — what parents say") | 2-3 new comparison articles shipped per month, compounding organic traffic |
| Product | Quarterly feature-gap memo from competitor reviews | Roadmap input cheaper than user interviews |
| Partnerships | Market-specific verbatim quotes for pitches | Evidence-led pitches in LatAm markets |
| Leadership | Weekly read on what parents care about across the category | Early warning system for competitor moves |

The honest framing: *this is a marketing-efficiency play, not a direct
CAC-attribution play.* Same teams making the same number of decisions every
week, with better evidence behind each one.

---

## Maintenance — what the new owner actually has to do

### Weekly (5 min, if anything)

- The cron runs by itself every Monday at 13:00 UTC.
- New artifacts land in `outputs/` automatically. The dashboard auto-redeploys.
- **The new owner's only job:** forward the weekly memo to the marketing
  leadership distribution list, and pull 1-2 specific ad-copy or SEO briefs to
  hand to the creative and content teams.
- That's it. If they skip a week, nothing breaks.

### Quarterly (~30 min)

- Read the **Competitor Strengths memo** and the **Switching Opportunities
  memo** side by side.
- Summarize the 3-5 most consistent themes (e.g., "Lovevery parents want offline
  mode," "BabyCenter parents tired of ads"). Send to the product team as
  roadmap input.

### When the system needs a human (rare — maybe once a year)

| Trigger | What to do | Time |
|---|---|---|
| The weekly cron emails them about a failure | Open `docs/OPERATIONS.md` → find the symptom in the triage table → follow the fix | 5-15 min |
| They want to add a new competitor app | Edit `config/apps.yaml`, run the helper script, commit | 5 min |
| The Gemini API key needs rotating | Generate a new one at aistudio.google.com, update two secrets (GitHub + Streamlit Cloud) | 5 min |
| Marketing wants a new artifact type (e.g., a sales brief) | Add a new function to `src/synthesize.py`, modeled after the existing ones | 30 min with a Python-comfortable engineer |

---

## What the new owner inherits (the literal "things")

- **Public GitHub repo:** https://github.com/stronsop000/defector
- **Live dashboard:** https://defector.streamlit.app/
- **GitHub Actions weekly cron:** runs every Monday, already wired up
- **Three documentation files** in `docs/`:
  - `ONBOARDING.md` — 30-min checklist for the new owner
  - `OPERATIONS.md` — triage runbook for when something breaks
  - `MARKETING_GUIDE.md` — for non-technical team members consuming the outputs

---

## Honest risk callouts (anticipate the hard questions)

- **"How accurate is the classifier?"**
  ~85% on a hand-labeled 50-review eval set. Confidence is reported per-row.
  Treat individual classifications as suggestions; volume signals (3+ reviews
  saying the same thing) are robust.

- **"Is scraping app store reviews legal?"**
  Yes. App store reviews are public, intentionally so. We use them for internal
  intelligence only, don't republish, and don't run literal "competitor X is
  bad" comparison ads (rules vary by market).

- **"What if Gemini's free tier changes?"**
  The LLM layer is pluggable. One env-var switch moves to Claude (~$5 for
  5000 reviews) or any other provider.

- **"What if the original author isn't around?"**
  This entire document exists for that reason. The 30-min onboarding gets a new
  technical owner operational. The system runs itself; humans only consume the
  outputs.

- **"Could we extend this to Kinedu's own user feedback?"**
  Yes, post-submission. The classifier and synthesizer are domain-agnostic;
  feeding internal review/feedback data into the same pipeline is a Phase 2 add.
  See `docs/PHASE_2_VERCEL.md` for the broader roadmap.

- **"Streamlit looks a little plain — is that the final form?"**
  No. Streamlit was the right choice to ship in two weeks. Phase 2 is a Next.js
  + Vercel rebuild on the same Python pipeline — better polish, internal auth,
  saved views per user. Already scoped in `docs/PHASE_2_VERCEL.md`.

---

## Closing line

> *"Parent Feedback is intentionally boring. It runs every Monday whether
> anyone is paying attention. The win is that there's now a constant,
> high-signal feed of what parents say about our category — and four teams who
> each know what to do with it."*
