"""Dark-mode CSS for the pick cards, badges, and grids — injected once at the
top of app.py. Cards render dark regardless of the viewer's Streamlit theme,
matching the original skill's "dark mode default" report styling."""

TIER_COLORS = {
    "surge": "#f5a623",  # 🚀 gold/amber
    "gain": "#2ecc71",  # 📈 green
    "watch": "#8899a6",  # 👀 grey
    "fall": "#e74c3c",  # 📉 red
}

CSS = """
<style>
.mra-card {
    background: #14181f;
    border: 1px solid #262b36;
    border-left-width: 5px;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 14px;
    color: #e6e9ef;
}
.mra-card .mra-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 2px;
}
.mra-card .mra-sub {
    font-size: 0.85rem;
    color: #9aa4b2;
    margin-bottom: 8px;
}
.mra-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    margin-right: 6px;
    margin-bottom: 6px;
    background: #262b36;
    color: #e6e9ef;
}
.mra-badge.reversal { background: #3a2a12; color: #f5a623; }
.mra-badge.unconfirmed { background: #3a1f1f; color: #e88; }
.mra-badge.lower-conviction { background: #2a2a2a; color: #ccc; }
.mra-section-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #6b7280;
    margin-top: 8px;
    margin-bottom: 2px;
}
.mra-section-body {
    font-size: 0.88rem;
    color: #d3d8e0;
    line-height: 1.4;
}
.mra-iss-breakdown {
    font-family: monospace;
    font-size: 0.8rem;
    color: #9aa4b2;
    margin-top: 8px;
}
.mra-stat-bar {
    display: flex;
    gap: 20px;
    background: #14181f;
    border: 1px solid #262b36;
    border-radius: 8px;
    padding: 12px 18px;
    margin-bottom: 18px;
}
.mra-stat {
    text-align: center;
}
.mra-stat .mra-stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #ffffff;
}
.mra-stat .mra-stat-label {
    font-size: 0.72rem;
    color: #9aa4b2;
    text-transform: uppercase;
}
.mra-sector-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    margin-bottom: 18px;
}
.mra-sector-tile {
    background: #14181f;
    border: 1px solid #262b36;
    border-radius: 8px;
    padding: 10px 12px;
}
.mra-sector-tile .mra-sector-name {
    font-weight: 600;
    color: #ffffff;
    font-size: 0.9rem;
}
.mra-sector-tile .mra-sector-reason {
    font-size: 0.78rem;
    color: #9aa4b2;
    margin-top: 2px;
}
.mra-disclaimer {
    font-size: 0.78rem;
    color: #6b7280;
    border-top: 1px solid #262b36;
    padding-top: 14px;
    margin-top: 24px;
    line-height: 1.5;
}
</style>
"""
