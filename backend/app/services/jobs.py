"""DB-backed job queue. Workers atomically claim queued jobs, so any number of API replicas can share one DB."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from ..agents.orchestrator import execute_job
from ..config import get_settings
from ..db import session_factory
from ..models import ResearchJob

log = logging.getLogger(__name__)
STALE_AFTER = timedelta(minutes=10)


class JobRunner:
    def __init__(self) -> None:
        self._wake = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        self._stopping = False

    async def start(self) -> None:
        self._stopping = False
        self._wake = asyncio.Event()
        await self._requeue_stale()
        n = get_settings().max_concurrent_jobs
        self._tasks = [asyncio.create_task(self._worker(i), name=f"job-worker-{i}") for i in range(n)]
        log.info("started %d job workers", n)

    async def stop(self) -> None:
        self._stopping = True
        self._wake.set()
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    def notify(self) -> None:
        self._wake.set()

    async def _requeue_stale(self) -> None:
        cutoff = datetime.now(timezone.utc) - STALE_AFTER
        async with session_factory()() as s:
            await s.execute(update(ResearchJob).where(
                ResearchJob.status == "running", ResearchJob.updated_at < cutoff).values(status="queued", progress=0))
            await s.commit()

    async def _claim(self) -> ResearchJob | None:
        async with session_factory()() as s:
            cid = (await s.execute(select(ResearchJob.id).where(ResearchJob.status == "queued")
                                   .order_by(ResearchJob.created_at).limit(1))).scalar_one_or_none()
            if cid is None:
                return None
            res = await s.execute(update(ResearchJob).where(ResearchJob.id == cid, ResearchJob.status == "queued")
                                  .values(status="running", stage="starting",
                                          updated_at=datetime.now(timezone.utc)))
            await s.commit()
            if res.rowcount != 1:  # another worker won the race
                return None
            return await s.get(ResearchJob, cid)

    async def _worker(self, idx: int) -> None:
        while not self._stopping:
            try:
                job = await self._claim()
                if job is None:
                    self._wake.clear()
                    try:
                        await asyncio.wait_for(self._wake.wait(), timeout=2.0)
                    except asyncio.TimeoutError:
                        pass
                    continue
                await execute_job(job)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                log.exception("worker %d crashed iteration", idx)
                await asyncio.sleep(1)


runner = JobRunner()
