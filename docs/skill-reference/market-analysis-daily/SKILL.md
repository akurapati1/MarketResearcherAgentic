---
name: market-analysis-daily
description: Same-day market analysis website with two modes — (A) Global: US + India + geopolitical impact, full fundamentals; (B) India Intraday: 5 picks each in Large/Mid/Small Cap, scored by catalyst (deal/order/approval/result/investment), social buzz, and momentum, with tiers for >10% surge, >5% gain, and certain fall. Captures reversal candidates (stocks in prior downtrends with a fresh catalyst today). Trigger for: market analysis, intraday picks India, NSE/BSE stocks today, daily briefing, deals signed today, small cap stocks today.
---

# Market Analysis Daily — Global + India Intraday Edition

This skill builds a same-day market-watch website. It has two modes that can be run together or independently:

- **Mode A — Global Briefing**: US + India stocks + geopolitical impact. Full fundamentals, dual-market predictions.
- **Mode B — India Intraday**: India-only, cap-tier structured predictions (Large/Mid/Small, 5 each), deal/catalyst-driven, intraday signal scoring. Social media scan included.

Default behavior: Run both modes and combine into one HTML output unless the user specifies one only.

## Trigger phrases

- "market analysis for today" → Both modes
- "intraday picks India" / "NSE stocks to buy today" / "India intraday" → Mode B only
- "US and India market news" / "global market briefing" → Mode A only
- "deals signed today India" / "small cap stocks today" → Mode B only

## Core Philosophy

**For intraday (Mode B):** A stock that has been falling for weeks can still be today's best intraday bet if something material happened in the last 24 hours. The catalyst is everything. Find the catalyst, find the trade.

**For global (Mode A):** Markets move on what happened in the last 24 hours — geopolitical events often move stocks more than earnings. Every run must do fresh searches.

### What Mode B hunts for (intraday catalysts)

- Deals signed / MoUs announced today
- Order wins from government, PSU, or large corporate clients
- SEBI / regulatory approvals received today
- QIP, FII block deals, promoter buys — fresh capital events
- Partnerships, JVs, contracts announced on exchange filings
- Social media buzz that precedes price moves
- Analyst upgrades or target price revisions published today
- Quarterly result beats (even from a stock in a prior downtrend)

### What Mode B ignores

- Long-term value / DCF analysis
- Multi-year growth stories with no today catalyst
- General macro unless there's a same-day trigger (e.g. RBI rate decision today)

---

## WORKFLOW

### ─── MODE A: GLOBAL BRIEFING ───

#### Phase A1 — Gather Global News (parallel searches, 8–12 total)

**US queries:**
- US stock market news today [DATE]
- S&P 500 movers today
- Nasdaq biggest gainers losers today
- US earnings reports today
- Wall Street premarket movers today

**India queries:**
- Indian stock market news today [DATE]
- Nifty 50 movers today
- BSE Sensex today
- NSE biggest gainers losers today [DATE]
- India earnings results today

