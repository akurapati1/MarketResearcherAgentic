from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

Emit = Callable[..., Awaitable[None]]


@dataclass
class ResearchContext:
    query: str
    depth: str
    requested_tickers: list[str]
    emit: Emit
    plan: Any = None
    snapshots: dict[str, dict] = field(default_factory=dict)
    news: list[dict] = field(default_factory=list)
    analysis: Any = None
    sections: list[dict] = field(default_factory=list)
    review_notes: list[str] = field(default_factory=list)
    engine_used: set[str] = field(default_factory=set)

    @property
    def synthetic(self) -> bool:
        return any(s["quote"]["source"] == "synthetic" for s in self.snapshots.values())
