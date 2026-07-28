"""yfinance wrappers for NSE-listed tickers: price, day-change%, market cap,
52-week range, average volume, and a 20-day momentum trend used by the ISS
Momentum sub-score. All lookups fail soft — a bad ticker or a yfinance outage
returns MarketSnapshot(data_available=False) rather than raising, per the
skill's rule: missing data shows "—", never a fabricated number."""
from __future__ import annotations

import logging

import yfinance as yf

import config
from agents.schemas import MarketSnapshot

logger = logging.getLogger(__name__)


def _nse_symbol(ticker: str) -> str:
    ticker = ticker.strip().upper()
    return ticker if ticker.endswith(".NS") else f"{ticker}.NS"


def get_market_snapshot(ticker: str) -> MarketSnapshot:
    symbol = _nse_symbol(ticker)
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="2mo")
        if hist.empty:
            return MarketSnapshot(ticker=ticker, data_available=False)

        price = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
        day_change_pct = ((price - prev_close) / prev_close * 100) if prev_close else None

        trend_20d_pct = None
        lookback = min(20, len(hist) - 1)
        if lookback >= 1:
            base = float(hist["Close"].iloc[-1 - lookback])
            trend_20d_pct = ((price - base) / base * 100) if base else None

        avg_volume = None
        if not hist["Volume"].empty:
            avg_volume = float(hist["Volume"].tail(20).mean())

        info = {}
        try:
            info = tk.get_info()
        except Exception:
            logger.warning("yfinance .info lookup failed for %s", symbol)

        market_cap = info.get("marketCap")
        market_cap_cr = (market_cap / 1e7) if market_cap else None

        return MarketSnapshot(
            ticker=ticker,
            price=price,
            day_change_pct=day_change_pct,
            market_cap_cr=market_cap_cr,
            avg_volume=avg_volume,
            trend_20d_pct=trend_20d_pct,
            week52_high=info.get("fiftyTwoWeekHigh"),
            week52_low=info.get("fiftyTwoWeekLow"),
            pe_ttm=info.get("trailingPE"),
            sector=info.get("sector"),
            data_available=True,
        )
    except Exception:
        logger.exception("Failed to fetch market data for %s", symbol)
        return MarketSnapshot(ticker=ticker, data_available=False)


def get_market_snapshots(tickers: list[str]) -> dict[str, MarketSnapshot]:
    return {t: get_market_snapshot(t) for t in dict.fromkeys(tickers)}


def classify_cap_tier(market_cap_cr: float | None) -> str | None:
    """Returns "Large" | "Mid" | "Small", or None if market cap is unknown."""
    if market_cap_cr is None:
        return None
    if market_cap_cr > config.LARGE_CAP_MIN_CR:
        return "Large"
    if market_cap_cr >= config.MID_CAP_MIN_CR:
        return "Mid"
    return "Small"
