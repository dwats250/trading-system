# ============================================================
# MACRO SUITE — Options Sniper HTML Dashboard
# ============================================================

from __future__ import annotations

from datetime import datetime

from core.formatter import arrow, fmt_pct, fmt_price
from macro.incidents import detect
from macro.regime import classify, cross_asset_read, drivers
from reports.options_sniper import Rejection, TradeIdea


def _regime_cls(regime: str) -> str:
    return {"RISK ON": "on", "RISK OFF": "off", "MIXED": "mixed"}.get(regime, "mixed")


def _grade_cls(grade: str) -> str:
    return {"A": "grade-a", "B": "grade-b", "C": "grade-c"}.get(grade, "")


def _bias_cls(bias: str) -> str:
    return {"LONG": "long", "SHORT": "short"}.get(bias, "neutral")


def _liq_cls(liq: str) -> str:
    return {"High": "liq-high", "Medium": "liq-med", "Low": "liq-low"}.get(liq, "")


def _score_cls(score: int) -> str:
    if score >= 80: return "score-a"
    if score >= 60: return "score-b"
    return "score-c"


def _composite_grade_cls(grade: str) -> str:
    return {"A+": "grade-aplus", "A": "grade-a", "B": "grade-b"}.get(grade, "grade-c")


def _rank_header(rank: int, idea: TradeIdea) -> str:
    icons = {1: "🥇", 2: "🟡", 3: "⚪"}
    grade = idea.composite_grade
    grade_labels = {"A+": "A+ SETUP", "A": "A SETUP", "B": "WATCH"}
    label = grade_labels.get(grade, grade)
    return (
        f'{icons.get(rank, f"#{rank}")} #{rank} &nbsp; '
        f'<span class="grade-badge {_composite_grade_cls(grade)}">{label}</span> &nbsp; '
        f'<span class="score-badge {_score_cls(idea.score)}">{idea.score}/100</span>'
    )


def _idea_card(idea: TradeIdea) -> str:
    s    = idea.setup
    opts = idea.options
    is_watch = idea.composite_grade == "B"

    # A+ gap — show what prevented full A+ on A-grade ideas
    aplus_gap_html = ""
    if idea.composite_grade == "A" and idea.failures:
        items = " &nbsp;·&nbsp; ".join(idea.failures)
        aplus_gap_html = f'<div class="aplus-gap">A+ gap: {items}</div>'

    watch_banner = ""
    if is_watch:
        watch_banner = '<div class="watch-banner">WATCH ONLY — not tradeable today</div>'

    opts_html = ""
    if opts:
        opts_html = f"""
        <div class="opts-section">
            <div class="opts-row">
                <span class="opts-label">Structure</span>
                <span class="opts-val">{opts.suggested_structure}</span>
                <span class="opts-contract">{opts.contract_note}</span>
            </div>
            <div class="opts-row">
                <span class="opts-label">Liquidity</span>
                <span class="liq-badge {_liq_cls(opts.liquidity)}">{opts.liquidity}</span>
                <span class="opts-meta">IV {opts.iv_pct} &nbsp;|&nbsp; Bid/Ask {opts.bid}/{opts.ask} &nbsp;|&nbsp; OI {opts.open_interest:,}</span>
            </div>
            <div class="opts-row">
                <span class="opts-label">Delta</span>
                <span class="opts-delta">{opts.delta_guidance}</span>
            </div>
            <div class="opts-note">{opts.structure_reason}</div>
        </div>"""
    else:
        opts_html = '<div class="opts-unavail">Options data unavailable — check chain manually</div>'

    return f"""
    <div class="idea-card rank-{idea.rank}{' watch-card' if is_watch else ''}">
        <div class="idea-header">
            <div class="idea-rank">{_rank_header(idea.rank, idea)}</div>
            <div class="idea-ticker-wrap">
                <span class="idea-ticker">{s.ticker}</span>
                <span class="bias-badge {_bias_cls(s.bias)}">{s.bias}</span>
            </div>
            <div class="idea-conf">Confidence <strong>{s.confidence}/10</strong></div>
        </div>

        {watch_banner}
        {aplus_gap_html}
        <div class="idea-why">{idea.why}</div>

        <div class="idea-grid">
            <div class="idea-cell">
                <div class="cell-label">Setup</div>
                <div class="cell-val">{s.setup_type.title()}</div>
            </div>
            <div class="idea-cell">
                <div class="cell-label">EMA</div>
                <div class="cell-val">{s.alignment.title()}</div>
            </div>
            <div class="idea-cell">
                <div class="cell-label">RSI</div>
                <div class="cell-val">{s.rsi_val}</div>
            </div>
            <div class="idea-cell">
                <div class="cell-label">R:R</div>
                <div class="cell-val rr-val">{s.rr:.1f}:1</div>
            </div>
        </div>

        <div class="levels-row">
            <div class="level-item">
                <span class="level-label">Entry</span>
                <span class="level-val">{s.entry_note}</span>
            </div>
            <div class="level-item">
                <span class="level-label">Target</span>
                <span class="level-val level-target">{s.resistance}</span>
            </div>
            <div class="level-item">
                <span class="level-label">Invalidation</span>
                <span class="level-val level-inv">{s.invalidation}</span>
            </div>
            <div class="level-item">
                <span class="level-label">S / R</span>
                <span class="level-val">{s.support} / {s.resistance}</span>
            </div>
        </div>

        {opts_html}
    </div>"""


