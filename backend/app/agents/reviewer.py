from __future__ import annotations

import json

from pydantic import ValidationError

from ..llm import LLMUnavailable, get_llm
from .context import ResearchContext
from .schemas import Review

SYSTEM = (
    "You are the Reviewer agent. Fact-check the draft against the supplied data, flag unsupported claims, "
    'overconfidence or missing caveats. Return JSON: {"issues":[str],"revised_summary":str (optional improved '
    "executive summary, or empty)}."
)


async def run_reviewer(ctx: ResearchContext) -> None:
    await ctx.emit("reviewer", "step", "Reviewing draft for unsupported claims and data quality")
    notes: list[str] = []
    llm = get_llm()
    if llm.available:
        try:
            payload = json.dumps({"summary": ctx.analysis.executive_summary, "findings": ctx.analysis.key_findings,
                                  "recommendation": ctx.analysis.recommendation.model_dump(),
                                  "sections": ctx.sections,
                                  "indicators": {k: v["indicators"] for k, v in ctx.snapshots.items()}}, default=str)
            review = Review.model_validate(await llm.generate_json(SYSTEM, payload))
            notes.extend(review.issues[:6])
            if review.revised_summary.strip():
                ctx.analysis.executive_summary = review.revised_summary.strip()
            ctx.engine_used.add(llm.name)
        except (LLMUnavailable, ValidationError):
            pass
    # deterministic checks always run
    if ctx.synthetic:
        notes.append("Price data is deterministic demo data, not a live feed — do not use for real decisions.")
    if not ctx.news:
        notes.append("No headlines were retrieved; sentiment signal is absent.")
    if ctx.analysis.recommendation.confidence > 75 and len(ctx.snapshots) < 2:
        ctx.analysis.recommendation.confidence = 75
        notes.append("Confidence capped at 75% because the view rests on a single instrument.")
    ctx.review_notes = notes
    await ctx.emit("reviewer", "log", f"Review complete: {len(notes)} note(s)")
