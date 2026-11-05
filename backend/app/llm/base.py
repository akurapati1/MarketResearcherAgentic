import json
import re
from abc import ABC, abstractmethod


class LLMUnavailable(Exception):
    """Raised when no LLM is configured or a call fails; callers fall back to heuristics."""


class LLMProvider(ABC):
    name: str = "none"
    available: bool = False

    @abstractmethod
    async def generate(self, system: str, prompt: str, max_tokens: int | None = None) -> str: ...

    async def generate_json(self, system: str, prompt: str, max_tokens: int | None = None) -> dict:
        text = await self.generate(
            system + "\nRespond with a single valid JSON object only. No markdown fences, no commentary.",
            prompt, max_tokens,
        )
        return extract_json(text)


def extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise LLMUnavailable("model returned no JSON object")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMUnavailable(f"invalid JSON from model: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMUnavailable("model JSON was not an object")
    return data
