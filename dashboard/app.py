"""Parent Feedback dashboard.

Run from project root:
    streamlit run dashboard/app.py

Reads from data/reviews.duckdb. Read-only — never writes back.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# Make `src` importable when running via `streamlit run dashboard/app.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DB_PATH, ROOT, load_taxonomy  # noqa: E402

st.set_page_config(page_title="Parent Feedback — a weekly reading of what parents say", layout="wide", page_icon=":newspaper:")

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

    <style>
    :root {
        --bg: #fdfaf3;
        --ink: #1a1a1a;
        --ink-soft: #3d3d3d;
        --muted: #8a7f73;
        --border: #e6dfd0;
        --rule: #d6cdb9;
        --terracotta: #b8443a;
        --sage: #3a6b5c;
        --quote-bg: #f5efe1;
    }

    html, body, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--ink);
    }
    .stApp { background: var(--bg); }

    /* Body text inside Streamlit content uses Inter — but don't blanket-override
       every st- class, that breaks Material Symbols icon fonts (chevrons, etc). */
    .stMarkdown, .stText, .stCaption,
    [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] *,
    [data-baseweb="select"] *,
    [data-baseweb="tab"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Explicitly restore Material Symbols on the icon spans so chevrons render. */
    [class*="material-symbols"],
    [class*="MaterialSymbols"],
    [data-testid="stExpander"] details summary svg,
    [data-testid="stExpander"] details summary span[class*="icon"] {
        font-family: 'Material Symbols Outlined', 'Material Icons' !important;
    }

    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Fraunces', 'Times New Roman', Georgia, serif;
        color: var(--ink);
        font-weight: 500;
        letter-spacing: -0.01em;
    }

    /* ---------- Editorial hero ---------- */
    .editorial-hero {
        margin: 0.5rem 0 2.5rem 0;
        padding-bottom: 2rem;
        border-bottom: 1px solid var(--rule);
    }
    .editorial-hero .masthead {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: var(--muted);
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .editorial-hero h1 {
        font-family: 'Fraunces', serif;
        font-size: 4.5rem;
        font-weight: 600;
        margin: 0;
        line-height: 1.0;
        letter-spacing: -0.035em;
        color: var(--ink);
    }
    .editorial-hero .lede {
        font-family: 'Fraunces', serif;
        font-size: 1.35rem;
        line-height: 1.45;
        color: var(--ink-soft);
        font-weight: 400;
        font-style: italic;
        max-width: 720px;
        margin-top: 1.25rem;
    }
    .editorial-hero .byline {
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--muted);
        margin-top: 1.75rem;
        font-weight: 500;
    }
    .editorial-hero .byline .sep { margin: 0 0.6rem; color: var(--rule); }

    /* ---------- Reading line (replaces KPI tiles) ---------- */
    .reading-line {
        font-family: 'Fraunces', serif;
        font-size: 1.35rem;
        font-weight: 400;
        color: var(--ink);
        line-height: 1.5;
        padding: 0 0 1.75rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid var(--rule);
        max-width: 820px;
    }
    .reading-line .num { font-weight: 600; color: var(--ink); }
    .reading-line .neg { color: var(--terracotta); font-weight: 600; }
    .reading-line .pos { color: var(--sage); font-weight: 600; }

    /* ---------- Opportunity / Strength briefs ---------- */
    .brief {
        display: grid;
        grid-template-columns: 4.5rem 1fr;
        gap: 1.75rem;
        padding: 2rem 0;
        border-bottom: 1px solid var(--rule);
    }
    .brief .rank {
        font-family: 'Fraunces', serif;
        font-size: 3.5rem;
        font-weight: 400;
        color: var(--terracotta);
        line-height: 0.9;
        font-style: italic;
    }
    .brief.positive .rank { color: var(--sage); }
    .brief .kicker {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--muted);
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .brief h3 {
        font-family: 'Fraunces', serif;
        font-size: 1.55rem;
        font-weight: 500;
        margin: 0 0 0.6rem 0;
        line-height: 1.2;
        color: var(--ink);
    }
    .brief .stats {
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        color: var(--ink-soft);
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    .brief .stats .num { font-weight: 600; color: var(--ink); }

    /* ---------- Pull-quotes ---------- */
    .editorial-quote {
        font-family: 'Fraunces', serif;
        font-size: 1.1rem;
        font-style: italic;
        line-height: 1.5;
        color: var(--ink);
        border-left: 2px solid var(--terracotta);
        padding: 0.15rem 0 0.15rem 1.25rem;
        margin: 0.6rem 0;
        max-width: 700px;
    }
    .brief.positive .editorial-quote { border-left-color: var(--sage); }

    /* ---------- Section labels ---------- */
    .section-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: var(--muted);
        font-weight: 600;
        margin: 2rem 0 0.5rem 0;
    }

    /* ---------- Hide Streamlit chrome ---------- */
    #MainMenu      { visibility: hidden; }
    footer         { visibility: hidden; }
    .stDeployButton { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stHeader"] { background: transparent; }

    /* ---------- Tabs as editorial nav ---------- */
    [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--rule) !important;
        gap: 2.25rem;
    }
    [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        color: var(--muted) !important;
        padding: 0.75rem 0 !important;
        background: transparent !important;
    }
    [data-baseweb="tab"][aria-selected="true"] { color: var(--ink) !important; }
    [data-baseweb="tab-highlight"] {
        background: var(--terracotta) !important;
        height: 2px !important;
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: #f5efe1;
        border-right: 1px solid var(--rule);
    }
    [data-testid="stSidebar"] h1 {
        font-family: 'Fraunces', serif;
        font-size: 1.4rem;
        font-weight: 600;
    }
    [data-testid="stSidebar"] label {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        color: var(--ink-soft) !important;
    }

    /* ---------- Form widgets ---------- */
    [data-baseweb="select"] > div {
        background: var(--bg) !important;
        border-color: var(--rule) !important;
    }
    [data-baseweb="tag"] {
        background: var(--quote-bg) !important;
        border: 1px solid var(--rule) !important;
        color: var(--ink) !important;
    }

    /* ---------- Buttons ---------- */
    .stButton > button, .stDownloadButton > button {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        background: var(--ink) !important;
        color: var(--bg) !important;
        border: none !important;
        border-radius: 1px !important;
        padding: 0.5rem 1rem !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: var(--terracotta) !important;
        color: var(--bg) !important;
    }

    /* ---------- Markdown ---------- */
    .stMarkdown p, .stMarkdown li {
        font-family: 'Inter', sans-serif;
        color: var(--ink-soft);
        line-height: 1.65;
    }
    .stMarkdown blockquote {
        border-left: 2px solid var(--terracotta);
        padding-left: 1.25rem;
        font-family: 'Fraunces', serif;
        font-style: italic;
        font-size: 1.1rem;
        color: var(--ink);
    }
    .stMarkdown code {
        background: var(--quote-bg) !important;
        color: var(--terracotta) !important;
        font-size: 0.85rem !important;
        padding: 1px 6px !important;
        border-radius: 2px !important;
    }

    /* ---------- Footer ---------- */
    .footer {
        font-family: 'Inter', sans-serif;
        border-top: 1px solid var(--rule);
        margin-top: 4rem;
        padding-top: 1.5rem;
        color: var(--muted);
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
    }
    .footer a { color: var(--terracotta); text-decoration: none; border-bottom: 1px solid var(--terracotta); }
    .footer .sep { margin: 0 0.6rem; color: var(--rule); }

    /* ---------- Container ---------- */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1080px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(ttl=300)
def base_reviews_df(since: str) -> pd.DataFrame:
    con = get_con()
    return con.execute(
        f"""
        SELECT r.review_id, r.app_name, r.app_category, r.country, r.lang,
               r.rating, r.title, r.body, r.review_date,
               c.category_key, c.sub_reason, c.sentiment, c.is_churn_signal,
               c.verbatim_quote, c.confidence
        FROM reviews r
        LEFT JOIN classifications c ON r.review_id = c.review_id
        WHERE r.review_date >= TIMESTAMP '{since}' OR r.review_date IS NULL
        """
    ).fetchdf()


def category_labels() -> dict[str, str]:
    return {c.key: c.label for c in load_taxonomy()}


# -------------- editorial hero --------------
_today = date.today()
_issue_num = (_today - date(2026, 5, 1)).days // 7 + 1
_week_label = f"{_today.strftime('%B')} {_today.day}, {_today.year}"
st.markdown(
    f"""
    <div class="editorial-hero">
        <div class="masthead">Vol. 1 &nbsp;·&nbsp; Issue {_issue_num} &nbsp;·&nbsp; Week of {_week_label}</div>
        <h1>Parent Feedback</h1>
        <div class="lede">
            A weekly reading of what parents say about every parenting app —
            in the markets that matter, in the languages they speak,
            with the words Kinedu should reply with.
        </div>
        <div class="byline">
            US <span class="sep">·</span> MX <span class="sep">·</span> BR <span class="sep">·</span> AR <span class="sep">·</span> CO <span class="sep">·</span> CL <span class="sep">·</span> PE
            &nbsp;&nbsp;&nbsp;
            EN <span class="sep">·</span> ES <span class="sep">·</span> PT
            &nbsp;&nbsp;&nbsp;
            <span style="color: var(--terracotta);">Refreshed every Monday</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("On method"):
    st.markdown(
        """
        Parent Feedback reads thirty parenting and baby-product apps every week — Lovevery,
        BabyCenter, BabySparks, Pampers Rewards, Huggies, Wonder Weeks, and twenty-four
        others. It pulls public reviews from Apple's App Store and Google Play across
        seven countries in English, Spanish, and Portuguese.

        A Gemini-based classifier sorts each review by topic (price, content, bugs,
        features, support, and so on) and by sentiment. The synthesizer then writes
        four artifacts: a memo on where parents are leaving competitors, a parallel
        memo on what competitors are winning at, ad copy aimed at the defectors, and
        SEO and influencer briefs for the content and partnership teams.

        Accuracy of the classifier is around 85% against a hand-labeled set of fifty
        reviews. The system uses no internal Kinedu data, runs on free LLM tiers, and
        refreshes itself via a Monday cron with no human in the loop.
        """
    )

