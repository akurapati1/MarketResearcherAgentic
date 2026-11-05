from __future__ import annotations

import json

from pydantic import ValidationError

from ..llm import LLMUnavailable, get_llm
from .analyst import pct
from .context import ResearchContext
from .schemas import Draft

SYSTEM = (
    "You are the Writer agent of a market research team. Write a professional research brief in concise markdown "
    "from the analysis provided. Use only supplied facts. Return JSON: "
    '{"sections":[{"heading":str,"body":markdown str}]} with sections: Market Snapshot, Momentum & Technicals, '
    "News & Sentiment, Competitive/Thematic Context, Risks, Outlook & What to Watch."
)


def _heuristic(ctx: ResearchContext) -> Draft:
    a = ctx.analysis
    snap_lines = ["| Symbol | Price | 1D | 3M | 1Y | RSI | Trend |", "|---|---|---|---|---|---|---|"]
    for sym, s in ctx.snapshots.items():
        i, q = s["indicators"], s["quote"]
        rsi = f"{i['rsi14']:.0f}" if i.get("rsi14") is not None else "n/a"
        snap_lines.append(f"| {sym} | {q['price']:,} | {q['change_pct']:+.2f}% | {pct(i.get('return_3m'))} | "
                          f"{pct(i.get('return_1y'))} | {rsi} | {i.get('trend', 'n/a')} |")
    tech = []
    for sym, s in ctx.snapshots.items():
        i = s["indicators"]
        m = i.get("macd")
        tech.append(
            f"**{sym}** — 50-day avg {i['sma50']:,.2f}" if i.get("sma50") else f"**{sym}**"
        )
        bits = []
        if i.get("sma200"): bits.append(f"200-day {i['sma200']:,.2f}")
        if m: bits.append(f"MACD histogram {m['histogram']:+.2f}")
        bits.append(f"52-week range {i['low_52w']:,.2f} – {i['high_52w']:,.2f}")
        bits.append(f"volatility {i['volatility'] * 100:.0f}% annualised" if i.get("volatility") else "")
        tech[-1] += (", " if len(tech[-1]) > len(f"**{sym}**") else " — ") + ", ".join(b for b in bits if b) + "."
    news_body = "\n".join(f"- {n['title']} _({n['source']})_" for n in ctx.news[:8]) or \
        "_No live headlines were retrievable for this run._"
    risks = "\n".join(f"- **{r.title}** ({r.severity}): {r.detail}" for r in a.risks)
    watch = "\n".join(f"- {o}" for o in a.swot.opportunities[:4] + a.swot.threats[:3])
    sections = [
        {"heading": "Market Snapshot", "body": "\n".join(snap_lines) if ctx.snapshots else "_No instruments in scope._"},
        {"heading": "Momentum & Technicals", "body": "\n\n".join(tech) or "_Not applicable._"},
        {"heading": "News & Sentiment", "body": news_body},
        {"heading": "Risks", "body": risks},
        {"heading": "Outlook & What to Watch",
         "body": f"**{a.recommendation.stance}** over {a.recommendation.horizon} "
                 f"({a.recommendation.confidence}% confidence). {a.recommendation.rationale}\n\n{watch}"},
    ]
    return Draft.model_validate({"sections": sections})


async def run_writer(ctx: ResearchContext) -> None:
    await ctx.emit("writer", "step", "Writing research brief")
    draft: Draft | None = None
    llm = get_llm()
    if llm.available:
        try:
            payload = json.dumps({"analysis": ctx.analysis.model_dump(), "plan": ctx.plan.model_dump(),
                                  "headlines": [n["title"] for n in ctx.news[:10]],
                                  "instruments": {k: {"quote": v["quote"] | {"spark": None}, "indicators": v["indicators"]}
                                                  for k, v in ctx.snapshots.items()}}, default=str)
            draft = Draft.model_validate(await llm.generate_json(SYSTEM, payload))
            ctx.engine_used.add(llm.name)
        except (LLMUnavailable, ValidationError) as exc:
            await ctx.emit("writer", "log", f"LLM drafting unavailable ({type(exc).__name__}); using template writer")
    if draft is None or not draft.sections:
        draft = _heuristic(ctx)
        ctx.engine_used.add("heuristic")
    ctx.sections = [s.model_dump() for s in draft.sections]
    await ctx.emit("writer", "log", f"Drafted {len(ctx.sections)} sections")
