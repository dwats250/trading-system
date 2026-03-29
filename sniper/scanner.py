# ============================================================
# MACRO SUITE — Sniper Scanner
# ============================================================
# Fetches OHLCV history for each ticker in the watchlist,
# runs the analysis engine on it, and returns ranked setups.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf

from sniper.analysis import (
    classify_setup,
    ema_alignment,
    latest_ema,
    rsi,
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
    alignment: str       # bullish / bearish / mixed
    support: float
    resistance: float
    score: int
    grade: str           # IDEAL / FALLBACK / NO TRADE
    bias: str            # LONG / SHORT / NEUTRAL
    entry_note: str      # plain-English entry suggestion


def _fetch_ohlcv(ticker: str, days: int = 90) -> dict | None:
    """Return OHLCV lists for the given ticker, or None on failure."""
    try:
        df = yf.Ticker(ticker).history(period=f"{days}d")
        if len(df) < 55:   # need at least 50 candles for EMA50
            return None
        return {
            "closes": df["Close"].tolist(),
            "opens":  df["Open"].tolist(),
            "highs":  df["High"].tolist(),
            "lows":   df["Low"].tolist(),
        }
    except Exception:
        return None


def _bias(alignment: str, rsi_val: float) -> str:
    if alignment == "bullish" and rsi_val < 72:
        return "LONG"
    if alignment == "bearish" and rsi_val > 28:
        return "SHORT"
    return "NEUTRAL"


def _entry_note(
    bias: str,
    price: float,
    e9: float,
    e21: float,
    resistance: float,
    support: float,
    rsi_val: float,
) -> str:
    if bias == "LONG":
        dip_target = round(e21, 2)
        if price > e9 * 1.03:
            # Price extended above EMA9 — wait for pullback
            return f"Wait for pullback to EMA21 (~{dip_target})"
        return f"Entry near EMA9 (~{round(e9, 2)}) or break above {round(resistance, 2)}"
    if bias == "SHORT":
        bounce_target = round(e21, 2)
        if price < e9 * 0.97:
            return f"Wait for bounce to EMA21 (~{bounce_target}) to short"
        return f"Short below support (~{round(support, 2)})"
    return "No clean entry — wait for structure"


def scan(tickers: dict[str, str]) -> list[Setup]:
    """
    Scan all tickers. Returns setups sorted best → worst.
    tickers: {label: yahoo_symbol}
    """
    setups: list[Setup] = []

    for label, symbol in tickers.items():
        data = _fetch_ohlcv(symbol)
        if not data:
            continue

        closes = data["closes"]
        opens  = data["opens"]
        highs  = data["highs"]
        lows   = data["lows"]

        e9  = latest_ema(closes, 9)
        e21 = latest_ema(closes, 21)
        e50 = latest_ema(closes, 50)
        rsi_val = rsi(closes, 14)

        if any(v is None for v in [e9, e21, e50, rsi_val]):
            continue

        price = closes[-1]
        alignment = ema_alignment(price, e9, e21, e50)
        support, resistance = support_resistance(highs, lows)
        last_candle_bullish = closes[-1] > opens[-1]

        score = setup_score(price, e9, e21, e50, rsi_val, last_candle_bullish)
        grade = classify_setup(score)
        bias  = _bias(alignment, rsi_val)
        note  = _entry_note(bias, price, e9, e21, resistance, support, rsi_val)

        setups.append(Setup(
            ticker=label,
            price=round(price, 2),
            e9=round(e9, 2),
            e21=round(e21, 2),
            e50=round(e50, 2),
            rsi_val=round(rsi_val, 1),
            alignment=alignment,
            support=round(support, 2),
            resistance=round(resistance, 2),
            score=score,
            grade=grade,
            bias=bias,
            entry_note=note,
        ))

    # Best score first
    setups.sort(key=lambda s: s.score, reverse=True)
    return setups