# -------------- sidebar filters --------------
st.sidebar.title("Filters")
default_since = (date.today() - timedelta(days=90)).isoformat()
since_date = st.sidebar.date_input("Reviews since", value=date.fromisoformat(default_since))

if not DB_PATH.exists():
    st.error(
        f"No database found at `{DB_PATH}`.\n\n"
        "This usually means the scraper hasn't run yet. From the project root, run:\n\n"
        "```bash\n"
        "python -m src.scrape\n"
        "python -m scripts.seed_demo_data    # optional — populates demo clusters\n"
        "```\n\n"
        "Then refresh this page. See `docs/ONBOARDING.md` for the full quickstart."
    )
    st.stop()

df = base_reviews_df(since_date.isoformat())

if df.empty:
    st.warning(
        "No reviews in the selected window.\n\n"
        "**If this is a fresh install:** seed the dashboard with demo data — run "
        "`python -m scripts.seed_demo_data` then refresh.\n\n"
        "**If real data should be here:** widen the *Reviews since* filter in the sidebar, "
        "or run `python -m src.scrape` to pull fresh reviews from the app stores."
    )
    st.stop()

countries = sorted(df["country"].dropna().unique().tolist())
country_pick = st.sidebar.multiselect("Markets", countries, default=countries)
categories_in_data = sorted(df["app_category"].dropna().unique().tolist())
cat_pick = st.sidebar.multiselect("App categories", categories_in_data, default=categories_in_data)
star_range = st.sidebar.slider("Star range", 1, 5, (1, 5))
sentiment_pick = st.sidebar.multiselect(
    "Sentiment",
    ["negative", "mixed", "positive"],
    default=["negative", "mixed", "positive"],
    help="Negative + mixed = switching opportunities. Positive = competitor strengths.",
)
only_churn = st.sidebar.checkbox("Only explicit churn/loyalty signals", value=False)

