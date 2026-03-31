# ============================================================
# MACRO SUITE — Shared UI Foundation
# ============================================================
# All dashboard page builders import from here.
# Provides: unified CSS tokens, nav bar, report header,
# page shell wrapper, and footer helper.
# ============================================================

from __future__ import annotations

import os
from html import escape

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
    .nav-link.primary {
        color: #dbeafe;
        background: rgba(96,165,250,0.1);
        border-color: rgba(96,165,250,0.22);
    }
    .nav-link.secondary {
        color: #c6ccd8;
        opacity: 0.92;
    }
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
    .report-note { color: var(--blue); font-size: 0.8rem; margin-top: 6px; }

    /* ── Cards ──────────────────────────────────────────── */
    .card, .surface-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 14px; padding: 16px; box-shadow: var(--shadow);
    }
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
    .section-head {
        display: flex; justify-content: space-between; align-items: baseline;
        gap: 12px; margin-bottom: 10px;
    }
    .section-action { color: var(--blue); font-size: 0.8rem; text-decoration: none; }
    .section-action:hover { text-decoration: underline; }

    /* ── Two-col grid ───────────────────────────────────── */
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }

    /* ── Shared chips / info blocks ────────────────────── */
    .chip-row { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 10px; border-radius: 999px; font-size: 0.78rem;
        border: 1px solid var(--border); background: rgba(255,255,255,0.03);
    }
    .chip-label { color: var(--muted); }
    .chip-value { color: var(--text); font-weight: 700; }
    .chip.info {
        color: #93c5fd; border-color: rgba(96,165,250,0.24);
        background: rgba(96,165,250,0.08);
    }
    .chip.up {
        color: #a8d69e; border-color: rgba(152,195,121,0.28);
        background: rgba(152,195,121,0.08);
    }
    .chip.dn {
        color: #e89099; border-color: rgba(224,108,117,0.28);
        background: rgba(224,108,117,0.08);
    }
    .chip.flat {
        color: #ecd09a; border-color: rgba(229,192,123,0.28);
        background: rgba(229,192,123,0.08);
    }
    .stat-grid {
        display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px;
    }
    .stat-block {
        padding: 12px; border-radius: 12px;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.04);
    }
    .stat-label {
        color: var(--muted); font-size: 0.72rem;
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;
    }
    .stat-value { font-size: 1rem; font-weight: 700; color: var(--text); }
    .banner {
        display: flex; justify-content: space-between; align-items: center;
        gap: 14px; flex-wrap: wrap;
    }
    .banner-copy { color: var(--text); font-size: 0.9rem; }
    .banner-copy span {
        color: var(--muted); display: block; font-size: 0.8rem; margin-top: 3px;
    }
    .banner-link {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 8px 12px; border-radius: 999px;
        border: 1px solid rgba(96,165,250,0.24); color: #dbeafe;
        background: rgba(96,165,250,0.08); text-decoration: none;
        font-size: 0.82rem; font-weight: 700;
    }
    .banner-link:hover { text-decoration: none; }

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
        .stat-grid { grid-template-columns: 1fr; }
    }
"""

# ── Nav links ────────────────────────────────────────────────

_NAV_LINKS = [
    ("index.html",          "Dashboard",      "index"),
    ("premarket.html",      "Pre-Market",     "premarket"),
    ("macro_pulse.html",    "Macro Pulse",    "macro_pulse"),
    ("options_sniper.html", "Advanced Options", "options_sniper"),
]


# ── Helpers ──────────────────────────────────────────────────

def regime_pill_cls(regime: str) -> str:
    return {"RISK ON": "on", "RISK OFF": "off", "MIXED": "mixed"}.get(regime, "mixed")


def nav_bar(active: str = "") -> str:
    """Navigation bar linking all dashboard pages."""
    items = []
    for href, label, key in _NAV_LINKS:
        tone = "primary" if key == "premarket" else ("secondary" if key == "options_sniper" else "")
        cls = "nav-link"
        if tone:
            cls += f" {tone}"
        if active == key:
            cls += " active"
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
    note_text: str = "",
) -> str:
    """Standard report header: title/meta left, regime pill + driver right."""
    rcls = regime_pill_cls(regime)
    drv  = f'<div class="driver-text">{driver_text}</div>' if driver_text else ""
    note = f'<div class="report-note">{note_text}</div>' if note_text else ""
    return f"""
    <div class="report-header">
        <div>
            <div class="report-title">{title}</div>
            <div class="report-meta">{meta_line}</div>
            {note}
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


def info_chip(label: str, value: str, tone: str = "info") -> str:
    return (
        f'<span class="chip {tone}">'
        f'<span class="chip-label">{escape(label)}</span>'
        f'<span class="chip-value">{escape(value)}</span>'
        f'</span>'
    )


def stat_block(label: str, value: str, extra_cls: str = "") -> str:
    cls = f"stat-block {extra_cls}".strip()
    return (
        f'<div class="{cls}">'
        f'<div class="stat-label">{escape(label)}</div>'
        f'<div class="stat-value">{escape(value)}</div>'
        f'</div>'
    )


def card_block(content: str, title: str = "", extra_cls: str = "") -> str:
    title_html = f'<div class="card-title">{escape(title)}</div>' if title else ""
    cls = f"surface-card {extra_cls}".strip()
    return f'<div class="{cls}">{title_html}{content}</div>'


def section_block(
    title: str,
    content: str,
    subtitle: str = "",
    action_html: str = "",
    extra_cls: str = "",
) -> str:
    subtitle_html = f'<div class="section-subtitle">{escape(subtitle)}</div>' if subtitle else ""
    head = (
        f'<div class="section-head"><div class="section-title">{escape(title)}</div>{action_html}</div>'
        if action_html else f'<div class="section-title">{escape(title)}</div>'
    )
    cls = f"section {extra_cls}".strip()
    return f'<section class="{cls}">{head}{subtitle_html}{content}</section>'
