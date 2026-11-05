"""Runs the multi-agent pipeline for one job: plan → collect → analyse → write → (review) → finalise."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import update

from ..db import session_factory
from ..models import JobEvent, ResearchJob
from .analyst import run_analyst
from .collector import run_collector
from .context import ResearchContext
from .planner import run_planner
from .report import build_report
from .reviewer import run_reviewer
from .writer import run_writer

log = logging.getLogger(__name__)
STAGE_TIMEOUT = 240


async def _emit(job_id: str, agent: str, kind: str, message: str, data: dict | None = None,
                progress: int | None = None, stage: str | None = None) -> None:
    async with session_factory()() as s:
        s.add(JobEvent(job_id=job_id, agent=agent, kind=kind, message=message, data=data))
        values: dict = {"updated_at": datetime.now(timezone.utc)}
        if progress is not None:
            values["progress"] = progress
        if stage:
            values["stage"] = stage
        await s.execute(update(ResearchJob).where(ResearchJob.id == job_id).values(**values))
        await s.commit()


async def execute_job(job: ResearchJob) -> None:
    job_id = job.id

    async def emit(agent, kind, message, data=None):
        await _emit(job_id, agent, kind, message, data)

    ctx = ResearchContext(query=job.query, depth=job.depth, requested_tickers=list(job.tickers or []), emit=emit)
    try:
        await _emit(job_id, "system", "log", f"Job started (depth: {job.depth})", progress=3, stage="planning")
        ctx.plan = await asyncio.wait_for(run_planner(ctx), STAGE_TIMEOUT)
        await _emit(job_id, "system", "log", "Planning complete", progress=15, stage="collecting")

        await asyncio.wait_for(run_collector(ctx), STAGE_TIMEOUT)
        await _emit(job_id, "system", "log", "Data collection complete", progress=50, stage="analysing")

        meta = await asyncio.wait_for(run_analyst(ctx), STAGE_TIMEOUT)
        await _emit(job_id, "system", "log", "Analysis complete", progress=72, stage="writing")

        await asyncio.wait_for(run_writer(ctx), STAGE_TIMEOUT)
        progress = 88
        if ctx.depth != "quick":
            await _emit(job_id, "system", "log", "Draft complete", progress=progress, stage="reviewing")
            await asyncio.wait_for(run_reviewer(ctx), STAGE_TIMEOUT)

        report = build_report(ctx, job_id, meta)
        async with session_factory()() as s:
            await s.execute(update(ResearchJob).where(ResearchJob.id == job_id).values(
                status="completed", progress=100, stage="done", report=report, title=report["title"][:300],
                tickers=list(ctx.snapshots), engine=report["engine"],
                finished_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)))
            await s.commit()
        await _emit(job_id, "system", "done", "Report ready", {"stance": report["recommendation"]["stance"]})
    except Exception as exc:  # noqa: BLE001 — job failures must never kill the worker
        log.exception("job %s failed", job_id)
        msg = "Stage timed out" if isinstance(exc, asyncio.TimeoutError) else f"{type(exc).__name__}: {exc}"
        async with session_factory()() as s:
            await s.execute(update(ResearchJob).where(ResearchJob.id == job_id).values(
                status="failed", error=msg[:2000], stage="failed",
                finished_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)))
            await s.commit()
        await _emit(job_id, "system", "error", msg)
