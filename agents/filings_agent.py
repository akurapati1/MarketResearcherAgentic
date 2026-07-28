"""Phase B1 specialist: BSE/NSE Exchange Filing Scan (ground truth).

Per docs/skill-reference/market-analysis-daily/SKILL.md § Phase B1: exchange filings
run FIRST and are always treated as "confirmed" — they are the ground truth the news
agent's less-certain findings get checked against.
"""
from __future__ import annotations

from datetime import datetime

from agents.llm_utils import extract_json_array, run_search_agent
from agents.schemas import CATALYST_EVENT_JSON_SCHEMA_DESCRIPTION, CatalystEvent

FILINGS_SYSTEM_PROMPT = f"""You are an exchange-filings research specialist for Indian
markets. Your job is to find TODAY's corporate announcements filed directly with
BSE India or NSE India — these are ground truth, more reliable than general news.

Use the web_search tool to run searches such as:
- BSE India corporate announcements today [DATE]
- NSE India exchange filings today [DATE] order win contract
- BSE filing MoU agreement [DATE]
- site:bseindia.com corporate announcement [DATE]
- site:nseindia.com corporate announcement [DATE]

For each filing you find, extract the NSE ticker, catalyst type, deal size (if stated in
₹ crore), and counterparty. Every event you extract from this search should be marked
"confirmed": true, since it comes directly from an exchange filing.

Rules:
- Never copy filing/article text verbatim — paraphrase in your own words. At most one
  quote under 15 words per source.
- A stock in a prior multi-week downtrend is still valid if a filing happened today — set
  "prior_downtrend": true, don't discard it.

{CATALYST_EVENT_JSON_SCHEMA_DESCRIPTION}

After searching, respond with ONLY a JSON array of catalyst event objects — no prose before
or after, no markdown code fences. If you find nothing, respond with exactly: []
"""


def run_filings_agent(max_uses: int = 10) -> list[CatalystEvent]:
    today = datetime.now().strftime("%A, %B %d, %Y")
    user_message = (
        f"Today's date is {today}. Find today's BSE/NSE corporate announcements and "
        "exchange filings for Indian listed companies — order wins, deals, MoUs, "
        "investments, and regulatory approvals filed today."
    )
    text = run_search_agent(FILINGS_SYSTEM_PROMPT, user_message, max_uses=max_uses, effort="medium")
    raw_events = extract_json_array(text)
    events = [CatalystEvent.from_dict(e) for e in raw_events if e.get("ticker")]
    for e in events:
        e.confirmed = True  # ground truth by definition
    return events
