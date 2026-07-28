"""Renders a self-contained, dark-mode HTML report — no external CDN/script
references — for parity with the original skill's report artifact. Kept free
of any Streamlit dependency so it could later run outside the app (e.g. a
scheduled script) if needed.
"""
from __future__ import annotations

import html

import config
from agents.orchestrator import PipelineResult
from agents.schemas import StockPick
from data.scoring import PREDICTION_TIER_LABELS
from ui.styles import CSS, TIER_COLORS


def _esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""


def _fmt_price(v) -> str:
    return f"₹{v:,.2f}" if v is not None else "—"


def _fmt_pct(v) -> str:
    return f"{v:+.2f}%" if v is not None else "—"


def _card_html(pick: StockPick) -> str:
    color = TIER_COLORS.get(pick.prediction_tier, "#8899a6")
    tier_label = PREDICTION_TIER_LABELS.get(pick.prediction_tier, pick.prediction_tier)

    badges = [f'<span class="mra-badge">{_esc(pick.cap_tier)} Cap</span>']
    badges.append(f'<span class="mra-badge">{_esc(pick.catalyst.catalyst_type.replace("_", " ").title())}</span>')
    if pick.reversal_candidate:
        badges.append('<span class="mra-badge reversal">🔄 Reversal</span>')
    if not pick.catalyst.confirmed:
        badges.append('<span class="mra-badge unconfirmed">Unconfirmed</span>')
    if pick.lower_conviction:
        badges.append('<span class="mra-badge lower-conviction">Lower conviction — monitor entry</span>')

    score = pick.score
    if pick.prediction_tier == "fall":
        iss_line = f"Negative catalyst score: {score.negative}"
    else:
        iss_line = (
            f"Catalyst({score.catalyst}) + Social({score.social}) + "
            f"Momentum({score.momentum}) + Liquidity({score.liquidity}) = {score.total}"
        )
    source_link = (
        f'<a href="{_esc(pick.catalyst.source_url)}" target="_blank">source</a>'
        if pick.catalyst.source_url
        else "source unavailable"
    )

    return f"""
<div class="mra-card" style="border-left-color: {color};">
    <div class="mra-title">{_esc(pick.ticker)} — {_esc(pick.company)}</div>
    <div class="mra-sub">{_fmt_price(pick.market.price)} &nbsp;({_fmt_pct(pick.market.day_change_pct)}) &nbsp;·&nbsp; {_esc(tier_label)}</div>
    <div>{''.join(badges)}</div>
    <div class="mra-section-label">Catalyst</div>
    <div class="mra-section-body">{_esc(pick.catalyst_text or pick.catalyst.summary)}</div>
    <div class="mra-section-label">Why today</div>
    <div class="mra-section-body">{_esc(pick.why_today_text)}</div>
    <div class="mra-section-label">Entry note</div>
    <div class="mra-section-body">{_esc(pick.entry_note)}</div>
    <div class="mra-section-label">Risk note</div>
    <div class="mra-section-body">{_esc(pick.risk_note)}</div>
    <div class="mra-iss-breakdown">ISS: {_esc(iss_line)}</div>
    <div class="mra-section-body" style="margin-top:6px;">{source_link}</div>
</div>
"""


def _hub_section(result: PipelineResult) -> str:
    columns = []
    for tier in ["Large", "Mid", "Small"]:
        picks = sorted(result.by_tier.get(tier, []), key=lambda p: p.score.total, reverse=True)
        cards = "".join(_card_html(p) for p in picks) or '<p style="color:#6b7280;">No qualifying candidates found today.</p>'
        columns.append(f'<div style="flex:1;min-width:280px;"><h3>{tier} Cap</h3>{cards}</div>')
    return f'<section><h2>India Intraday Hub</h2><div style="display:flex;gap:16px;flex-wrap:wrap;">{"".join(columns)}</div></section>'


def _deal_flow_section(all_picks: list[StockPick]) -> str:
    rows = sorted(all_picks, key=lambda p: p.catalyst.deal_size_cr or 0, reverse=True)
    if not rows:
        body = '<p style="color:#6b7280;">No deals extracted today.</p>'
    else:
        trs = "".join(
            f"<tr><td>{_esc(p.company)}</td><td>{_esc(p.ticker)}</td>"
            f"<td>{_esc(p.catalyst.catalyst_type.replace('_', ' ').title())}</td>"
            f"<td>{p.catalyst.deal_size_cr if p.catalyst.deal_size_cr is not None else '—'}</td>"
            f"<td>{_esc(p.catalyst.counterparty or '—')}</td><td>{p.score.total}</td>"
            f"<td>{_esc(p.cap_tier)}</td></tr>"
            for p in rows
        )
        body = (
            '<table style="width:100%;border-collapse:collapse;color:#d3d8e0;">'
            "<thead><tr><th>Company</th><th>Ticker</th><th>Deal Type</th>"
            "<th>Size (₹ Cr)</th><th>Counterparty</th><th>ISS</th><th>Tier</th></tr></thead>"
            f"<tbody>{trs}</tbody></table>"
        )
    return f"<section><h2>Deal Flow Timeline</h2>{body}</section>"


def _sector_pulse_section(sector_pulse: dict[str, dict]) -> str:
    tiles = []
    for sector in config.SECTORS:
        info = sector_pulse.get(sector, {"emoji": "⚪", "reason": "No notable catalysts today."})
        tiles.append(
            f'<div class="mra-sector-tile"><div class="mra-sector-name">{info["emoji"]} {_esc(sector)}</div>'
            f'<div class="mra-sector-reason">{_esc(info["reason"])}</div></div>'
        )
    return f'<section><h2>Sector Pulse</h2><div class="mra-sector-grid">{"".join(tiles)}</div></section>'


def build_html_report(result: PipelineResult) -> str:
    generated = result.generated_at.strftime("%A, %B %d, %Y %H:%M")
    sections = [
        _hub_section(result),
        _deal_flow_section(result.all_picks),
        _sector_pulse_section(result.sector_pulse),
    ]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>India Intraday Briefing — {_esc(generated)}</title>
{CSS}
<style>
body {{ background:#0b0e13; color:#e6e9ef; font-family: -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px; }}
h1 {{ margin-bottom: 4px; }}
.mra-generated {{ color:#6b7280; margin-bottom: 20px; }}
section {{ margin-bottom: 28px; }}
</style>
</head>
<body>
<h1>India Intraday Briefing — {_esc(generated)}</h1>
<div class="mra-generated">Generated by MarketResearcherAgentic — {result.total_picks} picks,
{result.reversal_count} reversal candidates, {result.fall_count} fall predictions.</div>
{"".join(sections)}
<div class="mra-disclaimer">{_esc(config.DISCLAIMER_TEXT)}</div>
</body>
</html>"""
