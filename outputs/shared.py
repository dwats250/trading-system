# ============================================================
# MACRO SUITE — Shared UI Foundation
# ============================================================
# All dashboard page builders import from here.
# Provides: unified CSS tokens, nav bar, report header,
# page shell wrapper, and footer helper.
# ============================================================

from __future__ import annotations

import os

OUTPUT_DIR = "reports/output"


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Shared CSS ───────────────────────────────────────────────
# Defines design tokens, base layout, nav, report header,
# cards, badges, and common utilities shared across all pages.
# Page-specific CSS lives in each output module as _PAGE_CSS.

SHARED_CSS = """
    :root {
        --bg:      #1b1f27;
        --surface: #252b36;
        --surface2:#2a3140;
        --border:  #374151;
        --text:    #d8dee9;
        --muted:   #8b93a6;
        --green:   #98c379;
        --red:     #e06c75;
        --yellow:  #e5c07b;
        --blue:    #61afef;
        --gold:    #e5c07b;
        --purple:  #c678dd;
        --shadow:  0 2px 16px rgba(0,0,0,0.5);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        background: var(--bg); color: var(--text);
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'SF Mono', ui-monospace, monospace;
        font-size: 14px; line-height: 1.6; padding: 16px;
    }
    .page { max-width: 1060px; margin: 0 auto; }

    /* ── Navigation ─────────────────────────────────────── */
    .nav-bar {
        display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
        margin-bottom: 14px; padding: 8px 14px;
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 10px; font-size: 0.78rem;
    }
    .nav-brand {
        color: var(--muted); font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; font-size: 0.72rem; margin-right: 10px;
        flex-shrink: 0;
    }
    .nav-link {
        color: var(--muted); text-decoration: none;
        padding: 3px 10px; border-radius: 999px; border: 1px solid transparent;
    }
    .nav-link:hover { background: rgba(96,165,250,0.1); color: var(--text); }
    .nav-link.active {
        background: rgba(96,165,250,0.12); color: #93c5fd;
        border-color: rgba(96,165,250,0.25);
    }
    .nav-sep { color: var(--border); margin: 0 2px; user-select: none; }

    /* ── Report header ──────────────────────────────────── */
    .report-header {
        background: linear-gradient(135deg, #252b36, #2a3140);
        border: 1px solid var(--border); border-radius: 10px;
        padding: 20px 24px; margin-bottom: 16px;
        display: flex; justify-content: space-between; align-items: flex-start;
        flex-wrap: wrap; gap: 16px;
    }
    .report-title { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; }
    .report-meta  { color: var(--muted); font-size: 0.88rem; margin-top: 4px; }
    .regime-block { text-align: right; flex-shrink: 0; }
    .regime-pill {
        display: inline-block; padding: 8px 20px; border-radius: 999px;
        font-size: 1rem; font-weight: 700; letter-spacing: 0.05em; border: 1px solid;
    }
    .regime-pill.off   { background: rgba(224,108,117,0.15); border-color: rgba(224,108,117,0.4); color: #e89099; }
    .regime-pill.on    { background: rgba(152,195,121,0.15); border-color: rgba(152,195,121,0.4); color: #a8d69e; }
    .regime-pill.mixed { background: rgba(229,192,123,0.15); border-color: rgba(229,192,123,0.4); color: #ecd09a; }
    .driver-text { color: var(--muted); font-size: 0.82rem; margin-top: 6px; }

    /* ── Cards ──────────────────────────────────────────── */
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
    .card-title {
        font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: var(--muted); margin-bottom: 12px;
    }

    /* ── Sections ───────────────────────────────────────── */
    .section { margin-bottom: 16px; }
    .section-title {
        font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: var(--muted); margin-bottom: 10px;
    }
    .section-subtitle { color: var(--muted); font-size: 0.8rem; font-style: italic; margin-bottom: 10px; }

    /* ── Two-col grid ───────────────────────────────────── */
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }

    /* ── Grade badges ───────────────────────────────────── */
    .grade-badge {
        padding: 2px 10px; border-radius: 999px;
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em;
    }
    .grade-aplus { background: rgba(198,120,221,0.18); color: #d4a0e8; border: 1px solid rgba(198,120,221,0.4); }
    .grade-a     { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .grade-b     { background: rgba(229,192,123,0.15); color: #ecd09a; }
    .grade-c     { background: rgba(139,147,166,0.15); color: #a3a8b4; }

    /* ── Score badges ───────────────────────────────────── */
    .score-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; }
    .score-a { background: rgba(152,195,121,0.12); color: #a8d69e; }
    .score-b { background: rgba(229,192,123,0.12); color: #ecd09a; }
    .score-c { background: rgba(224,108,117,0.12); color: #e89099; }

    /* ── Bias badges ────────────────────────────────────── */
    .bias-badge { padding: 3px 12px; border-radius: 4px; font-size: 0.8rem; font-weight: 700; }
    .bias-badge.long    { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .bias-badge.short   { background: rgba(224,108,117,0.15); color: #e89099; }
    .bias-badge.neutral { background: rgba(229,192,123,0.15); color: #ecd09a; }

    /* ── Liquidity badges ───────────────────────────────── */
    .liq-badge { padding: 2px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
    .liq-high { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .liq-med  { background: rgba(229,192,123,0.15); color: #ecd09a; }
    .liq-low  { background: rgba(224,108,117,0.15); color: #e89099; }

    /* ── Pipeline banner ────────────────────────────────── */
    .pipeline {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; padding: 10px 16px; margin-bottom: 16px;
        display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
        font-size: 0.78rem; color: var(--muted);
    }
    .pipe-step  { color: var(--text); font-weight: 600; }
    .pipe-arrow { color: var(--border); }

    /* ── Color helpers ──────────────────────────────────── */
    .up   { color: var(--green); }
    .dn   { color: var(--red);   }
    .flat { color: var(--yellow); }

    /* ── Empty state ────────────────────────────────────── */
    .no-setups { color: var(--muted); text-align: center; padding: 30px; font-size: 1rem; }

    /* ── Footer ─────────────────────────────────────────── */
    .footer { text-align: center; color: var(--muted); font-size: 0.78rem; padding: 20px 0 4px; }

    @media (max-width: 640px) {
        .two-col { grid-template-columns: 1fr; }
    }
"""