def _rejection_section(rejections: list[Rejection]) -> str:
    if not rejections:
        return ""
    rows = ""
    for r in rejections:
        reasons_html = "".join(f"<li>{reason}</li>" for reason in r.reasons)
        rows += f"""
        <div class="reject-row">
            <div class="reject-header">
                <span class="reject-ticker">{r.ticker}</span>
                <span class="reject-grade">Chart {r.chart_grade}</span>
                <span class="score-badge score-c">{r.score}/100</span>
            </div>
            <ul class="reject-reasons">{reasons_html}</ul>
        </div>"""
    return f"""
    <div class="rejection-section">
        <div class="section-title">Rejected Setups</div>
        <div class="card">
            {rows}
        </div>
    </div>"""


def _macro_tags(data_map: dict) -> str:
    tags_config = [
        ("DXY",  "pressure on risk"),
        ("10Y",  "rates signal"),
        ("VIX",  "volatility"),
        ("WTI",  "inflation impulse"),
        ("XAU",  "monetary stress"),
        ("HYG",  "credit tone"),
    ]
    tags = []
    for label, tag in tags_config:
        d = data_map.get(label)
        if d:
            cls = "up" if d["pct"] > 0 else "dn"
            tags.append(
                f'<span class="macro-tag {cls}">'
                f'{label} {arrow(d["pct"])} {fmt_pct(d["pct"])} '
                f'<span class="tag-note">({tag})</span>'
                f'</span>'
            )
    return "".join(tags)


