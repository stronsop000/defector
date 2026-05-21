"""Defector dashboard.

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

st.set_page_config(page_title="Defector — Competitor Switching Intelligence", layout="wide", page_icon=":dart:")

st.markdown(
    """
    <style>
    /* hero */
    .hero {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 60%, #ec4899 100%);
        color: white; padding: 2rem 2rem 1.5rem 2rem; border-radius: 14px;
        margin-bottom: 1.5rem;
    }
    .hero h1 { color: white; font-size: 2.4rem; margin: 0 0 0.25rem 0; letter-spacing: -0.02em; }
    .hero p  { color: #ede9fe; font-size: 1.05rem; margin: 0; max-width: 900px; line-height: 1.5; }
    .hero .pill {
        display: inline-block; background: rgba(255,255,255,0.18);
        padding: 2px 10px; border-radius: 999px; font-size: 0.8rem;
        margin-right: 6px; margin-top: 10px;
    }

    /* opportunity card */
    .opp-card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px;
        padding: 1rem 1.25rem; margin-bottom: 0.75rem;
    }
    .opp-meta { color: #6b7280; font-size: 0.85rem; margin-bottom: 0.5rem; }
    .opp-tag {
        display: inline-block; background: #eef2ff; color: #4338ca;
        padding: 2px 8px; border-radius: 999px; font-size: 0.75rem;
        font-weight: 500; margin-right: 4px;
    }
    .opp-tag.churn { background: #fef2f2; color: #b91c1c; }
    .opp-tag.positive { background: #ecfdf5; color: #047857; }
    .opp-card.positive { border-left: 3px solid #10b981; }

    .quote.positive {
        border-left-color: #10b981; background: #f0fdf4;
    }

    .quote {
        font-style: italic; color: #374151;
        border-left: 3px solid #818cf8; background: #f9fafb;
        padding: 0.55rem 0.85rem; margin: 0.35rem 0;
        border-radius: 0 6px 6px 0; font-size: 0.95rem;
    }

    /* footer */
    .footer {
        border-top: 1px solid #e5e7eb; margin-top: 3rem; padding-top: 1rem;
        color: #6b7280; font-size: 0.85rem; text-align: center;
    }
    .footer a { color: #6366f1; text-decoration: none; }

    /* hide Streamlit chrome that screams 'this is a Streamlit app' */
    #MainMenu      { visibility: hidden; }
    footer         { visibility: hidden; }
    .stDeployButton { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }

    /* tighten KPI numbers + bring back contrast */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important; font-weight: 600; color: #111827;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem; color: #6b7280;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.8rem;
    }

    /* less aggressive default padding */
    .block-container {
        padding-top: 1.5rem; padding-bottom: 2rem;
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


# -------------- hero --------------
st.markdown(
    """
    <div class="hero">
        <h1>Defector</h1>
        <p>Multilingual marketing intelligence + copy engine. We listen to what
        parents say when they leave competing parenting and baby-product apps —
        across 30 apps, 7 markets, and 3 languages — and turn it into ad copy,
        SEO briefs, and influencer talking points for the Kinedu growth team.</p>
        <div>
            <span class="pill">🇺🇸 🇲🇽 🇧🇷 🇦🇷 🇨🇴 🇨🇱 🇵🇪</span>
            <span class="pill">EN · ES · PT</span>
            <span class="pill">Refreshed weekly · zero cost</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("About this project · how it works"):
    st.markdown(
        """
        **What this is.** A continuously-refreshed view of what parents publicly
        complain about when they leave competing apps — Lovevery, BabySparks,
        BabyCenter, Pampers Rewards, Huggies, Wonder Weeks, and 24 others — and
        what Kinedu should say to win those parents.

        **How it works.**
        1. *Scrape.* Pull 1★/2★ reviews from the Apple App Store + Google Play across 7 markets.
        2. *Classify.* A Gemini-based classifier sorts each review into one of 11 defection categories with ~85% accuracy.
        3. *Synthesize.* For each top opportunity, generate ad copy, an SEO comparison brief, and influencer talking points — all in the parents' own language.
        4. *Refresh.* The whole pipeline runs weekly via GitHub Actions.

        **Public data only.** No internal Kinedu data used. The whole system is
        reproducible from a public GitHub repo.
        """
    )

# -------------- sidebar filters --------------
st.sidebar.title("Filters")
default_since = (date.today() - timedelta(days=90)).isoformat()
since_date = st.sidebar.date_input("Reviews since", value=date.fromisoformat(default_since))

if not DB_PATH.exists():
    st.error(f"No database found at {DB_PATH}. Run `python -m src.scrape` first.")
    st.stop()

df = base_reviews_df(since_date.isoformat())

if df.empty:
    st.warning("No reviews in the selected window. Try widening the date range or running the scraper.")
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


# -------------- header KPIs --------------
total_reviews = len(filtered)
classified_count = int(filtered["category_key"].notna().sum())
neg_count = int(filtered["sentiment"].isin(["negative", "mixed"]).sum())
pos_count = int(filtered["sentiment"].eq("positive").sum())
churn_count = int(filtered["is_churn_signal"].fillna(False).sum())
apps_count = filtered["app_name"].nunique()
markets_count = filtered["country"].nunique()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Reviews", f"{total_reviews:,}", help="Reviews in the selected window + filters.")
col2.metric("Switching signal", f"{neg_count:,}", help="Negative + mixed classified reviews — switching opportunities.")
col3.metric("Strength signal", f"{pos_count:,}", help="Positive classified reviews — what competitors do well.")
col4.metric("Churn / loyalty", f"{churn_count:,}", help="Reviews where the parent explicitly cancelled/switched (or switched TO this app).")
col5.metric("Apps × Markets", f"{apps_count} × {markets_count}", help="Distinct apps and country codes in this window.")


# -------------- tabs --------------
tab_overview, tab_opps, tab_strengths, tab_explore, tab_outputs = st.tabs(
    ["Overview", "Switching Opportunities", "Competitor Strengths", "Explore reviews", "Generated outputs"]
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
            churn_badge = (
                f'<span class="opp-tag churn">{int(r["churn_signals"])} churn signals</span>'
                if int(r["churn_signals"]) > 0 else ""
            )
            st.markdown(
                f"""
                <div class="opp-card">
                    <div class="opp-meta">#{rank} · {r['country'].upper()} · {cat_label}</div>
                    <div style="font-size: 1.15rem; font-weight: 600; margin-bottom: 0.4rem;">
                        {r['app_name']} — {cat_label}
                    </div>
                    <div style="margin-bottom: 0.6rem;">
                        <span class="opp-tag">{int(r['volume'])} complaints</span>
                        {churn_badge}
                        <span class="opp-tag">{r['dominant_sub_reason'] or '—'}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Show verbatim parent voice + generated assets", expanded=False):
                for q in r["quotes"]:
                    st.markdown(f'<div class="quote">"{q}"</div>', unsafe_allow_html=True)
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
            loyalty_badge = (
                f'<span class="opp-tag positive">{int(r["loyalty_signals"])} loyalty signals</span>'
                if int(r["loyalty_signals"]) > 0 else ""
            )
            st.markdown(
                f"""
                <div class="opp-card positive">
                    <div class="opp-meta">#{rank} · {r['country'].upper()} · {cat_label}</div>
                    <div style="font-size: 1.15rem; font-weight: 600; margin-bottom: 0.4rem;">
                        {r['app_name']} is winning on — {cat_label}
                    </div>
                    <div style="margin-bottom: 0.6rem;">
                        <span class="opp-tag positive">{int(r['volume'])} rave reviews</span>
                        {loyalty_badge}
                        <span class="opp-tag positive">{r['dominant_sub_reason'] or '—'}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Show verbatim parent voice", expanded=False):
                for q in r["quotes"]:
                    st.markdown(f'<div class="quote positive">"{q}"</div>', unsafe_allow_html=True)

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
with tab_outputs:
    st.subheader("Weekly intelligence memo")
    memo_dir = ROOT / "outputs" / "memos"
    if memo_dir.exists():
        memos = sorted(memo_dir.glob("*.md"), reverse=True)
        if memos:
            pick = st.selectbox("Memo", [m.name for m in memos], index=0, key="memo_pick")
            st.markdown((memo_dir / pick).read_text(encoding="utf-8"))
        else:
            st.info("No memos yet. Run `python -m src.synthesize`.")
    else:
        st.info("No memos yet. Run `python -m src.synthesize`.")

    st.divider()

    # Per-opportunity artifacts grouped by output kind
    output_kinds = [
        ("Ad copy (Meta / Google / push)", ROOT / "outputs" / "copy"),
        ("SEO comparison-page briefs", ROOT / "outputs" / "seo"),
        ("Influencer / partner briefs", ROOT / "outputs" / "influencer"),
    ]
    for label, d in output_kinds:
        st.subheader(label)
        if d.exists():
            files = sorted(d.glob("*.md"), reverse=True)
            if files:
                pick = st.selectbox(label, [f.name for f in files], index=0, key=f"pick_{d.name}")
                st.markdown((d / pick).read_text(encoding="utf-8"))
            else:
                st.info(f"No files in `outputs/{d.name}/` yet.")
        else:
            st.info(f"`outputs/{d.name}/` does not exist yet.")
        st.divider()


# -------------- footer --------------
import os as _os
_gh = _os.getenv("GITHUB_REPO_URL", "https://github.com")
st.markdown(
    f"""
    <div class="footer">
      Defector · built for the Kinedu AI Challenge · May 2026 ·
      <a href="{_gh}" target="_blank">source on GitHub</a> ·
      data refreshed weekly via GitHub Actions
    </div>
    """,
    unsafe_allow_html=True,
)
