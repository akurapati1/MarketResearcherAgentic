"""Market data service: Yahoo Finance (live) with deterministic synthetic fallback."""
from __future__ import annotations

import hashlib
import logging
import math
import random
from datetime import datetime, timedelta, timezone

import httpx

from ..config import get_settings
from .cache import TTLCache
from .indicators import summarize
from .symbols import BY_SYMBOL, OVERVIEW_SYMBOLS, search_catalog

log = logging.getLogger(__name__)
_cache = TTLCache()
_YAHOO = "https://query1.finance.yahoo.com"
_UA = {"User-Agent": "Mozilla/5.0 (compatible; MarketResearcherAgentic/1.0)"}

RANGES = {"1mo": 22, "3mo": 66, "6mo": 132, "1y": 252, "2y": 504, "5y": 1260}


class MarketDataError(Exception):
    pass


def _seed(symbol: str) -> random.Random:
    return random.Random(int(hashlib.sha256(symbol.encode()).hexdigest()[:12], 16))


def _synthetic_history(symbol: str, days: int) -> dict:
    """Deterministic geometric-random-walk series so the product works fully offline."""
    meta = BY_SYMBOL.get(symbol.upper())
    base = meta["base"] if meta else 20 + (int(hashlib.md5(symbol.encode()).hexdigest()[:4], 16) % 400)
    rng = _seed(symbol)
    drift = rng.uniform(-0.0001, 0.0006)
    vol = rng.uniform(0.007, 0.017) if not symbol.startswith("^") else rng.uniform(0.004, 0.011)
    # Walk backwards from "today" so the latest bar is anchored near base price.
    n = days + 1
    shocks = [rng.gauss(drift, vol) for _ in range(n)]
    prices = [base]
    for s in reversed(shocks[1:]):
        prices.append(prices[-1] / (1 + s))
    prices.reverse()
    today = datetime.now(timezone.utc).date()
    dates, bars = [], []
    d = today
    cal = []
    while len(cal) < n:
        if d.weekday() < 5 or symbol.endswith("-USD"):
            cal.append(d)
        d -= timedelta(days=1)
    cal.reverse()
    for dt, p in zip(cal, prices):
        spread = p * rng.uniform(0.002, 0.012)
        o, c = p * (1 + rng.uniform(-0.004, 0.004)), p
        bars.append({
            "t": dt.isoformat(), "o": round(o, 2), "h": round(max(o, c) + spread, 2),
            "l": round(min(o, c) - spread, 2), "c": round(c, 2),
            "v": int(rng.uniform(0.6, 1.6) * 5_000_000 * (1 + math.sin(len(bars) / 9) * 0.3)),
        })
        dates.append(dt)
    return {"symbol": symbol.upper(), "name": meta["name"] if meta else symbol.upper(),
            "currency": "USD", "source": "synthetic", "bars": bars}


async def _live_history(symbol: str, rng: str) -> dict:
    s = get_settings()
    url = f"{_YAHOO}/v8/finance/chart/{symbol}"
    async with httpx.AsyncClient(timeout=s.http_timeout_seconds, headers=_UA) as client:
        r = await client.get(url, params={"range": rng, "interval": "1d"})
        r.raise_for_status()
        payload = r.json()
    res = (payload.get("chart", {}).get("result") or [None])[0]
    if not res:
        raise MarketDataError(f"No data for {symbol}")
    q = res["indicators"]["quote"][0]
    bars = []
    for i, ts in enumerate(res.get("timestamp", [])):
        c = q["close"][i]
        if c is None:
            continue
        bars.append({
            "t": datetime.fromtimestamp(ts, timezone.utc).date().isoformat(),
            "o": round(q["open"][i] or c, 2), "h": round(q["high"][i] or c, 2),
            "l": round(q["low"][i] or c, 2), "c": round(c, 2), "v": int(q["volume"][i] or 0),
        })
    meta = res.get("meta", {})
    return {"symbol": symbol.upper(), "name": meta.get("longName") or meta.get("shortName") or symbol.upper(),
            "currency": meta.get("currency", "USD"), "source": "yahoo", "bars": bars}


async def get_history(symbol: str, rng: str = "1y") -> dict:
    symbol = symbol.upper().strip()
    if rng not in RANGES:
        rng = "1y"
    mode = get_settings().market_data_mode

    async def load() -> dict:
        if mode != "synthetic":
            try:
                data = await _live_history(symbol, rng)
                if data["bars"]:
                    return data
            except Exception as exc:  # network, 404, parse…
                if mode == "live":
                    raise MarketDataError(f"Live data unavailable for {symbol}: {exc}") from exc
                log.info("live market data failed for %s (%s); using synthetic", symbol, exc)
        return _synthetic_history(symbol, RANGES[rng])

    return await _cache.get_or_set(f"hist:{symbol}:{rng}", get_settings().cache_ttl_seconds, load)


def quote_from_history(h: dict) -> dict:
    bars = h["bars"]
    last = bars[-1]["c"]
    prev = bars[-2]["c"] if len(bars) > 1 else last
    return {
        "symbol": h["symbol"], "name": h["name"], "currency": h["currency"], "source": h["source"],
        "price": last, "change": round(last - prev, 4),
        "change_pct": round((last / prev - 1) * 100, 3) if prev else 0.0,
        "volume": bars[-1]["v"], "as_of": bars[-1]["t"],
        "spark": [b["c"] for b in bars[-40:]],
    }


async def get_quote(symbol: str) -> dict:
    return quote_from_history(await get_history(symbol, "3mo"))


async def get_quotes(symbols: list[str]) -> list[dict]:
    import asyncio

    results = await asyncio.gather(*(get_quote(s) for s in symbols), return_exceptions=True)
    return [r for r in results if isinstance(r, dict)]


async def overview() -> list[dict]:
    return await get_quotes(OVERVIEW_SYMBOLS)


async def snapshot(symbol: str) -> dict:
    """Everything an agent needs about one instrument: quote + indicators + trimmed series."""
    h = await get_history(symbol, "1y")
    closes = [b["c"] for b in h["bars"]]
    return {"quote": quote_from_history(h), "indicators": summarize(closes), "bars": h["bars"]}


async def search_symbols(q: str) -> list[dict]:
    local = search_catalog(q)
    if get_settings().market_data_mode == "synthetic" or len(q.strip()) < 2:
        return local

    async def load() -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=get_settings().http_timeout_seconds, headers=_UA) as client:
                r = await client.get(f"{_YAHOO}/v1/finance/search", params={"q": q, "quotesCount": 8, "newsCount": 0})
                r.raise_for_status()
            live = [{"symbol": x["symbol"], "name": x.get("longname") or x.get("shortname") or x["symbol"],
                     "sector": x.get("sector") or x.get("typeDisp", "")}
                    for x in r.json().get("quotes", []) if x.get("symbol")]
        except Exception:
            live = []
        seen, merged = set(), []
        for item in live + local:
            if item["symbol"] not in seen:
                seen.add(item["symbol"])
                merged.append(item)
        return merged[:8]

    return await _cache.get_or_set(f"search:{q.lower()}", 600, load)
