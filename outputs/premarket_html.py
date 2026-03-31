# ============================================================
# MACRO SUITE — Pre-Market HTML Dashboard
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone

from core.formatter import arrow, fmt_pct, fmt_price
from macro.incidents import detect
from macro.regime import classify, cross_asset_read, drivers
from macro.session import current_session
from reports.calendar import get_events, get_month_events

# ── Helpers ──────────────────────────────────────────────────


# ── Helpers ──────────────────────────────────────────────────

def _cls(pct: float) -> str:
    if pct > 0: return "up"
    if pct < 0: return "dn"
    return "flat"


def _fmt_change(change: float) -> str:
    sign = "+" if change >= 0 else ""
    if abs(change) >= 1000:
        return f"{sign}{change:,.0f}"
    return f"{sign}{change:.2f}"


def _regime_cls(regime: str) -> str:
    if regime == "RISK ON":  return "regime-on"
    if regime == "RISK OFF": return "regime-off"
    return "regime-mixed"


# ── Section builders ─────────────────────────────────────────

def _futures_cards(data_map: dict) -> str:
    futures = [("ES", "S&P 500 Fut"), ("NQ", "Nasdaq Fut"), ("RTY", "Russell Fut")]
    cards = []
    for label, name in futures:
        d = data_map.get(label)
        if not d:
            continue
        cls = _cls(d["pct"])
        cards.append(f"""
        <div class="fut-card">
            <div class="fut-name">{name}</div>
            <div class="fut-price">{fmt_price(d['price'])}</div>
            <div class="fut-change {cls}">{arrow(d['pct'])} {fmt_pct(d['pct'])}</div>
        </div>""")
    return "".join(cards)


def _macro_rows(data_map: dict) -> str:
    items = [
        ("DXY", "Dollar (DXY)"),
        ("10Y", "10Y Yield"),
        ("VIX", "VIX"),
        ("UJ",  "USD/JPY"),
        ("XAU", "Gold"),
        ("XAG", "Silver"),
        ("WTI", "WTI Oil"),
        ("BRT", "Brent Oil"),
        ("HYG", "HYG Credit"),
        ("BTC", "Bitcoin"),
        ("HG",  "Copper"),
    ]
    rows = []
    for label, name in items:
        d = data_map.get(label)
        if not d:
            continue
        cls = _cls(d["pct"])
        change     = d.get("change")
        change_html = f'<span class="row-change-dollar {cls}">{_fmt_change(change)}</span>' if change is not None else ""
        rows.append(f"""
        <tr>
            <td class="row-label">{name}</td>
            <td class="row-price">{fmt_price(d['price'])}</td>
            <td class="row-dollar">{change_html}</td>
            <td class="row-change {cls}">{arrow(d['pct'])} {fmt_pct(d['pct'])}</td>
        </tr>""")
    return "".join(rows)


def _calendar_rows(events: list[dict]) -> str:
    if not events:
        return '<tr><td colspan="4" class="no-events">No major events today</td></tr>'
    rows = []
    for e in events:
        impact_cls = "impact-high" if e["impact"] == "HIGH" else "impact-med"
        url = e.get("url", "#")
        rows.append(f"""
        <tr>
            <td class="ev-time">{e['time']} UTC</td>
            <td><span class="impact-badge {impact_cls}">{e['impact']}</span></td>
            <td class="ev-name"><a href="{url}" target="_blank" rel="noopener">{e['event']}</a></td>
            <td class="ev-est">{e['consensus']}</td>
        </tr>""")
    return "".join(rows)


def _primary_disqualifier(reasons: list[str]) -> str:
    """Single most important failure reason for trader-facing display."""
    checks = [
        ("regime",          "Conflicts with current macro regime"),
        ("R:R",             "R:R below 2:1 — risk not justified"),
        ("Chart grade",     "Chart not A-grade yet"),
        ("No clear chart",  "No clear setup structure"),
        ("liquidity",       "Options liquidity insufficient"),
    ]
    for keyword, label in checks:
        for r in reasons:
            if keyword.lower() in r.lower():
                return label
    return reasons[0] if reasons else "Failed guardrails"


