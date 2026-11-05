"""Four cooperating agents with typed hand-offs: Planner -> Collector -> Analyst -> Writer."""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from .llm import LLM, LLMError, get_llm

SECTIONS = ("size_growth", "competition", "positioning", "risks")


@dataclass
class Plan:
    question: str
    sections: tuple[str, ...] = SECTIONS
    keywords: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    rows: list[dict]
    snippets: list[tuple[str, str]]  # (source id, text)


@dataclass
class Findings:
    facts: dict
    swot: dict[str, list[str]]
    sources: dict[str, str]


def plan(question: str) -> Plan:
    kws = [w for w in re.findall(r"[a-z]{4,}", question.lower()) if w not in {"what", "which", "market", "should", "about", "with", "that"}]
    return Plan(question, SECTIONS, kws)


def collect(data_dir: str | Path, p: Plan) -> Evidence:
    d = Path(data_dir)
    with open(d / "market.csv", newline="") as f:
        rows = [{**r, "year": int(r["year"]), "revenue_musd": float(r["revenue_musd"])} for r in csv.DictReader(f)]
    snippets = []
    for note in sorted((d / "notes").glob("*.md")):
        for line in note.read_text().splitlines():
            if line.startswith("#") or not line.strip():
                continue
            snippets.append((note.stem, line.strip()))
    snippets.sort(key=lambda s: -sum(k in s[1].lower() for k in p.keywords))
    return Evidence(rows, snippets)


def cagr(first: float, last: float, years: int) -> float:
    if first <= 0 or years <= 0:
        raise ValueError("need positive start value and at least one period")
    return (last / first) ** (1 / years) - 1


def analyse(ev: Evidence) -> Findings:
    years = sorted({r["year"] for r in ev.rows})
    y0, y1 = years[0], years[-1]
    by_co: dict[str, dict[int, float]] = {}
    seg: dict[str, str] = {}
    for r in ev.rows:
        by_co.setdefault(r["company"], {})[r["year"]] = r["revenue_musd"]
        seg[r["company"]] = r["segment"]
    total = {y: sum(c.get(y, 0) for c in by_co.values()) for y in years}
    n = y1 - y0
    shares = {c: v[y1] / total[y1] for c, v in by_co.items()}
    growth = {c: cagr(v[y0], v[y1], n) for c, v in by_co.items()}
    hhi = sum((s * 100) ** 2 for s in shares.values())
    leader = max(shares, key=shares.get)
    fastest = max(growth, key=growth.get)
    slowest = min(growth, key=growth.get)
    facts = {"years": (y0, y1), "total": total, "market_cagr": cagr(total[y0], total[y1], n),
             "shares": shares, "growth": growth, "hhi": hhi, "leader": leader, "fastest": fastest,
             "slowest": slowest, "segments": seg}
    sources = {"S0": f"market.csv ({y0}-{y1}, {len(by_co)} companies)"}
    sw = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
    sw["strengths"].append(f"{leader} leads with {shares[leader]:.0%} share [S0]")
    sw["strengths"].append(f"{fastest} grows fastest at {growth[fastest]:.0%} CAGR [S0]")
    if growth[slowest] <= 0.01:
        sw["weaknesses"].append(f"{slowest} is stagnating ({growth[slowest]:+.1%} CAGR) [S0]")
    sw["opportunities"].append(f"Market grew {facts['market_cagr']:.0%} a year to ${total[y1]:,.0f}M [S0]")
    if hhi < 2500:
        sw["threats"].append(f"Fragmented market (HHI {hhi:,.0f}) invites price competition [S0]")
    else:
        sw["threats"].append(f"Concentrated market (HHI {hhi:,.0f}) favours incumbents [S0]")
    for i, (src, text) in enumerate(ev.snippets, 1):
        sid = f"S{i}"
        sources[sid] = f"{src}: {text}"
        low = text.lower()
        if any(w in low for w in ("subsid", "lower", "demand", "grow")) and "flatten" not in low:
            sw["opportunities"].append(f"{text} [{sid}]")
        elif any(w in low for w in ("flatten", "saturat", "rules", "require")):
            sw["threats"].append(f"{text} [{sid}]")
        else:
            sw["strengths"].append(f"Buyer priority: {text} [{sid}]")
    return Findings(facts, sw, sources)


def write(question: str, f: Findings, llm: LLM | None = None) -> str:
    llm, x = llm or get_llm(), f.facts
    y0, y1 = x["years"]
    summary = (f"The market grew from ${x['total'][y0]:,.0f}M to ${x['total'][y1]:,.0f}M ({x['market_cagr']:.0%} CAGR). "
               f"{x['leader']} leads; {x['fastest']} is the fastest grower. [S0]")
    if llm.available:
        try:
            summary = llm.complete(
                "Write a 3-sentence executive summary answering the question using ONLY these facts; cite [S#] ids.\n"
                f"Question: {question}\nFacts: {x}\nSWOT: {f.swot}",
                system="You are a market analyst. Never add numbers that are not in the facts.").strip()
        except LLMError:
            pass
    out = [f"# Market research: {question}", "", "## Executive summary", summary, "", "## Market size & growth",
           "| Year | Revenue ($M) |", "| --- | ---: |", *[f"| {y} | {v:,.0f} |" for y, v in x["total"].items()], "",
           "## Competition", "| Company | Segment | Share | CAGR |", "| --- | --- | ---: | ---: |",
           *[f"| {c} | {x['segments'][c]} | {x['shares'][c]:.0%} | {x['growth'][c]:+.0%} |"
             for c in sorted(x["shares"], key=x["shares"].get, reverse=True)],
           "", f"Concentration (HHI): **{x['hhi']:,.0f}** ({'fragmented' if x['hhi'] < 2500 else 'concentrated'}).", ""]
    for title, key in (("Strengths", "strengths"), ("Weaknesses", "weaknesses"), ("Opportunities", "opportunities"), ("Threats", "threats")):
        if f.swot[key]:
            out += [f"### {title}", *[f"- {b}" for b in f.swot[key]], ""]
    out += ["## Sources", *[f"- **{k}** {v}" for k, v in f.sources.items()]]
    return "\n".join(out)
