"""Tiny async TTL cache with in-flight de-duplication (thundering herd protection)."""
import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any


class TTLCache:
    def __init__(self, max_items: int = 2048):
        self._store: dict[str, tuple[float, Any]] = {}
        self._inflight: dict[str, asyncio.Future] = {}
        self._max = max_items

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        if item[0] < time.monotonic():
            self._store.pop(key, None)
            return None
        return item[1]

    def set(self, key: str, value: Any, ttl: float) -> None:
        if len(self._store) >= self._max:
            now = time.monotonic()
            for k in [k for k, (exp, _) in self._store.items() if exp < now]:
                self._store.pop(k, None)
            if len(self._store) >= self._max:
                self._store.pop(next(iter(self._store)))
        self._store[key] = (time.monotonic() + ttl, value)

    async def get_or_set(self, key: str, ttl: float, factory: Callable[[], Awaitable[Any]]) -> Any:
        hit = self.get(key)
        if hit is not None:
            return hit
        if key in self._inflight:
            return await asyncio.shield(self._inflight[key])
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._inflight[key] = fut
        try:
            value = await factory()
            self.set(key, value, ttl)
            fut.set_result(value)
            return value
        except Exception as exc:
            fut.set_exception(exc)
            fut.exception()  # mark retrieved
            raise
        finally:
            self._inflight.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