def _structural_guardrails(setup, regime: str) -> list[str]:
    """
    Structural guardrail check applicable without options data.
    Mirrors the execution-level hard guardrails except for options liquidity,
    which requires the full sniper pipeline. Any setup failing here must not
    be ranked — it is demoted to the watchlist.
    """
    failures = []
    if setup.rr < 2.0:
        failures.append(f"R:R {setup.rr:.1f} — below 2:1 minimum")
    if setup.grade != "A":
        failures.append(f"Chart grade {setup.grade} — A required")
    if setup.setup_type == "none":
        failures.append("No clear chart structure")
    if (regime == "RISK ON"  and setup.bias == "SHORT") or \
       (regime == "RISK OFF" and setup.bias == "LONG"):
        failures.append(f"Direction conflicts with {regime}")
    return failures


def _setup_cards(setups: list, regime: str) -> str:
    """
    Three-tier presentation:
      1. Validated Top Trades     — passed all structural guardrails, actionable
      2. Watchlist Setups         — grade A/B with identifiable structure, but one
                                    guardrail blocks execution; shows primary blocker
      3. Not on radar             — grade C or no structure; compact list only

    No setup may appear in tier 1 unless it passes every structural guardrail.
    """
    validated = []
    watchlist = []   # good chart + structure, but blocked
    off_radar = []   # grade C or setup_type=none

    for s in setups:
        failures = _structural_guardrails(s, regime)
        if not failures:
            validated.append(s)
        elif s.grade in ("A", "B") and s.setup_type != "none":
            watchlist.append((s, failures))
        else:
            off_radar.append(s)

    bias_cls_map  = {"LONG": "bias-long", "SHORT": "bias-short"}
    grade_cls_map = {"A": "grade-a", "B": "grade-b", "C": "grade-c"}
    html = ""

    # ── Tier 1: Validated Top Trades ──────────────────────────
    if not validated:
        html += '<div class="no-setups">No validated trades today — stay flat or wait</div>'
    else:
        for s in validated[:3]:
            bias_cls  = bias_cls_map.get(s.bias, "bias-neutral")
            grade_cls = grade_cls_map.get(s.grade, "")
            html += f"""
            <div class="setup-card">
                <div class="setup-header">
                    <span class="setup-ticker">{s.ticker}</span>
                    <span class="setup-bias {bias_cls}">{s.bias}</span>
                    <span class="setup-grade {grade_cls}">{s.grade}</span>
                </div>
                <div class="setup-row">
                    <span class="setup-stat">Price <strong>{s.price}</strong></span>
                    <span class="setup-stat">RSI <strong>{s.rsi_val}</strong></span>
                    <span class="setup-stat">R:R <strong>{s.rr:.1f}:1</strong></span>
                </div>
                <div class="setup-levels">S: {s.support} &nbsp;|&nbsp; R: {s.resistance}</div>
                <div class="setup-entry">{s.entry_note}</div>
                <div class="setup-inv">Stop: {s.invalidation}</div>
            </div>"""

    # ── Tier 2: Watchlist — Good Structure, Not Trade-Ready ───
    if watchlist:
        html += """
        <div class="watchlist-label">Watchlist Setups — Good Structure, Not Trade-Ready</div>
        <div class="watchlist-note">Chart structure is identifiable but at least one guardrail blocks execution. Monitor only.</div>"""
        for s, reasons in watchlist[:5]:
            bias_cls   = bias_cls_map.get(s.bias, "bias-neutral")
            grade_cls  = grade_cls_map.get(s.grade, "")
            disqualifier = _primary_disqualifier(reasons)
            html += f"""
            <div class="watchlist-card {bias_cls}">
                <div class="watchlist-row">
                    <span class="watchlist-ticker">{s.ticker}</span>
                    <span class="setup-bias {bias_cls}" style="font-size:0.72rem;padding:1px 7px">{s.bias}</span>
                    <span class="watchlist-grade grade-{s.grade.lower()}">{s.grade}</span>
                </div>
                <div class="watchlist-blocker">Why not trading: {disqualifier}</div>
            </div>"""

    # ── Tier 3: Off radar ─────────────────────────────────────
    if off_radar:
        tickers = ", ".join(s.ticker for s in off_radar)
        html += f'<div class="off-radar">Not on radar (weak chart / no structure): {tickers}</div>'

    return html


