"""Shared data structures passed between specialist agents, the scoring engine,
and the UI. Catalyst/filing events are parsed from LLM JSON output with tolerant
defaults — never trust the model to emit every field."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

# Catalyst types the search/filings agents are instructed to use — must match
# config.CATALYST_SCORE_TABLE and config.NEGATIVE_CATALYST_TABLE exactly.
POSITIVE_CATALYST_TYPES = [
    "deal", "order", "approval", "result_beat_major", "qip", "block_deal",
    "fii_dii_buy", "result_beat_minor", "promoter_buy", "analyst_upgrade",
    "mou", "social_buzz",
]
NEGATIVE_CATALYST_TYPES = [
    "earnings_miss_major", "regulatory_action", "deal_cancellation",
    "promoter_pledge_or_insider_sell", "analyst_downgrade",
    "negative_news_social_pileup",
]

CATALYST_EVENT_JSON_SCHEMA_DESCRIPTION = f"""\
Each object in the JSON array must have exactly these fields:
- "ticker": NSE symbol, e.g. "RELIANCE" (no .NS suffix)
- "company": full company name
- "catalyst_type": one of {POSITIVE_CATALYST_TYPES + NEGATIVE_CATALYST_TYPES}
- "deal_size_cr": deal/order size in INR crore as a number, or null if not mentioned
- "counterparty": counterparty name, or null
- "confirmed": true only if this appears in a BSE/NSE exchange filing or a named
  news publication (Economic Times, Moneycontrol, LiveMint, Business Standard,
  CNBCTV18, Financial Express, bseindia.com, nseindia.com). false if social-media-only.
- "prior_downtrend": true if the stock has been in a multi-week downtrend before
  today's catalyst (a 🔄 reversal candidate), false otherwise, null if unknown
- "summary": one-sentence paraphrase IN YOUR OWN WORDS of the catalyst — never copy
  article text verbatim, at most one quote under 15 words
- "source_url": the article or filing URL
- "source_name": publication or exchange name
"""


def _safe_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


@dataclass
class CatalystEvent:
    ticker: str
    company: str = ""
    catalyst_type: str = "social_buzz"
    deal_size_cr: Optional[float] = None
    counterparty: Optional[str] = None
    confirmed: bool = False
    prior_downtrend: Optional[bool] = None
    summary: str = ""
    source_url: str = ""
    source_name: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "CatalystEvent":
        ticker = str(d.get("ticker", "")).strip().upper()
        return cls(
            ticker=ticker,
            company=str(d.get("company", "") or ""),
            catalyst_type=str(d.get("catalyst_type", "social_buzz") or "social_buzz"),
            deal_size_cr=_safe_float(d.get("deal_size_cr")),
            counterparty=d.get("counterparty") or None,
            confirmed=bool(d.get("confirmed", False)),
            prior_downtrend=d.get("prior_downtrend"),
            summary=str(d.get("summary", "") or ""),
            source_url=str(d.get("source_url", "") or ""),
            source_name=str(d.get("source_name", "") or ""),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SocialSignal:
    ticker: str
    mention_count: int = 0
    sources: list = field(default_factory=list)  # e.g. ["reddit", "news:ET", "news:Moneycontrol"]


@dataclass
class MarketSnapshot:
    ticker: str
    price: Optional[float] = None
    day_change_pct: Optional[float] = None
    market_cap_cr: Optional[float] = None
    avg_volume: Optional[float] = None
    trend_20d_pct: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None
    pe_ttm: Optional[float] = None
    sector: Optional[str] = None
    data_available: bool = True


@dataclass
class ScoreBreakdown:
    catalyst: int = 0
    social: int = 0
    momentum: int = 0
    liquidity: int = 0
    negative: int = 0  # negative catalyst penalty, 0 if none

    @property
    def total(self) -> int:
        if self.negative:
            return self.negative  # negative overrides positive composition
        return self.catalyst + self.social + self.momentum + self.liquidity


@dataclass
class StockPick:
    ticker: str
    company: str
    cap_tier: str  # "Large" | "Mid" | "Small"
    catalyst: CatalystEvent
    market: MarketSnapshot
    score: ScoreBreakdown
    prediction_tier: str = ""  # "surge" | "gain" | "watch" | "fall"
    reversal_candidate: bool = False
    lower_conviction: bool = False
    catalyst_text: str = ""
    why_today_text: str = ""
    entry_note: str = ""
    risk_note: str = ""
