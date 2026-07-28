# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit app that re-implements the **India Intraday mode (Mode B)** of a Claude
Agent Skill called `market-analysis-daily`. The full skill spec (both Mode A —
Global Briefing, and Mode B — India Intraday) is preserved verbatim at
`docs/skill-reference/market-analysis-daily/SKILL.md` — that file is the
authoritative source of truth for scoring rules, phase ordering, and output
structure. Every module in this repo cites the SKILL.md phase it implements in
its module docstring; when in doubt about *why* a rule exists, read that
section of SKILL.md first. Mode A (US + India + geopolitical) is not yet built.

The original skill used Claude's native web-search/artifact tools inside a chat
session. This app reproduces the same workflow standalone via the Anthropic API
(`agents/llm_utils.py`) for search/synthesis, plus free market-data APIs
(yfinance, Reddit) for anything that can be deterministic instead of
LLM-judged.

## Commands

```bash
# Setup (Windows venv already at .venv/)
.venv\Scripts\activate
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Requires `ANTHROPIC_API_KEY` in `.env` (loaded via `config.py`/`python-dotenv`).
`REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` are optional — social scoring
degrades gracefully to a news-source-count proxy when absent
(`config.REDDIT_ENABLED`).

There is no test suite, linter, or build step configured in this repo yet.

## Architecture: the pipeline

`app.py` (Streamlit UI) calls the single entrypoint `agents.orchestrator.run_pipeline()`,
which sequences everything and returns a `PipelineResult`. The pipeline mirrors
SKILL.md's Mode B phases in order:

1. **Filings agent** (`agents/filings_agent.py`, Phase B1 exchange filings) — Claude +
   `web_search` tool scans BSE/NSE filings. Everything it returns is forced
   `confirmed=True` — it's treated as ground truth.
2. **News agent** (`agents/news_agent.py`, Phase B2) — Claude + `web_search` scans news
   sites for deal/catalyst signals. `confirmed` is set by the model per-item.
3. **Merge** (`orchestrator._merge_catalyst_events`) — dedupes by ticker: prefers
   confirmed over unconfirmed, then larger stated deal size.
4. **Social agent** (`agents/social_agent.py`, Phase B1 social) — Reddit search (if
   configured) + an independent-news-source-count proxy standing in for the
   skill's Twitter/Telegram/Reddit multi-platform score.
5. **Market data** (`data/market_data.py`) — yfinance snapshot per ticker
   (`TICKER.NS`): price, day-change%, market cap, 20-day trend, avg volume,
   52-week range. Fails soft to `MarketSnapshot(data_available=False)` — never
   raises, never fabricates a number.
6. **Cap-tier classification** (`data.market_data.classify_cap_tier`) — Large
   (> ₹20,000 Cr) / Mid (₹5,000–20,000 Cr) / Small (< ₹5,000 Cr), thresholds in
   `config.py`. Tickers with unknown market cap are dropped (can't be tiered).
7. **Scoring** (`data/scoring.py`, Phase B4 ISS rubric) — fully deterministic,
   table-driven from `config.py` (`CATALYST_SCORE_TABLE`,
   `NEGATIVE_CATALYST_TABLE`, momentum/liquidity/social thresholds). No LLM
   involved here, by design, so results are reproducible and auditable against
   SKILL.md. A negative catalyst score overrides the positive composition
   entirely (`ScoreBreakdown.total`).
8. **Selection** (`report/builder.py`, Phase B5) — exactly 5 picks per cap tier
   sorted by ISS descending, at least one 🔄 reversal candidate per tier where
   available, never a repeated ticker across tiers, fewer-than-5 picks get
   flagged `lower_conviction` instead of being padded with fabricated
   candidates. Fall predictions are distributed across tiers separately,
   most-severe-first, toward `config.MIN_FALL_PREDICTIONS_TARGET`.
9. **Writer agent** (`agents/writer_agent.py`) — one batched Claude call (no
   tools) turns the already-scored, already-selected picks into card copy
   (catalyst/why-today/entry/risk text). Falls back to the raw catalyst
   summary per-pick if the LLM call or JSON parsing fails, rather than leaving
   a card blank.
10. **Sector pulse / small-cap spotlight** (`orchestrator._sector_pulse`,
    `_small_cap_spotlight`) — derived from `all_picks` via keyword matching
    (`SECTOR_KEYWORDS`) and catalyst-type membership (`SPOTLIGHT_CATALYST_TYPES`).

Rendering has two independent paths that both consume `PipelineResult`:
`ui/components.py` (live Streamlit widgets) and `report/html_export.py`
(self-contained dark-mode HTML string for the download button, no external
CDN/JS, styled via `ui/styles.py`). Keep both in sync when changing what a
pick displays — they don't share templates.

## Key conventions carried over from the skill spec

- **Catalyst types are a closed vocabulary** — `agents/schemas.py`
  (`POSITIVE_CATALYST_TYPES` / `NEGATIVE_CATALYST_TYPES`) must stay in sync
  with `config.CATALYST_SCORE_TABLE` / `config.NEGATIVE_CATALYST_TABLE`. The
  JSON schema description given to the search agents
  (`CATALYST_EVENT_JSON_SCHEMA_DESCRIPTION`) is built from these lists, so
  adding a catalyst type means updating three places: the schema list, the
  config score table, and (if it changes prompt behavior) the relevant
  agent's system prompt.
- **Never fabricate data.** Missing price/fundamentals render as `—`
  (`report/html_export.py`), not zero or an invented figure. Every soft
  failure path (LLM call fails, JSON parse fails, yfinance lookup fails,
  Reddit unavailable) degrades to an empty/neutral result and logs a warning
  — it must not raise and crash `run_pipeline`.
- **Confirmed vs unconfirmed matters for scoring**, not just display —
  several rows in `CATALYST_SCORE_TABLE` require `confirmed=True` to match at
  all, and social-media-only signals cap out low. Exchange filings are always
  `confirmed=True` by construction (`run_filings_agent` forces it).
- **Prior downtrend does not disqualify a pick** — it's a reversal-candidate
  flag (`prior_downtrend` → `reversal_candidate`, 🔄), and
  `score_momentum` explicitly gives a downtrend +1 instead of 0 when the
  catalyst score is strong enough (`MOMENTUM_STRONG_CATALYST_MIN_SCORE`).
- **Copyright discipline**: agent system prompts instruct the model to
  paraphrase, never copy article/filing text verbatim (max one quote under 15
  words per source) — preserve this instruction if you touch any agent's
  system prompt.
- `agents/llm_utils.py` centralizes the two Claude call shapes used
  everywhere: `run_search_agent` (server-side `web_search` tool, auto-resumes
  on `pause_turn`) and `run_text_agent` (no-tool synthesis). Both return `""`
  on any API failure rather than raising — callers must treat that as "no
  results," not a fatal error. `extract_json_array` tolerantly pulls a JSON
  array out of LLM output that may have prose or markdown fences around it.
