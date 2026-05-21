"""Pluggable LLM layer. Default backend: Gemini 2.5 Flash on Google AI Studio
(free tier, no credit card). Anthropic Claude is also supported if
ANTHROPIC_API_KEY is set and LLM_PROVIDER is set to 'anthropic'.

Exports two functions that the rest of the codebase calls:
  - call_tool(...) -> dict          : forces a JSON-structured response.
                                       Used by the classifier.
  - call_text(...) -> str           : plain markdown/text generation.
                                       Used by the synthesizer + copy generator.

The function signatures stay the same regardless of provider so the rest of
the codebase doesn't change when you switch backends.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Optional

from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()

log = logging.getLogger(__name__)


# ============ Pacing ============
# Gemini Flash free tier is ~10 RPM. Pace at ~8 RPM by default to leave
# headroom for occasional retries. Override with REQUESTS_PER_MINUTE.

_REQ_PER_MIN = float(os.getenv("REQUESTS_PER_MINUTE", "8"))
_MIN_INTERVAL = 60.0 / max(_REQ_PER_MIN, 0.1)
_pace_lock = threading.Lock()
_last_call_at = 0.0


def _throttle() -> None:
    """Block until enough time has elapsed since the previous LLM call."""
    global _last_call_at
    with _pace_lock:
        wait = _MIN_INTERVAL - (time.monotonic() - _last_call_at)
        if wait > 0:
            time.sleep(wait)
        _last_call_at = time.monotonic()


# ============ Provider selection ============

def _resolve_provider() -> str:
    """Pick a backend. Explicit LLM_PROVIDER wins, otherwise auto-detect by key."""
    explicit = os.getenv("LLM_PROVIDER")
    if explicit:
        return explicit.lower()
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "gemini"  # default; will raise on first call if no key set


PROVIDER = _resolve_provider()

DEFAULT_CLASSIFIER_MODEL = os.getenv(
    "CLASSIFIER_MODEL",
    "gemini-2.5-flash" if PROVIDER == "gemini" else "claude-sonnet-4-6",
)
DEFAULT_SYNTHESIZER_MODEL = os.getenv(
    "SYNTHESIZER_MODEL",
    "gemini-2.5-flash" if PROVIDER == "gemini" else "claude-opus-4-7",
)


# ============ Gemini backend ============

_gemini_client = None


def _gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai  # imported lazily to keep startup fast

        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/apikey "
                "and add it to defector/.env"
            )
        _gemini_client = genai.Client(api_key=key)
    return _gemini_client


def _gemini_call_tool(model: str, system: str, messages: list[dict], tool: dict, max_tokens: int) -> dict:
    """Gemini's equivalent of forced tool-call: use JSON mode with a schema."""
    from google.genai import types

    user_text = "\n\n".join(m["content"] for m in messages if m["role"] == "user")
    schema = tool["input_schema"]

    resp = _gemini().models.generate_content(
        model=model,
        contents=[user_text],
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=_to_gemini_schema(schema),
            max_output_tokens=max_tokens,
            temperature=0.2,
        ),
    )
    text = resp.text or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        log.warning("Gemini returned non-JSON; attempting to repair. Raw: %r", text[:400])
        # Try to extract the first JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise RuntimeError(f"Gemini did not return JSON: {e}") from e


def _to_gemini_schema(schema: dict) -> dict:
    """Pass-through; Anthropic/JSON Schema and Gemini's response_schema are
    compatible for the small object shape we use. Keeping this as a hook
    in case we need to adjust later."""
    # Gemini doesn't allow `additionalProperties` in its OpenAPI subset.
    cleaned = {k: v for k, v in schema.items() if k != "additionalProperties"}
    if "properties" in cleaned:
        cleaned["properties"] = {
            k: _to_gemini_schema(v) if isinstance(v, dict) else v
            for k, v in cleaned["properties"].items()
        }
    return cleaned


def _gemini_call_text(model: str, system: str, messages: list[dict], max_tokens: int) -> str:
    from google.genai import types

    user_text = "\n\n".join(m["content"] for m in messages if m["role"] == "user")
    resp = _gemini().models.generate_content(
        model=model,
        contents=[user_text],
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=0.5,
        ),
    )
    return resp.text or ""


# ============ Anthropic backend ============

_anthropic_client = None


def _anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic

        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set.")
        _anthropic_client = Anthropic(api_key=key)
    return _anthropic_client


def _anthropic_call_tool(model: str, system: str, messages: list[dict], tool: dict, max_tokens: int) -> dict:
    resp = _anthropic().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return block.input  # type: ignore[return-value]
    raise RuntimeError(f"Anthropic did not return tool_use for {tool['name']!r}.")


def _anthropic_call_text(model: str, system: str, messages: list[dict], max_tokens: int) -> str:
    resp = _anthropic().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
    )
    return "".join(b.text for b in resp.content if b.type == "text")


# ============ Public API ============

def _system_to_text(system) -> str:
    """Accept either a plain string or the Anthropic-style block list."""
    if isinstance(system, str):
        return system
    return "\n\n".join(b["text"] for b in system if isinstance(b, dict) and "text" in b)


@retry(
    stop=stop_after_attempt(8),
    wait=wait_exponential(min=4, max=120),
    retry=retry_if_exception_type(Exception),
)
def call_tool(*, model: str, system, messages: list[dict], tools: list[dict], tool_choice_name: str, max_tokens: int = 2048) -> dict[str, Any]:
    """Force a JSON-structured response matching the tool's input_schema."""
    tool = next((t for t in tools if t["name"] == tool_choice_name), tools[0])
    sys_text = _system_to_text(system)
    _throttle()
    if PROVIDER == "gemini":
        return _gemini_call_tool(model, sys_text, messages, tool, max_tokens)
    return _anthropic_call_tool(model, sys_text, messages, tool, max_tokens)


@retry(
    stop=stop_after_attempt(8),
    wait=wait_exponential(min=4, max=120),
    retry=retry_if_exception_type(Exception),
)
def call_text(*, model: str, system, messages: list[dict], max_tokens: int = 4096) -> str:
    """Plain text response."""
    sys_text = _system_to_text(system)
    _throttle()
    if PROVIDER == "gemini":
        return _gemini_call_text(model, sys_text, messages, max_tokens)
    return _anthropic_call_text(model, sys_text, messages, max_tokens)