_STYLE = """
    :root {
        --bg: #060d1a; --surface: #0b1829; --surface2: #0f2035;
        --border: #1a3356; --text: #dde8f8; --muted: #7a9cc4;
        --green: #22c55e; --red: #ef4444; --yellow: #f59e0b; --blue: #60a5fa;
        --gold: #fbbf24; --purple: #a78bfa;
        --shadow: 0 4px 32px rgba(0,0,0,0.5);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text);
           font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           font-size: 14px; line-height: 1.5; padding: 16px; }
    .page { max-width: 1060px; margin: 0 auto; }

    /* Pipeline banner */
    .pipeline {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; padding: 10px 16px; margin-bottom: 16px;
        display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
        font-size: 0.78rem; color: var(--muted);
    }
    .pipe-step { color: var(--text); font-weight: 600; }
    .pipe-arrow { color: var(--border); }

    /* Header */
    .report-header {
        background: linear-gradient(135deg, #0b1829, #0f2035);
        border: 1px solid var(--border); border-radius: 16px;
        padding: 20px 24px; margin-bottom: 16px;
        display: flex; justify-content: space-between; align-items: flex-start;
        flex-wrap: wrap; gap: 16px;
    }
    .report-title { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; }
    .report-meta { color: var(--muted); font-size: 0.88rem; margin-top: 4px; }
    .regime-block { text-align: right; }
    .regime-pill {
        display: inline-block; padding: 8px 20px; border-radius: 999px;
        font-size: 1rem; font-weight: 700; letter-spacing: 0.05em; border: 1px solid;
    }
    .regime-pill.off  { background: rgba(239,68,68,0.15);  border-color: rgba(239,68,68,0.4);  color: #fca5a5; }
    .regime-pill.on   { background: rgba(34,197,94,0.15);  border-color: rgba(34,197,94,0.4);  color: #86efac; }
    .regime-pill.mixed{ background: rgba(245,158,11,0.15); border-color: rgba(245,158,11,0.4); color: #fde68a; }
    .driver-text { color: var(--muted); font-size: 0.82rem; margin-top: 6px; }

    /* Two col */
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }

    /* Cards */
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px; }
    .card-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                  letter-spacing: 0.1em; color: var(--muted); margin-bottom: 12px; }

    /* Playbook */
    .pb-row { display: flex; gap: 8px; margin-bottom: 8px; align-items: flex-start; }
    .pb-label { color: var(--muted); font-size: 0.8rem; width: 52px; flex-shrink: 0; padding-top: 2px; }
    .pb-val { font-size: 0.9rem; }
    .pb-focus { color: var(--blue); }
    .pb-avoid { color: var(--red); opacity: 0.85; }
    .pb-note { font-size: 0.82rem; color: var(--muted); border-left: 2px solid var(--border);
               padding-left: 8px; margin-top: 4px; }

    /* Incidents */
    .incident-card {
        background: rgba(239,68,68,0.07); border: 1px solid rgba(239,68,68,0.2);
        border-radius: 12px; padding: 14px; margin-bottom: 16px;
    }
    .inc-title { color: #fca5a5; font-weight: 700; margin-bottom: 8px; }
    .inc-item { margin-bottom: 10px; }
    .inc-name { color: #fca5a5; font-size: 0.9rem; font-weight: 600; }
    .inc-impl { color: var(--muted); font-size: 0.82rem; margin-top: 2px; }
    .inc-impl li { margin-left: 14px; list-style: disc; }

    /* Focus */
    .focus-row { display: flex; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
    .focus-label { color: var(--muted); font-size: 0.8rem; width: 74px; flex-shrink: 0; }
    .focus-ticker {
        background: rgba(96,165,250,0.1); border: 1px solid rgba(96,165,250,0.2);
        color: #93c5fd; padding: 2px 9px; border-radius: 999px; font-size: 0.78rem; font-weight: 600;
    }

    /* Idea cards */
    .ideas-section { margin-bottom: 16px; }
    .ideas-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                   letter-spacing: 0.1em; color: var(--muted); margin-bottom: 12px; }
    .idea-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 16px; padding: 18px; margin-bottom: 12px;
    }
    .idea-card.rank-1 { border-color: rgba(251,191,36,0.4); }
    .idea-header { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
    .idea-rank { font-size: 0.95rem; font-weight: 600; }
    .grade-badge { padding: 2px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; }
    .grade-aplus { background: rgba(167,139,250,0.2); color: #c4b5fd; border: 1px solid rgba(167,139,250,0.4); }
    .grade-a { background: rgba(34,197,94,0.15);  color: #86efac; }
    .grade-b { background: rgba(245,158,11,0.15); color: #fde68a; }
    .grade-c { background: rgba(156,163,175,0.15);color: #9ca3af; }
    .score-badge { padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }
    .score-a { background: rgba(34,197,94,0.12);  color: #86efac; }
    .score-b { background: rgba(245,158,11,0.12); color: #fde68a; }
    .score-c { background: rgba(239,68,68,0.12);  color: #fca5a5; }
    .idea-ticker-wrap { display: flex; align-items: center; gap: 8px; }
    .idea-ticker { font-size: 1.35rem; font-weight: 800; }
    .bias-badge { padding: 3px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: 700; }
    .bias-badge.long    { background: rgba(34,197,94,0.15);  color: #86efac; }
    .bias-badge.short   { background: rgba(239,68,68,0.15);  color: #fca5a5; }
    .bias-badge.neutral { background: rgba(245,158,11,0.15); color: #fde68a; }
    .idea-conf { margin-left: auto; color: var(--muted); font-size: 0.85rem; }
    .idea-conf strong { color: var(--text); }
    .idea-why { color: var(--muted); font-size: 0.85rem; margin-bottom: 12px;
                border-left: 3px solid var(--border); padding-left: 10px; }
    .idea-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px; }
    .idea-cell { background: var(--surface2); border-radius: 8px; padding: 8px 10px; }
    .cell-label { color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; }
    .cell-val { font-weight: 700; font-size: 0.95rem; margin-top: 2px; }
    .levels-row { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;
                  background: var(--surface2); border-radius: 10px; padding: 10px 12px; }
    .level-item { display: flex; gap: 6px; align-items: baseline; }
    .level-label { color: var(--muted); font-size: 0.78rem; }
    .level-val { font-size: 0.88rem; font-weight: 600; }
    .level-inv { color: #fca5a5; }
    .opts-section { border-top: 1px solid var(--border); padding-top: 12px; }
    .opts-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap; }
    .opts-label { color: var(--muted); font-size: 0.78rem; width: 66px; }
    .opts-val { font-weight: 700; font-size: 0.9rem; }
    .opts-contract { color: var(--blue); font-size: 0.85rem; }
    .opts-meta { color: var(--muted); font-size: 0.82rem; }
    .opts-delta { color: var(--purple); font-size: 0.82rem; }
    .opts-note { color: var(--muted); font-size: 0.82rem; border-left: 2px solid var(--border);
                 padding-left: 8px; margin-top: 4px; }
    .opts-unavail { color: var(--muted); font-size: 0.82rem; border-top: 1px solid var(--border);
                    padding-top: 10px; }
    .watch-card { border-color: rgba(245,158,11,0.3); opacity: 0.85; }
    .watch-banner {
        background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2);
        border-radius: 8px; padding: 6px 12px; margin-bottom: 10px;
        font-size: 0.8rem; font-weight: 600; color: #fde68a;
    }
    .aplus-gap {
        background: rgba(167,139,250,0.06); border: 1px solid rgba(167,139,250,0.15);
        border-radius: 8px; padding: 6px 12px; margin-bottom: 10px;
        font-size: 0.8rem; color: #c4b5fd;
    }
    .rr-val { color: var(--green); }
    .level-target { color: var(--green); }
    .rejection-section { margin-bottom: 16px; }
    .section-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                     letter-spacing: 0.1em; color: var(--muted); margin-bottom: 10px; }
    .reject-row { padding: 10px 0; border-bottom: 1px solid rgba(30,58,95,0.5); }
    .reject-row:last-child { border-bottom: none; }
    .reject-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
    .reject-ticker { font-weight: 700; font-size: 0.95rem; }
    .reject-grade { color: var(--muted); font-size: 0.8rem; }
    .reject-reasons { list-style: disc; padding-left: 20px; color: var(--muted); font-size: 0.82rem; }
    .reject-reasons li { margin: 2px 0; }
    .liq-badge { padding: 2px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }
    .liq-high { background: rgba(34,197,94,0.15);  color: #86efac; }
    .liq-med  { background: rgba(245,158,11,0.15); color: #fde68a; }
    .liq-low  { background: rgba(239,68,68,0.15);  color: #fca5a5; }

    /* Macro tags */
    .macro-tags { display: flex; flex-wrap: wrap; gap: 8px; }
    .macro-tag { padding: 4px 10px; border-radius: 8px; font-size: 0.8rem;
                 background: var(--surface2); border: 1px solid var(--border); }
    .macro-tag.up .tag-note { color: rgba(34,197,94,0.7); font-size: 0.75rem; }
    .macro-tag.dn .tag-note { color: rgba(239,68,68,0.7); font-size: 0.75rem; }

    /* Conclusion */
    .conclusion {
        background: rgba(96,165,250,0.07); border: 1px solid rgba(96,165,250,0.2);
        border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
        font-size: 1rem; font-weight: 600; color: #93c5fd;
    }

    /* No setups */
    .no-setups { color: var(--muted); text-align: center; padding: 30px; font-size: 1rem; }

    /* Colors */
    .up   { color: var(--green); }
    .dn   { color: var(--red);   }
    .flat { color: var(--yellow);}

    .footer { text-align: center; color: var(--muted); font-size: 0.78rem; padding: 20px 0 4px; }

    @media (max-width: 640px) {
        .two-col { grid-template-columns: 1fr; }
        .idea-grid { grid-template-columns: repeat(2, 1fr); }
        .levels-row { flex-direction: column; gap: 6px; }
    }
"""


