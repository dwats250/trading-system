# ============================================================
# MACRO SUITE — Macro Pulse HTML Dashboard
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone
from html import escape

from config.tickers import MACRO_SYMBOLS
from core.fetcher import fetch_all
from core.formatter import arrow, fmt_pct, fmt_price
from macro.focus import route
from macro.incidents import detect
from macro.playbook import generate
from macro.regime import classify, cross_asset_read, drivers
from macro.session import current_session
from outputs.shared import (
    card_block,
    ensure_output_dir,
    footer,
    nav_links,
    page_shell,
    section_block,
    stat_block,
)

_ASSET_SPECS = [
    ("DXY", "Dollar Index", -1),
    ("10Y", "US 10Y Yield", -1),
    ("WTI", "WTI Crude", -1),
    ("XAU", "Gold", 1),
    ("XAG", "Silver", 1),
    ("SPY", "SPY", 1),
    ("ES", "S&P Futures", 1),
    ("QQQ", "QQQ", 1),
    ("NQ", "Nasdaq Futures", 1),
    ("VIX", "VIX", -1),
]

_PAGE_CSS = """
    .incident-banner,
    .asset-card,
    .watch-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        box-shadow: var(--shadow);
    }
    .incident-banner,
    .dash-card {
        padding: 16px;
        margin-bottom: 16px;
    }
    .card-kicker {
        color: var(--blue);
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 10px;
    }
    .summary-card { margin-bottom: 16px; }
    .summary-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 14px;
    }
    .summary-title {
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .summary-meta {
        color: var(--muted);
        font-size: 0.88rem;
        margin-top: 4px;
    }
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
    }
    .incident-banner {
        background: rgba(127,29,29,0.32);
        border-color: rgba(224,108,117,0.35);
    }
    .incident-item {
        color: #f2b3b8;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
    }
    .asset-card,
    .watch-card {
        padding: 14px;
    }
    .asset-card {
        min-height: 136px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .asset-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 10px;
    }
    .asset-label {
        color: var(--muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .asset-symbol {
        color: var(--text);
        font-size: 1rem;
        font-weight: 700;
        margin-top: 2px;
    }
    .asset-value {
        font-size: 1.35rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .asset-change {
        font-size: 0.9rem;
        font-weight: 700;
    }
    .asset-meta {
        margin-top: auto;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 8px;
    }
    .status-badge {
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        border: 1px solid transparent;
    }
    .status-bullish {
        color: #a8d69e;
        background: rgba(152,195,121,0.12);
        border-color: rgba(152,195,121,0.3);
    }
    .status-bearish {
        color: #e89099;
        background: rgba(224,108,117,0.12);
        border-color: rgba(224,108,117,0.3);
    }
    .status-neutral {
        color: #ecd09a;
        background: rgba(229,192,123,0.12);
        border-color: rgba(229,192,123,0.3);
    }
    .asset-asof {
        color: var(--muted);
        font-size: 0.72rem;
    }
    .focus-copy {
        color: var(--text);
        font-size: 0.94rem;
        line-height: 1.6;
    }
    .watchlist-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 10px;
    }
    .watch-top {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    .watch-ticker {
        font-size: 1rem;
        font-weight: 800;
    }
    .watch-note {
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.5;
    }
"""


def _move_cls(pct: float | None) -> str:
    if pct is None:
        return "flat"
    if pct > 0:
        return "up"
    if pct < 0:
        return "dn"
    return "flat"


def _market_ref(data_map: dict) -> str:
    refs = [item.get("as_of") for item in data_map.values() if item and item.get("as_of")]
    return refs[0] if refs else "n/a"


def _asset_status(pct: float, orientation: int) -> tuple[str, str]:
    score = pct * orientation
    if score > 0:
        return "bullish", "status-bullish"
    if score < 0:
        return "bearish", "status-bearish"
    return "neutral", "status-neutral"


def _macro_dashboard(data_map: dict) -> str:
    cards = []
    for symbol, label, orientation in _ASSET_SPECS:
        data = data_map.get(symbol)
        if not data:
            continue
        pct = float(data.get("pct", 0.0))
        move_cls = _move_cls(pct)
        status_text, status_cls = _asset_status(pct, orientation)
        cards.append(f"""
        <div class="asset-card">
            <div class="asset-head">
                <div>
                    <div class="asset-label">{label}</div>
                    <div class="asset-symbol">{symbol}</div>
                </div>
                <span class="status-badge {status_cls}">{status_text}</span>
            </div>
            <div class="asset-value">{fmt_price(data.get("price"))}</div>
            <div class="asset-change {move_cls}">{arrow(pct)} {fmt_pct(pct)}</div>
            <div class="asset-meta">
                <span class="asset-asof">As of {escape(data.get("as_of") or "n/a")}</span>
            </div>
        </div>""")
    return "".join(cards)


def _summary_block(now: str, utc_str: str, market_ref: str, session: str, regime: str, primary: str, secondary: str) -> str:
    return card_block(
        f"""
        <div class="summary-top">
            <div>
                <div class="summary-title">Macro Pulse</div>
                <div class="summary-meta">Generated: {now} &nbsp;·&nbsp; Market ref: {utc_str} &nbsp;·&nbsp; Prices as of {market_ref}</div>
                {nav_links("macro_pulse")}
            </div>
        </div>
        <div class="summary-grid">
            {stat_block("Session", session)}
            {stat_block("Regime", regime)}
            {stat_block("Primary Driver", primary)}
            {stat_block("Secondary Driver", secondary)}
        </div>
        """,
        extra_cls="summary-card",
    )


