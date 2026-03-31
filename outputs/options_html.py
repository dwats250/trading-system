# ============================================================
# MACRO SUITE — Options Sniper HTML Dashboard
# ============================================================

from __future__ import annotations

import json
from datetime import datetime, timezone

from core.formatter import arrow, fmt_pct, fmt_price
from macro.incidents import detect
from macro.regime import classify, cross_asset_read, drivers
from macro.session import current_session
from outputs.shared import card_block, footer, nav_bar, page_shell, report_header, section_block
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


def _compute_ema(closes: list[float], period: int) -> list[float]:
    k = 2.0 / (period + 1)
    ema = [closes[0]]
    for c in closes[1:]:
        ema.append(c * k + ema[-1] * (1 - k))
    return [round(v, 2) for v in ema]


def _compute_rsi(closes: list[float], period: int = 14) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    if len(closes) < period + 1:
        return result
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains  = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    avg_g  = sum(gains[:period]) / period
    avg_l  = sum(losses[:period]) / period
    def _rsi(ag: float, al: float) -> float:
        return 100.0 if al == 0 else round(100 - 100 / (1 + ag / al), 1)
    result[period] = _rsi(avg_g, avg_l)
    for i in range(period, len(deltas)):
        avg_g = (avg_g * (period - 1) + gains[i])  / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
        result[i + 1] = _rsi(avg_g, avg_l)
    return result


def _chart_html(ticker: str, bars: list[dict], setup) -> str:
    if not bars or len(bars) < 10:
        return ""
    closes = [b["close"] for b in bars]
    labels = [b["date"]  for b in bars]
    ema9   = _compute_ema(closes, 9)
    ema21  = _compute_ema(closes, 21)
    ema50  = _compute_ema(closes, 50)
    rsi    = _compute_rsi(closes)
    cid    = ticker.replace("^", "").replace("=", "").replace("-", "").replace(".", "")
    annotations = {
        "support": {
            "type": "line", "yMin": setup.support, "yMax": setup.support,
            "borderColor": "rgba(34,197,94,0.8)", "borderWidth": 1.5, "borderDash": [5, 4],
            "label": {"display": True, "content": f"S {setup.support:.2f}",
                      "position": "start", "backgroundColor": "transparent",
                      "color": "#86efac", "font": {"size": 10}},
        },
        "resistance": {
            "type": "line", "yMin": setup.resistance, "yMax": setup.resistance,
            "borderColor": "rgba(239,68,68,0.8)", "borderWidth": 1.5, "borderDash": [5, 4],
            "label": {"display": True, "content": f"R {setup.resistance:.2f}",
                      "position": "start", "backgroundColor": "transparent",
                      "color": "#fca5a5", "font": {"size": 10}},
        },
        "invalidation": {
            "type": "line", "yMin": setup.invalidation, "yMax": setup.invalidation,
            "borderColor": "rgba(239,68,68,0.5)", "borderWidth": 1, "borderDash": [3, 3],
            "label": {"display": True, "content": f"INV {setup.invalidation:.2f}",
                      "position": "end", "backgroundColor": "transparent",
                      "color": "#fca5a5", "font": {"size": 9}},
        },
    }
    return f"""
    <div class="chart-wrap">
        <div style="position:relative;height:200px"><canvas id="pc-{cid}"></canvas></div>
        <div style="position:relative;height:70px;margin-top:3px"><canvas id="rsi-{cid}"></canvas></div>
    </div>
    <script>
    (function(){{
        var L={json.dumps(labels)}, C={json.dumps(closes)},
            E9={json.dumps(ema9)}, E21={json.dumps(ema21)}, E50={json.dumps(ema50)},
            RSI={json.dumps(rsi)};
        var grid={{'color':'rgba(26,51,86,0.5)'}}, tick={{'color':'#7a9cc4','font':{{'size':9}}}};
        new Chart(document.getElementById('pc-{cid}'),{{
            type:'line',
            data:{{labels:L,datasets:[
                {{label:'Close',data:C,borderColor:'#60a5fa',borderWidth:1.5,fill:true,
                  backgroundColor:'rgba(96,165,250,0.06)',pointRadius:0,tension:0.2}},
                {{label:'EMA9', data:E9, borderColor:'#22c55e',borderWidth:1.2,fill:false,pointRadius:0}},
                {{label:'EMA21',data:E21,borderColor:'#f59e0b',borderWidth:1.2,fill:false,pointRadius:0}},
                {{label:'EMA50',data:E50,borderColor:'#a78bfa',borderWidth:1.5,fill:false,pointRadius:0}},
            ]}},
            options:{{responsive:true,maintainAspectRatio:false,animation:false,
                plugins:{{
                    legend:{{display:true,position:'top',labels:{{boxWidth:10,font:{{size:10}},color:'#7a9cc4'}}}},
                    annotation:{{annotations:{json.dumps(annotations)}}},
                    tooltip:{{mode:'index',intersect:false}}
                }},
                scales:{{
                    x:{{grid:grid,ticks:{{...tick,maxTicksLimit:10}}}},
                    y:{{grid:grid,ticks:tick,position:'right'}}
                }}
            }}
        }});
        new Chart(document.getElementById('rsi-{cid}'),{{
            type:'line',
            data:{{labels:L,datasets:[
                {{label:'RSI',data:RSI,borderColor:'#f59e0b',borderWidth:1.2,fill:false,pointRadius:0,tension:0.2}}
            ]}},
            options:{{responsive:true,maintainAspectRatio:false,animation:false,
                plugins:{{
                    legend:{{display:false}},
                    annotation:{{annotations:{{
                        ob:{{type:'line',yMin:70,yMax:70,borderColor:'rgba(239,68,68,0.4)',borderWidth:1,borderDash:[3,3]}},
                        os:{{type:'line',yMin:30,yMax:30,borderColor:'rgba(34,197,94,0.4)',borderWidth:1,borderDash:[3,3]}},
                        mid:{{type:'line',yMin:50,yMax:50,borderColor:'rgba(100,100,100,0.3)',borderWidth:1}}
                    }}}},
                    tooltip:{{mode:'index',intersect:false}}
                }},
                scales:{{
                    x:{{display:false}},
                    y:{{min:0,max:100,grid:{{color:'rgba(26,51,86,0.3)'}},
                       ticks:{{...tick,stepSize:30}},position:'right'}}
                }}
            }}
        }});
    }})();
    </script>"""


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


