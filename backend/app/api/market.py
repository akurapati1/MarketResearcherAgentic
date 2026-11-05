from fastapi import APIRouter, HTTPException, Query

from ..data import indicators, market

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/overview")
async def overview():
    return await market.overview()


@router.get("/search")
async def search(q: str = Query(min_length=1, max_length=60)):
    return await market.search_symbols(q)


@router.get("/quote/{symbol}")
async def quote(symbol: str):
    try:
        return await market.get_quote(symbol)
    except market.MarketDataError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/history/{symbol}")
async def history(symbol: str, range: str = Query("1y", pattern="^(1mo|3mo|6mo|1y|2y|5y)$")):
    try:
        h = await market.get_history(symbol, range)
    except market.MarketDataError as exc:
        raise HTTPException(502, str(exc)) from exc
    closes = [b["c"] for b in h["bars"]]
    s20, s50 = indicators.sma(closes, 20), indicators.sma(closes, 50)
    series = [{**b, "sma20": s20[i], "sma50": s50[i]} for i, b in enumerate(h["bars"])]
    return {"quote": market.quote_from_history(h), "indicators": indicators.summarize(closes), "series": series}
