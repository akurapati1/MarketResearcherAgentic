"""Phase B1 (social) specialist — approximated per the user's chosen scope.

True Twitter/Telegram scanning needs paid/restricted APIs, so v1 uses:
1. Reddit's free API (praw) against r/IndiaInvestments, r/DalalStreetTalks,
   r/IndianStockMarket — a real (if partial) social signal.
2. An independent-news-source-count proxy built from the news/filings agents'
   own source_name fields, as a stand-in for "trending across platforms".

If Reddit credentials are absent (config.REDDIT_ENABLED is False), Reddit search is
skipped silently and social scoring falls back to the news-hit-count proxy alone —
this degrades gracefully rather than crashing the pipeline.
"""
from __future__ import annotations

import logging
from collections import defaultdict

import config
from agents.schemas import CatalystEvent, SocialSignal

logger = logging.getLogger(__name__)

REDDIT_SUBREDDITS = ["IndiaInvestments", "DalalStreetTalks", "IndianStockMarket"]

_reddit = None


def _get_reddit():
    global _reddit
    if not config.REDDIT_ENABLED:
        return None
    if _reddit is None:
        import praw

        _reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
        )
    return _reddit


def search_reddit_mentions(tickers: list[str], limit_per_query: int = 5) -> dict[str, int]:
    """Returns {ticker: reddit_mention_count} from the last day. Returns {} if
    Reddit credentials aren't configured."""
    reddit = _get_reddit()
    if reddit is None or not tickers:
        return {}
    counts: dict[str, int] = defaultdict(int)
    for ticker in tickers:
        try:
            for sub in REDDIT_SUBREDDITS:
                for _ in reddit.subreddit(sub).search(
                    ticker, sort="new", time_filter="day", limit=limit_per_query
                ):
                    counts[ticker] += 1
        except Exception:
            logger.warning("Reddit search failed for %s", ticker, exc_info=True)
            continue
    return dict(counts)


def build_social_signals(
    catalyst_events: list[CatalystEvent], reddit_counts: dict[str, int]
) -> dict[str, SocialSignal]:
    """Combines the independent-news-source count with Reddit hits into a
    per-ticker SocialSignal, approximating the skill's multi-platform
    amplification score (Twitter + Telegram + Reddit)."""
    sources_by_ticker: dict[str, set] = defaultdict(set)
    for e in catalyst_events:
        if e.ticker and e.source_name:
            sources_by_ticker[e.ticker].add(f"news:{e.source_name}")

    signals: dict[str, SocialSignal] = {}
    for ticker in set(sources_by_ticker) | set(reddit_counts):
        sources = set(sources_by_ticker.get(ticker, set()))
        if reddit_counts.get(ticker):
            sources.add("reddit")
        signals[ticker] = SocialSignal(ticker=ticker, mention_count=len(sources), sources=list(sources))
    return signals