def _market_posture(data_map: dict, regime: str) -> str:
    dxy = float(data_map.get("DXY", {}).get("pct", 0.0) or 0.0)
    tnx = float(data_map.get("10Y", {}).get("pct", 0.0) or 0.0)
    vix = float(data_map.get("VIX", {}).get("pct", 0.0) or 0.0)
    hyg = float(data_map.get("HYG", {}).get("pct", 0.0) or 0.0)
    btc = float(data_map.get("BTC", {}).get("pct", 0.0) or 0.0)

    risk_posture = regime.title()
    if btc > 0 and hyg > 0:
        liquidity = "Improving"
    elif dxy > 0 or tnx > 0 or hyg < 0:
        liquidity = "Tightening"
    else:
        liquidity = "Balanced"

    if vix > 1.0:
        volatility = "Elevated"
    elif vix < -1.0:
        volatility = "Compressing"
    else:
        volatility = "Contained"

    return f"""
    <div class="dash-card">
        <div class="card-kicker">Market Posture</div>
        <div class="stat-grid">
            {stat_block("Risk Tone", risk_posture)}
            {stat_block("Liquidity Tone", liquidity)}
            {stat_block("Volatility Condition", volatility)}
        </div>
    </div>"""


def _focus_section(regime: str, primary: str, secondary: str, read: str, data_map: dict) -> str:
    playbook = generate(regime, primary, secondary)
    major_moves = []
    for symbol, _, _ in _ASSET_SPECS:
        data = data_map.get(symbol)
        if data and abs(float(data.get("pct", 0.0))) >= 1.0:
            major_moves.append(f"{symbol} {fmt_pct(float(data['pct']))}")
    move_line = ", ".join(major_moves[:3])

    parts = [read]
    if playbook["notes"]:
        parts.append(playbook["notes"][0])
    if move_line:
        parts.append(f"Large moves: {move_line}.")

    copy = " ".join(part.rstrip(".") + "." for part in parts if part)
    return f"""
    <div class="dash-card">
        <div class="card-kicker">What Matters Today</div>
        <div class="focus-copy">{escape(copy)}</div>
    </div>"""


def _watchlist_preview(regime: str, primary: str, secondary: str) -> str:
    focus = route(primary, secondary, regime)
    names = [(ticker, "Primary focus") for ticker in focus["primary"]]
    names.extend((ticker, "Secondary focus") for ticker in focus["secondary"])
    names = names[:5]
    if not names:
        return ""

    if focus["sub_regime"] in {"OIL-DRIVEN", "METALS-DRIVEN", "RISK-ON"}:
        bias = "LONG"
        badge_cls = "long"
    elif regime == "RISK OFF":
        bias = "SHORT"
        badge_cls = "short"
    else:
        bias = "NEUTRAL"
        badge_cls = "neutral"

    cards = []
    for ticker, note in names:
        cards.append(f"""
        <div class="watch-card">
            <div class="watch-top">
                <span class="watch-ticker">{escape(ticker)}</span>
                <span class="bias-badge {badge_cls}">{bias}</span>
            </div>
            <div class="watch-note">{escape(note)}</div>
        </div>""")

    warning = (
        f'<div class="section-subtitle">{escape(focus["warning"])}</div>'
        if focus.get("warning") else ""
    )
    return section_block(
        title="Watchlist Preview",
        content=f'{warning}<div class="watchlist-grid">{"".join(cards)}</div>',
        action_html='<a class="section-action" href="premarket.html">Open Pre-Market →</a>',
    )


def build_html(data_map: dict | None = None) -> str:
    if data_map is None:
        data_map = fetch_all(MACRO_SYMBOLS)

    local_now = datetime.now().astimezone()
    utc_now = datetime.now(timezone.utc)
    now = local_now.strftime("%A, %B %d %Y  —  %I:%M %p %Z")
    utc_str = utc_now.strftime("%H:%M UTC")
    market_ref = _market_ref(data_map)
    session = current_session()
    regime = classify(data_map)
    primary, secondary = drivers(data_map)
    incidents = detect(data_map)
    read = cross_asset_read(data_map)

    incident_html = ""
    if incidents:
        items = "".join(f'<div class="incident-item">⚠ {escape(item)}</div>' for item in incidents)
        incident_html = f"""
        <div class="incident-banner">
            <div class="card-kicker">Active Incidents</div>
            {items}
        </div>"""

    body = f"""
    {_summary_block(now, utc_str, market_ref, session, regime, primary, secondary)}

    {_market_posture(data_map, regime)}

    {_focus_section(regime, primary, secondary, read, data_map)}

    {incident_html}

    {section_block("Macro Dashboard", f'<div class="dashboard-grid">{_macro_dashboard(data_map)}</div>')}

    {_watchlist_preview(regime, primary, secondary)}

    {footer("Macro Pulse")}
    """

    return page_shell(
        title="Macro Pulse",
        body_html=body,
        extra_css=_PAGE_CSS,
    )


def save(path: str = "macro_pulse.html", data_map: dict | None = None) -> None:
    """Write the HTML dashboard to a file."""
    if path.startswith("reports/output/"):
        ensure_output_dir()
    html = build_html(data_map)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved → {path}")


if __name__ == "__main__":
    print(build_html())
