"""Validated shapes for LLM output; anything that fails validation triggers the heuristic path."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Stance = Literal["Bullish", "Neutral", "Bearish"]


class Plan(BaseModel):
    title: str = ""
    tickers: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    news_queries: list[str] = Field(default_factory=list)

    @field_validator("tickers")
    @classmethod
    def _upper(cls, v: list[str]) -> list[str]:
        return [t.upper().strip() for t in v if t and len(t) <= 16][:6]


class Risk(BaseModel):
    title: str
    severity: Literal["low", "medium", "high"] = "medium"
    detail: str = ""


class Swot(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    stance: Stance = "Neutral"
    confidence: int = Field(default=50, ge=0, le=100)
    horizon: str = "3-6 months"
    rationale: str = ""


class Analysis(BaseModel):
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    swot: Swot = Field(default_factory=Swot)
    risks: list[Risk] = Field(default_factory=list)
    recommendation: Recommendation = Field(default_factory=Recommendation)


class Section(BaseModel):
    heading: str
    body: str


class Draft(BaseModel):
    sections: list[Section]


class Review(BaseModel):
    issues: list[str] = Field(default_factory=list)
    revised_summary: str = ""
