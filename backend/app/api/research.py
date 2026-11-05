import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session, session_factory
from ..models import JobEvent, ResearchJob
from ..schemas import EventOut, JobDetail, JobPage, JobSummary, ResearchCreate
from ..services.jobs import runner

router = APIRouter(prefix="/research", tags=["research"])


def _summary(job: ResearchJob) -> JobSummary:
    s = JobSummary.model_validate(job)
    if job.report:
        rec = job.report.get("recommendation", {})
        s.stance, s.confidence = rec.get("stance"), rec.get("confidence")
    return s


@router.post("", response_model=JobSummary, status_code=202)
async def create_job(body: ResearchCreate, db: AsyncSession = Depends(get_session)):
    job = ResearchJob(query=body.query.strip(), depth=body.depth, tickers=body.tickers,
                      title=body.query.strip()[:120])
    db.add(job)
    await db.commit()
    runner.notify()
    return _summary(job)


@router.get("", response_model=JobPage)
async def list_jobs(
    q: str | None = None, status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    stmt = select(ResearchJob)
    if status:
        stmt = stmt.where(ResearchJob.status == status)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(ResearchJob.query).like(like), func.lower(ResearchJob.title).like(like)))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (await db.execute(stmt.order_by(ResearchJob.created_at.desc())
                             .offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return JobPage(items=[_summary(r) for r in rows], total=total, page=page, page_size=page_size)


async def _get(db: AsyncSession, job_id: str) -> ResearchJob:
    job = await db.get(ResearchJob, job_id)
    if not job:
        raise HTTPException(404, "Research job not found")
    return job


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: str, db: AsyncSession = Depends(get_session)):
    job = await _get(db, job_id)
    out = JobDetail.model_validate(job)
    if job.report:
        rec = job.report.get("recommendation", {})
        out.stance, out.confidence = rec.get("stance"), rec.get("confidence")
    return out


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, db: AsyncSession = Depends(get_session)):
    await db.delete(await _get(db, job_id))
    await db.commit()


@router.post("/{job_id}/retry", response_model=JobSummary, status_code=202)
async def retry_job(job_id: str, db: AsyncSession = Depends(get_session)):
    job = await _get(db, job_id)
    if job.status not in ("failed", "completed"):
        raise HTTPException(409, "Job is still active")
    new = ResearchJob(query=job.query, depth=job.depth, tickers=[], title=job.title)
    db.add(new)
    await db.commit()
    runner.notify()
    return _summary(new)


@router.get("/{job_id}/events", response_model=list[EventOut])
async def list_events(job_id: str, after: int = 0, db: AsyncSession = Depends(get_session)):
    await _get(db, job_id)
    rows = (await db.execute(select(JobEvent).where(JobEvent.job_id == job_id, JobEvent.id > after)
                             .order_by(JobEvent.id))).scalars().all()
    return rows


@router.get("/{job_id}/stream")
async def stream(job_id: str, request: Request, after: int = 0):
    """Server-Sent Events. DB-polling keeps this correct across multiple API replicas."""
    async with session_factory()() as s:
        await _get(s, job_id)

    async def gen():
        last = after
        idle = 0
        while True:
            if await request.is_disconnected():
                return
            async with session_factory()() as s:
                rows = (await s.execute(select(JobEvent).where(JobEvent.job_id == job_id, JobEvent.id > last)
                                        .order_by(JobEvent.id))).scalars().all()
                job = await s.get(ResearchJob, job_id)
            if job is None:
                return
            for ev in rows:
                last = ev.id
                payload = EventOut.model_validate(ev).model_dump(mode="json")
                payload["progress"], payload["status"] = job.progress, job.status
                yield f"id: {ev.id}\nevent: {ev.kind}\ndata: {json.dumps(payload)}\n\n"
            if job.status in ("completed", "failed") and not rows:
                yield f"event: end\ndata: {json.dumps({'status': job.status})}\n\n"
                return
            idle += 1
            if idle % 20 == 0:
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/{job_id}/export")
async def export(job_id: str, format: str = Query("md", pattern="^(md|json)$"),
                 db: AsyncSession = Depends(get_session)):
    job = await _get(db, job_id)
    if not job.report:
        raise HTTPException(409, "Report not ready")
    fname = f"report-{job.id[:8]}"
    if format == "json":
        body = json.dumps(job.report, indent=2)
        return PlainTextResponse(body, media_type="application/json",
                                 headers={"Content-Disposition": f'attachment; filename="{fname}.json"'})
    return PlainTextResponse(job.report["markdown"], media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="{fname}.md"'})
