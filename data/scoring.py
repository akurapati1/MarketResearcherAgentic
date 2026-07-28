"""Deterministic Intraday Signal Score (ISS) calculator.

Implements Phase B4 of the skill's rubric as pure lookup-table functions —
no LLM judgment involved, so results are reproducible and auditable against
docs/skill-reference/market-analysis-daily/SKILL.md.
"""
from __future__ import annotations

from typing import Optional

import config
from agents.schemas import CatalystEvent, MarketSnapshot, ScoreBreakdown, SocialSignal


def _size_meets(deal_size_cr: Optional[float], min_size_cr: Optional[float]) -> bool:
    if min_size_cr is None:
        return True
    if min_size_cr == 0:
        # Fallback row: matches regardless of size, including unknown size.
        return True
    if deal_size_cr is None:
        return False
    return deal_size_cr >= min_size_cr


def score_catalyst(catalyst: CatalystEvent) -> int:
    for cat_type, min_size, requires_confirmed, score in config.CATALYST_SCORE_TABLE:
        if catalyst.catalyst_type != cat_type:
            continue
        if requires_confirmed and not catalyst.confirmed:
            continue
        if not _size_meets(catalyst.deal_size_cr, min_size):
            continue
        return score
    return config.CATALYST_SCORE_DEFAULT


def score_negative_catalyst(catalyst_type: str) -> Optional[int]:
    return config.NEGATIVE_CATALYST_TABLE.get(catalyst_type)


def score_social(signal: Optional[SocialSignal]) -> int:
    if not signal or not signal.sources:
        return config.SOCIAL_SCORE_DEFAULT
    n = len(set(signal.sources))
    for threshold, score in config.SOCIAL_SCORE_THRESHOLDS:
        if n >= threshold:
            return score
    return config.SOCIAL_SCORE_DEFAULT


def score_momentum(market: MarketSnapshot, catalyst_score: int) -> int:
    if market.day_change_pct is not None and market.day_change_pct >= config.MOMENTUM_ALREADY_UP_DAY_CHANGE_PCT:
        return 4
    trend = market.trend_20d_pct
    if trend is None:
        return 0
    if -config.MOMENTUM_FLAT_BAND_PCT <= trend <= config.MOMENTUM_MILD_UPTREND_20D_PCT:
        return 3
    if trend > config.MOMENTUM_MILD_UPTREND_20D_PCT:
        return 2
    # trend < -MOMENTUM_FLAT_BAND_PCT: downtrend. Strong catalyst overrides trend
    # per the skill's "prior downtrend is NOT disqualifying" rule.
    if catalyst_score >= config.MOMENTUM_STRONG_CATALYST_MIN_SCORE:
        return 1
    return 0


def score_liquidity(market: MarketSnapshot, confirmed: bool) -> int:
    vol = market.avg_volume
    if vol is None:
        return 0
    if vol > config.LIQUIDITY_HIGH_VOLUME:
        return 3
    if vol >= config.LIQUIDITY_MEDIUM_VOLUME:
        return 2
    if confirmed:
        return 1
    return 0


def compute_score(
    catalyst: CatalystEvent,
    market: MarketSnapshot,
    social: Optional[SocialSignal] = None,
) -> ScoreBreakdown:
    neg = score_negative_catalyst(catalyst.catalyst_type)
    if neg is not None:
        return ScoreBreakdown(negative=neg)
    c = score_catalyst(catalyst)
    s = score_social(social)
    m = score_momentum(market, c)
    l = score_liquidity(market, catalyst.confirmed)
    return ScoreBreakdown(catalyst=c, social=s, momentum=m, liquidity=l)


def prediction_tier_from_score(score: ScoreBreakdown) -> Optional[str]:
    """Returns "surge" | "gain" | "watch" | "fall", or None if the pick doesn't
    qualify (catalyst too weak — Phase B5 minimum catalyst score is 4)."""
    if score.negative:
        return "fall"
    if score.catalyst < config.MIN_CATALYST_SCORE_FOR_PICK:
        return None
    total = score.total
    lo, hi = config.ISS_TIER_SURGE
    if lo <= total <= hi:
        return "surge"
    lo, hi = config.ISS_TIER_GAIN
    if lo <= total <= hi:
        return "gain"
    lo, hi = config.ISS_TIER_WATCH
    if lo <= total <= hi:
        return "watch"
    return None


PREDICTION_TIER_LABELS = {
    "surge": "🚀 >10% Intraday Surge Potential",
    "gain": "📈 >5% Intraday Gain Potential",
    "watch": "👀 Watch — Moderate Upside",
    "fall": "📉 Likely to Fall Today",
}
