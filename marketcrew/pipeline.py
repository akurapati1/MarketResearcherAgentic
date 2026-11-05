from __future__ import annotations

import argparse
import time
from pathlib import Path

from . import agents
from .llm import LLM

DATA = Path(__file__).parents[1] / "data"


def run(question: str, data_dir=DATA, llm: LLM | None = None, trace: list | None = None) -> str:
    trace = trace if trace is not None else []
    t = time.perf_counter()
    p = agents.plan(question); trace.append(("planner", f"{len(p.sections)} sections, keywords={p.keywords}"))
    ev = agents.collect(data_dir, p); trace.append(("collector", f"{len(ev.rows)} rows, {len(ev.snippets)} snippets"))
    f = agents.analyse(ev); trace.append(("analyst", f"leader={f.facts['leader']} cagr={f.facts['market_cagr']:.1%}"))
    report = agents.write(question, f, llm); trace.append(("writer", f"{len(report.split())} words in {time.perf_counter()-t:.2f}s"))
    return report


def main() -> None:
    ap = argparse.ArgumentParser(prog="marketcrew")
    ap.add_argument("question", nargs="?", default="Which EV charging players should we benchmark against?")
    ap.add_argument("--data", default=str(DATA)); ap.add_argument("-o", "--out")
    a = ap.parse_args()
    trace: list = []
    report = run(a.question, a.data, trace=trace)
    for agent, msg in trace:
        print(f"[{agent:9}] {msg}")
    if a.out:
        Path(a.out).write_text(report); print("wrote", a.out)
    else:
        print("\n" + report)
