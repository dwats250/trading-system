# ============================================================
# MACRO SUITE — Sniper Scanner (Chart Quality Engine)
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field

import yfinance as yf

from sniper.analysis import (
    add_indicators,
    chart_grade,
    compute_rr,
    confidence_score,
    detect_setup_type,
    ema_alignment,
    invalidation_level,
    setup_score,
    support_resistance,
)


@dataclass
class Setup:
    ticker:      str
    price:       float
    e9:          float
    e21:         float
    e50:         float
    rsi_val:     float
    alignment:   str        # bullish / bearish / mixed
    support:     float
    resistance:  float
    score:       int        # raw 0-6
    grade:       str        # A / B / C
    confidence:  int        # 0-10
    setup_type:  str        # trend / pullback / breakout / reversal / none
    bias:        str        # LONG / SHORT / NEUTRAL
    entry_note:  str
    invalidation: float     # price that proves trade wrong
    rr:          float      # risk/reward ratio (reward ÷ risk)


def _fetch(symbol: str) -> object | None:
    try:
        df = yf.Ticker(symbol).history(period="90d")
        return df if len(df) >= 55 else None
    except Exception:
        return None


def _bias(alignment: str, rsi_val: float) -> str:
    if alignment == "bullish" and rsi_val < 72:   return "LONG"
    if alignment == "bearish" and rsi_val > 28:   return "SHORT"
    return "NEUTRAL"


def _entry_note(bias: str, price: float, e9: float, e21: float,
                resistance: float, support: float, setup_type: str) -> str:
    if bias == "LONG":
        if setup_type == "breakout":
            return f"Break and close above {resistance:.2f}"
        if setup_type == "pullback":
            return f"Entry on dip to EMA9 (~{e9:.2f}) or EMA21 (~{e21:.2f})"
        if price > e9 * 1.03:
            return f"Extended — wait for pullback to EMA21 (~{e21:.2f})"
        return f"Entry near EMA9 (~{e9:.2f}) or break above {resistance:.2f}"
    if bias == "SHORT":
        if price < e9 * 0.97:
            return f"Extended — wait for bounce to EMA21 (~{e21:.2f}) to short"
        return f"Short below support (~{support:.2f})"
    return "No clean entry — wait for structure"


def scan(tickers: dict[str, str]) -> list[Setup]:
    """Scan tickers and return setups sorted by grade then confidence."""
    setups: list[Setup] = []

    for label, symbol in tickers.items():
        df = _fetch(symbol)
        if df is None:
            continue

        df = add_indicators(df)
        row = df.iloc[-1]

        price   = round(float(row["Close"]), 2)
        e9      = round(float(row.get("EMA_9",  row["Close"])), 2)
        e21     = round(float(row.get("EMA_21", row["Close"])), 2)
        e50     = round(float(row.get("EMA_50", row["Close"])), 2)
        rsi_val = round(float(row.get("RSI_14", 50)), 1)

        alignment  = ema_alignment(price, e9, e21, e50)
        support, resistance = support_resistance(df)
        last_bullish = float(row["Close"]) > float(row["Open"])

        score      = setup_score(price, e9, e21, e50, rsi_val, last_bullish)
        grade      = chart_grade(score)
        setup_type = detect_setup_type(price, e9, e21, e50, rsi_val, resistance)
        conf       = confidence_score(score, setup_type, alignment)
        bias       = _bias(alignment, rsi_val)
        inv        = invalidation_level(bias, support, e21, e50)
        rr         = compute_rr(bias, price, support, resistance, inv)
        note       = _entry_note(bias, price, e9, e21, resistance, support, setup_type)

        setups.append(Setup(
            ticker=label, price=price,
            e9=e9, e21=e21, e50=e50,
            rsi_val=rsi_val, alignment=alignment,
            support=support, resistance=resistance,
            score=score, grade=grade,
            confidence=conf, setup_type=setup_type,
            bias=bias, entry_note=note, invalidation=inv,
            rr=rr,
        ))

    # Sort: A before B before C, then by confidence descending
    grade_order = {"A": 0, "B": 1, "C": 2}
    setups.sort(key=lambda s: (grade_order[s.grade], -s.confidence))
    return setups
