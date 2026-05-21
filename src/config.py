"""Load + validate config files. Single source of truth for apps, markets, taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "reviews.duckdb"


@dataclass(frozen=True)
class App:
    name: str
    category: str
    play_store_id: Optional[str]
    app_store_id: Optional[int]
    notes: Optional[str] = None

    @property
    def slug(self) -> str:
        return self.name.lower().replace(" ", "_").replace("+", "plus")


@dataclass(frozen=True)
class Market:
    country: str
    lang: str
    name: str


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    description: str
    examples: list[str]


def load_apps() -> list[App]:
    with open(CONFIG_DIR / "apps.yaml", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return [App(**entry) for entry in raw["apps"]]


def load_markets() -> list[Market]:
    with open(CONFIG_DIR / "markets.yaml", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return [Market(**entry) for entry in raw["markets"]]


def load_taxonomy() -> list[Category]:
    with open(CONFIG_DIR / "taxonomy.yaml", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return [Category(**entry) for entry in raw["categories"]]


def save_apps(apps: list[App]) -> None:
    """Write back to apps.yaml. Used by scripts/resolve_app_ids.py."""
    payload = {
        "apps": [
            {
                "name": a.name,
                "category": a.category,
                "play_store_id": a.play_store_id,
                "app_store_id": a.app_store_id,
                **({"notes": a.notes} if a.notes else {}),
            }
            for a in apps
        ]
    }
    with open(CONFIG_DIR / "apps.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)
