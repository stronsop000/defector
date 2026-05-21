"""One-shot helper: fill in missing play_store_id / app_store_id in apps.yaml
by searching both stores by name.

Usage:
    python -m scripts.resolve_app_ids                    # auto-pick top result for each
    python -m scripts.resolve_app_ids --interactive      # confirm each match
    python -m scripts.resolve_app_ids --dry-run          # show candidates, don't write
    python -m scripts.resolve_app_ids --only "Lovevery"  # only fill one app

Always review the diff in apps.yaml after running this — app store search is
noisy and the top result is occasionally wrong (e.g., a knockoff with a similar
name). For each filled-in ID, the script logs the resolved app's developer
name so you can sanity-check.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

import requests
from google_play_scraper import search as play_search

# Allow running as `python -m scripts.resolve_app_ids` from project root
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.config import App, load_apps, save_apps  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("resolve")

ITUNES_SEARCH = "https://itunes.apple.com/search"


def search_play(name: str) -> list[dict]:
    try:
        return play_search(name, lang="en", country="us", n_hits=5) or []
    except Exception as e:
        log.warning("Play search failed for %r: %s", name, e)
        return []


def search_apple(name: str) -> list[dict]:
    try:
        resp = requests.get(
            ITUNES_SEARCH,
            params={"term": name, "country": "us", "entity": "software", "limit": 5},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        log.warning("Apple search failed for %r: %s", name, e)
        return []


def pick(name: str, candidates: list[dict], key_label: str, key_id: str, interactive: bool) -> Optional[str]:
    if not candidates:
        return None
    if interactive:
        print(f"\n  Candidates for {name!r}:")
        for i, c in enumerate(candidates):
            print(f"    [{i}] {c[key_label]} — by {c.get('developer') or c.get('artistName')} ({c[key_id]})")
        choice = input("  Pick index (Enter to skip): ").strip()
        if not choice:
            return None
        try:
            return candidates[int(choice)][key_id]
        except (ValueError, IndexError):
            return None
    return candidates[0][key_id]


def resolve_one(app: App, interactive: bool) -> App:
    updated = app
    if not app.play_store_id:
        candidates = search_play(app.name)
        if candidates:
            top = candidates[0]
            chosen = pick(app.name, candidates, "title", "appId", interactive)
            if chosen:
                log.info("  Play : %-30s  %-40s  by %s", app.name, chosen, top.get("developer", "?"))
                updated = App(**{**updated.__dict__, "play_store_id": chosen})
            else:
                log.info("  Play : %-30s  (no match)", app.name)
        else:
            log.info("  Play : %-30s  (no results)", app.name)
    if not app.app_store_id:
        candidates = search_apple(app.name)
        if candidates:
            top = candidates[0]
            chosen = pick(app.name, candidates, "trackName", "trackId", interactive)
            if chosen:
                log.info("  Apple: %-30s  %-40s  by %s", app.name, chosen, top.get("artistName", "?"))
                updated = App(**{**updated.__dict__, "app_store_id": int(chosen)})
            else:
                log.info("  Apple: %-30s  (no match)", app.name)
        else:
            log.info("  Apple: %-30s  (no results)", app.name)
    return updated


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--interactive", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", help="Substring match on app name")
    args = p.parse_args()

    apps = load_apps()
    needle = args.only.lower() if args.only else None

    updated: list[App] = []
    for app in apps:
        if needle and needle not in app.name.lower():
            updated.append(app)
            continue
        if app.play_store_id and app.app_store_id:
            updated.append(app)
            continue
        log.info("Resolving %s …", app.name)
        updated.append(resolve_one(app, args.interactive))

    diffs = [
        (a.name, a.play_store_id, a.app_store_id)
        for a, b in zip(updated, apps)
        if a.play_store_id != b.play_store_id or a.app_store_id != b.app_store_id
    ]
    log.info("Resolved %d apps with new IDs", len(diffs))

    if args.dry_run:
        log.info("Dry run — not writing. Would update:\n%s", "\n".join(f"  {n}: play={p} apple={a}" for n, p, a in diffs))
        return

    save_apps(updated)
    log.info("Wrote config/apps.yaml")


if __name__ == "__main__":
    main()
