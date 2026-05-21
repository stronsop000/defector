"""Securely set the Gemini (or Anthropic) API key in .env.

Run this from the project root:
    python -m scripts.set_api_key

Behavior:
  - Prompts for the key with input hidden (uses getpass — characters don't
    echo to the terminal).
  - Writes/updates the key in defector/.env (creates the file if missing,
    preserves any other keys already there).
  - Makes one tiny test call to verify the key works.
  - .env is gitignored so the key never leaves this machine.

Defaults to Gemini. Pass --provider anthropic to set ANTHROPIC_API_KEY instead.
"""

from __future__ import annotations

import argparse
import getpass
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def read_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    pairs: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        pairs[k.strip()] = v.strip()
    return pairs


def write_env(pairs: dict[str, str]) -> None:
    # Preserve a friendly header
    lines = [
        "# Defector env — gitignored. Never commit this file.",
        "# Get a free Gemini key at https://aistudio.google.com/apikey",
        "",
    ]
    for k, v in pairs.items():
        lines.append(f"{k}={v}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def looks_valid(provider: str, key: str) -> tuple[bool, str]:
    if not key:
        return False, "empty key"
    if provider == "gemini":
        if not key.startswith("AIza"):
            return False, "Gemini keys normally start with 'AIza'."
        if len(key) < 30:
            return False, f"key looks too short ({len(key)} chars)."
    elif provider == "anthropic":
        if not key.startswith("sk-ant-"):
            return False, "Anthropic keys start with 'sk-ant-'."
    return True, ""


def test_gemini(key: str) -> tuple[bool, str]:
    """One tiny generation call. Returns (ok, message)."""
    try:
        from google import genai
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=["Reply with the single word: ok"],
        )
        text = (resp.text or "").strip().lower()
        if "ok" in text:
            return True, f"Gemini reply: {text[:40]!r}"
        return True, f"key works (unexpected reply: {text[:40]!r})"
    except Exception as e:
        msg = str(e)
        # Surface the most actionable bit
        m = re.search(r"(API key not valid|PERMISSION_DENIED|UNAUTHENTICATED|quota|rate)", msg, re.I)
        if m:
            return False, f"{m.group(0)} — {msg[:200]}"
        return False, msg[:300]


def test_anthropic(key: str) -> tuple[bool, str]:
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=20,
            messages=[{"role": "user", "content": "Reply with the single word: ok"}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip().lower()
        return True, f"Anthropic reply: {text[:40]!r}"
    except Exception as e:
        return False, str(e)[:300]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--provider", choices=["gemini", "anthropic"], default="gemini")
    args = p.parse_args()

    env_var = "GEMINI_API_KEY" if args.provider == "gemini" else "ANTHROPIC_API_KEY"
    where = "https://aistudio.google.com/apikey" if args.provider == "gemini" else "https://console.anthropic.com/settings/keys"

    print(f"\nThis sets {env_var} in {ENV_PATH}")
    print(f"Get a key at: {where}\n")
    print("Your input will be HIDDEN — characters won't show as you type/paste.")
    print("If your terminal doesn't support hidden input you'll see a warning.\n")

    try:
        key = getpass.getpass(f"Paste {env_var} (input hidden, then Enter): ").strip()
    except KeyboardInterrupt:
        print("\nAborted.")
        return 1
    if not key:
        print("No key entered. Aborted.")
        return 1

    ok, reason = looks_valid(args.provider, key)
    if not ok:
        print(f"⚠  That doesn't look like a valid {args.provider} key — {reason}")
        confirm = input("Continue anyway? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 1

    pairs = read_env()
    pairs[env_var] = key
    write_env(pairs)
    print(f"✓ Wrote {env_var} to {ENV_PATH} ({len(key)} chars)")

    print(f"Testing {args.provider} with a 1-token call …")
    test_fn = test_gemini if args.provider == "gemini" else test_anthropic
    ok, msg = test_fn(key)
    if ok:
        print(f"✓ Key works. {msg}")
        return 0
    print(f"✗ Test call failed: {msg}")
    print("\nThe key was still saved to .env in case you want to debug. If the")
    print("error mentions 'API key not valid', double-check you copied the whole")
    print("string. To overwrite, just re-run this script.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
