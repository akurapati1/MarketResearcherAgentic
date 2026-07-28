"""Streamlit renderers for the India Intraday report: stat bar, hub cards,
deal-flow timeline, small-cap spotlight, sector pulse grid, fundamentals
appendix, and the disclaimer footer."""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

import config
from agents.orchestrator import PipelineResult
from agents.schemas import StockPick
from data.scoring import PREDICTION_TIER_LABELS
from ui.styles import CSS, TIER_COLORS


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def _fmt_price(v) -> str:
    return f"₹{v:,.2f}" if v is not None else "—"


def _fmt_pct(v) -> str:
    return f"{v:+.2f}%" if v is not None else "—"


def _fmt_cr(v) -> str:
    return f"₹{v:,.0f} Cr" if v is not None else "—"


def _esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""


def render_stat_bar(result: PipelineResult) -> None:
    stats = [
        (result.total_picks, "Total Picks"),
        (result.reversal_count, "Reversal Candidates"),
        (result.fall_count, "Fall Predictions"),
        (result.active_sectors, "Active Sectors"),
    ]
    cells = "".join(
        f'<div class="mra-stat"><div class="mra-stat-value">{v}</div>'
        f'<div class="mra-stat-label">{_esc(label)}</div></div>'
        for v, label in stats
    )
    st.markdown(f'<div class="mra-stat-bar">{cells}</div>', unsafe_allow_html=True)


def _pick_card_html(pick: StockPick) -> str:
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


def render_hub(by_tier: dict[str, list[StockPick]]) -> None:
    st.subheader("India Intraday Hub")
    cols = st.columns(3)
    for col, tier in zip(cols, ["Large", "Mid", "Small"]):
        with col:
            st.markdown(f"**{tier} Cap**")
            picks = by_tier.get(tier, [])
            if not picks:
                st.caption("No qualifying candidates found today.")
            for pick in sorted(picks, key=lambda p: p.score.total, reverse=True):
                st.markdown(_pick_card_html(pick), unsafe_allow_html=True)


def render_deal_flow_timeline(all_picks: list[StockPick]) -> None:
    st.subheader("Deal Flow Timeline")
    if not all_picks:
        st.caption("No deals extracted today.")
        return
    rows = []
    for p in sorted(all_picks, key=lambda p: p.catalyst.deal_size_cr or 0, reverse=True):
        rows.append(
            {
                "Company": p.company,
                "Ticker": p.ticker,
                "Deal Type": p.catalyst.catalyst_type.replace("_", " ").title(),
                "Size (₹ Cr)": p.catalyst.deal_size_cr,
                "Counterparty": p.catalyst.counterparty or "—",
                "ISS": p.score.total,
                "Cap Tier": p.cap_tier,
                "Confirmed": "Yes" if p.catalyst.confirmed else "No",
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_small_cap_spotlight(spotlight: list[StockPick]) -> None:
    st.subheader("Small Cap Spotlight")
    if not spotlight:
        st.caption("No recent PE/VC/promoter/FII investment activity found in small caps today.")
        return
    rows = [
        {
            "Ticker": p.ticker,
            "Company": p.company,
            "Investor": p.catalyst.counterparty or "—",
            "Amount (₹ Cr)": p.catalyst.deal_size_cr,
            "Why it might move today": p.why_today_text or p.catalyst.summary,
            "Filing Link": p.catalyst.source_url or "—",
        }
        for p in spotlight
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_sector_pulse(sector_pulse: dict[str, dict]) -> None:
    st.subheader("Sector Pulse")
    tiles = []
    for sector in config.SECTORS:
        info = sector_pulse.get(sector, {"emoji": "⚪", "reason": "No notable catalysts today."})
        tiles.append(
            f'<div class="mra-sector-tile"><div class="mra-sector-name">{info["emoji"]} {_esc(sector)}</div>'
            f'<div class="mra-sector-reason">{_esc(info["reason"])}</div></div>'
        )
    st.markdown(f'<div class="mra-sector-grid">{"".join(tiles)}</div>', unsafe_allow_html=True)


def render_fundamentals_appendix(all_picks: list[StockPick]) -> None:
    st.subheader("Fundamentals Appendix")
    if not all_picks:
        st.caption("No tickers analyzed today.")
        return
    rows = []
    for p in all_picks:
        m = p.market
        rows.append(
            {
                "Ticker": p.ticker,
                "Cap Tier": p.cap_tier,
                "Market Cap (₹ Cr)": m.market_cap_cr,
                "Price": m.price,
                "Day Change %": m.day_change_pct,
                "P/E (TTM)": m.pe_ttm,
                "52W High": m.week52_high,
                "52W Low": m.week52_low,
                "Avg Volume": m.avg_volume,
                "ISS": p.score.total,
                "Catalyst Type": p.catalyst.catalyst_type.replace("_", " ").title(),
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_disclaimer() -> None:
    st.markdown(f'<div class="mra-disclaimer">{_esc(config.DISCLAIMER_TEXT)}</div>', unsafe_allow_html=True)
