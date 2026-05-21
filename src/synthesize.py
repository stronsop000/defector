"""Generate the weekly intelligence brief and per-opportunity creative artifacts.

Four outputs per run, written to outputs/:
  1. Memo            — ranked switching opportunities (one weekly memo)
  2. Ad copy         — Meta/Google ad variants per opportunity, in market language
  3. SEO brief       — comparison-page brief (H1, meta, hook, outline) per opportunity
  4. Influencer brief — 4-6 talking points per opportunity for influencer/partner briefs

Usage:
    python -m src.synthesize                    # all four outputs
    python -m src.synthesize --top 3            # only top 3 opportunities (default 5)
    python -m src.synthesize --memo-only
    python -m src.synthesize --skip ads,seo     # skip specific output types
    python -m src.synthesize --since 2026-01-01 # window for the analysis
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import ROOT, load_taxonomy
from .db import connect
from .llm import DEFAULT_SYNTHESIZER_MODEL, call_text


def _as_quote_list(raw) -> list[str]:
    """DuckDB LIST columns come back as numpy ndarrays, not Python lists.
    Some older paths stored a JSON-encoded string. Normalize to a real list."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return [raw]
    # list, tuple, ndarray, anything iterable
    try:
        return [str(q) for q in raw if q is not None and str(q).strip()]
    except TypeError:
        return []

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("synthesize")

MEMO_DIR = ROOT / "outputs" / "memos"
COPY_DIR = ROOT / "outputs" / "copy"
SEO_DIR = ROOT / "outputs" / "seo"
INFLUENCER_DIR = ROOT / "outputs" / "influencer"
STRENGTHS_DIR = ROOT / "outputs" / "strengths"


def _themes_query(since: str, sentiments: tuple[str, ...]) -> str:
    """Cluster competitor reviews by (app × category × market), filtered to a
    sentiment direction. `sentiments=('negative','mixed')` produces switching
    opportunities; `sentiments=('positive',)` produces competitor strengths."""
    sent_in = ",".join(f"'{s}'" for s in sentiments)
    return f"""
    WITH base AS (
        SELECT r.app_name, r.app_category, r.country, r.lang,
               c.category_key, c.sub_reason, c.verbatim_quote, c.is_churn_signal,
               c.sentiment, r.review_date
        FROM reviews r
        JOIN classifications c ON r.review_id = c.review_id
        WHERE r.app_category != 'kinedu'
          AND r.review_date >= TIMESTAMP '{since}'
          AND c.sentiment IN ({sent_in})
    ),
    grouped AS (
        SELECT app_name, app_category, country, lang, category_key,
               COUNT(*) AS volume,
               SUM(CASE WHEN is_churn_signal THEN 1 ELSE 0 END) AS churn_signals,
               LIST(verbatim_quote)[1:5] AS quotes,
               MODE(sub_reason) AS dominant_sub_reason
        FROM base
        WHERE verbatim_quote IS NOT NULL AND verbatim_quote != ''
        GROUP BY app_name, app_category, country, lang, category_key
    ),
    app_totals AS (
        SELECT app_name, country, COUNT(*) AS total_in_direction
        FROM base
        GROUP BY app_name, country
    )
    SELECT g.app_name, g.app_category, g.country, g.lang, g.category_key,
           g.volume, g.churn_signals, g.dominant_sub_reason,
           ROUND(100.0 * g.volume / NULLIF(t.total_in_direction, 0), 1) AS pct_of_app_total,
           g.quotes
    FROM grouped g
    JOIN app_totals t ON g.app_name = t.app_name AND g.country = t.country
    WHERE g.volume >= 3
    ORDER BY g.volume DESC, g.churn_signals DESC
    """


def opportunities_query(since: str) -> str:
    """Negative + mixed reviews — these are switching opportunities."""
    return _themes_query(since, ("negative", "mixed"))


def strengths_query(since: str) -> str:
    """Positive reviews — these are competitor strengths to match or defend."""
    return _themes_query(since, ("positive",))


