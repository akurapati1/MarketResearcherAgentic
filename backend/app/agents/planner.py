from __future__ import annotations

import re

from pydantic import ValidationError

from ..data.symbols import BY_SYMBOL, resolve_names
from ..llm import LLMUnavailable, get_llm
from .context import ResearchContext
from .schemas import Plan

SYSTEM = (
    "You are the Planner agent of a market research team. Turn the user's request into a research plan. "
    'Return JSON: {"title": str, "tickers": [Yahoo Finance symbols, max 5], "questions": [3-6 sharp research '
    'questions], "news_queries": [1-3 news search queries]}.'
)


def _heuristic(ctx: ResearchContext) -> Plan:
    tickers = list(dict.fromkeys([*ctx.requested_tickers, *resolve_names(ctx.query)]))[:5]
    # explicit $TICKER mentions
    for m in re.findall(r"\$([A-Za-z.\-]{1,10})", ctx.query):
        if m.upper() not in tickers:
            tickers.append(m.upper())
    names = [BY_SYMBOL[t]["name"] if t in BY_SYMBOL else t for t in tickers]
    subject = ", ".join(names) if names else ctx.query.strip()[:80]
    qs = [
        f"What is the current price trend and momentum for {subject}?",
        f"What are the main catalysts and headwinds for {subject}?",
        f"How is market sentiment around {subject} evolving in recent news?",
        f"What are the key risks an investor should weigh for {subject}?",
    ]
    if len(tickers) > 1:
        qs.append("How do the selected instruments compare on returns, volatility and drawdown?")
    if ctx.depth == "deep":
        qs.append("What would change the thesis (invalidation triggers) and what should be monitored?")
    return Plan(
        title=f"{subject}: market research brief" if names else f"Market research: {subject}",
        tickers=tickers,
        questions=qs,
        news_queries=[f"{n} stock" for n in names[:3]] or [ctx.query.strip()[:100]],
    )


async def run_planner(ctx: ResearchContext) -> Plan:
    await ctx.emit("planner", "step", "Drafting research plan")
    plan: Plan | None = None
    llm = get_llm()
    if llm.available:
        try:
            data = await llm.generate_json(
                SYSTEM,
                f"Request: {ctx.query}\nUser-specified tickers: {ctx.requested_tickers or 'none'}\nDepth: {ctx.depth}",
                1024,
            )
            plan = Plan.model_validate(data)
            plan.tickers = list(dict.fromkeys([*ctx.requested_tickers, *plan.tickers]))[:5]
            ctx.engine_used.add(llm.name)
        except (LLMUnavailable, ValidationError) as exc:
            await ctx.emit("planner", "log", f"LLM planning unavailable ({type(exc).__name__}); using rule-based planner")
    if plan is None or not plan.questions:
        base = _heuristic(ctx)
        if plan:
            base.tickers = plan.tickers or base.tickers
            base.title = plan.title or base.title
        plan = base
        ctx.engine_used.add("heuristic")
    await ctx.emit(
        "planner", "log",
        f"Plan ready: {len(plan.questions)} questions, instruments: {', '.join(plan.tickers) or 'none (topic research)'}",
        {"plan": plan.model_dump()},
    )
    return plan
