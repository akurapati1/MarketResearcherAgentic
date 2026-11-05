from __future__ import annotations

import json

from pydantic import ValidationError

from ..llm import LLMUnavailable, get_llm
from .context import ResearchContext
from .schemas import Analysis, Recommendation, Risk, Swot

SYSTEM = (
    "You are the Analyst agent of a market research team. Using ONLY the data provided, produce a rigorous, "
    "balanced analysis. Do not invent figures. Return JSON: "
    '{"executive_summary": str (3-5 sentences), "key_findings": [4-7 short strings with numbers], '
    '"swot": {"strengths":[],"weaknesses":[],"opportunities":[],"threats":[]}, '
    '"risks": [{"title":str,"severity":"low|medium|high","detail":str}], '
    '"recommendation": {"stance":"Bullish|Neutral|Bearish","confidence":0-100,"horizon":str,"rationale":str}}. '
    "This is research, not personalised financial advice."
)


def pct(x: float | None, digits: int = 1) -> str:
    return "n/a" if x is None else f"{x * 100:+.{digits}f}%"


def score_instrument(ind: dict, news_sent: float) -> tuple[float, list[str]]:
    """Composite score in [-1, 1] with human-readable drivers."""
    score, why = 0.0, []
    trend = ind.get("trend")
    if trend == "uptrend":
        score += 0.30; why.append("price above rising 50/200-day averages")
    elif trend == "downtrend":
        score -= 0.30; why.append("price below falling 50/200-day averages")
    r = ind.get("rsi14")
    if r is not None:
        if r > 70:
            score -= 0.10; why.append(f"RSI {r:.0f} signals overbought conditions")
        elif r < 30:
            score += 0.10; why.append(f"RSI {r:.0f} signals oversold conditions")
        elif r > 55:
            score += 0.08
        elif r < 45:
            score -= 0.08
    m = ind.get("macd")
    if m:
        score += 0.12 if m["histogram"] > 0 else -0.12
        why.append("MACD histogram positive" if m["histogram"] > 0 else "MACD histogram negative")
    r3 = ind.get("return_3m")
    if r3 is not None:
        score += max(-0.2, min(0.2, r3 * 1.2))
    score += max(-0.15, min(0.15, news_sent * 0.3))
    return max(-1.0, min(1.0, score)), why


def stance_for(score: float) -> str:
    return "Bullish" if score > 0.2 else "Bearish" if score < -0.2 else "Neutral"


def news_sentiment(news: list[dict]) -> dict:
    pos = sum(1 for n in news if n["sentiment"] > 0.15)
    neg = sum(1 for n in news if n["sentiment"] < -0.15)
    neu = len(news) - pos - neg
    avg = sum(n["sentiment"] for n in news) / len(news) if news else 0.0
    label = "Positive" if avg > 0.15 else "Negative" if avg < -0.15 else "Neutral"
    return {"score": round(avg, 2), "label": label, "positive": pos, "negative": neg, "neutral": neu,
            "count": len(news)}


