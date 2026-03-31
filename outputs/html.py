# ============================================================
# MACRO SUITE — HTML Dashboard Output
# ============================================================
# Generates a self-contained HTML file from live macro data.
# Run:  python outputs/html.py > macro_pulse.html
# Then open macro_pulse.html in a browser.
# ============================================================

from __future__ import annotations

from datetime import datetime

from config.tickers import MACRO_SYMBOLS
from core.fetcher import fetch_all
from core.formatter import arrow, fmt_pct, fmt_price
from macro.incidents import detect
from macro.regime import classify, cross_asset_read, drivers
from macro.session import current_session


# ── Data → HTML helpers ──────────────────────────────────────

def _change_class(pct: float) -> str:
    if pct > 0:
        return "move-up"
    if pct < 0:
        return "move-down"
    return "move-flat"


def _macro_card(label: str, data: dict | None) -> str:
    if not data:
        value = "n/a"
        change = "n/a"
        css = "move-flat"
    else:
        value = fmt_price(data["price"])
        change = f"{arrow(data['pct'])} {fmt_pct(data['pct'])}"
        css = _change_class(data["pct"])

    return f"""
        <div class="card macro-card">
            <div class="card-label">{label}</div>
            <div class="card-value">{value}</div>
            <div class="card-change {css}">{change}</div>
        </div>"""


# ── HTML Template ────────────────────────────────────────────

_STYLE = """
        :root {
            --bg: #1b1f27;
            --panel: #252b36;
            --panel-2: #2a3140;
            --border: #374151;
            --text: #d8dee9;
            --muted: #8b93a6;
            --green: #98c379;
            --red: #e06c75;
            --yellow: #e5c07b;
            --blue: #61afef;
            --incident-bg: rgba(224,108,117,0.12);
            --incident-border: rgba(224,108,117,0.4);
            --shadow: 0 2px 16px rgba(0,0,0,0.4);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0; padding: 18px;
            font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'SF Mono', ui-monospace, monospace;
            background: var(--bg);
            color: var(--text);
        }
        .container { max-width: 1100px; margin: 0 auto; }
        .hero {
            background: linear-gradient(180deg, rgba(19,34,63,0.98), rgba(12,22,42,0.98));
            border: 1px solid var(--border); border-radius: 18px;
            padding: 18px; box-shadow: var(--shadow); margin-bottom: 16px;
        }
        .hero-top {
            display: flex; justify-content: space-between;
            align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 14px;
        }
        .title-block h1 { margin: 0 0 6px 0; font-size: 1.7rem; line-height: 1.15; }
        .subtitle { color: var(--muted); font-size: 0.95rem; }
        .timestamp { color: var(--muted); font-size: 0.92rem; white-space: nowrap; }
        .pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
        .pill {
            background: rgba(96,165,250,0.1); border: 1px solid rgba(96,165,250,0.25);
            color: #dbeafe; padding: 7px 10px; border-radius: 999px; font-size: 0.88rem;
        }
        .pill strong { color: white; }
        .summary-box {
            background: rgba(255,255,255,0.03); border: 1px solid var(--border);
            border-radius: 14px; padding: 14px;
        }
        .summary-title {
            color: var(--muted); font-size: 0.82rem;
            text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;
        }
        .summary-text { font-size: 1rem; line-height: 1.45; }
        .incident-banner {
            background: var(--incident-bg); border: 1px solid var(--incident-border);
            border-radius: 14px; padding: 14px; margin-bottom: 16px; box-shadow: var(--shadow);
        }
        .incident-title {
            font-size: 0.82rem; text-transform: uppercase;
            letter-spacing: 0.08em; opacity: 0.9; margin-bottom: 6px;
        }
        .incident-text { font-size: 1rem; font-weight: bold; }
        .section { margin-bottom: 18px; }
        .section-title { font-size: 1.05rem; font-weight: bold; margin: 0 0 10px 0; color: #f8fbff; }
        .grid { display: grid; gap: 10px; }
        .macro-grid { grid-template-columns: repeat(auto-fit, minmax(125px, 1fr)); }
        .card {
            background: linear-gradient(180deg, rgba(20,33,61,0.98), rgba(14,24,44,0.98));
            border: 1px solid var(--border); border-radius: 16px;
            padding: 14px; box-shadow: var(--shadow);
        }
        .macro-card { min-height: 108px; display: flex; flex-direction: column; justify-content: space-between; }
        .card-label { color: var(--muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
        .card-value { font-size: 1.25rem; font-weight: bold; line-height: 1.15; }
        .card-change { font-size: 0.96rem; font-weight: bold; margin-top: 8px; }
        .move-up   { color: var(--green); }
        .move-down { color: var(--red); }
        .move-flat { color: var(--yellow); }
        .footer { color: var(--muted); text-align: center; font-size: 0.86rem; padding: 10px 0 2px; }
        @media (max-width: 600px) {
            body { padding: 12px; }
            .hero { padding: 14px; border-radius: 16px; }
            .title-block h1 { font-size: 1.45rem; }
            .card-value { font-size: 1.1rem; }
        }
"""


def build_html(data_map: dict | None = None) -> str:
    if data_map is None:
        data_map = fetch_all(MACRO_SYMBOLS)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    session = current_session()
    regime = classify(data_map)
    primary, secondary = drivers(data_map)
    incidents = detect(data_map)
    read = cross_asset_read(data_map)

    macro_cards = "".join(
        _macro_card(label, data_map.get(label))
        for label in MACRO_SYMBOLS
    )

    incident_html = ""
    if incidents:
        items = "".join(f"<div class='incident-text'>⚠ {i}</div>" for i in incidents)
        incident_html = f"""
        <div class="incident-banner">
            <div class="incident-title">Active Incidents</div>
            {items}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Macro Pulse</title>
    <style>{_STYLE}</style>
</head>
<body>
    <div class="container">
        <section class="hero">
            <div class="hero-top">
                <div class="title-block">
                    <h1>Macro Pulse</h1>
                    <div class="subtitle">Macro regime dashboard</div>
                </div>
                <div class="timestamp">{now}</div>
            </div>
            <div class="pill-row">
                <div class="pill"><strong>Session:</strong> {session}</div>
                <div class="pill"><strong>Regime:</strong> {regime}</div>
                <div class="pill"><strong>Primary:</strong> {primary}</div>
                <div class="pill"><strong>Secondary:</strong> {secondary}</div>
            </div>
            <div class="summary-box">
                <div class="summary-title">Cross-Asset Read</div>
                <div class="summary-text">{read}</div>
            </div>
        </section>

        {incident_html}

        <section class="section">
            <h2 class="section-title">Macro</h2>
            <div class="grid macro-grid">
                {macro_cards}
            </div>
        </section>

        <div class="footer">Macro Suite — Macro Pulse</div>
    </div>
</body>
</html>"""


def save(path: str = "macro_pulse.html", data_map: dict | None = None) -> None:
    """Write the HTML dashboard to a file."""
    html = build_html(data_map)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved → {path}")


if __name__ == "__main__":
    print(build_html())
