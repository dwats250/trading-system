#!/usr/bin/env python3
# ============================================================
# MACRO SUITE — Options Sniper Report
# ============================================================
# On-demand. Run when you want a full trade evaluation.
# Pipeline: MACRO → REGIME → PLAYBOOK → FOCUS → CHART → OPTIONS → VALIDATE → RANK → OUTPUT
#
# Scoring (0–100):
#   Regime Alignment  25 pts
#   Chart Quality     25 pts
#   Risk/Reward       20 pts
#   Options Quality   20 pts
#   Clarity           10 pts
#
# Grade thresholds:
#   80+   → A / A+  (tradeable — hard guardrails still apply)
#   60–79 → B       (watch only)
#   <60   → C       (reject)
#
# Hard guardrails (override composite score):
#   R:R < 2:1 | Chart not A-grade | Options liquidity Low
#   No clear structure | Trade conflicts with regime
#
# A+ checklist (all 8 must pass to earn A+ label):
#   Clear structure | Clean levels | Regime aligned | R:R ≥ 2:1
#   Not extended | Momentum confirmation | Liquid options | Entry + invalidation defined
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
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
    setup:           Setup
    options:         OptionsAnalysis | None
    rank:            int
    why:             str
    score:           int             # composite 0-100
    composite_grade: str             # A+ / A / B
    failures:        list[str] = field(default_factory=list)  # A+ checklist failures
    trigger_condition: str = ""  # Phase 2B: primary condition to become tradeable (Tier 2 only)
    trigger_type:      str = ""  # Phase 2C: category of blocking reason (rr/grade/regime/liquidity)


@dataclass
class Rejection:
    ticker:      str
    chart_grade: str
    score:       int
    reasons:     list[str]


# ── Composite scoring (0–100) ─────────────────────────────────

def _composite_score(setup: Setup, opts: OptionsAnalysis | None, regime: str) -> int:
    # Regime Alignment (0-25)
    aligned = (
        (regime == "RISK ON"  and setup.bias == "LONG") or
        (regime == "RISK OFF" and setup.bias == "SHORT")
    )
    conflicting = (
        (regime == "RISK ON"  and setup.bias == "SHORT") or
        (regime == "RISK OFF" and setup.bias == "LONG")
    )
    regime_pts = 25 if aligned else (5 if conflicting else 12)

    # Chart Quality (0-25)
    chart_pts = {"A": 25, "B": 12, "C": 0}.get(setup.grade, 0)

    # Risk/Reward (0-20)
    rr = setup.rr
    rr_pts = 20 if rr >= 3.0 else (16 if rr >= 2.0 else (8 if rr >= 1.5 else 0))

    # Options Quality (0-20)
    liq_pts = 0
    if opts:
        liq_pts = {"High": 20, "Medium": 12, "Low": 4}.get(opts.liquidity, 0)

    # Clarity (0-10)
    clarity_pts = {
        "trend": 10, "breakout": 10, "pullback": 10, "reversal": 6, "none": 2
    }.get(setup.setup_type, 5)

    return regime_pts + chart_pts + rr_pts + liq_pts + clarity_pts


# ── Hard guardrails ───────────────────────────────────────────
# Any failure here = not tradeable, regardless of composite score.

def _hard_guardrails(setup: Setup, opts: OptionsAnalysis | None, regime: str) -> list[str]:
    failures = []

    if setup.rr < 2.0:
        failures.append(f"R:R {setup.rr:.1f} — below 2:1 minimum")

    if setup.grade != "A":
        failures.append(f"Chart grade {setup.grade} — A-level chart required to trade")

    if not opts or opts.liquidity == "Low":
        failures.append("Options liquidity insufficient")

    if setup.setup_type == "none":
        failures.append("No clear chart structure")

    if regime == "RISK OFF" and setup.bias == "LONG":
        failures.append("LONG suppressed — RISK OFF regime")
    if regime == "RISK ON" and setup.bias == "SHORT" and setup.grade != "A":
        # A-grade shorts are permitted in RISK ON (exceptional structure required)
        # Non-A shorts are suppressed — regime strongly favours longs
        failures.append("SHORT suppressed in RISK ON — A-grade chart required")

    return failures