def _upcoming_rows(events: list[dict]) -> str:
    if not events:
        return '<tr><td colspan="4" class="no-events">No major events remaining this month</td></tr>'
    rows = []
    current_date = None
    for e in events:
        d = e.get("date", "")
        if d != current_date:
            current_date = d
            try:
                from datetime import datetime as _dt
                label = _dt.strptime(d, "%Y-%m-%d").strftime("%a  %b %d")
            except Exception:
                label = d
            rows.append(f'<tr><td colspan="4" class="ev-date-header">{label}</td></tr>')
        url = e.get("url", "#")
        rows.append(f"""
        <tr>
            <td class="ev-time">{e['time']} UTC</td>
            <td><span class="impact-badge impact-high">HIGH</span></td>
            <td class="ev-name"><a href="{url}" target="_blank" rel="noopener">{e['event']}</a></td>
            <td class="ev-est">{e['consensus']}</td>
        </tr>""")
    return "".join(rows)


def _sector_rows(data_map: dict, extra: dict) -> str:
    combined = {**data_map, **extra}
    sections = [
        ("Metals",   ["XAU", "XAG", "GDX"]),
        ("Oil",      ["WTI", "BRT", "XLE"]),
        ("Equities", ["SPY", "QQQ", "IWM"]),
        ("Credit",   ["HYG", "BTC"]),
    ]
    rows = []
    for name, labels in sections:
        cells = []
        for label in labels:
            d = combined.get(label)
            if d:
                cls = _cls(d["pct"])
                cells.append(f'<span class="sector-item {cls}">{label} {arrow(d["pct"])} {fmt_pct(d["pct"])}</span>')
        if cells:
            rows.append(f"""
        <tr>
            <td class="sector-name">{name}</td>
            <td class="sector-cells">{"".join(cells)}</td>
        </tr>""")
    return "".join(rows)


# ── Stylesheet ───────────────────────────────────────────────

