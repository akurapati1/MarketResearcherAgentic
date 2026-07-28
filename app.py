"""MarketResearcherAgentic — Streamlit entrypoint.

Multi-agent port of the `market-analysis-daily` Claude skill's India Intraday
mode (Mode B). See docs/skill-reference/market-analysis-daily/SKILL.md for the
authoritative spec this app reproduces.
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

import config
from agents.orchestrator import PipelineResult, run_pipeline
from report.html_export import build_html_report
from ui.components import (
    inject_css,
    render_deal_flow_timeline,
    render_disclaimer,
    render_fundamentals_appendix,
    render_hub,
    render_sector_pulse,
    render_small_cap_spotlight,
    render_stat_bar,
)

st.set_page_config(page_title="India Intraday Briefing", page_icon="📈", layout="wide")
inject_css()

with st.sidebar:
    st.title("📈 MarketResearcherAgentic")
    st.caption("Multi-agent port of the `market-analysis-daily` skill — India Intraday mode.")

    if config.ANTHROPIC_API_KEY:
        st.success("Anthropic API key configured", icon="✅")
    else:
        st.error("ANTHROPIC_API_KEY not set", icon="⚠️")
        st.caption("Copy `.env.example` to `.env` and add your key from console.anthropic.com.")

    if config.REDDIT_ENABLED:
        st.success("Reddit social signal enabled", icon="✅")
    else:
        st.info("Reddit credentials not set — social score will use the news-hit-count proxy only.", icon="ℹ️")

    st.divider()
    run_disabled = not config.ANTHROPIC_API_KEY
    run_clicked = st.button("Run India Intraday Analysis", type="primary", disabled=run_disabled, width="stretch")

    if st.session_state.get("result"):
        result: PipelineResult = st.session_state["result"]
        st.divider()
        st.caption(f"Last run: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        html_report = build_html_report(result)
        st.download_button(
            "Download HTML report",
            data=html_report,
            file_name=f"india-intraday-{result.generated_at.strftime('%Y-%m-%d')}.html",
            mime="text/html",
            width="stretch",
        )

if run_clicked:
    with st.status("Running India Intraday analysis…", expanded=True) as status:
        def on_progress(phase: str) -> None:
            status.write(phase)

        try:
            result = run_pipeline(on_progress=on_progress)
            st.session_state["result"] = result
            status.update(label="Analysis complete", state="complete")
        except Exception as exc:  # surfaced to the user, not a silent failure
            status.update(label="Analysis failed", state="error")
            st.exception(exc)

result: PipelineResult | None = st.session_state.get("result")

if result is None:
    st.title(f"India Intraday Briefing — {datetime.now().strftime('%A, %B %d, %Y')}")
    st.info(
        "Run the analysis from the sidebar to generate today's India intraday picks. "
        "Mode B (India Intraday) only — Global Briefing (US + India + geopolitical) is "
        "planned as a follow-up."
    )
else:
    st.title(f"India Intraday Briefing — {result.generated_at.strftime('%A, %B %d, %Y')}")
    st.caption(f"Generated {result.generated_at.strftime('%H:%M:%S')}")

    render_stat_bar(result)
    render_hub(result.by_tier)
    render_deal_flow_timeline(result.all_picks)
    render_small_cap_spotlight(result.small_cap_spotlight)
    render_sector_pulse(result.sector_pulse)
    render_fundamentals_appendix(result.all_picks)
    render_disclaimer()