# ── A+ checklist ──────────────────────────────────────────────
# All 8 must pass to earn the A+ label within an A-grade trade.

def _aplus_checklist(setup: Setup, opts: OptionsAnalysis | None, regime: str) -> list[str]:
    failures = []

    if setup.setup_type == "none":
        failures.append("No clear chart structure")

    if setup.support <= 0 or setup.resistance <= 0:
        failures.append("Support/resistance levels unclear")

    if (regime == "RISK ON"  and setup.bias == "SHORT") or \
       (regime == "RISK OFF" and setup.bias == "LONG"):
        failures.append(f"Trade conflicts with {regime} regime")

    if setup.rr < 2.0:
        failures.append(f"R:R {setup.rr:.1f} — below 2:1 minimum")

    if setup.bias == "LONG"  and setup.rsi_val > 72:
        failures.append(f"RSI {setup.rsi_val} — overbought, do not chase")
    elif setup.bias == "SHORT" and setup.rsi_val < 28:
        failures.append(f"RSI {setup.rsi_val} — oversold, do not chase")

    if setup.alignment == "mixed":
        failures.append("EMA alignment mixed — no momentum confirmation")

    if not opts or opts.liquidity == "Low":
        failures.append("Options liquidity insufficient")

    if not setup.entry_note or not setup.invalidation:
        failures.append("Entry or invalidation not defined")

    return failures


# ── Why string ────────────────────────────────────────────────

def _derive_trigger(reasons: list[str]) -> str:
    """Phase 2B single-source trigger mapper: first blocking reason → forward-looking condition."""
    checks = [
        ("regime",         "Regime shifts to align with setup bias"),
        ("R:R",            "R:R improves to ≥ 2:1"),
        ("Chart grade",    "Chart grade upgrades to A"),
        ("No clear chart", "Clear breakout or breakdown structure forms"),
        ("liquidity",      "Options liquidity improves"),
    ]
    for keyword, label in checks:
        for r in reasons:
            if keyword.lower() in r.lower():
                return label
    return reasons[0] if reasons else "Primary blocking condition resolves"


def _b_grade_trigger(setup: Setup, opts: OptionsAnalysis | None, regime: str) -> str:
    """Sniper Tier 2: synthesize first soft-blocking reason and delegate to _derive_trigger."""
    aligned = (
        (regime == "RISK ON"  and setup.bias == "LONG") or
        (regime == "RISK OFF" and setup.bias == "SHORT")
    )
    if not aligned:
        # Bias-specific label — cannot be derived from a generic failure string
        return f"Regime shifts to align with {setup.bias} bias"
    if opts and opts.liquidity == "Medium":
        return _derive_trigger(["Options liquidity insufficient"])
    if setup.rr < 3.0:
        return "R:R strengthens to ≥ 3:1"
    return "Composite score reaches 80 — setup conviction improves"


def _b_grade_trigger_type(setup: Setup, opts: OptionsAnalysis | None, regime: str) -> str:
    """Phase 2C: mirror _b_grade_trigger branches, returning trigger_type instead of label."""
    aligned = (
        (regime == "RISK ON"  and setup.bias == "LONG") or
        (regime == "RISK OFF" and setup.bias == "SHORT")
    )
    if not aligned:
        return "regime"
    if opts and opts.liquidity == "Medium":
        return "liquidity"
    if setup.rr < 3.0:
        return "rr"
    return ""


def _build_why(setup: Setup, opts: OptionsAnalysis | None, regime: str) -> str:
    parts = [f"{regime} regime"]
    if setup.alignment != "mixed":
        parts.append(f"EMA {setup.alignment}")
    if setup.setup_type != "none":
        parts.append(f"{setup.setup_type} setup")
    if opts and opts.liquidity != "Low":
        parts.append(f"options {opts.liquidity.lower()} liquidity")
    return " — ".join(parts)


# ── Output builders ───────────────────────────────────────────

