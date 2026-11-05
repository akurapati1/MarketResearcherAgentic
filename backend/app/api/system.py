from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..llm import get_llm
from ..models import ResearchJob, WatchlistItem

router = APIRouter(tags=["system"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_session)):
    await db.execute(select(1))
    return {"status": "ok"}


@router.get("/config")
async def config():
    s, llm = get_settings(), get_llm()
    return {"app": s.app_name, "llm": {"provider": llm.name, "enabled": llm.available},
            "market_data_mode": s.market_data_mode, "max_concurrent_jobs": s.max_concurrent_jobs,
            "auth_required": bool(s.api_key)}


@router.get("/dashboard/stats")
async def stats(db: AsyncSession = Depends(get_session)):
    counts = dict((await db.execute(select(ResearchJob.status, func.count()).group_by(ResearchJob.status))).all())
    since = datetime.now(timezone.utc) - timedelta(days=14)
    done = (await db.execute(select(ResearchJob).where(ResearchJob.status == "completed")
                             .order_by(ResearchJob.created_at.desc()).limit(200))).scalars().all()
    stance = {"Bullish": 0, "Neutral": 0, "Bearish": 0}
    per_day: dict[str, int] = {}
    for j in (await db.execute(select(ResearchJob.created_at).where(ResearchJob.created_at >= since))).scalars():
        d = j.date().isoformat()
        per_day[d] = per_day.get(d, 0) + 1
    for j in done:
        st = (j.report or {}).get("recommendation", {}).get("stance")
        if st in stance:
            stance[st] += 1
    days = [(since + timedelta(days=i + 1)).date().isoformat() for i in range(14)]
    watch = (await db.execute(select(func.count()).select_from(WatchlistItem))).scalar_one()
    return {
        "total": sum(counts.values()), "completed": counts.get("completed", 0), "running": counts.get("running", 0),
        "queued": counts.get("queued", 0), "failed": counts.get("failed", 0), "watchlist": watch,
        "stance": stance, "activity": [{"date": d, "count": per_day.get(d, 0)} for d in days],
    }
