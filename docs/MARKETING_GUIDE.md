# How to use Parent Feedback — guide for the Kinedu team

If you're on marketing, content, product, or partnerships and someone said *"check Parent Feedback"* — this is what to do. Five-minute read.

## What is this?

Every Monday, Parent Feedback reads thousands of public reviews of competing parenting and baby-product apps (Lovevery, BabyCenter, BabySparks, Pampers Rewards, Huggies, Wonder Weeks, and 24 others) across the US and Latin America in English, Spanish, and Portuguese. It categorizes why parents praise or leave them, and writes:

- A **Switching Opportunities memo** — where parents are publicly leaving competitors and what to say to win them
- A **Competitor Strengths memo** — what competitors do well that Kinedu should match or position against
- **Ad copy packages** — 3 Meta headlines + primary text + landing hero + push notifications per top opportunity
- **SEO comparison-page briefs** — H1, meta, hook, outline, verbatim quotes for a content writer
- **Influencer / partner briefs** — 4–6 talking points, hook line, what-not-to-say

All in the parents' own language, in the right market language.

## Where to find it

**Public dashboard:** https://defector.streamlit.app/

**Files in the repo:** https://github.com/stronsop000/defector
- `outputs/memos/` — weekly switching memo
- `outputs/strengths/` — competitor strengths memo
- `outputs/copy/` — ad copy packages
- `outputs/seo/` — SEO briefs
- `outputs/influencer/` — influencer briefs

Files are dated. Newest is most recent.

## How each team should use it

### Performance marketing / paid acquisition

**Weekly:** open the Switching Opportunities memo. Pick 1–2 of the top 5 to test that week. Use the ad-copy file for those opportunities as your creative brief — the 3 headlines + 3 primary text variants are A/B-test-ready.

**Where the lift comes from:** the copy mirrors the exact emotional language parents already use to describe their frustration with that competitor. Message-market fit on day one.

**Don't:** literally paste the headlines without reading them. They're a starting point, not a final spec. Always tweak for brand voice.

### Content / SEO

**Weekly:** open `outputs/seo/`. Each file is a brief for one comparison page (e.g., *"Lovevery alternative — for parents tired of $80 a kit"*). Each has H1, meta, hook, outline, target keyword, and verbatim pull-quotes ready to embed.

**Time to publish:** with a brief in hand, a writer can publish in 30–60 min instead of starting from blank page.

**SEO wins:** comparison pages capture high-intent search like *"<competitor> alternative"* — among the highest-converting B2C subscription patterns.

**Don't:** copy quotes verbatim without attribution. They're public reviews so reusing is legal, but for tone you'll want light editing.

### Product

**Quarterly:** open the Competitor Strengths memo and the Opportunities memo together. What features are competitors bleeding on? (e.g., "Lovevery parents want offline mode," "Huckleberry users praise multi-caregiver sync"). That's roadmap input — what to defend, what to attack.

**Don't:** treat one quote as a roadmap mandate. Look for volume signals (10+ complaints across 3+ weeks) before acting.

### Partnerships

**Per pitch:** open the dashboard and filter to the market and category relevant to your prospect. Pull 2–3 verbatim parent quotes to use as evidence in the pitch. "In Brazil, 847 parents leaving competitor X cite the same problem we solve."

**Influencer briefs:** when briefing a parenting influencer for a Kinedu campaign, hand them the `outputs/influencer/` brief for that market. It has talking points already grounded in real parent language.

### Leadership

**Monthly:** read the latest Switching Opportunities memo. The opening paragraph names the top 3 places this month where parents are publicly leaving competitors. That's where the cheap conversions live.

## How to brief a teammate on Parent Feedback in 60 seconds

> *Public reviews of every parenting app, classified into 11 reasons parents praise or leave them, refreshed weekly, with ready-to-ship ad copy, SEO briefs, and influencer briefs in EN/ES/PT. The dashboard is at [URL], the files are in this GitHub repo. Marketing uses the ad copy. Content uses the SEO briefs. Product uses the feature-gap signal. Partnerships uses the quotes for pitch evidence.*

## Common questions

**"Where do these reviews come from?"**
Public Apple App Store + Google Play Store reviews for the apps in `config/apps.yaml`. No internal Kinedu data, no scraped Kinedu users, nothing private.

**"How fresh is the data?"**
Weekly. Last refresh date is shown in the dashboard footer and is the most recent date in `outputs/` filenames.

**"What if I want a new app added?"**
File a GitHub issue on the repo with the app name. The maintainer adds it to `config/apps.yaml` and the next weekly run picks it up.

**"Can I trust the classifications?"**
The classifier was validated against a hand-labeled 50-review set and scores ~85% accuracy. Treat individual classifications as suggestions; volume signals (multiple reviews saying the same thing) are robust.

**"Is this legal? It's scraping reviews."**
Yes — app store reviews are public, intentionally written to be public, and we only use them for internal intelligence. We don't republish them publicly without attribution and we don't run *literal* "competitor X is bad" ads (comparative advertising rules vary by market).

**"What if a competitor adds a feature that makes us look bad?"**
You'll see it in the Strengths memo before the marketing impact lands. That's the early-warning system.

**"What if I want a different kind of output (e.g., investor briefing, board update)?"**
Add a new generator in `src/synthesize.py` modeled after the existing ones. Or ask the maintainer. The prompt template approach makes new artifact types cheap to add.