_STYLE = """
    :root {
        --bg: #1b1f27;
        --surface: #252b36;
        --surface2: #2a3140;
        --border: #374151;
        --text: #d8dee9;
        --muted: #8b93a6;
        --green: #98c379;
        --red: #e06c75;
        --yellow: #e5c07b;
        --blue: #61afef;
        --purple: #c678dd;
        --shadow: 0 2px 16px rgba(0,0,0,0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        background: var(--bg); color: var(--text);
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'SF Mono', ui-monospace, monospace;
        font-size: 14px; line-height: 1.6; padding: 16px;
    }
    .page { max-width: 1000px; margin: 0 auto; }

    /* Header */
    .report-header {
        background: linear-gradient(135deg, #252b36, #2a3140);
        border: 1px solid var(--border); border-radius: 10px;
        padding: 20px 24px; margin-bottom: 16px;
        display: flex; justify-content: space-between; align-items: center;
        flex-wrap: wrap; gap: 12px;
    }
    .report-title { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
    .report-meta { color: var(--muted); font-size: 0.88rem; margin-top: 4px; }
    .pill-group { display: flex; gap: 8px; flex-wrap: wrap; }
    .pill {
        padding: 6px 14px; border-radius: 999px; font-size: 0.82rem;
        font-weight: 600; letter-spacing: 0.04em; border: 1px solid;
    }
    .regime-on   { background: rgba(152,195,121,0.12); border-color: rgba(152,195,121,0.4); color: #a8d69e; }
    .regime-off  { background: rgba(224,108,117,0.12); border-color: rgba(224,108,117,0.4); color: #e89099; }
    .regime-mixed{ background: rgba(229,192,123,0.12); border-color: rgba(229,192,123,0.4); color: #ecd09a; }

    /* Sections */
    .section { margin-bottom: 16px; }
    .section-title {
        font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.1em; color: var(--muted); margin-bottom: 10px;
    }
    .card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 14px; padding: 16px; box-shadow: var(--shadow);
    }

    /* Futures */
    .futures-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .fut-card {
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 12px; padding: 14px; text-align: center;
    }
    .fut-name  { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
    .fut-price { font-size: 1.3rem; font-weight: 700; margin-bottom: 4px; }
    .fut-change { font-size: 0.95rem; font-weight: 600; }

    /* Macro table */
    .macro-table { width: 100%; border-collapse: collapse; }
    .macro-table tr { border-bottom: 1px solid rgba(55,65,81,0.5); }
    .macro-table tr:last-child { border-bottom: none; }
    .row-label  { color: var(--muted); padding: 7px 0; width: 38%; }
    .row-price  { font-weight: 600; padding: 7px 8px; }
    .row-dollar { padding: 7px 6px; font-size: 0.85rem; }
    .row-change { font-weight: 600; padding: 7px 0; text-align: right; }

    /* Calendar */
    .cal-table { width: 100%; border-collapse: collapse; }
    .cal-table tr { border-bottom: 1px solid rgba(55,65,81,0.5); }
    .cal-table tr:last-child { border-bottom: none; }
    .ev-time  { color: var(--muted); padding: 7px 12px 7px 0; white-space: nowrap; width: 110px; }
    .ev-name  { padding: 7px 8px; }
    .ev-est   { color: var(--muted); padding: 7px 0; text-align: right; font-size: 0.85rem; }
    .impact-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; }
    .impact-high { background: rgba(224,108,117,0.2); color: #e89099; }
    .impact-med  { background: rgba(97,175,239,0.15); color: #93c5fd; }
    .no-events   { color: var(--muted); padding: 12px 0; text-align: center; }
    .ev-date-header { background: rgba(30,58,95,0.4); color: var(--muted);
                      font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                      letter-spacing: 0.07em; padding: 6px 4px; }
    .ev-name a  { color: var(--text); text-decoration: none; }
    .ev-name a:hover { color: var(--blue); text-decoration: underline; }

    /* Setups */
    .setups-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }
    .setup-card {
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 12px; padding: 14px;
    }
    .setup-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    .setup-ticker { font-size: 1.1rem; font-weight: 700; }
    .setup-bias, .setup-grade {
        padding: 2px 10px; border-radius: 999px;
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;
    }
    .bias-long    { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .bias-short   { background: rgba(224,108,117,0.15); color: #e89099; }
    .bias-neutral { background: rgba(229,192,123,0.15); color: #ecd09a; }
    .grade-a { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .grade-b { background: rgba(229,192,123,0.15); color: #ecd09a; }
    .grade-c { background: rgba(139,147,166,0.15); color: #a3a8b4; }

    /* ── Watchlist — visually and semantically distinct from validated trades ── */
    .watchlist-label {
        margin-top: 20px; padding: 6px 0 2px;
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: #6b7280;
        border-top: 1px dashed rgba(75,85,99,0.4);
    }
    .watchlist-note {
        font-size: 0.75rem; color: #6b7280; margin-bottom: 8px; font-style: italic;
    }
    .watchlist-card {
        background: var(--surface); border: 1px solid var(--border);
        border-left-width: 3px; border-radius: 6px;
        padding: 8px 12px; margin-bottom: 5px;
    }
    .watchlist-card.bias-long  { border-left-color: var(--green); }
    .watchlist-card.bias-short { border-left-color: var(--red);   }
    .watchlist-card.bias-long  .watchlist-ticker { color: var(--green); }
    .watchlist-card.bias-short .watchlist-ticker { color: var(--red);   }
    .watchlist-row { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }
    .watchlist-ticker { font-weight: 700; font-size: 0.88rem; color: var(--muted); }
    .watchlist-grade  { font-size: 0.72rem; margin-left: auto; padding: 1px 7px;
                        border-radius: 4px; }
    .watchlist-blocker { font-size: 0.75rem; color: var(--muted); }
    .watchlist-blocker::before { content: "↳ "; color: var(--border); }
    /* Off-radar — minimal, no card treatment */
    .off-radar {
        margin-top: 10px; font-size: 0.72rem; color: #4b5563; font-style: italic;
    }
    .setup-row { display: flex; gap: 16px; margin-bottom: 6px; }
    .setup-stat { font-size: 0.85rem; color: var(--muted); }
    .setup-stat strong { color: var(--text); }
    .setup-levels { font-size: 0.82rem; color: var(--muted); margin-bottom: 8px; }
    .setup-entry { font-size: 0.88rem; color: var(--blue); border-top: 1px solid var(--border); padding-top: 8px; }
    .skip-list { color: var(--muted); font-size: 0.85rem; margin-top: 8px; }
    .no-setups { color: var(--muted); text-align: center; padding: 20px; }
    .regime-note {
        padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;
        font-size: 0.88rem; font-weight: 600;
        background: rgba(224,108,117,0.08); border: 1px solid rgba(224,108,117,0.2); color: #e89099;
    }
    .regime-note.on   { background: rgba(152,195,121,0.08); border-color: rgba(152,195,121,0.2); color: #a8d69e; }
    .regime-note.mixed{ background: rgba(229,192,123,0.08); border-color: rgba(229,192,123,0.2); color: #ecd09a; }

    /* Incidents */
    .incident-box {
        background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25);
        border-radius: 10px; padding: 10px 14px; margin-bottom: 12px;
    }
    .incident-item { color: #fca5a5; font-size: 0.88rem; margin: 2px 0; }

    /* Sector */
    .sector-table { width: 100%; border-collapse: collapse; }
    .sector-table tr { border-bottom: 1px solid rgba(30,58,95,0.5); }
    .sector-table tr:last-child { border-bottom: none; }
    .sector-name  { color: var(--muted); padding: 8px 12px 8px 0; width: 90px; font-weight: 600; }
    .sector-cells { padding: 8px 0; display: flex; flex-wrap: wrap; gap: 12px; }
    .sector-item  { font-size: 0.88rem; font-weight: 600; }

    /* Summary box */
    .summary-box {
        background: rgba(255,255,255,0.03); border: 1px solid var(--border);
        border-radius: 10px; padding: 12px 14px; margin-top: 12px;
        color: var(--muted); font-size: 0.9rem;
    }

    /* Colors */
    .up   { color: var(--green); }
    .dn   { color: var(--red); }
    .flat { color: var(--yellow); }

    /* Two-col layout */
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

    /* Footer */
    .footer { text-align: center; color: var(--muted); font-size: 0.8rem; padding: 20px 0 4px; }

    @media (max-width: 640px) {
        .futures-grid { grid-template-columns: 1fr; }
        .two-col { grid-template-columns: 1fr; }
        .setups-grid { grid-template-columns: 1fr; }
        .sector-cells { flex-direction: column; gap: 4px; }
    }
"""