def build_options_html(
    data_map: dict,
    ideas: list[TradeIdea],
    playbook: dict,
    focus: dict,
    incidents: list[str],
    rejections: list[Rejection] | None = None,
) -> str:
    now = datetime.now().strftime("%A, %B %d %Y  —  %I:%M %p PST")
    regime   = classify(data_map)
    primary, secondary = drivers(data_map)
    read     = cross_asset_read(data_map)
    reg_cls  = _regime_cls(regime)

    # Pipeline banner
    pipeline_steps = ["MACRO", "REGIME", "PLAYBOOK", "FOCUS", "CHART", "OPTIONS", "RANK", "OUTPUT"]
    pipe_html = " <span class='pipe-arrow'>→</span> ".join(
        f"<span class='pipe-step'>{s}</span>" for s in pipeline_steps
    )

    # Incidents
    incident_html = ""
    if incidents:
        from reports.options_sniper import _incident_implications
        items = ""
        for inc in incidents:
            impls = _incident_implications(inc)
            impl_html = "".join(f"<li>{i}</li>" for i in impls)
            items += f"""
            <div class="inc-item">
                <div class="inc-name">⚠ {inc}</div>
                <ul class="inc-impl">{impl_html}</ul>
            </div>"""
        incident_html = f"""
        <div class="incident-card">
            <div class="inc-title">Active Incidents</div>
            {items}
        </div>"""

    # Playbook
    pb_focus = " ".join(f'<span class="focus-ticker">{f}</span>' for f in playbook["focus"]) or "—"
    pb_avoid = " ".join(f'<span class="focus-ticker" style="background:rgba(239,68,68,0.1);border-color:rgba(239,68,68,0.2);color:#fca5a5">{a}</span>' for a in playbook["avoid"]) or "—"
    pb_notes = "".join(f'<div class="pb-note">{n}</div>' for n in playbook["notes"])

    # Focus
    focus_primary = " ".join(f'<span class="focus-ticker">{t}</span>' for t in focus["primary"]) or "—"
    focus_secondary = " ".join(f'<span class="focus-ticker">{t}</span>' for t in focus["secondary"]) or "—"

    # Ideas
    if ideas:
        ideas_html = "".join(_idea_card(i) for i in ideas[:3])
    else:
        ideas_html = '<div class="no-setups">No setups cleared guardrails — WAIT</div>'

    # Rejection section
    rejections_html = _rejection_section(rejections or [])

    # Conclusion
    from reports.options_sniper import _conclusion
    conclusion_text = _conclusion(ideas, regime)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Options Sniper — {datetime.now().strftime('%b %d')}</title>
    <style>{_STYLE}</style>
