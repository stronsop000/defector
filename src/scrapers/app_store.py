"""Apple App Store review scraper via the iTunes RSS feed.

The RSS feed is public, returns JSON, and requires no auth. Limitations:
  - Max ~500 most-recent reviews per (app, country)
  - Some country/app combos return empty or 404 — that's fine, we skip
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterator

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import App, Market

log = logging.getLogger(__name__)

RSS_URL = (
    "https://itunes.apple.com/{country}/rss/customerreviews/"
    "id={app_id}/sortBy=mostRecent/page={page}/json"
)
MAX_PAGES = 10  # Apple caps at 10
HTTP_TIMEOUT = 20


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _fetch_page(app_id: int, country: str, page: int) -> dict:
    url = RSS_URL.format(country=country.lower(), app_id=app_id, page=page)
    resp = requests.get(url, timeout=HTTP_TIMEOUT, headers={"User-Agent": "defector/1.0"})
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json()


def scrape(app: App, market: Market) -> Iterator[dict]:
    if not app.app_store_id:
        return
    for page in range(1, MAX_PAGES + 1):
        try:
            payload = _fetch_page(app.app_store_id, market.country, page)
        except Exception as e:
            log.warning("Apple scrape failed for %s @ %s p%d: %s", app.name, market.country, page, e)
            return
        entries = (payload.get("feed") or {}).get("entry") or []
        # Page 1 includes the app metadata as the first entry; skip it.
        if page == 1 and entries and "im:name" in entries[0]:
            entries = entries[1:]
        if not entries:
            return
        for e in entries:
            row = _to_row(e, app, market)
            if row:
                yield row


def _to_row(e: dict, app: App, market: Market) -> dict | None:
    try:
        native_id = e.get("id", {}).get("label")
        if not native_id:
            return None
        review_id = f"apple:{app.app_store_id}:{market.country}:{native_id}"
        rating = int(e.get("im:rating", {}).get("label", 0))
        title = (e.get("title", {}).get("label") or "").strip() or None
        body = (e.get("content", {}).get("label") or "").strip()
        author = (e.get("author", {}).get("name", {}).get("label") or "").strip() or None
        version = e.get("im:version", {}).get("label")
        updated = e.get("updated", {}).get("label")
        review_date = None
        if updated:
            try:
                review_date = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except ValueError:
                review_date = None
        return {
            "review_id": review_id,
            "store": "apple",
            "app_name": app.name,
            "app_category": app.category,
            "country": market.country,
            "lang": market.lang,
            "rating": rating,
            "title": title,
            "body": body,
            "author": author,
            "review_date": review_date,
            "app_version": version,
        }
    except Exception as exc:
        log.warning("Could not parse Apple review entry: %s", exc)
        return None
