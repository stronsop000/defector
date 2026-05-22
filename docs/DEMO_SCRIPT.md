# 5-minute Demo Script — Parent Feedback

Read-aloud script for the recorded video (or live presentation) demo.
Placeholders in `{curly_braces}` are real numbers you'll fill in after the
classification run finishes. Total target: 5 minutes spoken, 1 minute slack
for transitions.

---

## [0:00 — 0:30] Hook

> **[on screen: the dashboard Opportunities tab, prefiltered to the top 3]**

"Hi, I'm Sophia, and this is Parent Feedback.

Every week, thousands of parents publicly post why they're leaving Lovevery,
BabySparks, BabyCenter, Pampers Rewards, and every other brand we compete
with for parent attention. It's in their App Store reviews. It's all public.
Nobody at Kinedu reads it systematically.

Parent Feedback does. In three languages, across thirty apps, across seven markets,
every week."

---

## [0:30 — 1:30] What it builds

> **[switch to: the architecture diagram from README.md, or just the file tree]**

"It's a Python pipeline. The scrapers pull 1- and 2-star reviews from the
Apple App Store and Google Play across the US, Mexico, Brazil, Argentina,
Colombia, Chile, and Peru. {N_REVIEWS} reviews currently sit in DuckDB on
my laptop.

A Gemini classifier — running on Google's free tier so the whole project
costs zero — sorts each review into one of eleven defection-reason
categories with eighty-something percent accuracy against a hand-labeled
eval set. Pricing, content quality, bugs, missing features, broken
localization, the rest.

A Claude-style synthesizer turns those classifications into four artifacts
every week: a switching-opportunities memo, ad-copy packages for the
performance marketing team, SEO comparison-page briefs for the content team,
and influencer talking points."

---

## [1:30 — 3:00] The dashboard — real numbers

> **[on screen: Overview tab → heatmap]**

"This is the overview. Each cell is one app crossed with one defection
category. Darker means more complaints. Right away you can see {OBSERVATION_1
e.g., 'Lovevery has a price-value cluster three times the size of its
content-quality cluster'}.

> **[switch to: Switching Opportunities tab]**

"And these are the ranked switching opportunities for this week. The top
one: **{TOP_OPP_APP} in {TOP_OPP_COUNTRY}, complaining about {TOP_OPP_CATEGORY}**.
{TOP_OPP_VOLUME} parents in the last 90 days, {TOP_OPP_CHURN} of them
explicitly saying they're cancelling.

Listen to them in their own words.

> **[expand the opportunity card to show 3 verbatim quotes]**

"[Read one quote aloud, then a second one.]

This is the data the marketing team would otherwise pay an agency to gather
in a quarterly study. Parent Feedback refreshes it weekly. No human labor."

---

## [3:00 — 4:00] The outputs the team actually uses

> **[switch to: Generated Outputs tab → Ad copy section → pick one file]**

"For each opportunity, Parent Feedback writes four artifacts. Here's the ad-copy
package for the {TOP_OPP_APP} opportunity. Three Meta headlines, three
primary text variants, a landing page hero, two push notifications — all in
the parents' own language, in this case {LANGUAGE}. Notice the hook uses
the exact phrase from the verbatim quote.

> **[switch to the SEO brief for the same opportunity]**

"And this is the SEO brief. H1, meta description, hero paragraph, outline,
verbatim pull-quotes. Our content team can publish this in thirty minutes
instead of starting from a blank page.

> **[switch to influencer brief]**

"And the influencer brief — four talking points an influencer can riff on
for a 30-second Reel, plus a hook line, plus what NOT to say so we don't
get into legal trouble with comparative advertising rules."

---

## [4:00 — 4:30] Impact

> **[back to the dashboard overview, or a slide with three bullets]**

"What does this move?

**Performance marketing** gets continuously refreshed creative briefs
grounded in real parent language. Realistic uplift on creative test hit
rate: ten to thirty percent.

**Content/SEO** gets two to three new comparison articles a month, with
hooks taken directly from parents who are searching for those very
comparisons.

**Product** gets a quarterly memo of competitor feature gaps. The Lovevery
parents asking for offline mode. The BabyCenter parents tired of ads.
That's roadmap input that would otherwise require user interviews.

**Partnerships** — my team — gets market-specific intelligence I can drop
into pitches. 'In Brazil, parents talk about X three times more than in
the US.' Real numbers, not vibes."

---

## [4:30 — 5:00] What's next

"The pipeline runs weekly on cron. The code is on a public GitHub repo
that's reproducible from scratch in twenty minutes with a free Gemini API
key. Total cost: zero. Total time to build: thirteen days.

Roadmap from here: add Mercado Libre product reviews to broaden the LatAm
signal, add Reddit parenting threads for open-ended discussion data, and
hand this off to a named owner on the marketing team for the weekly memo.

Thanks. Happy to take questions."

---

## After recording

- Trim to under 5:00 total
- Caption it in EN, ES, PT if you have time (Descript or YouTube auto-captions both work)
- Upload to YouTube as **unlisted** (not public, not private) so the link works in the submission form
- Paste the YouTube URL into `SUBMISSION.md` and the My Kinedu form

## Live demo backup plan (if you go live instead of recorded)

Bring a deck with the same 5 slides (one per section) plus screenshots of
each tab in case the dashboard URL has a hiccup. Keep your laptop on
ethernet if possible — Streamlit Cloud cold-boots in ~30s and that's the
worst moment to discover Wi-Fi is flaky.
