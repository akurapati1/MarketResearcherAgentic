from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResearchCreate(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    tickers: list[str] = Field(default_factory=list, max_length=5)
    depth: Literal["quick", "standard", "deep"] = "standard"

    @field_validator("tickers")
    @classmethod
    def _clean(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(t.upper().strip() for t in v if t.strip()))


class JobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query: str
    title: str
    depth: str
    tickers: list[str]
    status: str
    progress: int
    stage: str
    error: str | None = None
    engine: str = ""
    created_at: datetime
    finished_at: datetime | None = None
    stance: str | None = None
    confidence: int | None = None


class JobDetail(JobSummary):
    report: dict | None = None


class JobPage(BaseModel):
    items: list[JobSummary]
    total: int
    page: int
    page_size: int


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: datetime
    agent: str
    kind: str
    message: str
    data: dict | None = None


class WatchlistCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    name: str = ""
    note: str = ""

    @field_validator("symbol")
    @classmethod
    def _up(cls, v: str) -> str:
        return v.upper().strip()


class WatchlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    note: str
    added_at: datetime