def _format_idea(idea: TradeIdea) -> list[str]:
    s    = idea.setup
    opts = idea.options
    rank_icons = {1: "🥇", 2: "🟡", 3: "⚪"}
    icon = rank_icons.get(idea.rank, f"#{idea.rank}")

    grade_label = idea.composite_grade   # A+ / A / B
    watch_note  = "  ↳ WATCH ONLY — not tradeable today" if grade_label == "B" else ""

    lines = [
        f"{icon}  #{idea.rank} {s.ticker}  —  {s.bias}"
        f"  ({grade_label}  |  Score: {idea.score}/100  |  Confidence: {s.confidence}/10)",
        f"   Why:          {idea.why}",
    ]

    if grade_label == "A" and idea.failures:
        lines.append(f"   A+ gap:       {' | '.join(idea.failures)}")

    if watch_note:
        lines.append(watch_note)

    lines += [
        f"   Setup:        {s.setup_type.title()} | EMA {s.alignment} | RSI {s.rsi_val}",
        f"   R:R:          {s.rr:.1f}:1  "
        f"(Target {s.resistance}  /  Stop {s.invalidation})",
        f"   Entry:        {s.entry_note}",
        f"   Invalidation: {s.invalidation}  (below this = trade is wrong)",
        f"   Levels:       S {s.support}  /  R {s.resistance}",
    ]

    if opts:
        lines += [
            f"   Options:      {opts.suggested_structure}  ({opts.contract_note})",
            f"   Liquidity:    {opts.liquidity}  |  IV {opts.iv_pct}"
            f"  |  Bid/Ask {opts.bid}/{opts.ask}",
            f"   Delta:        {opts.delta_guidance}",
            f"   Note:         {opts.structure_reason}",
        ]
    else:
        lines.append("   Options:      Data unavailable — check chain manually")

    return lines


def _format_rejections(rejections: list[Rejection]) -> list[str]:
    if not rejections:
        return ["  None"]
    lines = []
    for r in rejections:
        lines.append(f"  ✗  {r.ticker}  ({r.chart_grade} chart  |  Score {r.score}/100)")
        for reason in r.reasons:
            lines.append(f"       • {reason}")
    return lines


# ── Incident implications ─────────────────────────────────────

def _incident_implications(incident: str) -> list[str]:
    inc = incident.lower()
    if "oil shock up"    in inc: return ["Inflation pressure building", "Energy sector likely to lead", "Risk assets vulnerable"]
    if "oil shock down"  in inc: return ["Deflationary signal", "Energy sector under pressure", "Potential relief for risk assets"]
    if "rate spike"      in inc or "rate spiking" in inc: return ["Growth and tech under pressure", "Dollar likely to strengthen", "Watch TLT short"]
    if "dollar breakout" in inc: return ["Commodities headwind", "Gold/Silver pressure", "USD pairs active"]
    if "vol spike"       in inc: return ["Do not chase — wait for VIX to contract", "Reduce all position sizes"]
    return []


# ── Conclusion ────────────────────────────────────────────────

def _conclusion(ideas: list[TradeIdea], regime: str) -> str:
    aplus     = [i for i in ideas if i.composite_grade == "A+"]
    a_grade   = [i for i in ideas if i.composite_grade == "A"]
    tradeable = aplus + a_grade

    if not ideas:
        return "CONCLUSION: No setups found — WAIT"
    if not tradeable:
        return "CONCLUSION: Watch list only — no setups clear all guardrails today — WAIT"
    if aplus:
        tickers = ", ".join(i.setup.ticker for i in aplus)
        return f"CONCLUSION: {len(aplus)} A+ setup(s) [{tickers}] — execute highest conviction only"
    tickers = ", ".join(i.setup.ticker for i in a_grade[:3])
    return f"CONCLUSION: {len(a_grade)} A setup(s) [{tickers}] — proceed with discipline, defined size"


# ── Main report builder ───────────────────────────────────────

