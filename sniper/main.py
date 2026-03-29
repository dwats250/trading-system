#!/usr/bin/env python3
# ============================================================
# MACRO SUITE — Entry Sniper
# ============================================================
# Scans the watchlist for high-quality trade setups using
# EMA structure, RSI, and momentum. Output is ranked:
#   IDEAL → FALLBACK → NO TRADE
# Run: python main.py  (sniper runs after macro pulse)
# ============================================================

from __future__ import annotations

from datetime import datetime

from config.tickers import SNIPER_SYMBOLS
from core.formatter import divider
from macro.regime import classify
from macro.session import current_session
from sniper.scanner import Setup, scan


# ── Regime warning ───────────────────────────────────────────

_REGIME_NOTES = {
    "RISK OFF": "⚠  RISK OFF — reduce size, prefer shorts or cash",
    "MIXED":    "~  Mixed environment — be selective, wait for clarity",
    "RISK ON":  "✓  RISK ON — favorable for long setups",
}


# ── Format a single setup ────────────────────────────────────

def _format_setup(rank: int, s: Setup) -> str:
    lines = [
        f"{rank}. {s.ticker}  —  {s.bias} BIAS  [{s.grade}]",
        f"   Price: {s.price}  |  RSI: {s.rsi_val}  |  EMA: {s.alignment}",
        f"   EMA9: {s.e9}  EMA21: {s.e21}  EMA50: {s.e50}",
        f"   S: {s.support}  R: {s.resistance}",
        f"   Entry: {s.entry_note}",
    ]
    return "\n".join(lines)


# ── Build terminal output ────────────────────────────────────

def build_output(macro_data: dict | None = None) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    session = current_session()

    lines: list[str] = []
    lines.append("ENTRY SNIPER")
    lines.append(f"{now}  |  {session} Session")
    lines.append(divider())

    # Macro context note (if data passed in)
    if macro_data:
        regime = classify(macro_data)
        lines.append(_REGIME_NOTES.get(regime, regime))
        lines.append("")

    print("Scanning watchlist...", flush=True)
    setups = scan(SNIPER_SYMBOLS)

    tradeable = [s for s in setups if s.grade != "NO TRADE"]
    no_trade  = [s for s in setups if s.grade == "NO TRADE"]

    # Top setups
    if tradeable:
        lines.append(f"TOP SETUPS ({len(tradeable)})")
        lines.append("")
        for i, s in enumerate(tradeable[:3], 1):
            lines.append(_format_setup(i, s))
            lines.append("")
    else:
        lines.append("NO SETUPS — conditions unfavorable across watchlist")
        lines.append("")

    # No-trade list
    if no_trade:
        tickers = ", ".join(s.ticker for s in no_trade)
        lines.append(f"NO TRADE: {tickers}")

    lines.append(divider())
    return "\n".join(lines)


def run(macro_data: dict | None = None) -> None:
    output = build_output(macro_data)
    print(output)
