"""Orchestrator: sequences the specialist agents, merges/dedupes catalyst
events by ticker, scores every candidate deterministically, selects the
final picks per cap tier, and drives the writer agent for card copy.

This is the single entrypoint the Streamlit UI calls.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from agents.filings_agent import run_filings_agent
from agents.news_agent import run_news_agent
from agents.schemas import CatalystEvent, MarketSnapshot, StockPick
from agents.social_agent import build_social_signals, search_reddit_mentions
from agents.writer_agent import write_pick_copy
from data.market_data import classify_cap_tier, get_market_snapshots
from data.scoring import compute_score, prediction_tier_from_score
from report.builder import CAP_TIERS, flatten_picks, select_picks

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]


def _noop(_: str) -> None:
    pass


SECTOR_KEYWORDS: dict[str, list[str]] = {
    "Defence": ["defence", "defense", "hal", "bharat electronics", "bharat dynamics", "mazagon", "shipbuilder"],
    "Pharma": ["pharma", "drug approval", "cdsco", "biotech", "healthcare", "hospital"],
    "IT": ["software", "it services", "information technology", "infosys", "tcs", "wipro", "saas"],
    "Power & Renewables": ["power", "renewable", "solar", "electricity", "transmission", "energy grid"],
    "Real Estate": ["real estate", "realty", "housing project", "construction", "residential"],
    "Railways": ["railway", " rail ", "irfc", "ircon", "rvnl", "metro rail"],
    "Banking & NBFC": ["bank", "nbfc", "financial services", "lending", "microfinance"],
    "Chemicals": ["chemical", "specialty chem", "petrochemical", "fertiliser", "fertilizer", "agrochemical"],
}

SPOTLIGHT_CATALYST_TYPES = {"qip", "block_deal", "fii_dii_buy", "promoter_buy"}


def _match_sectors(pick: StockPick) -> list[str]:
    haystack = " ".join(
        [pick.company or "", pick.catalyst.summary or "", pick.catalyst.catalyst_type or ""]
    ).lower()
    return [sector for sector, keywords in SECTOR_KEYWORDS.items() if any(k in haystack for k in keywords)]


def _sector_pulse(all_picks: list[StockPick]) -> dict[str, dict]:
    by_sector: dict[str, list[StockPick]] = {s: [] for s in SECTOR_KEYWORDS}
    for p in all_picks:
        for sector in _match_sectors(p):
            by_sector[sector].append(p)

    pulse: dict[str, dict] = {}
    for sector, picks in by_sector.items():
        if not picks:
            pulse[sector] = {"emoji": "⚪", "reason": "No notable catalysts today."}
            continue
        avg_score = sum(p.score.total for p in picks) / len(picks)
        if avg_score > 0:
            top = max(picks, key=lambda p: p.score.total)
            pulse[sector] = {"emoji": "🟢", "reason": f"{top.ticker}: {top.catalyst.summary or top.catalyst.catalyst_type}"}
        else:
            worst = min(picks, key=lambda p: p.score.total)
            pulse[sector] = {"emoji": "🔴", "reason": f"{worst.ticker}: {worst.catalyst.summary or worst.catalyst.catalyst_type}"}
    return pulse


def _small_cap_spotlight(all_picks: list[StockPick]) -> list[StockPick]:
    return [
        p for p in all_picks
        if p.cap_tier == "Small" and p.catalyst.catalyst_type in SPOTLIGHT_CATALYST_TYPES
    ]


def _merge_catalyst_events(events: list[CatalystEvent]) -> dict[str, CatalystEvent]:
    """Dedupes by ticker: prefers confirmed (exchange filing / named
    publication) over unconfirmed, then the larger stated deal size."""
    best: dict[str, CatalystEvent] = {}
    for e in events:
        if not e.ticker:
            continue
        current = best.get(e.ticker)
        if current is None:
            best[e.ticker] = e
            continue
        if e.confirmed and not current.confirmed:
            best[e.ticker] = e
        elif e.confirmed == current.confirmed:
            if (e.deal_size_cr or 0) > (current.deal_size_cr or 0):
                best[e.ticker] = e
    return best


@dataclass
class PipelineResult:
    generated_at: datetime
    by_tier: dict[str, list[StockPick]]
    all_picks: list[StockPick]
    sector_pulse: dict[str, dict]
    small_cap_spotlight: list[StockPick]

    @property
    def total_picks(self) -> int:
        return sum(len(v) for v in self.by_tier.values())

    @property
    def reversal_count(self) -> int:
        return sum(1 for p in flatten_picks(self.by_tier) if p.reversal_candidate)

    @property
    def fall_count(self) -> int:
        return sum(1 for p in flatten_picks(self.by_tier) if p.prediction_tier == "fall")

    @property
    def active_sectors(self) -> int:
        return sum(1 for v in self.sector_pulse.values() if v["emoji"] != "⚪")


def run_pipeline(on_progress: Optional[ProgressCallback] = None) -> PipelineResult:
    progress = on_progress or _noop

    progress("Scanning BSE/NSE exchange filings (ground truth)…")
    filings_events = run_filings_agent()

    progress("Scanning news for deal/catalyst signals…")
    news_events = run_news_agent()

    merged = _merge_catalyst_events(filings_events + news_events)
    tickers = list(merged.keys())

    if not tickers:
        empty_tier: dict[str, list[StockPick]] = {t: [] for t in CAP_TIERS}
        return PipelineResult(datetime.now(), empty_tier, [], {}, [])

    progress(f"Checking social buzz for {len(tickers)} tickers…")
    reddit_counts = search_reddit_mentions(tickers)
    social_signals = build_social_signals(list(merged.values()), reddit_counts)

    progress(f"Pulling market data for {len(tickers)} tickers…")
    market_snapshots = get_market_snapshots(tickers)

    progress("Scoring candidates against the ISS rubric…")
    all_picks: list[StockPick] = []
    for ticker, catalyst in merged.items():
        market = market_snapshots.get(ticker) or MarketSnapshot(ticker=ticker, data_available=False)
        cap_tier = classify_cap_tier(market.market_cap_cr)
        if cap_tier is None:
            logger.info("Skipping %s: no market cap data to classify cap tier", ticker)
            continue
        score = compute_score(catalyst, market, social_signals.get(ticker))
        tier = prediction_tier_from_score(score)
        if tier is None:
            continue  # catalyst too weak to qualify (Phase B5 minimum catalyst score)
        all_picks.append(
            StockPick(
                ticker=ticker,
                company=catalyst.company or ticker,
                cap_tier=cap_tier,
                catalyst=catalyst,
                market=market,
                score=score,
                prediction_tier=tier,
                reversal_candidate=bool(catalyst.prior_downtrend),
            )
        )

    progress("Selecting top 5 picks per cap tier…")
    by_tier = select_picks(all_picks)

    progress("Writing catalyst summaries…")
    write_pick_copy(flatten_picks(by_tier))

    sector_pulse = _sector_pulse(all_picks)
    small_cap_spotlight = _small_cap_spotlight(all_picks)

    progress("Done.")
    return PipelineResult(
        generated_at=datetime.now(),
        by_tier=by_tier,
        all_picks=all_picks,
        sector_pulse=sector_pulse,
        small_cap_spotlight=small_cap_spotlight,
    )
