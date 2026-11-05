from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..data import market
from ..db import get_session
from ..models import WatchlistItem
from ..schemas import WatchlistCreate, WatchlistOut

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistOut])
async def list_items(db: AsyncSession = Depends(get_session)):
    return (await db.execute(select(WatchlistItem).order_by(WatchlistItem.added_at))).scalars().all()


@router.get("/quotes")
async def quotes(db: AsyncSession = Depends(get_session)):
    items = (await db.execute(select(WatchlistItem).order_by(WatchlistItem.added_at))).scalars().all()
    q = {x["symbol"]: x for x in await market.get_quotes([i.symbol for i in items])}
    return [{"id": i.id, "symbol": i.symbol, "note": i.note, "added_at": i.added_at, "quote": q.get(i.symbol)}
            for i in items]


@router.post("", response_model=WatchlistOut, status_code=201)
async def add_item(body: WatchlistCreate, db: AsyncSession = Depends(get_session)):
    name = body.name
    if not name:
        try:
            name = (await market.get_quote(body.symbol))["name"]
        except market.MarketDataError:
            raise HTTPException(404, f"Unknown symbol {body.symbol}")
    item = WatchlistItem(symbol=body.symbol, name=name, note=body.note)
    db.add(item)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Already on watchlist")
    return item


@router.delete("/{symbol}", status_code=204)
async def remove_item(symbol: str, db: AsyncSession = Depends(get_session)):
    item = (await db.execute(select(WatchlistItem).where(WatchlistItem.symbol == symbol.upper()))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Not on watchlist")
    await db.delete(item)
    await db.commit()
