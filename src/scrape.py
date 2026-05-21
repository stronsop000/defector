"""Scrape every (app, market) pair into reviews.duckdb.

Usage:
    python -m src.scrape                    # full run
    python -m src.scrape --app Kinedu       # one app, all markets
    python -m src.scrape --country br       # all apps, one market
    python -m src.scrape --dry-run          # no DB writes; just count

Idempotent: re-running is safe; only genuinely new reviews are inserted.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Iterable

from tqdm import tqdm

from .config import App, Market, load_apps, load_markets
from .db import connect, upsert_reviews
from .scrapers import app_store, play_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("scrape")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", help="Filter to one app name (case-insensitive substring match)")
    p.add_argument("--country", help="Filter to one country code (e.g. us, br, mx)")
    p.add_argument("--category", help="Filter to one category (competitor, brand_product, ...)")
    p.add_argument("--cap", type=int, default=1000, help="Max reviews per (app, market, store). Default 1000.")
    p.add_argument("--dry-run", action="store_true", help="Don't write to DB, just count")
    p.add_argument("--throttle", type=float, default=1.0, help="Sleep seconds between (app, market) pairs. Default 1.")
    return p.parse_args()


def filter_apps(apps: list[App], args) -> list[App]:
    out = apps
    if args.app:
        needle = args.app.lower()
        out = [a for a in out if needle in a.name.lower()]
    if args.category:
        out = [a for a in out if a.category == args.category]
    if not out:
        log.error("No apps matched filters.")
        sys.exit(1)
    return out


def filter_markets(markets: list[Market], args) -> list[Market]:
    if args.country:
        return [m for m in markets if m.country == args.country.lower()]
    return markets


def scrape_pair(app: App, market: Market, cap: int) -> list[dict]:
    rows = []
    if app.play_store_id:
        rows.extend(play_store.scrape(app, market, cap=cap))
    if app.app_store_id:
        rows.extend(app_store.scrape(app, market))
    return rows


def main() -> None:
    args = parse_args()
    apps = filter_apps(load_apps(), args)
    markets = filter_markets(load_markets(), args)

    # Warn about apps without resolved IDs.
    unresolved = [a for a in apps if not a.play_store_id and not a.app_store_id]
    if unresolved:
        log.warning(
            "%d apps have no store IDs yet (run scripts/resolve_app_ids.py): %s",
            len(unresolved),
            ", ".join(a.name for a in unresolved),
        )

    con = None if args.dry_run else connect()
    total_new = 0
    pairs = [(a, m) for a in apps for m in markets if a.play_store_id or a.app_store_id]
    pbar = tqdm(pairs, desc="scraping", unit="pair")
    for app, market in pbar:
        pbar.set_postfix_str(f"{app.name} @ {market.country}/{market.lang}")
        try:
            rows = scrape_pair(app, market, args.cap)
        except Exception as e:
            log.exception("Failed pair %s @ %s: %s", app.name, market.country, e)
            continue
        if args.dry_run:
            log.info("[dry] %s @ %s/%s: %d reviews", app.name, market.country, market.lang, len(rows))
        else:
            new = upsert_reviews(con, rows)
            total_new += new
            log.info("%s @ %s/%s: %d fetched, %d new", app.name, market.country, market.lang, len(rows), new)
        time.sleep(args.throttle)

    if con is not None:
        con.close()
    log.info("Done. %d new reviews inserted.", total_new)


if __name__ == "__main__":
    main()
