"""DuckDB schema + helpers. Single embedded file at data/reviews.duckdb."""

from __future__ import annotations

import duckdb

from .config import DATA_DIR, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id      VARCHAR PRIMARY KEY,    -- store_prefix + native id; deterministic so re-runs are idempotent
    store          VARCHAR NOT NULL,       -- 'play' | 'apple'
    app_name       VARCHAR NOT NULL,
    app_category   VARCHAR NOT NULL,
    country        VARCHAR NOT NULL,
    lang           VARCHAR NOT NULL,
    rating         INTEGER NOT NULL,
    title          VARCHAR,
    body           VARCHAR NOT NULL,
    author         VARCHAR,
    review_date    TIMESTAMP,
    app_version    VARCHAR,
    scraped_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reviews_app      ON reviews(app_name);
CREATE INDEX IF NOT EXISTS idx_reviews_market   ON reviews(country, lang);
CREATE INDEX IF NOT EXISTS idx_reviews_rating   ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_date     ON reviews(review_date);

CREATE TABLE IF NOT EXISTS classifications (
    review_id        VARCHAR PRIMARY KEY,
    category_key     VARCHAR NOT NULL,        -- taxonomy.yaml key
    sub_reason       VARCHAR,                  -- free-form short phrase from the model
    sentiment        VARCHAR,                  -- 'negative' | 'mixed' | 'positive'
    is_churn_signal  BOOLEAN,                  -- explicit "I'm leaving / cancelled / switching" language
    verbatim_quote   VARCHAR,                  -- short verbatim snippet useful for ads
    confidence       DOUBLE,                   -- 0.0 - 1.0 self-reported by the model
    model            VARCHAR NOT NULL,
    classified_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(review_id)
);

CREATE INDEX IF NOT EXISTS idx_class_category   ON classifications(category_key);
CREATE INDEX IF NOT EXISTS idx_class_churn      ON classifications(is_churn_signal);
"""


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open the DB. If `read_only`, opens a shared connection that can
    coexist with the Streamlit dashboard (which also opens read-only).

    Write-mode (`read_only=False`) requires exclusive access — Streamlit
    must be stopped first, or the open will fail with 'file is already
    open in another process'.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=read_only)
    if not read_only:
        con.execute(SCHEMA)
    return con


def upsert_reviews(con: duckdb.DuckDBPyConnection, rows: list[dict]) -> int:
    """Insert reviews idempotently. Returns count of newly-inserted rows.

    Uses INSERT OR IGNORE — re-running the scraper for the same app/market
    is a no-op for already-seen reviews.
    """
    if not rows:
        return 0
    before = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    con.executemany(
        """
        INSERT OR IGNORE INTO reviews
            (review_id, store, app_name, app_category, country, lang,
             rating, title, body, author, review_date, app_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r["review_id"],
                r["store"],
                r["app_name"],
                r["app_category"],
                r["country"],
                r["lang"],
                r["rating"],
                r.get("title"),
                r["body"],
                r.get("author"),
                r.get("review_date"),
                r.get("app_version"),
            )
            for r in rows
        ],
    )
    after = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    return after - before


def unclassified_reviews(
    con: duckdb.DuckDBPyConnection,
    max_stars: int = 5,
    min_stars: int = 1,
    limit: int | None = None,
) -> list[dict]:
    """Fetch reviews that haven't been classified yet.

    By default returns ALL star ratings — the classifier handles both
    positive (5★ praise) and negative (1★ complaints) reviews and labels
    each with a sentiment field. Use --max-stars 2 (CLI) for negative-only
    runs.
    """
    sql = f"""
        SELECT r.review_id, r.app_name, r.app_category, r.country, r.lang,
               r.rating, r.title, r.body, r.review_date
        FROM reviews r
        LEFT JOIN classifications c ON r.review_id = c.review_id
        WHERE c.review_id IS NULL
          AND r.rating BETWEEN {min_stars} AND {max_stars}
        ORDER BY r.review_date DESC NULLS LAST
        {f"LIMIT {limit}" if limit else ""}
    """
    return [dict(row) for row in con.execute(sql).fetchdf().to_dict("records")]


# Backwards-compat shim — synonym kept so older callers don't break.
unclassified_low_star_reviews = unclassified_reviews
