"""Central config: env loading, cap-tier thresholds, and ISS lookup tables.

Values are transcribed verbatim from docs/skill-reference/market-analysis-daily/SKILL.md
(Phase B3 cap classification, Phase B4 Intraday Signal Score rubric).
"""
import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "market-researcher-agentic/0.1")

REDDIT_ENABLED = bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)

# ─── Phase B3: Cap Classification (₹ crore) ───
LARGE_CAP_MIN_CR = 20_000
MID_CAP_MIN_CR = 5_000

# ─── Phase B4: Intraday Signal Score (ISS) ───

# Catalyst Score (0-10) — matched by catalyst_type + deal_size_cr + confirmed flag.
# Order matters: first matching rule wins. See scoring.py for match logic.
CATALYST_SCORE_TABLE = [
    # (catalyst_type, min_size_cr, requires_confirmed, score)
    ("deal", 500, True, 10),
    ("order", 500, True, 10),
    ("deal", 100, True, 8),
    ("order", 100, True, 8),
    ("approval", None, True, 8),  # regulatory approval (drug, SEBI, NCLT)
    ("result_beat_major", None, True, 8),  # PAT > 15% above estimates
    ("qip", None, True, 7),
    ("block_deal", None, True, 7),
    ("fii_dii_buy", None, True, 7),
    ("deal", 0, False, 6),  # deal/order < 100cr OR media-only
    ("order", 0, False, 6),
    ("result_beat_minor", None, True, 6),  # PAT 5-15% above estimates
    ("promoter_buy", None, True, 6),
    ("analyst_upgrade", None, True, 5),
    ("mou", None, False, 4),  # JV/MoU announced, no size yet
    ("social_buzz", None, False, 2),  # vague social buzz, no confirmed filing
]
CATALYST_SCORE_DEFAULT = 2  # unrecognized catalyst type, unconfirmed

# Negative catalyst triggers (ISS goes negative -> "Likely to Fall" tier)
NEGATIVE_CATALYST_TABLE = {
    "earnings_miss_major": -8,  # PAT > 10% below estimates
    "regulatory_action": -9,  # SEBI notice / ED raid
    "deal_cancellation": -7,
    "promoter_pledge_or_insider_sell": -6,
    "analyst_downgrade": -5,
    "negative_news_social_pileup": -4,
}

# Social Amplification Score (0-3) — approximated via independent source count
# (Twitter/Telegram unavailable without paid APIs; Reddit + news-hit-count used instead)
SOCIAL_SCORE_THRESHOLDS = [
    (3, 3),  # >=3 independent sources -> +3
    (2, 2),  # 2 independent sources -> +2
    (1, 1),  # 1 mention -> +1
]
SOCIAL_SCORE_DEFAULT = 0

# Liquidity Score (0-3) — avg daily volume (shares)
LIQUIDITY_HIGH_VOLUME = 500_000  # >5L shares -> +3
LIQUIDITY_MEDIUM_VOLUME = 100_000  # 1-5L shares -> +2
# <1L shares but deal confirmed -> +1; illiquid/no data -> 0

# Momentum Context Score (0-4)
MOMENTUM_ALREADY_UP_DAY_CHANGE_PCT = 2.0  # already up with volume -> +4
MOMENTUM_MILD_UPTREND_20D_PCT = 2.0  # mild uptrend -> +2 if 20d trend > this
MOMENTUM_FLAT_BAND_PCT = 1.0  # within +-this% of flat -> +3 (fresh catalyst reversal)
MOMENTUM_DEEP_DOWNTREND_20D_PCT = -15.0  # below this -> +0 unless strong catalyst
MOMENTUM_STRONG_CATALYST_MIN_SCORE = 8  # catalyst score needed to get +1 in a downtrend

# Prediction tiers from ISS (Phase B4)
ISS_TIER_SURGE = (15, 20)  # 🚀 >10% Intraday Surge Potential
ISS_TIER_GAIN = (10, 14)  # 📈 >5% Intraday Gain Potential
ISS_TIER_WATCH = (5, 9)  # 👀 Watch — Moderate Upside
# ISS < 5 and non-negative -> excluded (catalyst too weak, per Phase B5 min catalyst score 4)
# negative ISS -> 📉 Likely to Fall Today

# Phase B5: Selection rules
PICKS_PER_TIER = 5
MIN_CATALYST_SCORE_FOR_PICK = 4
MIN_FALL_PREDICTIONS_TARGET = 3

SECTORS = [
    "Defence",
    "Pharma",
    "IT",
    "Power & Renewables",
    "Real Estate",
    "Railways",
    "Banking & NBFC",
    "Chemicals",
]

DISCLAIMER_TEXT = (
    "FOR INFORMATIONAL PURPOSES ONLY. This report is generated from public news "
    "sources, social media signals, exchange filings, and financial data. It is NOT "
    "investment advice. Intraday picks are for intraday use only — they are not "
    "recommendations for swing or long-term positions. Stock predictions are "
    "inherently uncertain; geopolitical events are particularly difficult to forecast. "
    "Reversal candidates carry additional risk from prior negative momentum. Always "
    "verify exchange filings directly on NSE/BSE before trading. Do your own research "
    "and consult a SEBI-registered or licensed financial advisor before making "
    "investment decisions."
)
