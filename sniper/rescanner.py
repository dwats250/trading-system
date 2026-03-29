# ============================================================
# MACRO SUITE — Rescanner / Promotion Engine (Phase 2C)
# ============================================================
# Targeted candidate validation loop.
# Rescans watchlist candidates + validated trades only.
# Does NOT rescan the full ticker universe.
#
# Intervals:
#   INTERVAL_DEFAULT       = 15 min  (full watchlist)
#   INTERVAL_NEAR_TRIGGER  =  5 min  (small subset approaching trigger)
#   INTERVAL_HUNT          =  1 min  (max 1-3 tickers, time-limited)
#
# Per-cycle:
#   1. Refresh market data
#   2. Recompute setup / grade / invalidation / R:R
#   3. Re-run all sniper guardrails
#   4. Determine state transition: Promote / Retain / Demote / Reject
#
# Promotion rule: passes ALL guardrails — no partial promotion.
# ============================================================

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from config.tickers import MACRO_SYMBOLS
from core.fetcher import fetch_all
from macro.regime import classify
from options.chain import analyze
from reports.options_sniper import (
    TradeIdea,
    _aplus_checklist,
    _b_grade_trigger,
    _b_grade_trigger_type,
    _build_why,
    _composite_score,
    _hard_guardrails,
)
from sniper.scanner import scan

# ── Scan intervals (seconds) ──────────────────────────────────

INTERVAL_DEFAULT      = 15 * 60   # 15 minutes
INTERVAL_NEAR_TRIGGER =  5 * 60   # 5 minutes
INTERVAL_HUNT         =      60   # 1 minute


# ── Result dataclass ──────────────────────────────────────────

@dataclass
class CycleResult:
    ticker:         str
    transition:     str              # Promote / Retain / Demote / Reject
    previous_grade: str              # A+ / A / B at entry
    current_grade:  str              # A+ / A / B / C after rescan
    score:          int              # composite 0-100
    idea:           TradeIdea | None = None   # populated for Promote / Retain / Demote
    badge:          str              = ""     # "Promoted This Cycle" / "Lost Validity This Cycle"


# ── Single-ticker evaluation ──────────────────────────────────

def _rescan_ticker(ticker: str, previous_grade: str, regime: str) -> CycleResult:
    """Re-evaluate one ticker and return its state transition."""
    new_setups = scan({ticker: ticker})

    if not new_setups:
        return CycleResult(
            ticker=ticker, transition="Reject",
            previous_grade=previous_grade, current_grade="C", score=0,
            badge="Lost Validity This Cycle" if previous_grade in ("A+", "A", "B") else "",
        )

    s    = new_setups[0]
    opts = analyze(s.ticker, s.bias, s.price) if s.grade in ("A", "B") else None

    score           = _composite_score(s, opts, regime)
    guardrail_fails = _hard_guardrails(s, opts, regime)

    # Hard guardrail failure or below-threshold score → Reject
    if guardrail_fails or score < 60:
        return CycleResult(
            ticker=ticker, transition="Reject",
            previous_grade=previous_grade, current_grade=s.grade, score=score,
            badge="Lost Validity This Cycle" if previous_grade in ("A+", "A", "B") else "",
        )

    why = _build_why(s, opts, regime)

    # B-grade (watchlist-valid, score 60-79)
    if score < 80:
        idea = TradeIdea(
            setup=s, options=opts, rank=0, why=why,
            score=score, composite_grade="B",
            trigger_condition=_b_grade_trigger(s, opts, regime),
            trigger_type=_b_grade_trigger_type(s, opts, regime),
        )
        if previous_grade in ("A+", "A"):
            return CycleResult(
                ticker=ticker, transition="Demote",
                previous_grade=previous_grade, current_grade="B", score=score,
                idea=idea, badge="Lost Validity This Cycle",
            )
        return CycleResult(
            ticker=ticker, transition="Retain",
            previous_grade=previous_grade, current_grade="B", score=score,
            idea=idea,
        )

    # A-territory (score ≥ 80) — run A+ checklist
    aplus_fails   = _aplus_checklist(s, opts, regime)
    current_grade = "A+" if not aplus_fails else "A"
    idea = TradeIdea(
        setup=s, options=opts, rank=0, why=why,
        score=score, composite_grade=current_grade,
        failures=aplus_fails,
    )

    if previous_grade == "B":
        return CycleResult(
            ticker=ticker, transition="Promote",
            previous_grade=previous_grade, current_grade=current_grade, score=score,
            idea=idea, badge="Promoted This Cycle",
        )
    # Was already A / A+ — retain
    return CycleResult(
        ticker=ticker, transition="Retain",
        previous_grade=previous_grade, current_grade=current_grade, score=score,
        idea=idea,
    )


# ── Single cycle ──────────────────────────────────────────────

def run_cycle(
    candidates: list[TradeIdea],
    macro_data: dict | None = None,
) -> list[CycleResult]:
    """
    Run one rescan pass over the provided candidates.

    Args:
        candidates: TradeIdea objects to evaluate (watchlist B + validated A/A+).
        macro_data: pre-fetched macro data; fetched fresh if None.

    Returns:
        List of CycleResult, one per candidate.
    """
    if macro_data is None:
        macro_data = fetch_all(MACRO_SYMBOLS)

    regime  = classify(macro_data)
    results = []

    for idea in candidates:
        result = _rescan_ticker(idea.setup.ticker, idea.composite_grade, regime)
        results.append(result)

    return results


# ── Timed loop ────────────────────────────────────────────────

def run_loop(
    candidates: list[TradeIdea],
    interval: int = INTERVAL_DEFAULT,
    max_cycles: int | None = None,
    on_cycle: Callable[[list[CycleResult]], None] | None = None,
) -> None:
    """
    Run the rescanner on a timed loop.

    Args:
        candidates:  Initial list of TradeIdea to track.
        interval:    Seconds between cycles (use INTERVAL_* constants).
        max_cycles:  Stop after N cycles. None = run until interrupted or
                     no candidates remain.
        on_cycle:    Optional callback invoked after each cycle with the
                     list of CycleResults for that cycle.
    """
    cycle = 0
    active = list(candidates)

    while active and (max_cycles is None or cycle < max_cycles):
        now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        print(f"\n[Rescanner] Cycle {cycle + 1}  —  {now}  ({len(active)} candidates)", flush=True)

        results = run_cycle(active)

        # Print transitions; rebuild active list
        next_active: list[TradeIdea] = []
        for result in results:
            if result.badge:
                print(
                    f"  [{result.badge}]  {result.ticker}: "
                    f"{result.previous_grade} → {result.transition} "
                    f"({result.current_grade}  score {result.score})",
                    flush=True,
                )
            else:
                print(
                    f"  {result.ticker}: {result.transition} "
                    f"({result.current_grade}  score {result.score})",
                    flush=True,
                )

            if result.transition != "Reject" and result.idea is not None:
                next_active.append(result.idea)

        if on_cycle:
            on_cycle(results)

        active = next_active
        cycle += 1

        if active and (max_cycles is None or cycle < max_cycles):
            print(f"[Rescanner] Next cycle in {interval // 60}m {interval % 60:02d}s", flush=True)
            time.sleep(interval)

    if not active:
        print("[Rescanner] No candidates remaining — stopped.", flush=True)
