"""Final synthesis specialist: turns scored, selected picks into the card copy
(catalyst paragraph, why-today reasoning, entry note, risk note) that the UI
renders. Scoring itself is already deterministic (data/scoring.py) — this
agent's job is narration only, in one batched call for all picks.
"""
from __future__ import annotations

import json
import logging

from agents.llm_utils import extract_json_array, run_text_agent
from agents.schemas import StockPick
from data.scoring import PREDICTION_TIER_LABELS

logger = logging.getLogger(__name__)

WRITER_SYSTEM_PROMPT = """You write the copy for an intraday India-stocks briefing card.
You will be given a JSON list of already-selected, already-scored stock picks. For each
pick, write four short fields:

- "catalyst_text": 1-2 sentences on what the deal/event/catalyst actually is, its size,
  and the counterparty, in your own words (never copy source text verbatim — at most one
  quote under 15 words).
- "why_today_text": 1-2 sentences on why this catalyst could move the stock TODAY
  specifically, referencing the ISS score breakdown given (catalyst/social/momentum/
  liquidity) and, if reversal_candidate is true, noting the prior downtrend explicitly.
- "entry_note": one short practical line, e.g. "Watch for a gap-up open above ₹X" or
  "Confirm volume before entry" — use the given price if useful, but never invent a
  specific target price beyond simple observations like "above today's open".
- "risk_note": one short line on what could go wrong intraday (e.g. profit booking,
  unconfirmed filing, thin liquidity, broader market weakness).

Rules (non-negotiable):
- Use probabilistic language: "likely to", "may", "could" — never "will surge" or
  "guaranteed". These are not certainties.
- If catalyst.confirmed is false, your why_today_text MUST note it's unconfirmed / social
  chatter only, not an exchange filing.
- Keep each field to one or two sentences, plain text, no markdown.

Respond with ONLY a JSON array, one object per pick, each with exactly these keys:
"ticker", "catalyst_text", "why_today_text", "entry_note", "risk_note".
No prose before or after, no markdown code fences.
"""


def _pick_to_prompt_dict(pick: StockPick) -> dict:
    return {
        "ticker": pick.ticker,
        "company": pick.company,
        "cap_tier": pick.cap_tier,
        "prediction_tier": PREDICTION_TIER_LABELS.get(pick.prediction_tier, pick.prediction_tier),
        "reversal_candidate": pick.reversal_candidate,
        "lower_conviction": pick.lower_conviction,
        "price": pick.market.price,
        "day_change_pct": pick.market.day_change_pct,
        "iss_total": pick.score.total,
        "iss_breakdown": {
            "catalyst": pick.score.catalyst,
            "social": pick.score.social,
            "momentum": pick.score.momentum,
            "liquidity": pick.score.liquidity,
        },
        "catalyst": {
            "catalyst_type": pick.catalyst.catalyst_type,
            "deal_size_cr": pick.catalyst.deal_size_cr,
            "counterparty": pick.catalyst.counterparty,
            "confirmed": pick.catalyst.confirmed,
            "summary": pick.catalyst.summary,
            "source_name": pick.catalyst.source_name,
        },
    }


def write_pick_copy(picks: list[StockPick]) -> list[StockPick]:
    """Mutates and returns `picks` with catalyst_text/why_today_text/entry_note/
    risk_note filled in. Falls back to the raw catalyst summary if the LLM call
    or JSON parsing fails, rather than leaving cards blank."""
    if not picks:
        return picks

    payload = json.dumps([_pick_to_prompt_dict(p) for p in picks], ensure_ascii=False, indent=2)
    text = run_text_agent(WRITER_SYSTEM_PROMPT, payload, effort="high")
    entries = extract_json_array(text)
    by_ticker = {str(e.get("ticker", "")).strip().upper(): e for e in entries}

    for pick in picks:
        entry = by_ticker.get(pick.ticker)
        if entry:
            pick.catalyst_text = str(entry.get("catalyst_text", "") or pick.catalyst.summary)
            pick.why_today_text = str(entry.get("why_today_text", ""))
            pick.entry_note = str(entry.get("entry_note", ""))
            pick.risk_note = str(entry.get("risk_note", ""))
        else:
            logger.warning("Writer agent produced no copy for %s; falling back to raw summary", pick.ticker)
            pick.catalyst_text = pick.catalyst.summary or "Catalyst details unavailable."
            pick.why_today_text = "Score breakdown suggests intraday relevance — verify before trading."
            pick.entry_note = "Verify price action and volume before entry."
            pick.risk_note = "Catalyst narration unavailable — treat with extra caution."
    return picks