# ── Nav links ────────────────────────────────────────────────

_NAV_LINKS = [
    ("index.html",          "Dashboard",      "index"),
    ("macro_pulse.html",    "Macro Pulse",    "macro_pulse"),
    ("premarket.html",      "Pre-Market",     "premarket"),
    ("options_sniper.html", "Options Sniper", "options_sniper"),
]


# ── Helpers ──────────────────────────────────────────────────

def regime_pill_cls(regime: str) -> str:
    return {"RISK ON": "on", "RISK OFF": "off", "MIXED": "mixed"}.get(regime, "mixed")


def nav_bar(active: str = "") -> str:
    """Navigation bar linking all dashboard pages."""
    items = []
    for href, label, key in _NAV_LINKS:
        cls = "nav-link active" if active == key else "nav-link"
        items.append(f'<a href="{href}" class="{cls}">{label}</a>')
    links_html = ' <span class="nav-sep">·</span> '.join(items)
    return (
        f'<nav class="nav-bar">'
        f'<span class="nav-brand">Macro Suite</span>'
        f'{links_html}'
        f'</nav>'
    )


def report_header(
    title: str,
    meta_line: str,
    regime: str,
    driver_text: str = "",
) -> str:
    """Standard report header: title/meta left, regime pill + driver right."""
    rcls = regime_pill_cls(regime)
    drv  = f'<div class="driver-text">{driver_text}</div>' if driver_text else ""
    return f"""
    <div class="report-header">
        <div>
            <div class="report-title">{title}</div>
            <div class="report-meta">{meta_line}</div>
        </div>
        <div class="regime-block">
            <div class="regime-pill {rcls}">{regime}</div>
            {drv}
        </div>
    </div>"""


def page_shell(
    title: str,
    body_html: str,
    extra_css: str = "",
    extra_head: str = "",
) -> str:
    """Complete HTML document with shared CSS + optional page-specific extras."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{SHARED_CSS}{extra_css}</style>
    {extra_head}
</head>
<body>
<div class="page">
{body_html}
</div>
</body>
</html>"""


def footer(subtitle: str) -> str:
    return f'<div class="footer">Macro Suite — {subtitle}</div>'
