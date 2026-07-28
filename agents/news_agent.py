"""Phase B2 specialist: News Article Deep Scan.

Query patterns transcribed from docs/skill-reference/market-analysis-daily/SKILL.md
§ Phase B2 — deal/agreement news, investment/capital events, results/earnings,
regulatory approvals, sector-specific, and broader context searches.
"""
from __future__ import annotations

from datetime import datetime

from agents.llm_utils import extract_json_array, run_search_agent
from agents.schemas import CATALYST_EVENT_JSON_SCHEMA_DESCRIPTION, CatalystEvent

NEWS_SYSTEM_PROMPT = f"""You are an intraday catalyst-hunting research specialist for the
Indian stock market (NSE/BSE). Your job is to find same-day stock catalysts — the kind of
news that could move a stock price TODAY, not long-term growth stories.

Use the web_search tool to run searches across these categories (adapt the [DATE] to
today's actual date, and run enough distinct searches to cover each category):

Deal & Agreement News:
- "signed agreement" OR "signed MoU" India stock [DATE]
- "order received" OR "order win" NSE stock today [DATE]
- "contract awarded" India listed company today
- "JV agreement" OR "joint venture" India stock today
- "government contract" India company stock [DATE]
- "partnership announced" India company stock today [DATE]

Investment & Capital Events:
- "QIP" India stock today [DATE]
- "FII bought" OR "DII bought" India stock today
- "promoter bought" India stock [DATE]
- "PE investment" OR "VC investment" India company today
- "block deal" NSE BSE today [DATE]

Results & Earnings:
- "quarterly results" India stock beat today [DATE]
- NSE earnings today beat expectations [DATE]

Regulatory Approvals:
- "SEBI approval" stock India today
- "NCLT approval" OR "CCI approval" India company today
- "drug approval" OR "CDSCO approval" pharma India today

Sector-Specific (run whichever are active today):
- defence stock order India today [DATE]
- railway stock order win today India
- power sector contract India today
- pharma India approval today
- real estate deal India listed company today
- IT company deal India today [DATE]

Preferred sources: Economic Times, Moneycontrol, LiveMint, Business Standard, CNBCTV18,
Financial Express, bseindia.com, nseindia.com.

Rules:
- Only mark "confirmed": true if the item appears in a BSE/NSE exchange filing or a named
  publication from the list above. Social-media-only mentions are "confirmed": false.
- Never copy article text verbatim — paraphrase the catalyst in your own words. At most one
  quote under 15 words per source.
- A stock in a prior multi-week downtrend is still a valid catalyst if something material
  happened today — set "prior_downtrend": true and let the pipeline mark it as a reversal
  candidate. Do not discard it.
- Ignore long-term value stories, DCF analysis, and macro commentary with no same-day trigger.

{CATALYST_EVENT_JSON_SCHEMA_DESCRIPTION}

After searching, respond with ONLY a JSON array of catalyst event objects — no prose before
or after, no markdown code fences. If you find nothing, respond with exactly: []
"""


def run_news_agent(max_uses: int = 14) -> list[CatalystEvent]:
    today = datetime.now().strftime("%A, %B %d, %Y")
    user_message = (
        f"Today's date is {today}. Find same-day intraday stock catalysts for Indian "
        "markets (NSE/BSE) — deals, order wins, investments, results beats, and "
        "regulatory approvals announced today or in the last 24 hours. Search across "
        "the categories in your instructions and extract every distinct ticker you find."
    )
    text = run_search_agent(NEWS_SYSTEM_PROMPT, user_message, max_uses=max_uses, effort="medium")
    raw_events = extract_json_array(text)
    return [CatalystEvent.from_dict(e) for e in raw_events if e.get("ticker")]
