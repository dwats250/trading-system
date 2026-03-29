#!/usr/bin/env python3
# ============================================================
# MACRO SUITE — Options Sniper Report
# ============================================================
# On-demand. Run when you want a full trade evaluation.
# Pipeline: MACRO → REGIME → PLAYBOOK → FOCUS → CHART → OPTIONS → RANK → OUTPUT
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from config.tickers import MACRO_SYMBOLS, SNIPER_SYMBOLS
from core.fetcher import fetch_all
from core.formatter import divider
from core.notifier import send
from macro.focus import format_focus, route
from macro.incidents import detect
from macro.playbook import format_playbook, generate
from macro.regime import classify, cross_asset_read, drivers
from macro.session import current_session
from options.chain import OptionsAnalysis, analyze
from sniper.scanner import Setup, scan


@dataclass
class TradeIdea:
    setup:   Setup
    options: OptionsAnalysis | None
    rank:    int
    why:     str


# ── Ranking ──────────────────────────────────────────────────
# Combines chart grade, confidence, and options liquidity into
# a final ranking score. Only top 3 are shown.

def _rank_score(setup: Setup, opts: OptionsAnalysis | None) -> float:
    grade_pts = {"A": 100, "B": 50, "C": 10}
    liq_pts   = {"High": 20, "Medium": 10, "Low": 0}

    base  = grade_pts.get(setup.grade, 0)
    conf  = setup.confidence * 5
    liq   = liq_pts.get(opts.liquidity, 0) if opts else 0
    return base + conf + liq


def _build_why(setup: Setup, opts: OptionsAnalysis | None, regime: str) -> str:
    parts = []
    parts.append(f"{regime} regime")
    if setup.alignment != "mixed":
        parts.append(f"EMA {setup.alignment}")
    if setup.setup_type != "none":
        parts.append(f"{setup.setup_type} setup")
    if opts and opts.liquidity != "Low":
        parts.append(f"options {opts.liquidity.lower()} liquidity")
    return " — ".join(parts)


# ── Output builders ──────────────────────────────────────────

def _format_idea(idea: TradeIdea, regime: str) -> list[str]:
    s    = idea.setup
    opts = idea.options
    rank_icons = {1: "🥇", 2: "🟡", 3: "⚪"}
    icon = rank_icons.get(idea.rank, f"#{idea.rank}")

    grade_label = {"A": "A SETUP", "B": "WATCH", "C": "PASS"}[s.grade]

    lines = [
        f"{icon}  #{idea.rank} {s.ticker}  —  {s.bias}  ({grade_label}  |  Confidence: {s.confidence}/10)",
        f"   Why:          {idea.why}",
        f"   Setup:        {s.setup_type.title()} | EMA {s.alignment} | RSI {s.rsi_val}",
        f"   Entry:        {s.entry_note}",
        f"   Invalidation: {s.invalidation}  (below this = trade is wrong)",
        f"   Levels:       S {s.support}  /  R {s.resistance}",
    ]

    if opts:
        lines += [
            f"   Options:      {opts.suggested_structure}  ({opts.contract_note})",
            f"   Liquidity:    {opts.liquidity}  |  IV {opts.iv_pct}  |  Bid/Ask {opts.bid}/{opts.ask}",
            f"   Note:         {opts.structure_reason}",
        ]
    else:
        lines.append("   Options:      Data unavailable — check chain manually")

    return lines


def build_report(macro_data: dict | None = None) -> tuple[str, list[TradeIdea]]:
    now = datetime.now().strftime("%Y-%m-%d  %I:%M %p PST")
    session = current_session()

    if macro_data is None:
        print("Fetching macro data...", flush=True)
        macro_data = fetch_all(MACRO_SYMBOLS)

    regime  = classify(macro_data)
    primary, secondary = drivers(macro_data)
    incidents = detect(macro_data)
    playbook  = generate(regime, primary, secondary)
    focus     = route(primary, secondary)

    # Use focus primary tickers if available, else full sniper list
    focus_tickers = {t: t for t in focus["primary"]} if focus["primary"] else SNIPER_SYMBOLS

    print("Scanning charts...", flush=True)
    setups = scan(focus_tickers)

    # Only A/B setups proceed to options layer
    print("Evaluating options...", flush=True)
    ideas: list[TradeIdea] = []
    for s in setups:
        if s.grade == "C":
            continue
        opts = analyze(s.ticker, s.bias, s.price) if s.grade == "A" else None
        why  = _build_why(s, opts, regime)
        ideas.append(TradeIdea(setup=s, options=opts, rank=0, why=why))

    # Rank and assign positions
    ideas.sort(key=lambda i: _rank_score(i.setup, i.options), reverse=True)
    for i, idea in enumerate(ideas[:3], 1):
        idea.rank = i

    # ── Build output ──────────────────────────────────────────
    lines: list[str] = []
    lines.append("OPTIONS SNIPER")
    lines.append(f"{now}  |  {session} Session")
    lines.append(divider("═"))

    # Regime
    lines.append(f"REGIME: {regime}")
    lines.append(f"  Primary:   {primary}")
    lines.append(f"  Secondary: {secondary}")

    # Incidents
    if incidents:
        lines.append("")
        for inc in incidents:
            lines.append(f"  ⚠  {inc}")
            # Add implications
            impl = _incident_implications(inc)
            for imp in impl:
                lines.append(f"     → {imp}")

    lines.append(divider())

    # Playbook
    lines.extend(format_playbook(playbook))
    lines.append("")

    # Focus
    lines.extend(format_focus(focus))
    lines.append(divider())

    # Top setups
    lines.append("TOP SETUPS")
    lines.append("")

    if not ideas:
        lines.append("  No A or B setups found — WAIT")
    else:
        for idea in ideas[:3]:
            lines.extend(_format_idea(idea, regime))
            lines.append("")

    # Conclusion
    lines.append(divider())
    lines.append(_conclusion(ideas, regime))
    lines.append(divider("═"))

    return "\n".join(lines), ideas


def _incident_implications(incident: str) -> list[str]:
    inc = incident.lower()
    if "oil shock up" in inc:
        return ["Inflation pressure building", "Energy sector likely to lead", "Risk assets vulnerable"]
    if "oil shock down" in inc:
        return ["Deflationary signal", "Energy sector under pressure", "Potential relief for risk assets"]
    if "rate spike" in inc or "rate spiking" in inc:
        return ["Growth and tech under pressure", "Dollar likely to strengthen", "Watch TLT short"]
    if "dollar breakout" in inc:
        return ["Commodities headwind", "Gold/Silver pressure", "USD pairs active"]
    if "vol spike" in inc:
        return ["Do not chase — wait for VIX to contract", "Reduce all position sizes"]
    return []


def _conclusion(ideas: list[TradeIdea], regime: str) -> str:
    a_setups = [i for i in ideas if i.setup.grade == "A"]
    if not ideas:
        return "CONCLUSION: No setups — WAIT"
    if not a_setups:
        return "CONCLUSION: B setups only — WATCHLIST, not tradeable today"
    if regime == "RISK OFF" and len(a_setups) == 1:
        return f"CONCLUSION: 1 A setup ({a_setups[0].setup.ticker}) — proceed with discipline, reduced size"
    return f"CONCLUSION: {len(a_setups)} A setup(s) — execute only the highest conviction"


def run(macro_data: dict | None = None) -> None:
    report, _ = build_report(macro_data)
    print(report)
    send(report, title="Options Sniper")