def _heuristic(ctx: ResearchContext, scores: dict[str, tuple[float, list[str]]], sent: dict) -> Analysis:
    findings, strengths, weaknesses, opps, threats, risks = [], [], [], [], [], []
    for sym, snap in ctx.snapshots.items():
        ind, q = snap["indicators"], snap["quote"]
        findings.append(f"{sym} trades at {q['price']:,} {q['currency']} ({q['change_pct']:+.2f}% last session); "
                        f"3M return {pct(ind.get('return_3m'))}, 1Y return {pct(ind.get('return_1y'))}.")
        if ind.get("trend") == "uptrend":
            strengths.append(f"{sym}: sustained uptrend with price above the 50- and 200-day averages")
        elif ind.get("trend") == "downtrend":
            weaknesses.append(f"{sym}: confirmed downtrend below key moving averages")
        if (ind.get("return_1y") or 0) > 0.15:
            strengths.append(f"{sym}: strong 12-month performance ({pct(ind['return_1y'])})")
        if (ind.get("return_3m") or 0) < -0.08:
            weaknesses.append(f"{sym}: negative 3-month momentum ({pct(ind['return_3m'])})")
        if ind.get("rsi14") is not None and ind["rsi14"] < 35:
            opps.append(f"{sym}: oversold RSI ({ind['rsi14']:.0f}) may attract mean-reversion buyers")
        if ind.get("rsi14") is not None and ind["rsi14"] > 68:
            threats.append(f"{sym}: stretched RSI ({ind['rsi14']:.0f}) raises pullback risk")
        if (ind.get("pct_from_high") or 0) > -0.05:
            opps.append(f"{sym}: trading near 52-week high — breakout continuation possible")
        elif (ind.get("pct_from_high") or 0) < -0.25:
            weaknesses.append(f"{sym}: {abs(ind['pct_from_high']) * 100:.0f}% below its 52-week high")
        vol = ind.get("volatility")
        if vol is not None:
            sev = "high" if vol > 0.45 else "medium" if vol > 0.25 else "low"
            risks.append(Risk(title=f"{sym} volatility", severity=sev,
                              detail=f"Annualised volatility {vol * 100:.0f}%; worst drawdown over the window "
                                     f"{ind['max_drawdown'] * 100:.0f}%."))
    if sent["count"]:
        findings.append(f"News tone is {sent['label'].lower()} ({sent['positive']} positive / {sent['negative']} "
                        f"negative of {sent['count']} headlines).")
        (strengths if sent["score"] > 0.15 else threats if sent["score"] < -0.15 else opps).append(
            f"Headline sentiment is {sent['label'].lower()} (score {sent['score']:+.2f})")
    if len(ctx.snapshots) > 1:
        best = max(ctx.snapshots, key=lambda s: ctx.snapshots[s]["indicators"].get("return_3m") or -9)
        findings.append(f"{best} leads the group on 3-month momentum.")
    if not ctx.snapshots:
        findings.append("No tradable instruments were identified; this brief is based on news flow only.")
        threats.append("Without instrument-level data, conclusions are qualitative")
    threats.append("Macro shocks (rates, inflation, geopolitics) can override company-specific signals")
    opps.append("Earnings and guidance updates are the next scheduled catalysts to monitor")

    avg = sum(s for s, _ in scores.values()) / len(scores) if scores else sent["score"] * 0.5
    stance = stance_for(avg)
    drivers = [f"{sym}: {w}" for sym, (_, ws) in scores.items() for w in ws][:4]
    conf = int(min(85, 40 + abs(avg) * 60 + (10 if len(ctx.snapshots) else -15)))
    names = ", ".join(ctx.snapshots) or "the subject"
    summary = (
        f"Quantitative signals for {names} are {stance.lower()} (composite score {avg:+.2f}). "
        + (f"Key drivers: {'; '.join(drivers)}. " if drivers else "")
        + f"News flow reads {sent['label'].lower()}. "
        "Treat this as a screening-level view; confirm with fundamentals before acting."
    )
    return Analysis(
        executive_summary=summary, key_findings=findings[:7],
        swot=Swot(strengths=strengths[:5] or ["No standout strengths in the available data"],
                  weaknesses=weaknesses[:5] or ["No material weaknesses flagged by technical screens"],
                  opportunities=opps[:5], threats=threats[:5]),
        risks=risks[:6] + [Risk(title="Model limitation", severity="low",
                                detail="Signals are technical/news-derived; fundamentals are not scored.")],
        recommendation=Recommendation(
            stance=stance, confidence=conf, horizon="1-3 months" if ctx.depth == "quick" else "3-6 months",
            rationale=f"Composite of trend, RSI, MACD, 3-month momentum and headline tone ({avg:+.2f})."),
    )


def _llm_payload(ctx: ResearchContext, scores: dict, sent: dict) -> str:
    slim = {
        sym: {"quote": {k: s["quote"][k] for k in ("price", "change_pct", "currency", "as_of")},
              "indicators": s["indicators"], "composite_score": round(scores[sym][0], 2)}
        for sym, s in ctx.snapshots.items()
    }
    return json.dumps({
        "request": ctx.query, "questions": ctx.plan.questions, "instruments": slim,
        "headlines": [{"title": n["title"], "source": n["source"], "sentiment": n["sentiment"]} for n in ctx.news],
        "news_sentiment": sent,
        "data_quality": "synthetic demo data" if ctx.synthetic else "live market data",
    }, default=str)


async def run_analyst(ctx: ResearchContext) -> dict:
    await ctx.emit("analyst", "step", "Analysing price action, indicators and news tone")
    sent = news_sentiment(ctx.news)
    scores = {sym: score_instrument(s["indicators"], sent["score"]) for sym, s in ctx.snapshots.items()}
    for sym, (sc, _) in scores.items():
        await ctx.emit("analyst", "log", f"{sym}: composite score {sc:+.2f} → {stance_for(sc)}")

    analysis: Analysis | None = None
    llm = get_llm()
    if llm.available:
        try:
            data = await llm.generate_json(SYSTEM, _llm_payload(ctx, scores, sent))
            analysis = Analysis.model_validate(data)
            ctx.engine_used.add(llm.name)
        except (LLMUnavailable, ValidationError) as exc:
            await ctx.emit("analyst", "log", f"LLM analysis unavailable ({type(exc).__name__}); using rule-based analysis")
    if analysis is None:
        analysis = _heuristic(ctx, scores, sent)
        ctx.engine_used.add("heuristic")
    ctx.analysis = analysis
    await ctx.emit("analyst", "log", f"Recommendation: {analysis.recommendation.stance} "
                                      f"({analysis.recommendation.confidence}% confidence)")
    return {"scores": {k: round(v[0], 3) for k, v in scores.items()}, "sentiment": sent}