</head>
<body>
<div class="page">

    <div class="pipeline">{pipe_html}</div>

    <div class="report-header">
        <div>
            <div class="report-title">Options Sniper</div>
            <div class="report-meta">{now}</div>
        </div>
        <div class="regime-block">
            <div class="regime-pill {reg_cls}">{regime}</div>
            <div class="driver-text">{primary}</div>
        </div>
    </div>

    {incident_html}

    <div class="two-col">
        <div class="card">
            <div class="card-title">Playbook</div>
            <div class="pb-row"><span class="pb-label">Size</span><span class="pb-val">{playbook['size']}</span></div>
            <div class="pb-row"><span class="pb-label">Bias</span><span class="pb-val">{playbook['bias']}</span></div>
            <div class="pb-row"><span class="pb-label">Focus</span><span class="pb-val pb-focus">{pb_focus}</span></div>
            <div class="pb-row"><span class="pb-label">Avoid</span><span class="pb-val pb-avoid">{pb_avoid}</span></div>
            {pb_notes}
        </div>

        <div class="card">
            <div class="card-title">Focus Router</div>
            <div class="focus-row">
                <span class="focus-label">Primary</span>
                {focus_primary}
            </div>
            <div class="focus-row">
                <span class="focus-label">Secondary</span>
                {focus_secondary}
            </div>
            <div style="margin-top:12px">
                <div class="card-title" style="margin-bottom:8px">Macro Tags</div>
                <div class="macro-tags">{_macro_tags(data_map)}</div>
            </div>
        </div>
    </div>

    <div class="ideas-section">
        <div class="ideas-title">Top Setups</div>
        {ideas_html}
    </div>

    {rejections_html}

    <div class="conclusion">{conclusion_text}</div>

    <div class="card">
        <div class="card-title">Macro Snapshot</div>
        <div class="macro-tags" style="gap:10px">{_macro_tags(data_map)}</div>
        <div style="margin-top:12px;color:var(--muted);font-size:0.88rem;border-left:3px solid var(--border);padding-left:10px">{read}</div>
    </div>

    <div class="footer">Macro Suite — Options Sniper</div>
</div>
</body>
</html>"""


def save(path: str = "options_sniper.html", data_map: dict | None = None,
         ideas: list | None = None, rejections: list | None = None,
         playbook: dict | None = None, focus: dict | None = None,
         incidents: list | None = None) -> None:
    from config.tickers import MACRO_SYMBOLS
    from core.fetcher import fetch_all
    from macro.focus import route
    from macro.incidents import detect
    from macro.playbook import generate
    from macro.regime import classify, drivers
    from reports.options_sniper import build_report

    if data_map is None:
        data_map = fetch_all(MACRO_SYMBOLS)
    if ideas is None or rejections is None:
        _, ideas, rejections = build_report(data_map)
    if playbook is None or focus is None or incidents is None:
        regime = classify(data_map)
        primary, secondary = drivers(data_map)
        playbook  = playbook  or generate(regime, primary, secondary)
        focus     = focus     or route(primary, secondary, regime)
        incidents = incidents or detect(data_map)

    html = build_options_html(data_map, ideas, playbook, focus, incidents, rejections)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved → {path}")