# ── Full HTML builder ────────────────────────────────────────

def build_premarket_html(data_map: dict, setups: list, extra: dict | None = None,
                         month_events: list | None = None) -> str:
    if extra is None:
        extra = {}
    if month_events is None:
        month_events = []

    _local  = datetime.now().astimezone()
    _utc    = datetime.now(timezone.utc)
    now     = _local.strftime("%A, %B %d %Y  —  %I:%M %p %Z")
    utc_str = _utc.strftime("%H:%M UTC")
    session = current_session()
    _as_of_raw = next((d["as_of"] for d in data_map.values() if d and d.get("as_of")), None)
    data_as_of = f"Prices as of {_as_of_raw}" if _as_of_raw else "Prices as of —"
    regime = classify(data_map)
    primary, secondary = drivers(data_map)
    incidents = detect(data_map)
    read = cross_asset_read(data_map)
    events = get_events()

    regime_cls = _regime_cls(regime)

    incident_html = ""
    if incidents:
        items = "".join(f'<div class="incident-item">⚠ {i}</div>' for i in incidents)
        incident_html = f'<div class="incident-box">{items}</div>'

    regime_note_cls = "on" if regime == "RISK ON" else ("mixed" if regime == "MIXED" else "")
    regime_note_text = {
        "RISK OFF": "⚠ RISK OFF — reduce size, favor shorts or cash",
        "MIXED":    "~ Mixed environment — be selective",
        "RISK ON":  "✓ RISK ON — favorable for long setups",
    }.get(regime, regime)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pre-Market Report — {datetime.now().strftime('%b %d')}</title>
    <style>{_STYLE}</style>
