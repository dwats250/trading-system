# ============================================================
# MACRO SUITE — Dashboard Hub (Index Page)
# ============================================================
# Generates reports/output/index.html — the landing page that
# links to all three report pages.
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone

from core.formatter import fmt_pct
from macro.regime import classify, cross_asset_read, drivers
from macro.session import current_session
from outputs.shared import (
    SHARED_CSS, ensure_output_dir, footer, nav_bar, page_shell,
    regime_pill_cls,
)


# ── Page-specific CSS ────────────────────────────────────────

_PAGE_CSS = """
    /* Hero */
    .hub-hero {
        background: linear-gradient(135deg, #252b36, #2a3140);
        border: 1px solid var(--border); border-radius: 10px;
        padding: 28px 24px; margin-bottom: 20px; text-align: center;
    }
    .hub-title   { font-size: 2rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 6px; }
    .hub-tagline { color: var(--muted); font-size: 0.95rem; margin-bottom: 18px; }
    .hub-regime  {
        display: inline-block; padding: 10px 24px; border-radius: 999px;
        font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; border: 1px solid;
        margin-bottom: 8px;
    }
    .hub-read { color: var(--muted); font-size: 0.9rem; max-width: 600px; margin: 10px auto 0; }
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

    /* Meta strip */
    .meta-strip {
        text-align: center; color: var(--muted); font-size: 0.82rem;
        margin-bottom: 20px;
    }

    @media (max-width: 640px) {
        .report-grid { grid-template-columns: 1fr; }
        .hub-title { font-size: 1.5rem; }
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
    primary, secondary = drivers(data_map)
    read    = cross_asset_read(data_map)

    rcls    = regime_pill_cls(regime)

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
    {nav_bar("index")}

    <div class="hub-hero">
        <div class="hub-title">Macro Suite</div>
        <div class="hub-tagline">One workflow: context first, execution second, options drilldown only when needed</div>
        <div class="hub-regime regime-pill {rcls}">{regime}</div>
        <div class="hub-read">{read}</div>
        <div class="hub-flow">
            <span>Macro Pulse</span>
            <span>→</span>
            <span>Pre-Market</span>
            <span>→</span>
            <span>Embedded Options Context</span>
        </div>
    </div>

    <div class="meta-strip">
        {now} &nbsp;·&nbsp; Market ref: {utc_str} &nbsp;·&nbsp; {session} Session
        &nbsp;·&nbsp; Primary: {primary} &nbsp;·&nbsp; Secondary: {secondary}
    </div>

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
