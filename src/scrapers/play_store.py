"""Google Play Store review scraper.

Uses the `google-play-scraper` library. Returns review dicts ready for db.upsert_reviews.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterator

from google_play_scraper import Sort, reviews
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import App, Market

log = logging.getLogger(__name__)

MAX_PER_REQUEST = 200  # Play Store API max per call
DEFAULT_CAP = 1000     # Stop after this many per app+market


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _fetch_page(play_store_id: str, lang: str, country: str, token, count: int):
    return reviews(
        play_store_id,
        lang=lang,
        country=country,
        sort=Sort.NEWEST,
        count=count,
        continuation_token=token,
    )


def scrape(app: App, market: Market, cap: int = DEFAULT_CAP) -> Iterator[dict]:
    """Yield review dicts for one (app, market). Idempotent at the DB layer
    via review_id — re-runs only add genuinely new reviews."""
    if not app.play_store_id:
        return
    fetched = 0
    token = None
    while fetched < cap:
        batch_size = min(MAX_PER_REQUEST, cap - fetched)
        try:
            batch, token = _fetch_page(app.play_store_id, market.lang, market.country, token, batch_size)
        except Exception as e:
            log.warning("Play scrape failed for %s @ %s/%s: %s", app.name, market.country, market.lang, e)
            return
        if not batch:
            return
        for r in batch:
            yield _to_row(r, app, market)
        fetched += len(batch)
        if token is None:
            return


def _to_row(r: dict, app: App, market: Market) -> dict:
    raw_id = r.get("reviewId") or f"{r.get('userName','?')}|{r.get('at')}"
    review_id = f"play:{app.play_store_id}:{market.country}:{raw_id}"
    at = r.get("at")
    return {
        "review_id": review_id,
        "store": "play",
        "app_name": app.name,
        "app_category": app.category,
        "country": market.country,
        "lang": market.lang,
        "rating": int(r.get("score") or 0),
        "title": None,  # Play Store reviews have no title field
        "body": (r.get("content") or "").strip(),
        "author": r.get("userName"),
        "review_date": at if isinstance(at, datetime) else None,
        "app_version": r.get("reviewCreatedVersion"),
    }
