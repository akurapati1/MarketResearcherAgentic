from __future__ import annotations

import asyncio

from ..data import market, news
from .context import ResearchContext


async def run_collector(ctx: ResearchContext) -> None:
    plan = ctx.plan
    await ctx.emit("collector", "step", f"Collecting data for {len(plan.tickers)} instrument(s) and news")

    async def one(sym: str) -> None:
        try:
            ctx.snapshots[sym] = await market.snapshot(sym)
            q = ctx.snapshots[sym]["quote"]
            await ctx.emit("collector", "log", f"{sym}: {q['price']} ({q['change_pct']:+.2f}%) via {q['source']}")
        except Exception as exc:
            await ctx.emit("collector", "log", f"{sym}: market data failed ({exc})")

    async def headlines() -> None:
        queries = plan.news_queries or [ctx.query]
        batches = await asyncio.gather(*(news.fetch_news(q, 8) for q in queries[:3]))
        seen, merged = set(), []
        for item in (i for b in batches for i in b):
            if item["title"] not in seen:
                seen.add(item["title"])
                merged.append(item)
        ctx.news = merged[:15]
        await ctx.emit("collector", "log", f"Fetched {len(ctx.news)} headline(s)" if ctx.news
                       else "No live headlines available (offline or no coverage)")

    await asyncio.gather(headlines(), *(one(t) for t in plan.tickers))
    if ctx.synthetic:
        await ctx.emit("collector", "log", "Using deterministic demo price data (live market feed unreachable)")