**Geopolitical queries (4–6, mix based on what's active):**
- geopolitical news today [DATE] markets
- oil price today war Middle East
- Russia Ukraine war markets today
- US China trade tariffs today
- India defense stocks news today
- Red Sea shipping disruption today
- OPEC oil production today
- China Taiwan tension semiconductor
- sanctions news today commodities

Fetch top 2–3 full articles per category from reliable sources:
- US: Reuters, Bloomberg, CNBC, WSJ, MarketWatch
- India: Economic Times, Moneycontrol, LiveMint, Business Standard, CNBCTV18
- Geopolitics: Reuters, AP, BBC, Al Jazeera, FT

Extract from each article:
- Ticker symbol(s), company name
- Catalyst type (earnings, M&A, regulatory, macro, geopolitical)
- Direction (positive/negative) and intensity
- One-line summary in YOUR own words (never copy article text)
- Source URL

For geopolitical articles also extract:
- Event/theme (e.g. "OPEC+ cut", "Red Sea attacks", "China chip curbs")
- Sector winners (defense, oil majors, gold, shipping rerouters, rare earth miners)
- Sector losers (airlines, importers, semis exposed to Taiwan/China)
- Magnitude: one-day reaction or structural shift?

Proactively map events to tickers using `references/geopolitical-playbook.md`. Articles rarely name all the beneficiaries — use sector logic to fill the gaps.

Target: 15–30 US tickers, 10–25 Indian tickers, 5–15 geopolitical-exposed tickers.

#### Phase A2 — Pull Fundamentals (for all Mode A tickers)

For each ticker, search for fundamentals:
- US: "AAPL" P/E ratio EPS market cap or Apple stock financials
- India: "RELIANCE" P/E P/B EPS Moneycontrol or Reliance fundamentals Screener

Reliable sources:
- US: Yahoo Finance, StockAnalysis.com, MarketWatch, Finviz
- India: Screener.in, Moneycontrol, Trendlyne, NSE India

Fields: Current price (with currency), Day change %, Market cap, P/E (TTM), Forward P/E, P/B, EPS (TTM), Revenue (TTM), Net income (TTM), Total assets, Total liabilities, Debt/Equity, Profit margin, ROE, 52-week high, 52-week low, Sector/industry.

#### Phase A3 — Score & Rank (Global Stocks)

**News score (−5 to +5):**
- +5: blowout catalyst (major contract, FDA approval, large accretive deal)
- +3: solid beat / upgrade / positive guidance
- +1: mildly positive / sector tailwind
- 0: neutral
- −1: mildly negative
- −3: miss / downgrade / guidance cut
- −5: major negative (fraud, severe miss, regulatory hit)

**Geopolitical tilt (−3 to +3)** — only apply when there's an active dated event in today's news:
- +3: direct clear beneficiary (defense contractor during conflict, oil major during supply shock)
- +2: moderate beneficiary
- +1: tangential
- 0: not exposed
- −1: tangential victim
- −2: moderate victim (airline on oil spike, EM importer on dollar surge)
- −3: direct victim (revenue from sanctioned country, semis with Taiwan exposure on a Taiwan flare-up)

**Fundamental tilt (−2 to +2):**
- +2: deeply undervalued (P/E below sector, strong margins, ROE > 15%, low debt)
- +1: fairly valued, healthy balance sheet
- 0: mixed
- −1: stretched valuation, weakening margins
- −2: overextended (high P/E, weak margins, high debt/equity)

**Momentum tilt (−1 to +1):**
- +1: near 52-week high, positive momentum
- 0: range-bound
- −1: near 52-week low / downtrend

**Final score (Mode A) = News + Geopolitical + Fundamental + Momentum** (range −11 to +11)

Ranking:
- "Likely to rise today": scores ≥ +3, sorted descending, cap 10 per market
- "Likely to fall today": scores ≤ −3, sorted ascending, cap 10 per market
- "On the radar": scores −2 to +2 with notable news

### ─── MODE B: INDIA INTRADAY ───

#### Phase B1 — Social Media & Exchange Filing Scan (run FIRST — leads price action by 30–60 min)

**Twitter/X searches (5–7):**
- "NSE" OR "BSE" deal signed today [DATE]
- "small cap" stock deal announcement today India
- "order win" OR "contract win" NSE today [DATE]
- "MoU signed" OR "agreement signed" India stock today
- "QIP" OR "block deal" India today [DATE]
- "circuit breaker" OR "upper circuit" NSE today
- "results today" NSE BSE beat
- "investment" "crore" stock India today

**Reddit / StockTwits (2–3):**
- site:reddit.com/r/IndiaInvestments OR site:reddit.com/r/DalalStreetTalks stock deal today
- "NSE" OR "BSE" small cap catalyst today

**BSE/NSE Exchange Filings — ground truth (always run these):**
- BSE India corporate announcements today [DATE]
- NSE India exchange filings today [DATE] order win contract
- BSE filing MoU agreement [DATE]
- Fetch BSE announcements page if URL appears in results

**Telegram summaries (indirect):**
- "Telegram" India stock deal today [DATE]
- "market guru" OR "stock operator" India deal today

For each signal: Ticker (NSE symbol), catalyst type, sentiment, source URL/filing ID.

#### Phase B2 — News Article Deep Scan (10–15 searches)

**Deal & Agreement News:**
- "signed agreement" OR "signed MoU" India stock [DATE]
- "order received" OR "order win" NSE stock today [DATE]
- "contract awarded" India listed company today
- "JV agreement" OR "joint venture" India stock today
- "government contract" India company stock [DATE]
- "partnership announced" India company stock today [DATE]

**Investment & Capital Events:**
- "QIP" India stock today [DATE]
- "FII bought" OR "DII bought" India stock today
- "promoter bought" India stock [DATE]
- "PE investment" OR "VC investment" India company today
- "block deal" NSE BSE today [DATE]
- "rights issue" OR "bonus shares" India stock today

**Results & Earnings:**
- "quarterly results" India stock beat today [DATE]
- NSE earnings today beat expectations [DATE]

**Regulatory Approvals:**
- "SEBI approval" stock India today
- "NCLT approval" OR "CCI approval" India company today
- "drug approval" OR "CDSCO approval" pharma India today

**Sector-Specific (run whichever are active):**
- defence stock order India today [DATE]
- railway stock order win today India
- power sector contract India today
- pharma India approval today
- real estate deal India listed company today
- IT company deal India today [DATE]

**Broader Context (2–3 only):**
- Nifty 50 outlook today [DATE]
- FII DII flow India today [DATE]
- RBI news today India markets

Preferred sources: Economic Times, Moneycontrol, LiveMint, Business Standard, CNBCTV18, Financial Express, BSE India (bseindia.com), NSE India (nseindia.com).

Extract from each article:
- NSE ticker symbol
- Company name
- Catalyst type (Deal / Order Win / Investment / Result Beat / Approval / Block Deal / Other)
- Deal size ₹ crore (if mentioned)
- Counterparty
- One-line summary in YOUR own words
- Prior downtrend? (Yes → flag 🔄 Reversal Candidate)
- Source URL

#### Phase B3 — Cap Classification

| Tier | Market Cap |
|---|---|
| Large Cap | > ₹20,000 crore |
| Mid Cap | ₹5,000 – ₹20,000 crore |
| Small Cap | < ₹5,000 crore |

For small caps, additionally flag:
- "Recent Investment" if PE/VC/promoter/FII buy within last 7 days
- "Exchange Filing Today" if BSE/NSE announcement filed today
- "Social Buzz" if appeared in Phase B1

Target: 8–10 candidates per tier. If short, run tier-specific searches:
- Large cap: Nifty 100 stock deal announcement today
- Mid cap: "mid cap" India stock news today [DATE]
- Small cap: "small cap" India stock deal today

#### Phase B4 — Intraday Signal Score (ISS, 0–20)

**Catalyst Score (0–10) — the anchor:**

| Catalyst | Score |
|---|---|
| Major deal/order > ₹500 Cr, named counterparty, confirmed BSE/NSE filing | 10 |
| Deal/order ₹100–500 Cr, confirmed filing | 8 |
| Regulatory approval (drug, SEBI, NCLT) today | 8 |
| Result beat PAT > 15% above estimates | 8 |
| QIP / block deal / FII/DII large buy today | 7 |
| Deal/order < ₹100 Cr OR media-only (no filing yet) | 6 |
| Result beat PAT 5–15% above estimates | 6 |
| Promoter purchase today | 6 |
| JV / MoU announced (no size yet) | 4 |
| Analyst upgrade with meaningful target raise today | 5 |
| Vague social media buzz, no confirmed filing | 2 |

**Social Amplification Score (0–3):**
- +3: Trending simultaneously on Twitter + Telegram + Reddit
- +2: Trending on one platform with high engagement
- +1: Mentioned in a few posts
- +0: Not visible

**Momentum Context Score (0–4):**
- +4: Already up pre-market / early session with volume spike
- +3: Flat/slightly down recently — fresh catalyst creates reversal
- +2: Mild uptrend — catalyst adds fuel
- +1: Downtrend but catalyst is strong enough for intraday reversal
- +0: Deep downtrend + weak catalyst

Note: A stock falling for weeks with Catalyst Score ≥ 8 is STILL a valid pick. Prior trend does not disqualify. Mark 🔄.

**Liquidity Score (0–3):**
- +3: High (avg daily volume > 5L shares or ₹10 Cr turnover)
- +2: Medium (1–5L shares)
- +1: Low (< 1L shares, but deal confirmed)
- +0: Illiquid / no data

**ISS = Catalyst + Social + Momentum + Liquidity (max 20)**

Prediction tier from ISS:

| ISS | Tier |
|---|---|
| 15–20 | 🚀 >10% Intraday Surge Potential |
| 10–14 | 📈 >5% Intraday Gain Potential |
| 5–9 | 👀 Watch — Moderate Upside |
| Negative catalyst | 📉 Likely to Fall Today |

Negative ISS triggers (for fall predictions):
- Earnings miss PAT > 10% below estimates: −8
- Regulatory action / SEBI notice / ED raid: −9
- Deal cancellation / order cancellation: −7
- Promoter pledge increase / insider sell: −6
- Analyst downgrade with target cut: −5
- Confirmed negative news + social pile-on: −4

#### Phase B5 — Select Final Intraday Predictions

**Mandatory: Exactly 5 picks per cap tier = 15 total predictions.**

Rules:
- Pick top 5 by ISS per tier where Catalyst Score ≥ 4.
- If fewer than 5 confirmed in a tier, include best available with note "Lower conviction — monitor entry."
- Include at least 1 Reversal Candidate (🔄) per tier where possible.
- "Likely to Fall" picks can appear in any tier — aim for ≥ 3 total fall predictions across all tiers.
- Never repeat a ticker across tiers.

Each pick must document:
- NSE ticker + company name
- Current price (₹) + prior day change %
- Cap tier (Large / Mid / Small)
- Prediction tier (🚀 >10% / 📈 >5% / 👀 Watch / 📉 Fall)
- ISS score breakdown: Catalyst(X) + Social(X) + Momentum(X) + Liquidity(X) = Total
- Catalyst: what deal/event, size, counterparty, when announced
- Source URL (BSE filing or news article)
- Reversal Candidate? Yes/No + brief comment on prior trend
- Intraday entry note (e.g. "Watch gap-up above ₹XXX")
- Risk note (one line on what could go wrong intraday)

---

### ─── COMBINED WEBSITE BUILD ───

#### Phase C1 — Build the HTML

One self-contained HTML file. Dark mode default. No external CDN. All CSS and JS inline. Use `assets/template.html` as the scaffold.

Required sections in this order:

1. **Header** — Title "Market Briefing + India Intraday — [DATE]", generation timestamp, one-sentence overall market tone, quick stat bar (total picks, reversal candidates, fall predictions, geopolitical themes active)
2. **India Intraday Hub** (most prominent, first after header) — Three columns Large/Mid/Small Cap, cards sorted by ISS descending, color-coded (🚀 gold/amber, 📈 green, 📉 red, 👀 grey). Each card: ticker, company, price, prior day %, prediction badge, cap tier badge, catalyst type badge, 🔄 badge if reversal, catalyst paragraph, why-today paragraph, source link, entry note, risk note, ISS breakdown
3. **Deal Flow Timeline** — All India deals/events today sorted by size descending. Table: Time | Company | Ticker | Deal Type | Size (₹ Cr) | Counterparty | ISS | Tier
4. **Small Cap Spotlight** — small caps with recent PE/VC/promoter/FII investment (last 7 days), even if not top-5. Fields: Ticker, Company, Investor, Amount, Why It Might Move Today, Filing Link
5. **Sector Pulse** — grid: Defence / Pharma / IT / Power & Renewables / Real Estate / Railways / Banking & NBFC / Chemicals, each 🟢/🔴/⚪ + one-line reason
6. **Global Market Overview** (Mode A) — two columns US | India (Global), sorted by score, color-coded. Each pick: ticker, company, price, score, 2–4 sentence reasoning. 🌐 tag for geopolitically-driven picks. "On the radar" subsection.
7. **Geopolitical Impact** — 2–4 dominant themes, each: theme name, context paragraph, beneficiaries list, victims list, source links. If quiet: single note card.
8. **US Market News** — cards: paraphrased headline, tickers, catalyst type, summary paragraph, source link. Grouped by sector where thematic.
9. **India Market News** (macro/RBI/FII-DII flows, broader than intraday deal focus) — same structure as US news
10. **Fundamentals Appendix** — sortable HTML table, all tickers both modes. Columns: Ticker, Market, Cap Tier, Market Cap, Price, P/E, P/B, EPS TTM, Revenue TTM, Debt/Equity, ROE, 52W High, 52W Low, ISS (if applicable), Catalyst Type. Pure JS sort, no external libraries.
11. **Disclaimer Footer**:
> FOR INFORMATIONAL PURPOSES ONLY. This report is generated from public news sources, social media signals, exchange filings, and financial data. It is NOT investment advice. Intraday picks are for intraday use only — they are not recommendations for swing or long-term positions. Stock predictions are inherently uncertain; geopolitical events are particularly difficult to forecast. Reversal candidates carry additional risk from prior negative momentum. Always verify exchange filings directly on NSE/BSE before trading. Do your own research and consult a SEBI-registered or licensed financial advisor before making investment decisions.

#### Phase C2 — Save and Present

- Mode A+B combined: `/mnt/user-data/outputs/market-briefing-[YYYY-MM-DD].html`
- Mode B only: `/mnt/user-data/outputs/india-intraday-[YYYY-MM-DD].html`
- Mode A only: `/mnt/user-data/outputs/global-briefing-[YYYY-MM-DD].html`

Call `present_files` after saving.

#### Phase C3 — Chat Summary

After presenting the file, give a brief in-chat summary:
- Top pick per cap tier (ticker + one-line reason) from Mode B
- Top 1–2 names from Mode A rise/fall lists
- Any strong reversal candidates (prior downtrend + strong catalyst)
- Active geopolitical themes and which sectors they hit
- Any clustering of catalysts in one sector today

Do NOT dump the full report in chat. The website is the artifact. Chat is the 60-second briefing.

---

## Critical Rules

**Copyright**
- Never reproduce article headlines or body text verbatim
- All summaries must be your own paraphrase
- One quote under 15 words per source maximum
- Always include source URL

**Date Handling**
- Use the actual current date from the system prompt in all searches, filenames, and page titles. Never default to training-data dates.

**Intraday Discipline (Mode B)**
- Ask for every pick: "Does this catalyst move the stock TODAY?" If yes, it belongs. If it's a long-term growth story with no same-day trigger, drop it.

**Prior Downtrend Is NOT Disqualifying (Mode B)**
- A stock fallen 30% over 2 months but with a ₹200 Cr order win on BSE today IS a valid intraday pick. Mark 🔄. Note the prior trend in Risk. The catalyst overrides the trend for intraday purposes.

**Geopolitical Tilt Is Live-Only (Mode A)**
- Only apply geopolitical score when there's an active dated event in TODAY'S news. A defense stock doesn't get +3 in a quiet news week just because it's a defense stock.

**Ticker Disambiguation**
- US: NYSE/Nasdaq primary (e.g. AAPL, not AAPL.L)
- India: NSE symbol preferred (e.g. RELIANCE, TATAPOWER, IRFC); add .NS only when disambiguation needed
- India ADRs on US exchanges (INFY, WIT): put in US section, note the underlying Indian listing

**Currency & Number Formatting**
- US figures in USD ($); India figures in INR (₹). Never convert — reader expects native currency.
- India large numbers: use lakh/crore convention where source uses it; include USD equivalent in parentheses when helpful (e.g. "₹2,40,000 crore (~$28.8B)")

**Data Accuracy**
- Only label a deal "confirmed" if it appears in a BSE/NSE filing or named news publication
- Social media signals alone → Catalyst Score max 2, always add "Unconfirmed" tag
- Never fabricate prices, deal sizes, or counterparty names
- If price unavailable: note "Price unavailable — verify before trading"
- Missing fundamentals: show "—" in table, note "limited data" in reasoning

**Minimum Viable Run**
- If you can't find 5 candidates in a tier after exhaustive searching, state "Only X candidates found in [tier]" and present what you have. Never pad with fabricated or very weak signals.

**Honest Uncertainty**
- These are probabilistic calls based on public information. Use "likely to rise," "may face pressure" — not "will surge" or "guaranteed gains." The disclaimer is not optional.

## File Layout (original Claude skill)

```
market-analysis-daily/
├── SKILL.md                          ← this file
├── assets/
│   └── template.html                 ← HTML scaffold (dark/light, cards, sortable table)
└── references/
    ├── scoring-examples.md           ← ISS calibration + Mode A score calibration
    ├── sources.md                    ← canonical sources for India + US data
    └── geopolitical-playbook.md      ← event-type → sector/ticker winner/loser mapping
```

Read before running:
- `references/scoring-examples.md` before Phase A3 and Phase B4 — calibrates both scoring systems
- `references/sources.md` if unsure which site to fetch for a specific data type
- `references/geopolitical-playbook.md` as soon as a geopolitical theme is identified in Phase A1

---

## Porting notes (MarketResearcherAgentic project)

This file is preserved verbatim (from the user-supplied Claude skill) as the spec that `MarketResearcherAgentic` — a standalone Streamlit multi-agent app — is being built to replicate. The Streamlit app re-implements this workflow using its own orchestrator + specialist agent pipeline (Claude via Anthropic API) and free market-data APIs (yfinance, etc.) instead of Claude's native web-search/artifact tools. See project root `CLAUDE.md` / README for the current architecture mapping from skill phases → app modules.
