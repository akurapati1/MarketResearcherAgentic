"""Pure-python technical indicators (no numpy dependency)."""
from __future__ import annotations

import math
from statistics import pstdev


def sma(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= window:
            total -= values[i - window]
        out.append(total / window if i >= window - 1 else None)
    return out


def ema(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    k = 2 / (window + 1)
    prev: float | None = None
    for i, v in enumerate(values):
        if i < window - 1:
            out.append(None)
            continue
        prev = sum(values[:window]) / window if prev is None else v * k + prev * (1 - k)
        out.append(prev)
    return out


def rsi(values: list[float], window: int = 14) -> float | None:
    if len(values) <= window:
        return None
    gains = losses = 0.0
    for i in range(1, window + 1):
        d = values[i] - values[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    avg_g, avg_l = gains / window, losses / window
    for i in range(window + 1, len(values)):
        d = values[i] - values[i - 1]
        avg_g = (avg_g * (window - 1) + max(d, 0)) / window
        avg_l = (avg_l * (window - 1) + max(-d, 0)) / window
    if avg_l == 0:
        return 100.0
    return 100 - 100 / (1 + avg_g / avg_l)


def macd(values: list[float]) -> dict | None:
    e12, e26 = ema(values, 12), ema(values, 26)
    line = [a - b for a, b in zip(e12, e26) if a is not None and b is not None]
    if len(line) < 9:
        return None
    sig = ema(line, 9)
    if sig[-1] is None:
        return None
    return {"macd": line[-1], "signal": sig[-1], "histogram": line[-1] - sig[-1]}


def returns(values: list[float]) -> list[float]:
    return [values[i] / values[i - 1] - 1 for i in range(1, len(values)) if values[i - 1]]


def volatility_annualized(values: list[float]) -> float | None:
    r = returns(values)
    if len(r) < 5:
        return None
    return pstdev(r) * math.sqrt(252)


def max_drawdown(values: list[float]) -> float:
    peak, worst = float("-inf"), 0.0
    for v in values:
        peak = max(peak, v)
        if peak:
            worst = min(worst, v / peak - 1)
    return worst


def pct_change(values: list[float], lookback: int) -> float | None:
    if len(values) <= lookback or not values[-lookback - 1]:
        return None
    return values[-1] / values[-lookback - 1] - 1


def summarize(closes: list[float]) -> dict:
    """Condensed indicator snapshot used by the agents and the UI."""
    if not closes:
        return {}
    s20, s50, s200 = sma(closes, 20), sma(closes, 50), sma(closes, 200)
    m = macd(closes)
    last = closes[-1]
    hi, lo = max(closes[-252:]), min(closes[-252:])
    trend = "sideways"
    if s50[-1] and s200[-1]:
        trend = "uptrend" if last > s50[-1] > s200[-1] else "downtrend" if last < s50[-1] < s200[-1] else "sideways"
    elif s20[-1]:
        trend = "uptrend" if last > s20[-1] else "downtrend"
    return {
        "last": last,
        "sma20": s20[-1], "sma50": s50[-1], "sma200": s200[-1],
        "rsi14": rsi(closes),
        "macd": m,
        "volatility": volatility_annualized(closes),
        "max_drawdown": max_drawdown(closes),
        "return_1m": pct_change(closes, 21),
        "return_3m": pct_change(closes, 63),
        "return_6m": pct_change(closes, 126),
        "return_1y": pct_change(closes, 252),
        "high_52w": hi, "low_52w": lo,
        "pct_from_high": last / hi - 1 if hi else None,
        "trend": trend,
    }
