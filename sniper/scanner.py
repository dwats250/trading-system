# ============================================================
# MACRO SUITE — Sniper Scanner
# ============================================================
# Fetches OHLCV history, runs pandas-ta indicators,
# scores and ranks trade setups.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf

from sniper.analysis import (
    add_indicators,
    classify_setup,
    ema_alignment,
    setup_score,
    support_resistance,
)


@dataclass
class Setup:
    ticker: str
    price: float
    e9: float
    e21: float
    e50: float
    rsi_val: float
    alignment: str
    support: float
    resistance: float
    score: int
    grade: str
    bias: str
    entry_note: str


def _fetch(symbol: str) -> object | None:
    try:
        df = yf.Ticker(symbol).history(period="90d")
        if len(df) < 55:
            return None
        return df
    except Exception:
        return None


def _bias(alignment: str, rsi_val: float) -> str:
    if alignment == "bullish" and rsi_val < 72:
        return "LONG"
    if alignment == "bearish" and rsi_val > 28:
        return "SHORT"
    return "NEUTRAL"


def _entry_note(bias: str, price: float, e9: float, e21: float,
                resistance: float, support: float) -> str:
    if bias == "LONG":
        if price > e9 * 1.03:
            return f"Extended — wait for pullback to EMA21 (~{e21:.2f})"
        return f"Entry near EMA9 (~{e9:.2f}) or break above {resistance:.2f}"
    if bias == "SHORT":
        if price < e9 * 0.97:
            return f"Extended — wait for bounce to EMA21 (~{e21:.2f}) to short"
        return f"Short below support (~{support:.2f})"
    return "No clean entry — wait for structure"


def scan(tickers: dict[str, str]) -> list[Setup]:
    """Scan all tickers and return setups sorted best → worst."""
    setups: list[Setup] = []

    for label, symbol in tickers.items():
        df = _fetch(symbol)
        if df is None:
            continue

        df = add_indicators(df)
        row = df.iloc[-1]
        prev = df.iloc[-2]

        price   = round(float(row["Close"]), 2)
        e9      = round(float(row.get("EMA_9",  row["Close"])), 2)
        e21     = round(float(row.get("EMA_21", row["Close"])), 2)
        e50     = round(float(row.get("EMA_50", row["Close"])), 2)
        rsi_val = round(float(row.get("RSI_14", 50)), 1)

        alignment = ema_alignment(price, e9, e21, e50)
        support, resistance = support_resistance(df)
        last_bullish = float(row["Close"]) > float(row["Open"])

        score = setup_score(price, e9, e21, e50, rsi_val, last_bullish)
        grade = classify_setup(score)
        bias  = _bias(alignment, rsi_val)
        note  = _entry_note(bias, price, e9, e21, resistance, support)

        setups.append(Setup(
            ticker=label, price=price,
            e9=e9, e21=e21, e50=e50,
            rsi_val=rsi_val, alignment=alignment,
            support=support, resistance=resistance,
            score=score, grade=grade, bias=bias,
            entry_note=note,
        ))

    setups.sort(key=lambda s: s.score, reverse=True)
    return setups
