# ============================================================
# MACRO SUITE — Chart Quality Engine
# ============================================================
# Evaluates a ticker's chart structure and grades it A/B/C.
#
# Core reasoning: options are expensive. Buying options on a
# weak chart is the fastest way to lose money. The chart must
# pass before the options layer is even consulted.
#
# Grade rules:
#   A (score 5-6) → proceed to options layer
#   B (score 3-4) → watchlist only, not tradeable today
#   C (score 0-2) → discard
# ============================================================

from __future__ import annotations

import pandas as pd
import pandas_ta as ta


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMA (9/21/50) and RSI (14) to the dataframe."""
    df.ta.ema(length=9,  append=True)
    df.ta.ema(length=21, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.rsi(length=14, append=True)
    return df


def ema_alignment(price: float, e9: float, e21: float, e50: float) -> str:
    if price > e9 > e21 > e50:   return "bullish"
    if price < e9 < e21 < e50:   return "bearish"
    return "mixed"


def support_resistance(df: pd.DataFrame, lookback: int = 20) -> tuple[float, float]:
    recent = df.tail(lookback)
    return round(recent["Low"].min(), 2), round(recent["High"].max(), 2)


def detect_setup_type(
    price: float,
    e9: float,
    e21: float,
    e50: float,
    rsi: float,
    resistance: float,
) -> str:
    """
    Identify the setup type based on price position relative to EMAs and RSI.

    - trend:     price above all EMAs, RSI healthy (50-72)
    - pullback:  price between EMA21-EMA9 (dipped to support), RSI cooling (40-60)
    - breakout:  price within 2% of resistance, EMAs aligned, RSI 50-65
    - reversal:  price below EMAs but RSI oversold (<35) near support
    - none:      no clean structure
    """
    near_resistance = price >= resistance * 0.98

    if price > e9 > e21 > e50 and 50 <= rsi <= 72:
        if near_resistance and 50 <= rsi <= 65:
            return "breakout"
        return "trend"

    if e9 > e21 > e50 and e21 <= price <= e9 and 40 <= rsi <= 62:
        return "pullback"

    if price < e21 and rsi < 35:
        return "reversal"

    return "none"


def setup_score(
    price: float,
    e9: float,
    e21: float,
    e50: float,
    rsi: float,
    last_candle_bullish: bool,
) -> int:
    score = 0
    if price > e9:   score += 1
    if e9 > e21:     score += 1
    if e21 > e50:    score += 1
    if 45 <= rsi <= 65:             score += 2
    elif 35 <= rsi < 45 or 65 < rsi <= 72: score += 1
    if last_candle_bullish:         score += 1
    return score


def confidence_score(score: int, setup_type: str, alignment: str) -> int:
    """
    Convert raw score + qualitative factors to a 0-10 confidence rating.
    This is the number shown to the trader — more intuitive than a raw score.
    """
    base = round((score / 6) * 8)   # scale 0-6 → 0-8

    # Bonus for clean setup type
    if setup_type in ("trend", "pullback"):
        base += 1
    if setup_type == "breakout":
        base += 2

    # Penalty for mixed EMAs
    if alignment == "mixed":
        base -= 1

    return max(0, min(10, base))


def chart_grade(score: int) -> str:
    if score >= 5:  return "A"
    if score >= 3:  return "B"
    return "C"


def invalidation_level(
    bias: str,
    support: float,
    e21: float,
    e50: float,
) -> float:
    """
    The price level that proves the trade idea wrong.
    For longs: below support or EMA50 (whichever is closer to price).
    For shorts: above resistance.
    """
    if bias == "LONG":
        return round(min(support, e50) * 0.99, 2)  # 1% below the level
    if bias == "SHORT":
        return round(max(support, e21) * 1.01, 2)
    return round(support, 2)
