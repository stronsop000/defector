"""Classify low-star reviews into defection categories using Claude + tool forcing.

Usage:
    python -m src.classify                 # classify all unclassified 1-2 star reviews
    python -m src.classify --limit 50      # smoke test
    python -m src.classify --eval          # classify the eval set and print accuracy
    python -m src.classify --max-stars 3   # also include 3-star reviews

Idempotent: each review is classified at most once (PRIMARY KEY on classifications.review_id).
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

from tqdm import tqdm

from .config import load_taxonomy, ROOT
from .db import connect, unclassified_reviews
from .llm import DEFAULT_CLASSIFIER_MODEL, call_tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("classify")

EVAL_PATH = ROOT / "data" / "eval" / "labeled_sample.csv"


def build_system_blocks() -> list[dict]:
    """System prompt with taxonomy. Cached across all calls."""
    tax = load_taxonomy()
    rules = (
        "You are an analyst classifying app store reviews from parents about parenting and baby-product apps. "
        "Reviews can be POSITIVE (4-5★ praise), MIXED, or NEGATIVE (1-3★ complaints). For each review, return a "
        "single best-fit category (topic) from the taxonomy below, plus a sentiment direction, a short sub-reason, "
        "a churn-or-loyalty signal flag, a verbatim quote useful for marketing, and a confidence score.\n\n"
        "GUIDELINES:\n"
        "- The TAXONOMY is topic-neutral. The category names a TOPIC the review is about (price, content, bugs, etc.). "
        "  Whether the review is positive or negative is captured separately in the sentiment field. A 5★ review "
        "  raving about price-value still gets category_key='price_value' with sentiment='positive'.\n"
        "- Choose exactly one category. If the review touches multiple topics, pick the dominant one.\n"
        "- sub_reason: a 2-6 word phrase describing the specific point within the category. "
        "  Negative examples: 'paywall after trial', 'crash on iPhone 15', 'no offline mode'. "
        "  Positive examples: 'great onboarding flow', 'one-tap logging', 'cited research'.\n"
        "- sentiment: 'negative' for clear complaints, 'positive' for clear praise, 'mixed' when both appear meaningfully.\n"
        "- is_churn_signal: true only when the parent explicitly says they cancelled, uninstalled, switched, or won't come back. "
        "  For POSITIVE reviews, set this to true only when the parent says they switched TO this app FROM another one "
        "  (loyalty/acquisition signal). Implied loyalty alone is NOT a signal.\n"
        "- verbatim_quote: copy a 5-15 word phrase directly from the review that captures the point in the parent's own voice. "
        "  Keep the original language (do not translate). If nothing quotable, return an empty string.\n"
        "- confidence: 0.0-1.0. Lower it when the review is short, ambiguous, or doesn't clearly fit a category.\n"
        "- Reviews may be in English, Spanish, or Portuguese. Read fluently in all three.\n\n"
        "TAXONOMY (use the `key` value verbatim):\n"
    )
    for c in tax:
        examples = "\n      - ".join(c.examples)
        rules += f"\n- key: {c.key}\n  label: {c.label}\n  description: {c.description}\n  examples:\n      - {examples}\n"

    # Two blocks: the static rules (cached) + a fresh marker (not cached).
    return [
        {"type": "text", "text": rules, "cache_control": {"type": "ephemeral"}},
    ]


def build_tool() -> list[dict]:
    keys = [c.key for c in load_taxonomy()]
    return [
        {
            "name": "record_classification",
            "description": "Record the classification of a single review.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category_key": {"type": "string", "enum": keys},
                    "sub_reason": {"type": "string", "description": "2-6 word phrase"},
                    "sentiment": {"type": "string", "enum": ["negative", "mixed", "positive"]},
                    "is_churn_signal": {"type": "boolean"},
                    "verbatim_quote": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["category_key", "sub_reason", "sentiment", "is_churn_signal", "verbatim_quote", "confidence"],
            },
        }
    ]


def review_to_message(review: dict) -> list[dict]:
    parts = []
    if review.get("title"):
        parts.append(f"Title: {review['title']}")
    parts.append(f"Rating: {review['rating']}/5")
    parts.append(f"App: {review['app_name']} (category: {review['app_category']})")
    parts.append(f"Market: {review['country']}/{review['lang']}")
    parts.append("Review:")
    parts.append(review["body"])
    return [{"role": "user", "content": "\n".join(parts)}]


def classify_one(review: dict, system_blocks: list[dict], tools: list[dict], model: str) -> dict:
    result = call_tool(
        model=model,
        system=system_blocks,
        messages=review_to_message(review),
        tools=tools,
        tool_choice_name="record_classification",
        max_tokens=1024,
    )
    return result


def insert_classification(con, review_id: str, result: dict, model: str) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO classifications
            (review_id, category_key, sub_reason, sentiment, is_churn_signal, verbatim_quote, confidence, model)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review_id,
            result["category_key"],
            result.get("sub_reason"),
            result.get("sentiment"),
            bool(result.get("is_churn_signal")),
            result.get("verbatim_quote"),
            float(result.get("confidence", 0.0)),
            model,
        ),
    )


def run_eval(model: str) -> None:
    """Classify the labeled eval set and print accuracy."""
    if not EVAL_PATH.exists():
        log.error("Eval file not found: %s", EVAL_PATH)
        sys.exit(1)
    with open(EVAL_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        log.error("Eval file is empty.")
        sys.exit(1)
    system_blocks = build_system_blocks()
    tools = build_tool()
    correct = 0
    confusion: dict[tuple[str, str], int] = {}
    for r in tqdm(rows, desc="eval"):
        review_for_model = {
            "title": r.get("title") or None,
            "rating": int(r["rating"]),
            "app_name": r["app_name"],
            "app_category": r.get("app_category", "competitor"),
            "country": r.get("country", "us"),
            "lang": r.get("lang", "en"),
            "body": r["body"],
        }
        try:
            result = classify_one(review_for_model, system_blocks, tools, model)
        except Exception as e:
            log.warning("Eval row failed: %s", e)
            continue
        gold = r["expected_category_key"]
        pred = result["category_key"]
        if pred == gold:
            correct += 1
        confusion[(gold, pred)] = confusion.get((gold, pred), 0) + 1
    log.info("Eval accuracy: %d/%d = %.1f%%", correct, len(rows), 100 * correct / len(rows))
    log.info("Mismatches:")
    for (gold, pred), n in sorted(confusion.items()):
        if gold != pred:
            log.info("  gold=%-20s pred=%-20s n=%d", gold, pred, n)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--max-stars", type=int, default=5, help="Upper bound on star rating to classify. Default 5 = all reviews (positive + negative). Use 2 for negative-only.")
    p.add_argument("--min-stars", type=int, default=1, help="Lower bound on star rating. Default 1.")
    p.add_argument("--model", default=DEFAULT_CLASSIFIER_MODEL)
    p.add_argument("--eval", action="store_true", help="Run accuracy eval against data/eval/labeled_sample.csv")
    p.add_argument("--dry-run", action="store_true", help="Classify but do not write to DB")
    args = p.parse_args()

    if args.eval:
        run_eval(args.model)
        return

    con = connect()
    system_blocks = build_system_blocks()
    tools = build_tool()

    pending = unclassified_reviews(con, min_stars=args.min_stars, max_stars=args.max_stars, limit=args.limit)
    log.info("Classifying %d reviews with %s", len(pending), args.model)

    for review in tqdm(pending, desc="classify"):
        try:
            result = classify_one(review, system_blocks, tools, args.model)
        except Exception as e:
            log.warning("Failed review %s: %s", review["review_id"], e)
            continue
        if args.dry_run:
            log.info("[dry] %s → %s (%s)", review["review_id"][:60], result["category_key"], result.get("sub_reason"))
        else:
            insert_classification(con, review["review_id"], result, args.model)

    con.close()


if __name__ == "__main__":
    main()