def fetch_opportunities(con, since: str, top: int) -> list[dict]:
    df = con.execute(opportunities_query(since)).fetchdf()
    if df.empty:
        return []
    return df.head(top).to_dict("records")


def fetch_strengths(con, since: str, top: int) -> list[dict]:
    df = con.execute(strengths_query(since)).fetchdf()
    if df.empty:
        return []
    return df.head(top).to_dict("records")


def category_lookup() -> dict[str, str]:
    return {c.key: c.label for c in load_taxonomy()}


def _themes_to_bullets(themes: list[dict], since: str, label: str) -> str:
    """Render a list of theme rows as a markdown bullet block for the synthesizer prompt."""
    cats = category_lookup()
    bullets = []
    for i, o in enumerate(themes, 1):
        quotes = _as_quote_list(o["quotes"])
        quote_lines = "\n".join(f'        - "{q}"' for q in quotes[:3] if q)
        bullets.append(
            f"""{i}. **{o['app_name']}** in **{o['country'].upper()}** — _{cats.get(o['category_key'], o['category_key'])}_
   - Volume: {int(o['volume'])} {label} in this category since {since}
   - Loyalty/churn signals: {int(o['churn_signals'])}
   - Share of all {o['app_name']} {label} in this market: {o['pct_of_app_total']}%
   - Dominant sub-reason: _{o['dominant_sub_reason']}_
   - Verbatim parent voice:
{quote_lines}
"""
        )
    return "\n".join(bullets)


def synthesize_memo(opps: list[dict], since: str) -> str:
    raw = _themes_to_bullets(opps, since, "complaints")
    system = (
        "You are a B2C growth strategist at Kinedu, a developmental activity app for babies and toddlers. "
        "You are reading a structured snapshot of why parents are leaving competing apps and brands. "
        "Write a tight weekly memo (max 600 words) titled 'Switching Opportunities — Week of {date}'. "
        "For each opportunity, write one short paragraph that names the competitor, the gap, what Kinedu offers "
        "instead, and one specific marketing action (channel + message angle). Be concrete, not generic. "
        "Use the parents' own verbatim language where possible. Markdown format. No filler."
    ).format(date=date.today().isoformat())

    user = (
        f"Here is the data for this week, since {since}. Top {len(opps)} switching opportunities ranked by volume:\n\n{raw}\n\n"
        "Write the memo."
    )
    return call_text(model=DEFAULT_SYNTHESIZER_MODEL, system=system, messages=[{"role": "user", "content": user}])


def synthesize_strengths_memo(strengths: list[dict], since: str) -> str:
    raw = _themes_to_bullets(strengths, since, "rave reviews")
    system = (
        "You are a B2C growth strategist at Kinedu, a developmental activity app for babies and toddlers. "
        "You are reading a structured snapshot of what parents PRAISE about competing parenting and baby-product apps. "
        "This is competitive intelligence on what those competitors do well — Kinedu needs to know which experiences "
        "are creating loyalty so we can either match them, exceed them, or position around them. "
        "Write a tight weekly memo (max 600 words) titled 'Competitor Strengths — Week of {date}'. "
        "For each strength, write one short paragraph: name the competitor, name the experience parents are praising, "
        "quote the verbatim language they use, and recommend ONE specific action for Kinedu — either how to match it, "
        "how to differentiate against it, or how to absorb the language into Kinedu's own positioning. "
        "Use the parents' own verbatim language. Markdown format. No filler. Do NOT bash competitors — this is "
        "intelligence about what works, not what doesn't."
    ).format(date=date.today().isoformat())
    user = (
        f"Here is the data for this week, since {since}. Top {len(strengths)} competitor strengths ranked by volume:\n\n{raw}\n\n"
        "Write the memo."
    )
    return call_text(model=DEFAULT_SYNTHESIZER_MODEL, system=system, messages=[{"role": "user", "content": user}])


