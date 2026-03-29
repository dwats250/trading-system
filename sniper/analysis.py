# ============================================================
# MACRO SUITE — Sniper Analysis Engine
# ============================================================
# Uses pandas-ta for all technical indicators.
# Input: pandas DataFrame with OHLCV columns
# Output: scored setup ready for ranking
# ============================================================

from __future__ import annotations

import pandas as pd
import pandas_ta as ta


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMA (9/21/50) and RSI (14) columns to the dataframe."""
    df.ta.ema(length=9,  append=True)
    df.ta.ema(length=21, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.rsi(length=14, append=True)
    return df


def ema_alignment(price: float, e9: float, e21: float, e50: float) -> str:
    if price > e9 > e21 > e50:
        return "bullish"
    if price < e9 < e21 < e50:
        return "bearish"
    return "mixed"


def support_resistance(df: pd.DataFrame, lookback: int = 20) -> tuple[float, float]:
    recent = df.tail(lookback)
    return round(recent["Low"].min(), 2), round(recent["High"].max(), 2)


def setup_score(
    price: float,
    e9: float,
    e21: float,
    e50: float,
    rsi_val: float,
    last_candle_bullish: bool,
) -> int:
    score = 0

    # EMA alignment (0–3): each level stacked correctly = +1
    if price > e9:  score += 1
    if e9 > e21:    score += 1
    if e21 > e50:   score += 1

    # RSI (0–2): sweet spot = momentum without overbought
    if 45 <= rsi_val <= 65:             score += 2
    elif 35 <= rsi_val < 45 or 65 < rsi_val <= 72: score += 1

    # Momentum (0–1)
    if last_candle_bullish:             score += 1

    return score


def classify_setup(score: int) -> str:
    if score >= 5:  return "IDEAL"
    if score >= 3:  return "FALLBACK"
    return "NO TRADE"
