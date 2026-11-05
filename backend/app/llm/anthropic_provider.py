import logging

from ..config import get_settings
from .base import LLMProvider, LLMUnavailable

log = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    available = True

    def __init__(self, api_key: str, model: str):
        from anthropic import AsyncAnthropic

        s = get_settings()
        self.name = model
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key, timeout=s.llm_timeout_seconds, max_retries=2)

    async def generate(self, system: str, prompt: str, max_tokens: int | None = None) -> str:
        try:
            msg = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or get_settings().llm_max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            log.warning("Anthropic call failed: %s", exc)
            raise LLMUnavailable(str(exc)) from exc
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