def _opp_context_block(opp: dict) -> str:
    """The shared 'here's the opportunity' user-prompt prefix."""
    cats = category_lookup()
    quotes = _as_quote_list(opp["quotes"])
    quote_block = "\n".join(f'- "{q}"' for q in quotes[:5] if q)
    return (
        f"Target opportunity: parents leaving **{opp['app_name']}** ({opp['app_category']}) in **{opp['country'].upper()}**.\n"
        f"Their #1 complaint category: **{cats.get(opp['category_key'], opp['category_key'])}**.\n"
        f"Dominant sub-reason: **{opp['dominant_sub_reason']}**.\n"
        f"Volume signal: {int(opp['volume'])} complaints, {int(opp['churn_signals'])} explicit churn statements.\n\n"
        f"Verbatim parent quotes (use these — do not invent feelings):\n{quote_block}\n\n"
    )


def generate_copy(opp: dict) -> str:
    system = (
        "You are a senior performance marketer at Kinedu writing conversion copy briefed by Defector — "
        "a system that mines verbatim complaints from parents who are leaving competing parenting apps. "
        "Mirror the parents' own language (use their verbatim complaints as raw material). Be specific, "
        "concrete, and emotionally intelligent — not salesy. "
        "Output four sections in Markdown:\n"
        "  1. **3 Meta/Instagram ad headlines** (max 7 words each)\n"
        "  2. **3 Meta/Instagram ad primary text variants** (max 30 words each)\n"
        "  3. **1 landing page hero** (headline + 1 sentence subhead + 1 CTA button text)\n"
        "  4. **2 push notifications for Kinedu trial users who match this complaint pattern** (max 12 words each)\n\n"
        "Write everything in the same language as the parent quotes. Do not translate."
    )
    user = _opp_context_block(opp) + "Now write the ad copy package."
    return call_text(model=DEFAULT_SYNTHESIZER_MODEL, system=system, messages=[{"role": "user", "content": user}])


def generate_seo_brief(opp: dict) -> str:
    system = (
        "You are an SEO content strategist at Kinedu. You write briefs for comparison and 'alternative' pages "
        "that capture high-intent search traffic (e.g. '<competitor> alternative', '<competitor> vs Kinedu', "
        "'why parents leave <competitor>'). Each brief should be ready for a content writer to flesh out in "
        "30-60 minutes.\n\n"
        "Output in Markdown with these sections:\n"
        "  1. **Target keyword + intent** (the primary query this page should rank for; what the searcher wants)\n"
        "  2. **Suggested URL slug**\n"
        "  3. **H1** (max 70 chars)\n"
        "  4. **Meta description** (max 155 chars, include emotional hook from real parent language)\n"
        "  5. **Hero paragraph** (~80 words; opens by validating the parent's frustration in their own language, "
        "     then names Kinedu as a credible alternative — do not be salesy)\n"
        "  6. **Section outline** (5-7 H2s, each with a one-sentence purpose)\n"
        "  7. **Verbatim quote callouts** (3 short quotes from the source data to embed as pull-quotes)\n"
        "  8. **Internal-link suggestions** (3 plausible Kinedu pages this should link to — name the topic, not the URL)\n\n"
        "Write the entire brief in the same language as the parent quotes (do not translate). "
        "For comparison/alternative pages, follow each market's advertising norms — be factual and parent-voice-led, "
        "not knock-down."
    )
    user = _opp_context_block(opp) + "Now write the SEO comparison-page brief."
    return call_text(model=DEFAULT_SYNTHESIZER_MODEL, system=system, messages=[{"role": "user", "content": user}])


