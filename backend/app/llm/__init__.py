from functools import lru_cache

from ..config import get_settings
from .base import LLMProvider, LLMUnavailable


class NullProvider(LLMProvider):
    name = "heuristic"
    available = False

    async def generate(self, system: str, prompt: str, max_tokens: int | None = None) -> str:
        raise LLMUnavailable("no LLM configured")


@lru_cache
def get_llm() -> LLMProvider:
    s = get_settings()
    if s.anthropic_api_key:
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(s.anthropic_api_key, s.llm_model)
    return NullProvider()


__all__ = ["get_llm", "LLMProvider", "LLMUnavailable", "NullProvider"]
