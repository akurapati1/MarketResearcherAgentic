"""News headlines via Google News RSS with a lexicon-based sentiment scorer."""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import httpx

from ..config import get_settings
from .cache import TTLCache

log = logging.getLogger(__name__)
_cache = TTLCache()

POSITIVE = {
    "surge", "surges", "soar", "soars", "beat", "beats", "record", "growth", "upgrade", "upgrades", "bullish",
    "rally", "gain", "gains", "profit", "profits", "strong", "expands", "partnership", "wins", "outperform",
    "breakthrough", "boost", "raises", "approval", "approved", "launch", "launches", "buyback", "dividend", "jumps",
}
NEGATIVE = {
    "plunge", "plunges", "miss", "misses", "downgrade", "downgrades", "bearish", "falls", "fall", "drop", "drops",
    "loss", "losses", "lawsuit", "probe", "investigation", "recall", "weak", "cuts", "layoffs", "slump", "warns",
    "warning", "fraud", "ban", "fine", "fined", "decline", "declines", "risk", "default", "bankruptcy", "tumbles",
}


def score_text(text: str) -> float:
    words = re.findall(r"[a-z']+", text.lower())
    pos = sum(w in POSITIVE for w in words)
    neg = sum(w in NEGATIVE for w in words)
    if pos == neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def _parse(xml_text: str, limit: int) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        source = (it.findtext("source") or "").strip()
        if source and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3]
        published = None
        try:
            published = parsedate_to_datetime(it.findtext("pubDate") or "").isoformat()
        except Exception:
            pass
        items.append({
            "title": title, "url": (it.findtext("link") or "").strip(),
            "source": source or "Google News", "published": published,
            "sentiment": round(score_text(title), 2),
        })
        if len(items) >= limit:
            break
    return items


async def fetch_news(query: str, limit: int = 10) -> list[dict]:
    if get_settings().market_data_mode == "synthetic":
        return []

    async def load() -> list[dict]:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        try:
            async with httpx.AsyncClient(timeout=get_settings().http_timeout_seconds, follow_redirects=True) as c:
                r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
            return _parse(r.text, limit)
        except Exception as exc:
            log.info("news fetch failed for %r: %s", query, exc)
            return []

    # Empty results are not cached long: build a short-lived entry only via the factory TTL.
    return await _cache.get_or_set(f"news:{query.lower()}:{limit}", get_settings().cache_ttl_seconds, load)