def generate_influencer_brief(opp: dict) -> str:
    system = (
        "You are a partnerships and creator-marketing lead at Kinedu. You're writing a brief for parenting "
        "influencers and partner organizations (pediatric clinics, daycare networks) so they can talk about "
        "Kinedu in a way that resonates with their audience. The brief should give them a tight angle to riff "
        "on without scripting them word-for-word.\n\n"
        "Output in Markdown with these sections:\n"
        "  1. **The angle** (one sentence — what's the story?)\n"
        "  2. **Why this matters to parents right now** (2-3 sentences, parent-voice, what we're hearing in this market)\n"
        "  3. **4-6 talking points** (each one short — a creator can riff for 15-30 seconds on each in TikTok/Reel format)\n"
        "  4. **Sample hook line** (one TikTok-style opener, max 12 words)\n"
        "  5. **What NOT to say** (1-2 lines — avoid claims we can't back up, avoid trashing competitors)\n\n"
        "Write in the language of the parent quotes."
    )
    user = _opp_context_block(opp) + "Now write the influencer / partner brief."
    return call_text(model=DEFAULT_SYNTHESIZER_MODEL, system=system, messages=[{"role": "user", "content": user}])


OUTPUT_KINDS = {"memo", "ads", "seo", "influencer", "strengths"}


def _opp_slug(opp: dict) -> str:
    return f"{opp['app_name']}_{opp['country']}_{opp['category_key']}".lower().replace(" ", "_")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--since", default=(date.today() - timedelta(days=90)).isoformat())
    p.add_argument("--memo-only", action="store_true", help="Equivalent to --skip ads,seo,influencer")
    p.add_argument(
        "--skip",
        default="",
        help="Comma-separated output kinds to skip: memo,ads,seo,influencer",
    )
    args = p.parse_args()

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    if args.memo_only:
        skip |= {"ads", "seo", "influencer"}
    unknown = skip - OUTPUT_KINDS
    if unknown:
        log.error("Unknown --skip values: %s. Valid: %s", unknown, OUTPUT_KINDS)
        return

    # synthesize only reads — open read-only so it can coexist with the
    # Streamlit dashboard which also holds a read-only handle.
    con = connect(read_only=True)
    opps = fetch_opportunities(con, args.since, args.top)
    strengths = fetch_strengths(con, args.since, args.top)
    con.close()

    if not opps and not strengths:
        log.error("No opportunities or strengths found. Make sure scrape + classify have run.")
        return

    stamp = date.today().isoformat()
    for d in (MEMO_DIR, COPY_DIR, SEO_DIR, INFLUENCER_DIR, STRENGTHS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    if "memo" not in skip and opps:
        log.info("Synthesizing switching-opportunities memo for %d opportunities…", len(opps))
        memo = synthesize_memo(opps, args.since)
        memo_path = MEMO_DIR / f"{stamp}_switching_opportunities.md"
        memo_path.write_text(memo, encoding="utf-8")
        log.info("Wrote %s", memo_path)

    if "strengths" not in skip and strengths:
        log.info("Synthesizing competitor-strengths memo for %d strengths…", len(strengths))
        smemo = synthesize_strengths_memo(strengths, args.since)
        smemo_path = STRENGTHS_DIR / f"{stamp}_competitor_strengths.md"
        smemo_path.write_text(smemo, encoding="utf-8")
        log.info("Wrote %s", smemo_path)
    elif "strengths" not in skip:
        log.info("No positive-sentiment data yet (skipping strengths memo). Run `python -m src.classify` to classify high-star reviews.")

    per_opp_generators = [
        ("ads", COPY_DIR, generate_copy, "ad copy"),
        ("seo", SEO_DIR, generate_seo_brief, "SEO brief"),
        ("influencer", INFLUENCER_DIR, generate_influencer_brief, "influencer brief"),
    ]

    for kind, out_dir, fn, label in per_opp_generators:
        if kind in skip:
            continue
        for i, opp in enumerate(opps, 1):
            log.info("Generating %s %d/%d (%s @ %s)…", label, i, len(opps), opp["app_name"], opp["country"])
            try:
                content = fn(opp)
            except Exception as e:
                log.warning("Failed %s for %s @ %s: %s", label, opp["app_name"], opp["country"], e)
                continue
            path = out_dir / f"{stamp}_{_opp_slug(opp)}.md"
            path.write_text(content, encoding="utf-8")
            log.info("Wrote %s", path)


if __name__ == "__main__":
    main()
