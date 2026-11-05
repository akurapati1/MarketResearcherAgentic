"""Static catalogue used for offline symbol search and market overview."""

CATALOG: list[dict] = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "base": 195},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "base": 420},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Semiconductors", "base": 900},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication", "base": 165},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "base": 185},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Communication", "base": 500},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Automotive", "base": 240},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Semiconductors", "base": 160},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication", "base": 620},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials", "base": 200},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Financials", "base": 275},
    {"symbol": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy", "base": 115},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare", "base": 28},
    {"symbol": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare", "base": 780},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Defensive", "base": 65},
    {"symbol": "DIS", "name": "The Walt Disney Company", "sector": "Communication", "base": 100},
    {"symbol": "INTC", "name": "Intel Corporation", "sector": "Semiconductors", "base": 32},
    {"symbol": "ORCL", "name": "Oracle Corporation", "sector": "Technology", "base": 125},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology", "base": 280},
    {"symbol": "PLTR", "name": "Palantir Technologies", "sector": "Technology", "base": 24},
    {"symbol": "COIN", "name": "Coinbase Global", "sector": "Financials", "base": 230},
    {"symbol": "BTC-USD", "name": "Bitcoin USD", "sector": "Crypto", "base": 67000},
    {"symbol": "ETH-USD", "name": "Ethereum USD", "sector": "Crypto", "base": 3300},
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy", "base": 2900},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "Technology", "base": 3900},
    {"symbol": "INFY.NS", "name": "Infosys Ltd.", "sector": "Technology", "base": 1500},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd.", "sector": "Financials", "base": 1600},
    {"symbol": "^GSPC", "name": "S&P 500", "sector": "Index", "base": 5200},
    {"symbol": "^IXIC", "name": "NASDAQ Composite", "sector": "Index", "base": 16300},
    {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "sector": "Index", "base": 39000},
    {"symbol": "^NSEI", "name": "NIFTY 50", "sector": "Index", "base": 22500},
    {"symbol": "^VIX", "name": "CBOE Volatility Index", "sector": "Index", "base": 15},
    {"symbol": "GC=F", "name": "Gold Futures", "sector": "Commodity", "base": 2350},
    {"symbol": "CL=F", "name": "Crude Oil WTI", "sector": "Commodity", "base": 80},
]

BY_SYMBOL = {c["symbol"]: c for c in CATALOG}

OVERVIEW_SYMBOLS = ["^GSPC", "^IXIC", "^DJI", "^NSEI", "BTC-USD", "GC=F"]


def search_catalog(q: str, limit: int = 8) -> list[dict]:
    q = q.strip().lower()
    if not q:
        return []
    scored = []
    for c in CATALOG:
        sym, name = c["symbol"].lower(), c["name"].lower()
        if sym == q:
            score = 0
        elif sym.startswith(q):
            score = 1
        elif name.startswith(q):
            score = 2
        elif q in name or q in sym:
            score = 3
        else:
            continue
        scored.append((score, c))
    scored.sort(key=lambda x: x[0])
    return [{"symbol": c["symbol"], "name": c["name"], "sector": c["sector"]} for _, c in scored[:limit]]


def resolve_names(text: str) -> list[str]:
    """Find known tickers mentioned by symbol or company name inside free text."""
    import re

    found: list[str] = []
    low = text.lower()
    for c in CATALOG:
        if c["sector"] == "Index":
            continue
        first = re.sub(r"[.,]", "", c["name"].lower()).split()[0]
        sym = c["symbol"]
        if re.search(rf"(?<![A-Za-z]){re.escape(sym)}(?![A-Za-z])", text) and len(sym) > 1:
            found.append(sym)
        elif len(first) > 3 and re.search(rf"\b{re.escape(first)}\b", low):
            found.append(sym)
    return list(dict.fromkeys(found))
