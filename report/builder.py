"""Phase B5 selection: exactly 5 picks per cap tier (or fewer, flagged
"lower conviction" — never padded with fabricated candidates), at least one
reversal candidate per tier where available, no repeated tickers across
tiers, and a minimum-fall-prediction target distributed by cap tier.
"""
from __future__ import annotations

import config
from agents.schemas import StockPick

CAP_TIERS = ["Large", "Mid", "Small"]


def select_picks(all_picks: list[StockPick]) -> dict[str, list[StockPick]]:
    """Returns {"Large": [...], "Mid": [...], "Small": [...]}, each up to
    config.PICKS_PER_TIER picks, sorted by ISS descending within the tier."""
    by_tier: dict[str, list[StockPick]] = {t: [] for t in CAP_TIERS}
    used_tickers: set[str] = set()

    positive = [p for p in all_picks if p.prediction_tier in ("surge", "gain", "watch")]
    fall = [p for p in all_picks if p.prediction_tier == "fall"]

    for tier in CAP_TIERS:
        candidates = sorted(
            (p for p in positive if p.cap_tier == tier and p.ticker not in used_tickers),
            key=lambda p: p.score.total,
            reverse=True,
        )
        selected = candidates[: config.PICKS_PER_TIER]

        # Guarantee at least one 🔄 reversal candidate per tier when one exists.
        if selected and not any(p.reversal_candidate for p in selected):
            reversal = next((p for p in candidates if p.reversal_candidate), None)
            if reversal is not None:
                if len(selected) >= config.PICKS_PER_TIER:
                    selected[-1] = reversal
                else:
                    selected.append(reversal)

        if 0 < len(selected) < config.PICKS_PER_TIER:
            for p in selected:
                p.lower_conviction = True

        used_tickers.update(p.ticker for p in selected)
        by_tier[tier] = selected

    # Distribute "likely to fall" predictions across tiers, most severe first,
    # aiming for the skill's minimum fall-prediction target without exceeding
    # PICKS_PER_TIER per tier or repeating a ticker.
    fall_sorted = sorted(fall, key=lambda p: p.score.total)  # most negative first
    fall_count = 0
    for p in fall_sorted:
        if fall_count >= config.MIN_FALL_PREDICTIONS_TARGET:
            break
        if p.ticker in used_tickers or p.cap_tier not in by_tier:
            continue
        if len(by_tier[p.cap_tier]) >= config.PICKS_PER_TIER:
            continue
        by_tier[p.cap_tier].append(p)
        used_tickers.add(p.ticker)
        fall_count += 1

    return by_tier


def flatten_picks(by_tier: dict[str, list[StockPick]]) -> list[StockPick]:
    return [p for tier in CAP_TIERS for p in by_tier[tier]]
