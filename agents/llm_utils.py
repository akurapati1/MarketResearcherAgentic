"""Shared Claude API helpers for the specialist agents.

`web_search_20260209` is a server-side tool: the model searches autonomously
within one request and returns a final text response with search results
interleaved — no client-side tool_result round trip is needed. The only loop
we handle is `pause_turn` (the server tool's internal 10-call cap), which we
resume automatically per shared/tool-use-concepts.md.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

import config

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def run_search_agent(
    system: str,
    user_message: str,
    max_uses: int = 10,
    effort: str = "medium",
    max_tokens: int = 8000,
) -> str:
    """Runs one Claude call with the web_search tool and returns the final
    text response (concatenated across text blocks). Auto-resumes on
    pause_turn. Returns "" on any API failure — callers must handle that as
    "no results found", not crash the whole pipeline (Minimum Viable Run rule)."""
    client = get_client()
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": max_uses}]

    response = None
    for _ in range(3):
        try:
            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=max_tokens,
                system=system,
                tools=tools,
                thinking={"type": "adaptive"},
                output_config={"effort": effort},
                messages=messages,
            )
        except Exception:
            logger.exception("Claude search-agent call failed")
            return ""
        if response.stop_reason == "pause_turn":
            messages = messages + [{"role": "assistant", "content": response.content}]
            continue
        break

    if response is None:
        return ""
    return "\n".join(b.text for b in response.content if b.type == "text")


def run_text_agent(
    system: str,
    user_message: str,
    effort: str = "high",
    max_tokens: int = 8000,
) -> str:
    """A plain (no-tool) Claude call for synthesis/narration steps."""
    client = get_client()
    try:
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception:
        logger.exception("Claude text-agent call failed")
        return ""
    return "\n".join(b.text for b in response.content if b.type == "text")


def extract_json_array(text: str) -> list[dict]:
    """Tolerantly extracts a JSON array from LLM output that may contain
    surrounding prose or markdown fences."""
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fence_match:
        try:
            data = json.loads(fence_match.group(1))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    start, end = text.find("["), text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    logger.warning("Could not extract a JSON array from LLM response (len=%d)", len(text))
    return []