def build_report(macro_data: dict | None = None) -> tuple[str, list[TradeIdea], list[Rejection]]:
    now     = datetime.now().strftime("%Y-%m-%d  %I:%M %p PST")
    session = current_session()

    if macro_data is None:
        print("Fetching macro data...", flush=True)
        macro_data = fetch_all(MACRO_SYMBOLS)

    regime            = classify(macro_data)
    primary, secondary = drivers(macro_data)
    incidents          = detect(macro_data)
    playbook           = generate(regime, primary, secondary)
    focus              = route(primary, secondary, regime)

    # Use focus primary tickers if available, else full sniper list
    focus_tickers = {t: t for t in focus["primary"]} if focus["primary"] else SNIPER_SYMBOLS

    print("Scanning charts...", flush=True)
    setups = scan(focus_tickers)

    # Evaluate every setup through scoring + guardrails
    print("Evaluating setups...", flush=True)
    ideas:      list[TradeIdea] = []
    rejections: list[Rejection] = []

    for s in setups:
        # Run options for A and B chart grades (C gets no options)
        opts = analyze(s.ticker, s.bias, s.price) if s.grade in ("A", "B") else None

        score             = _composite_score(s, opts, regime)
        guardrail_fails   = _hard_guardrails(s, opts, regime)

        # Hard guardrails override everything
        if guardrail_fails:
            rejections.append(Rejection(
                ticker=s.ticker, chart_grade=s.grade,
                score=score, reasons=guardrail_fails,
            ))
            continue

        # Composite score gates
        if score < 60:
            rejections.append(Rejection(
                ticker=s.ticker, chart_grade=s.grade,
                score=score, reasons=[f"Score {score}/100 below 60 threshold"],
            ))
            continue

        why = _build_why(s, opts, regime)

        if score < 80:
            # B — watchlist only
            ideas.append(TradeIdea(
                setup=s, options=opts, rank=0, why=why,
                score=score, composite_grade="B",
                trigger_condition=_b_grade_trigger(s, opts, regime),
                trigger_type=_b_grade_trigger_type(s, opts, regime),
            ))
            continue

        # A territory — run A+ checklist
        aplus_fails     = _aplus_checklist(s, opts, regime)
        composite_grade = "A+" if not aplus_fails else "A"
        ideas.append(TradeIdea(
            setup=s, options=opts, rank=0, why=why,
            score=score, composite_grade=composite_grade,
            failures=aplus_fails,
        ))

    # Sort: A+ first, then A, then B — each group by score descending
    _grade_order = {"A+": 0, "A": 1, "B": 2}
    ideas.sort(key=lambda i: (_grade_order.get(i.composite_grade, 3), -i.score))
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
            for imp in _incident_implications(inc):
                lines.append(f"     → {imp}")

    lines.append(divider())

    # Playbook + Focus
    lines.extend(format_playbook(playbook))
    lines.append("")
    lines.extend(format_focus(focus))
    lines.append(divider())

    # Top setups
    tradeable = [i for i in ideas[:3] if i.composite_grade in ("A+", "A")]
    watchlist = [i for i in ideas[:3] if i.composite_grade == "B"]

    lines.append("TOP SETUPS")
    lines.append("")

    if not tradeable and not watchlist:
        lines.append("  No setups cleared guardrails — WAIT")
    else:
        for idea in tradeable:
            lines.extend(_format_idea(idea))
            lines.append("")
        if watchlist:
            lines.append("  — WATCHLIST —")
            for idea in watchlist:
                lines.extend(_format_idea(idea))
                lines.append("")

    # Rejections
    lines.append(divider())
    lines.append("REJECTED")
    lines.extend(_format_rejections(rejections))
    lines.append("")

    # Conclusion
    lines.append(divider())
    lines.append(_conclusion(ideas, regime))
    lines.append(divider("═"))

    return "\n".join(lines), ideas, rejections


def run(
    macro_data: dict | None = None,
    rescan: bool = False,
    interval: int | None = None,
    max_cycles: int | None = None,
) -> None:
    report, ideas, rejections = build_report(macro_data)
    print(report)
    send(report, title="Options Sniper")

    if rescan and ideas:
        from sniper import rescanner as _rescanner  # deferred — breaks circular import
        _rescanner.run_loop(
            ideas,
            interval=interval if interval is not None else _rescanner.INTERVAL_DEFAULT,
            max_cycles=max_cycles,
        )
