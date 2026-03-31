# ============================================================
# MACRO SUITE — Dashboard Hub (Index Page)
# ============================================================
# Generates reports/output/index.html — the landing page that
# links to all three report pages.
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone

from macro.regime import classify
from macro.session import current_session
from outputs.shared import card_block, ensure_output_dir, footer, nav_links, page_shell, stat_block


# ── Page-specific CSS ────────────────────────────────────────

_PAGE_CSS = """
    /* Top summary */
    .hub-summary-card { margin-bottom: 20px; }
    .hub-summary-top {
        display: flex; justify-content: space-between; align-items: flex-start;
        gap: 16px; margin-bottom: 14px; flex-wrap: wrap;
    }
    .hub-title {
        font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em;
    }
    .hub-meta {
        color: var(--muted); font-size: 0.88rem; margin-top: 4px;
    }
    .hub-summary {
        display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px;
    }
    .hub-flow {
        display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap;
        margin-top: 14px; padding: 8px 14px; border-radius: 999px;
        border: 1px solid rgba(96,165,250,0.18); background: rgba(96,165,250,0.06);
        color: var(--text); font-size: 0.8rem;
    }
    .hub-flow span:last-child { color: var(--muted); }

    /* Report cards grid */
    .report-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px; }
    .report-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 14px; padding: 20px; text-decoration: none; color: var(--text);
        display: flex; flex-direction: column; gap: 8px;
        transition: border-color 0.15s, background 0.15s;
    }
    .report-card:hover {
        border-color: rgba(96,165,250,0.4);
        background: rgba(11,24,41,0.9);
    }
    .report-card.primary {
        border-color: rgba(96,165,250,0.28);
        background: linear-gradient(180deg, rgba(37,43,54,0.98), rgba(31,40,56,0.98));
    }
    .report-card.secondary {
        opacity: 0.94;
    }
    .rc-icon  { font-size: 1.5rem; }
    .rc-title { font-size: 1.05rem; font-weight: 700; }
    .rc-desc  { color: var(--muted); font-size: 0.82rem; line-height: 1.4; }
    .rc-arrow { color: var(--blue); font-size: 0.82rem; margin-top: auto; padding-top: 6px; }
    .rc-role {
        align-self: flex-start; padding: 3px 8px; border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.08); color: var(--muted); font-size: 0.7rem;
        text-transform: uppercase; letter-spacing: 0.06em;
    }
    @media (max-width: 640px) {
        .report-grid { grid-template-columns: 1fr; }
        .hub-summary { grid-template-columns: 1fr; }
        .hub-summary-top { flex-direction: column; }
    }
"""


# ── Report card definitions ──────────────────────────────────

_REPORT_CARDS = [
    {
        "href":  "premarket.html",
        "icon":  "🌅",
        "title": "Pre-Market Report",
        "desc":  "Primary execution plan: overnight context, market posture, validated top trades, watchlist setups, and embedded options context.",
        "role":  "Primary",
        "card_cls": "primary",
        "arrow": "Open execution plan →",
    },
    {
        "href":  "macro_pulse.html",
        "icon":  "📡",
        "title": "Macro Pulse",
        "desc":  "Context and regime dashboard: cross-asset tone, macro drivers, market posture, and the handoff into Pre-Market.",
        "role":  "Context",
        "card_cls": "",
        "arrow": "Open market context →",
    },
    {
        "href":  "options_sniper.html",
        "icon":  "🎯",
        "title": "Advanced Options",
        "desc":  "Secondary drilldown for deeper options structure review and ranked trade detail beyond the flagship Pre-Market flow.",
        "role":  "Advanced",
        "card_cls": "secondary",
        "arrow": "Open drilldown →",
    },
]


# ── HTML builder ─────────────────────────────────────────────

def build_index_html(data_map: dict | None = None) -> str:
    from config.tickers import MACRO_SYMBOLS
    from core.fetcher import fetch_all

    if data_map is None:
        data_map = fetch_all(MACRO_SYMBOLS)

    _local  = datetime.now().astimezone()
    _utc    = datetime.now(timezone.utc)
    now     = _local.strftime("%A, %B %d %Y  —  %I:%M %p %Z")
    utc_str = _utc.strftime("%H:%M UTC")
    session = current_session()
    regime  = classify(data_map)

    cards_html = "".join(
        f"""
        <a href="{c['href']}" class="report-card {c.get('card_cls', '')}">
            <div class="rc-icon">{c['icon']}</div>
            <div class="rc-role">{c['role']}</div>
            <div class="rc-title">{c['title']}</div>
            <div class="rc-desc">{c['desc']}</div>
            <div class="rc-arrow">{c['arrow']}</div>
        </a>"""
        for c in _REPORT_CARDS
    )

    body = f"""
    {card_block(
        f'<div class="hub-summary-top">'
        f'<div>'
        f'<div class="hub-title">Macro Suite</div>'
        f'<div class="hub-meta">Generated: {now} &nbsp;·&nbsp; Market ref: {utc_str}</div>'
        f'{nav_links("index")}'
        f'</div>'
        f'</div>'
        f'<div class="hub-summary">'
        f'{stat_block("Updated", now)}'
        f'{stat_block("Market Ref", utc_str)}'
        f'{stat_block("Session", session)}'
        f'{stat_block("Regime", regime)}'
        f'</div>'
        f'<div class="hub-flow">'
        f'<span>Macro Pulse</span>'
        f'<span>→</span>'
        f'<span>Pre-Market</span>'
        f'<span>→</span>'
        f'<span>Embedded Options Context</span>'
        f'</div>',
        extra_cls="hub-summary-card"
    )}
    <div class="report-grid">
        {cards_html}
    </div>

    {footer("Dashboard")}
    """

    return page_shell(
        title="Macro Suite — Dashboard",
        body_html=body,
        extra_css=_PAGE_CSS,
    )


def save(path: str = "reports/output/index.html", data_map: dict | None = None) -> None:
    ensure_output_dir()
    html = build_index_html(data_map)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved → {path}")


if __name__ == "__main__":
    save()