</head>
<body>
<div class="page">

    <!-- Header -->
    <div class="report-header">
        <div>
            <div class="report-title">Pre-Market Report</div>
            <div class="report-meta">Generated: {now} &nbsp;·&nbsp; Market ref: {utc_str} &nbsp;·&nbsp; {data_as_of} &nbsp;·&nbsp; {session} Session</div>
        </div>
        <div class="pill-group">
            <span class="pill {regime_cls}">{regime}</span>
        </div>
    </div>

    <!-- Futures -->
    <div class="section">
        <div class="section-title">Overnight Futures</div>
        <div class="futures-grid">
            {_futures_cards(data_map)}
        </div>
    </div>

    <!-- Macro + Calendar side by side -->
    <div class="two-col">
        <div class="section">
            <div class="section-title">Macro Snapshot</div>
            <div class="card">
                <table class="macro-table">
                    {_macro_rows(data_map)}
                </table>
                <div class="summary-box">{read}</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Today's Events</div>
            <div class="card">
                {incident_html}
                <table class="cal-table">
                    {_calendar_rows(events)}
                </table>
                <div class="summary-box">
                    Primary: {primary}<br>
                    Secondary: {secondary}
                </div>
            </div>
        </div>
    </div>

    <!-- Upcoming This Month -->
    <div class="section">
        <div class="section-title">Upcoming This Month — High Impact Only</div>
        <div class="card">
            <table class="cal-table">
                {_upcoming_rows(month_events)}
            </table>
        </div>
    </div>

    <!-- Setups -->
    <div class="section">
        <div class="section-title">Validated Top Trades <span style="font-size:0.65rem;font-weight:400;color:var(--muted);margin-left:6px">structural guardrails only — options not yet validated</span></div>
        <div class="regime-note {regime_note_cls}">{regime_note_text}</div>
        <div class="setups-grid">
            {_setup_cards(setups, regime)}
        </div>
    </div>

    <!-- Sector -->
    <div class="section">
        <div class="section-title">Sector Snapshot</div>
        <div class="card">
            <table class="sector-table">
                {_sector_rows(data_map, extra)}
            </table>
        </div>
    </div>

    <div class="footer">Macro Suite — Pre-Market Report</div>
</div>
</body>
</html>"""


def save(path: str = "premarket.html", data_map: dict | None = None,
         setups: list | None = None, extra: dict | None = None,
         month_events: list | None = None) -> None:
    from config.tickers import MACRO_SYMBOLS, SNIPER_SYMBOLS
    from core.fetcher import fetch_all
    from sniper.scanner import scan

    if data_map is None:
        data_map = fetch_all(MACRO_SYMBOLS)
    if setups is None:
        setups = scan(SNIPER_SYMBOLS)
    if extra is None:
        extra = fetch_all({"GDX": ["GDX"], "IWM": ["IWM"]})
    if month_events is None:
        month_events = get_month_events()

    html = build_premarket_html(data_map, setups, extra, month_events)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved → {path}")