filtered = df[
    df["country"].isin(country_pick)
    & df["app_category"].isin(cat_pick)
    & df["rating"].between(*star_range)
]
# Sentiment filter only applies to classified rows; unclassified rows pass through
# so the "Reviews in window" count remains meaningful even pre-classification.
if sentiment_pick:
    sent_mask = filtered["sentiment"].isna() | filtered["sentiment"].isin(sentiment_pick)
    filtered = filtered[sent_mask]
if only_churn:
    filtered = filtered[filtered["is_churn_signal"] == True]  # noqa: E712


# -------------- editorial reading line (replaces KPI tiles) --------------
total_reviews = len(filtered)
neg_count = int(filtered["sentiment"].isin(["negative", "mixed"]).sum())
pos_count = int(filtered["sentiment"].eq("positive").sum())
churn_count = int(filtered["is_churn_signal"].fillna(False).sum())
apps_count = filtered["app_name"].nunique()
markets_count = filtered["country"].nunique()

st.markdown(
    f"""
    <div class="reading-line">
        Reading <span class="num">{total_reviews:,}</span> reviews across
        <span class="num">{apps_count}</span> apps in
        <span class="num">{markets_count}</span> markets.
        <span class="neg">{neg_count:,}</span> reasons to leave,
        <span class="pos">{pos_count:,}</span> reasons to stay,
        <span class="num">{churn_count}</span> parents who said it out loud.
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------- tabs --------------
tab_howto, tab_overview, tab_opps, tab_strengths, tab_explore, tab_outputs = st.tabs(
    ["How to use this", "Overview", "Switching Opportunities", "Competitor Strengths", "Explore reviews", "Generated outputs"]
)


# === How to use this ===
with tab_howto:
    st.markdown(
        """
        <div style="margin-top: 1rem;">
            <p style="font-family: 'Fraunces', serif; font-size: 1.3rem; font-style: italic;
                       line-height: 1.5; color: var(--ink-soft); max-width: 720px;">
                Parent Feedback produces five artifacts every Monday. Below is what each
                Kinedu team should do with them — where to start, what to ship this week,
                what to measure.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    teams = [
        {
            "name": "Performance marketing",
            "kicker": "if you run Meta, Google, or TikTok ads",
            "start": "Open the **Switching Opportunities** tab. Pick 1-2 of the top 5 cards. Each one has a downloadable ad-copy file in the **Generated outputs** tab with 3 headlines, 3 primary-text variants, 1 landing hero, and 2 push notifications — already in the right market language.",
            "ship": "Test the headlines and primary text as your weekly creative variants. The hooks mirror the exact emotional language parents already use to describe their frustration with that competitor.",
            "measure": "Creative-test hit rate and CPM × CTR on Parent Feedback-briefed variants vs. your gut-written baseline. Realistic lift: 10-30% on test wins.",
        },
        {
            "name": "Content / SEO",
            "kicker": "if you own organic acquisition",
            "start": "Open the **Generated outputs** tab → **SEO comparison-page briefs**. Each file is one brief for one comparison page — *Lovevery alternative*, *BabyCenter vs Kinedu*, *why parents are leaving Pampers Rewards* — with H1, meta, hook, outline, target keyword, and verbatim pull-quotes.",
            "ship": "Publish 1-2 comparison pages per week. A writer can flesh out a brief in 30-60 min instead of starting from a blank page.",
            "measure": "Organic traffic to comparison URLs. These capture high-intent search like *<competitor> alternative* — among the highest-converting B2C subscription patterns.",
        },
        {
            "name": "Product",
            "kicker": "if you set roadmap priorities",
            "start": "Read the latest **Competitor Strengths memo** and **Switching Opportunities memo** side by side (both in the Generated outputs tab). What features are competitors bleeding on? What features are competitors winning with?",
            "ship": "Quarterly: pick 1-2 themes with volume signal (5+ reviews / 3+ weeks) and add to roadmap discussion as evidence-backed candidates.",
            "measure": "Roadmap consideration, not ship — Parent Feedback is signal, not mandate. Compare the recommended features against your current quarter's plan.",
        },
        {
            "name": "Partnerships",
            "kicker": "if you pitch B2B (clinics, daycares, employers, retailers)",
            "start": "Filter the dashboard to your prospect's market in the sidebar. Open **Switching Opportunities** to see what parents in that market are saying about competing apps and brands.",
            "ship": "For each pitch, pull 2-3 verbatim quotes from parents in the prospect's market. Drop them into the deck as evidence. *\"In Brazil, 847 parents leaving competitor X cite the same problem we solve.\"*",
            "measure": "Pitch evidence usage and partnership win rate in LatAm markets where we have the most data.",
        },
        {
            "name": "Leadership",
            "kicker": "if you allocate budget across channels",
            "start": "Read the weekly **Switching Opportunities memo** every Monday. The opening paragraph names the top 3 places this week where parents are publicly leaving competitors.",
            "ship": "Monthly: forward the most actionable memo to the marketing leadership distribution list with a 1-sentence framing.",
            "measure": "Where to invest paid acquisition or content effort next quarter. Parent Feedback is your early-warning system for competitor moves and category trends.",
        },
    ]

    for team in teams:
        st.markdown(
            f"""
            <div style="padding: 2rem 0; border-bottom: 1px solid var(--rule);">
                <div class="kicker" style="font-family: 'Inter', sans-serif;
                     font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase;
                     color: var(--muted); font-weight: 600; margin-bottom: 0.4rem;">
                    {team['kicker']}
                </div>
                <h3 style="font-family: 'Fraunces', serif; font-size: 1.7rem;
                     font-weight: 500; margin: 0 0 1.25rem 0; color: var(--ink);">
                    {team['name']}
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_start, col_ship, col_measure = st.columns(3, gap="large")
        with col_start:
            st.markdown(
                f"<div class='kicker' style=\"font-family: 'Inter', sans-serif; font-size: 0.7rem; "
                f"letter-spacing: 0.18em; text-transform: uppercase; color: var(--terracotta); "
                f"font-weight: 600; margin-bottom: 0.5rem;\">Start here</div>",
                unsafe_allow_html=True,
            )
            st.markdown(team["start"])
        with col_ship:
            st.markdown(
                f"<div class='kicker' style=\"font-family: 'Inter', sans-serif; font-size: 0.7rem; "
                f"letter-spacing: 0.18em; text-transform: uppercase; color: var(--terracotta); "
                f"font-weight: 600; margin-bottom: 0.5rem;\">Ship this week</div>",
                unsafe_allow_html=True,
            )
            st.markdown(team["ship"])
        with col_measure:
            st.markdown(
                f"<div class='kicker' style=\"font-family: 'Inter', sans-serif; font-size: 0.7rem; "
                f"letter-spacing: 0.18em; text-transform: uppercase; color: var(--terracotta); "
                f"font-weight: 600; margin-bottom: 0.5rem;\">Measure</div>",
                unsafe_allow_html=True,
            )
            st.markdown(team["measure"])

    st.markdown(
        """
        <div style="padding: 2.5rem 0 0.5rem 0;">
            <p style="font-family: 'Fraunces', serif; font-size: 1rem; font-style: italic;
                       color: var(--muted); max-width: 720px;">
                Not on this list? Anyone at Kinedu can browse — use the
                <b>Explore reviews</b> tab to filter by app, market, sentiment,
                or category, and read raw verbatim quotes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# === Overview ===
with tab_overview:
    st.subheader("Defection volume by app × category")

    classified = filtered.dropna(subset=["category_key"])
    if classified.empty:
        st.info("No classified reviews yet. Run `python -m src.classify`.")
    else:
        labels = category_labels()
        heat = (
            classified.assign(category=lambda d: d["category_key"].map(labels).fillna(d["category_key"]))
            .groupby(["app_name", "category"], as_index=False)
            .size()
            .rename(columns={"size": "complaints"})
        )
        fig = px.density_heatmap(
            heat, x="category", y="app_name", z="complaints",
            text_auto=True, color_continuous_scale="Sunset", height=600,
        )
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, width="stretch")

        st.subheader("Complaints over time")
        timeseries = (
            classified.assign(week=lambda d: pd.to_datetime(d["review_date"]).dt.to_period("W").dt.start_time)
            .groupby(["week", "app_category"], as_index=False)
            .size()
            .rename(columns={"size": "complaints"})
        )
        st.plotly_chart(
            px.line(timeseries, x="week", y="complaints", color="app_category", markers=True),
            width="stretch",
        )


# === Opportunities ===
with tab_opps:
    st.subheader("Top switching opportunities")
    st.caption("Ranked by complaint volume + explicit churn signals. Each card is a place we should be running targeted creative.")
    labels = category_labels()
    classified = filtered.dropna(subset=["category_key"])
    classified = classified[
        (classified["app_category"] != "kinedu")
        & (classified["sentiment"].isin(["negative", "mixed"]))
    ]

    if classified.empty:
        st.info(
            "No classified competitor reviews in this window yet. "
            "Once `python -m src.classify` has run, this is where the ranked "
            "switching opportunities will appear, each with verbatim parent quotes and links "
            "to the generated ad copy + SEO + influencer briefs."
        )
    else:
        opps = (
            classified.groupby(["app_name", "country", "category_key"])
            .agg(
                volume=("review_id", "count"),
                churn_signals=("is_churn_signal", lambda s: int(s.fillna(False).sum())),
                quotes=("verbatim_quote", lambda s: [q for q in s if isinstance(q, str) and q.strip()][:3]),
                dominant_sub_reason=("sub_reason", lambda s: s.value_counts().idxmax() if not s.empty else None),
            )
            .reset_index()
            .sort_values(["volume", "churn_signals"], ascending=False)
            .head(15)
        )
        for rank, (_, r) in enumerate(opps.iterrows(), 1):
            cat_label = labels.get(r["category_key"], r["category_key"])
            churn_line = (
                f' · <span class="num">{int(r["churn_signals"])}</span> said they cancelled'
                if int(r["churn_signals"]) > 0 else ""
            )
            st.markdown(
                f"""
                <div class="brief">
                    <div class="rank">{rank}</div>
                    <div>
                        <div class="kicker">{r['country'].upper()} &nbsp;·&nbsp; {cat_label}</div>
                        <h3>{r['app_name']}</h3>
                        <div class="stats">
                            <span class="num">{int(r['volume'])}</span> complaints in this category{churn_line}.<br>
                            Most common: <em>{r['dominant_sub_reason'] or '—'}</em>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("In their own words + generated assets", expanded=False):
                for q in r["quotes"]:
                    st.markdown(f'<div class="editorial-quote">"{q}"</div>', unsafe_allow_html=True)
                # Link to generated outputs for this opportunity, if they exist
                slug_root = f"{r['app_name']}_{r['country']}_{r['category_key']}".lower().replace(" ", "_")
                matches = []
                for kind, d in [("ad copy", ROOT / "outputs" / "copy"),
                                ("SEO brief", ROOT / "outputs" / "seo"),
                                ("influencer brief", ROOT / "outputs" / "influencer")]:
                    if d.exists():
                        hit = next((f for f in d.glob(f"*{slug_root}*.md")), None)
                        if hit:
                            matches.append((kind, hit))
                if matches:
                    st.markdown("**Generated assets for this opportunity:**")
                    for kind, f in matches:
                        with st.expander(f"📄 {kind} — {f.name}"):
                            st.markdown(f.read_text(encoding="utf-8"))


# === Competitor Strengths ===
with tab_strengths:
    st.subheader("Top competitor strengths")
    st.caption("What competitors do well, in fans' own words. Use this to match the experience, exceed it, or position around it.")
    labels = category_labels()
    classified_pos = filtered.dropna(subset=["category_key"])
    classified_pos = classified_pos[
        (classified_pos["app_category"] != "kinedu")
        & (classified_pos["sentiment"] == "positive")
    ]

    if classified_pos.empty:
        st.info(
            "No positive-sentiment classifications in this window yet. "
            "By default the classifier processes all 1-5★ reviews — run `python -m src.classify` "
            "to label them. Or run `python -m scripts.seed_demo_data` to populate demo strength data."
        )
    else:
        strengths = (
            classified_pos.groupby(["app_name", "country", "category_key"])
            .agg(
                volume=("review_id", "count"),
                loyalty_signals=("is_churn_signal", lambda s: int(s.fillna(False).sum())),
                quotes=("verbatim_quote", lambda s: [q for q in s if isinstance(q, str) and q.strip()][:3]),
                dominant_sub_reason=("sub_reason", lambda s: s.value_counts().idxmax() if not s.empty else None),
            )
            .reset_index()
            .sort_values(["volume", "loyalty_signals"], ascending=False)
            .head(15)
        )
        for rank, (_, r) in enumerate(strengths.iterrows(), 1):
            cat_label = labels.get(r["category_key"], r["category_key"])
            loyalty_line = (
                f' · <span class="num">{int(r["loyalty_signals"])}</span> said they switched here'
                if int(r["loyalty_signals"]) > 0 else ""
            )
            st.markdown(
                f"""
                <div class="brief positive">
                    <div class="rank">{rank}</div>
                    <div>
                        <div class="kicker">{r['country'].upper()} &nbsp;·&nbsp; {cat_label}</div>
                        <h3>{r['app_name']} is winning on this</h3>
                        <div class="stats">
                            <span class="num">{int(r['volume'])}</span> parents said so this period{loyalty_line}.<br>
                            Most common praise: <em>{r['dominant_sub_reason'] or '—'}</em>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("In their own words", expanded=False):
                for q in r["quotes"]:
                    st.markdown(f'<div class="editorial-quote">"{q}"</div>', unsafe_allow_html=True)

    # Link to the strengths memo if it exists
    strengths_dir = ROOT / "outputs" / "strengths"
    if strengths_dir.exists():
        files = sorted(strengths_dir.glob("*.md"), reverse=True)
        if files:
            st.divider()
            st.subheader("Latest strengths memo")
            st.markdown(files[0].read_text(encoding="utf-8"))


# === Explore ===
with tab_explore:
    st.subheader("Browse classified reviews")
    text_q = st.text_input("Search review text contains…", "")
    show = filtered.dropna(subset=["category_key"]).copy()
    if text_q:
        show = show[show["body"].str.contains(text_q, case=False, na=False)]
    show = show[
        ["app_name", "country", "rating", "category_key", "sub_reason",
         "is_churn_signal", "verbatim_quote", "body", "review_date"]
    ].sort_values("review_date", ascending=False).head(500)
    st.dataframe(show, width="stretch", hide_index=True)


# === Outputs ===
def _render_output_picker(label: str, dirpath, key: str, empty_hint: str) -> None:
    """Render a selectbox + viewer + download button for one outputs/ subdir."""
    st.subheader(label)
    if not dirpath.exists() or not list(dirpath.glob("*.md")):
        st.info(empty_hint)
        return
    files = sorted(dirpath.glob("*.md"), reverse=True)
    pick = st.selectbox(label, [f.name for f in files], index=0, key=key, label_visibility="collapsed")
    content = (dirpath / pick).read_text(encoding="utf-8")
    col_dl, col_spacer = st.columns([1, 5])
    with col_dl:
        st.download_button(
            "⬇ Download .md",
            data=content,
            file_name=pick,
            mime="text/markdown",
            key=f"dl_{key}",
        )
    st.markdown(content)


with tab_outputs:
    st.caption(
        "Generated weekly by the synthesize pipeline. Each section below has a download button — "
        "hand the file directly to the marketing, content, or partnerships team. New files appear "
        "every Monday after the GitHub Actions cron completes."
    )

    _render_output_picker(
        "Switching Opportunities memo",
        ROOT / "outputs" / "memos",
        key="memo_pick",
        empty_hint="No memos yet. Run `python -m src.synthesize` (locally) or trigger the weekly workflow.",
    )
    st.divider()

    _render_output_picker(
        "Competitor Strengths memo",
        ROOT / "outputs" / "strengths",
        key="strengths_pick",
        empty_hint="No strengths memo yet. Requires positive-sentiment classifications — run `python -m src.classify` then `python -m src.synthesize`.",
    )
    st.divider()

    # Per-opportunity artifacts grouped by output kind
    output_kinds = [
        ("Ad copy (Meta / Google / push)", ROOT / "outputs" / "copy",
         "No ad copy yet. Run `python -m src.synthesize` to generate per-opportunity ad packages."),
        ("SEO comparison-page briefs", ROOT / "outputs" / "seo",
         "No SEO briefs yet. Run `python -m src.synthesize` to generate comparison-page briefs."),
        ("Influencer / partner briefs", ROOT / "outputs" / "influencer",
         "No influencer briefs yet. Run `python -m src.synthesize` to generate."),
    ]
    for label, d, empty in output_kinds:
        _render_output_picker(label, d, key=f"pick_{d.name}", empty_hint=empty)
        st.divider()


# -------------- footer --------------
st.markdown(
    """
    <div class="footer">
      Parent Feedback <span class="sep">·</span>
      A weekly reading <span class="sep">·</span>
      <a href="https://github.com/stronsop000/defector" target="_blank">Source on GitHub</a> <span class="sep">·</span>
      Built for the Kinedu AI Challenge, May 2026
    </div>
    """,
    unsafe_allow_html=True,
)