def _idea_card(idea: TradeIdea, bars: list | None = None) -> str:
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
        {_chart_html(s.ticker, bars or [], s)}
    </div>"""


def _primary_disqualifier(reasons: list[str]) -> str:
    """Single most important failure reason for trader-facing display."""
    checks = [
        ("regime",         "Conflicts with current macro regime"),
        ("R:R",            "R:R below 2:1 — risk not justified"),
        ("Chart grade",    "Chart not A-grade yet"),
        ("No clear chart", "No clear setup structure"),
        ("liquidity",      "Options liquidity insufficient"),
    ]
    for keyword, label in checks:
        for r in reasons:
            if keyword.lower() in r.lower():
                return label
    return reasons[0] if reasons else "Failed guardrails"


def _rejection_section(rejections: list[Rejection]) -> str:
    if not rejections:
        return ""

    # Split: watchlist = chart A/B with identifiable structure; weak = everything else
    watchlist = [r for r in rejections
                 if r.chart_grade in ("A", "B")
                 and not any("No clear chart" in x for x in r.reasons)]
    weak      = [r for r in rejections if r not in watchlist]

    html = ""

    if watchlist:
        rows = ""
        for r in watchlist:
            disqualifier = _primary_disqualifier(r.reasons)
            rows += f"""
            <div class="wl-row">
                <div class="wl-header">
                    <span class="reject-ticker">{r.ticker}</span>
                    <span class="reject-grade">Chart {r.chart_grade}</span>
                    <span class="score-badge score-b">{r.score}/100</span>
                </div>
                <div class="wl-blocker">Why not trading: {disqualifier}</div>
            </div>"""
        html += f"""
        <div class="rejection-section">
            <div class="section-title">Watchlist Setups — Good Structure, Not Trade-Ready</div>
            <div class="section-subtitle">Chart structure is identifiable but at least one guardrail blocks execution. Monitor only.</div>
            <div class="card wl-card">
                {rows}
            </div>
        </div>"""

    if weak:
        tickers = "  ·  ".join(
            f"{r.ticker} (Grade {r.chart_grade})" for r in weak
        )
        html += f"""
        <div class="off-radar-sniper">
            <span class="off-radar-label">Not on radar</span> {tickers}
        </div>"""

    return html


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
    /* Pipeline banner */
    .pipeline {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; padding: 10px 16px; margin-bottom: 16px;
        display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
        font-size: 0.78rem; color: var(--muted);
    }
    .pipe-step { color: var(--text); font-weight: 600; }
    .pipe-arrow { color: var(--border); }

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
    .idea-card.rank-1 { border-color: rgba(229,192,123,0.5); }
    .idea-header { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
    .idea-rank { font-size: 0.95rem; font-weight: 600; }
    .grade-badge { padding: 2px 10px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; }
    .grade-aplus { background: rgba(198,120,221,0.18); color: #d4a0e8; border: 1px solid rgba(198,120,221,0.4); }
    .grade-a { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .grade-b { background: rgba(229,192,123,0.15); color: #ecd09a; }
    .grade-c { background: rgba(139,147,166,0.15); color: #a3a8b4; }
    .score-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; }
    .score-a { background: rgba(152,195,121,0.12); color: #a8d69e; }
    .score-b { background: rgba(229,192,123,0.12); color: #ecd09a; }
    .score-c { background: rgba(224,108,117,0.12); color: #e89099; }
    .idea-ticker-wrap { display: flex; align-items: center; gap: 8px; }
    .idea-ticker { font-size: 1.35rem; font-weight: 800; }
    .bias-badge { padding: 3px 12px; border-radius: 4px; font-size: 0.8rem; font-weight: 700; }
    .bias-badge.long    { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .bias-badge.short   { background: rgba(224,108,117,0.15); color: #e89099; }
    .bias-badge.neutral { background: rgba(229,192,123,0.15); color: #ecd09a; }
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
    .level-inv { color: #e89099; }
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
    .watch-card { border-color: rgba(229,192,123,0.35); }
    .watch-banner {
        background: rgba(229,192,123,0.08); border: 1px solid rgba(229,192,123,0.2);
        border-radius: 6px; padding: 6px 12px; margin-bottom: 6px;
        font-size: 0.8rem; font-weight: 600; color: #ecd09a;
    }
    .aplus-gap {
        background: rgba(198,120,221,0.06); border: 1px solid rgba(198,120,221,0.15);
        border-radius: 6px; padding: 6px 12px; margin-bottom: 10px;
        font-size: 0.8rem; color: #d4a0e8;
    }
    .rr-val { color: var(--green); }
    .level-target { color: var(--green); }
    .rejection-section { margin-bottom: 16px; }
    .section-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                     letter-spacing: 0.1em; color: var(--muted); margin-bottom: 10px; }
    .reject-row { padding: 10px 0; border-bottom: 1px solid rgba(55,65,81,0.5); }
    .reject-row:last-child { border-bottom: none; }
    .reject-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
    .reject-ticker { font-weight: 700; font-size: 0.95rem; }
    .reject-grade { color: var(--muted); font-size: 0.8rem; }
    .reject-reasons { list-style: disc; padding-left: 20px; color: var(--muted); font-size: 0.82rem; }
    .reject-reasons li { margin: 2px 0; }
    /* Watchlist tier — distinct from validated trades */
    .section-subtitle { color: var(--muted); font-size: 0.8rem; font-style: italic; margin-bottom: 10px; }
    .wl-card { border-color: rgba(55,65,81,0.5); background: var(--surface); }
    .wl-row { padding: 9px 0; border-bottom: 1px solid rgba(55,65,81,0.4); }
    .wl-row:last-child { border-bottom: none; }
    .wl-header { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }
    .wl-blocker { font-size: 0.8rem; color: var(--muted); }
    .wl-blocker::before { content: "↳ "; color: var(--border); }
    /* Off-radar — minimal, no card */
    .off-radar-sniper { margin-top: 8px; margin-bottom: 16px;
                        font-size: 0.75rem; color: #4b5563; }
    .off-radar-label { font-weight: 700; color: #6b7280; text-transform: uppercase;
                       font-size: 0.68rem; letter-spacing: 0.08em; margin-right: 6px; }
    .liq-badge { padding: 2px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
    .liq-high { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .liq-med  { background: rgba(229,192,123,0.15); color: #ecd09a; }
    .liq-low  { background: rgba(224,108,117,0.15); color: #e89099; }

    /* Macro tags */
    .macro-tags { display: flex; flex-wrap: wrap; gap: 8px; }
    .macro-tag { padding: 4px 10px; border-radius: 6px; font-size: 0.8rem;
                 background: var(--surface2); border: 1px solid var(--border); }
    .macro-tag.up .tag-note { color: rgba(152,195,121,0.85); font-size: 0.75rem; }
    .macro-tag.dn .tag-note { color: rgba(224,108,117,0.85); font-size: 0.75rem; }

    /* Conclusion */
    .conclusion {
        background: rgba(97,175,239,0.07); border: 1px solid rgba(97,175,239,0.2);
        border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;
        font-size: 1rem; font-weight: 600; color: #93c5fd;
    }
    .context-banner {
        margin-bottom: 16px; padding: 12px 14px; border-radius: 12px;
        background: rgba(255,255,255,0.03); border: 1px solid var(--border);
        color: var(--muted); font-size: 0.84rem;
    }
    .context-banner a { color: var(--blue); text-decoration: none; }
    .context-banner a:hover { text-decoration: underline; }

    /* No setups */
    .no-setups { color: var(--muted); text-align: center; padding: 30px; font-size: 1rem; }

    /* Colors */
    .up   { color: var(--green); }
    .dn   { color: var(--red);   }
    .flat { color: var(--yellow);}

    .chart-wrap { margin-top: 14px; border-top: 1px solid var(--border); padding-top: 12px; }
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
    chart_data: dict | None = None,
) -> str:
    _local  = datetime.now().astimezone()
    _utc    = datetime.now(timezone.utc)
    now     = _local.strftime("%A, %B %d %Y  —  %I:%M %p %Z")
    utc_str = _utc.strftime("%H:%M UTC")
    session = current_session()
    _as_of_raw = next((d["as_of"] for d in data_map.values() if d and d.get("as_of")), None)
    data_as_of = f"Prices as of {_as_of_raw}" if _as_of_raw else "Prices as of —"
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
    cd = chart_data or {}
    if ideas:
        ideas_html = "".join(_idea_card(i, cd.get(i.setup.ticker)) for i in ideas[:3])
    else:
        ideas_html = '<div class="no-setups">No validated trades today — stay flat or wait for better conditions</div>'

    # Rejection section
    rejections_html = _rejection_section(rejections or [])

    # Conclusion
    from reports.options_sniper import _conclusion
    conclusion_text = _conclusion(ideas, regime)

    body = f"""
    {nav_bar("options_sniper")}

    <div class="pipeline">{pipe_html}</div>

    {card_block(
        'Supplemental page only: Pre-Market is the flagship execution surface. '
        'Use this drilldown when you need deeper ranked trade detail or extra options structure review. '
        '<a href="premarket.html">Return to Pre-Market →</a>',
        extra_cls="context-banner",
    )}

    {report_header(
        title="Advanced Options Drilldown",
        meta_line=f"Generated: {now} &nbsp;·&nbsp; Market ref: {utc_str} &nbsp;·&nbsp; {data_as_of} &nbsp;·&nbsp; {session} Session",
        regime=regime,
        driver_text=primary,
        note_text="Secondary analysis page: advanced ranking and options detail beyond the main Pre-Market workflow.",
    )}

    {incident_html}

    <div class="two-col">
        {card_block(
            f'<div class="pb-row"><span class="pb-label">Size</span><span class="pb-val">{playbook["size"]}</span></div>'
            f'<div class="pb-row"><span class="pb-label">Bias</span><span class="pb-val">{playbook["bias"]}</span></div>'
            f'<div class="pb-row"><span class="pb-label">Focus</span><span class="pb-val pb-focus">{pb_focus}</span></div>'
            f'<div class="pb-row"><span class="pb-label">Avoid</span><span class="pb-val pb-avoid">{pb_avoid}</span></div>'
            f'{pb_notes}',
            title="Playbook",
        )}

        {card_block(
            f'<div class="focus-row"><span class="focus-label">Primary</span>{focus_primary}</div>'
            f'<div class="focus-row"><span class="focus-label">Secondary</span>{focus_secondary}</div>'
            f'<div style="margin-top:12px"><div class="card-title" style="margin-bottom:8px">Macro Tags</div><div class="macro-tags">{_macro_tags(data_map)}</div></div>',
            title="Focus Router",
        )}
    </div>

    {section_block("Validated Top Trades", ideas_html, extra_cls="ideas-section")}

    {rejections_html}

    <div class="conclusion">{conclusion_text}</div>

    {section_block(
        "Macro Snapshot",
        card_block(
            f'<div class="macro-tags" style="gap:10px">{_macro_tags(data_map)}</div>'
            f'<div style="margin-top:12px;color:var(--muted);font-size:0.88rem;border-left:3px solid var(--border);padding-left:10px">{read}</div>'
        ),
    )}

    {footer("Advanced Options Drilldown")}
    """

    return page_shell(
        title=f"Advanced Options Drilldown — {datetime.now().strftime('%b %d')}",
        body_html=body,
        extra_css=_STYLE,
        extra_head="""
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
    """,
    )


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

    from core.fetcher import fetch_ohlcv
    chart_data = {i.setup.ticker: fetch_ohlcv(i.setup.ticker) for i in ideas[:3]}

    html = build_options_html(data_map, ideas, playbook, focus, incidents, rejections, chart_data)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved → {path}")
