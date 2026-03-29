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
    """Add EMA (9/21/50), RSI (14), and ATR (14) to the dataframe."""
    df.ta.ema(length=9,  append=True)
    df.ta.ema(length=21, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.atr(length=14, append=True)   # used for volatility-normalised stop floors
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
    support: float = 0.0,
) -> str:
    """
    Identify the setup type based on price position relative to EMAs and RSI.

    LONG setups (unchanged):
    - trend:            price above all EMAs, RSI healthy (50-72)
    - pullback:         price between EMA21-EMA9, RSI cooling (40-62)
    - breakout:         price within 2% of resistance, EMAs aligned, RSI 50-65
    - reversal:         price below EMAs but RSI oversold (<35)

    SHORT setups (Phase 2A — bearish EMA stack: e9 < e21 < e50):
    - breakdown:        price at/below support, room to fall (RSI 25-55)
    - failed_breakout:  price reversed from near resistance, now falling (RSI 40-65)
    - trend_rejection:  price bounced into EMA9 overhead resistance (RSI 45-65)

    - none:             no clean structure
    """
    # ── LONG setups (logic unchanged) ────────────────────────
    near_resistance = price >= resistance * 0.98

    if price > e9 > e21 > e50 and 50 <= rsi <= 72:
        if near_resistance and 50 <= rsi <= 65:
            return "breakout"
        return "trend"

    if e9 > e21 > e50 and e21 <= price <= e9 and 40 <= rsi <= 62:
        return "pullback"

    # ── SHORT setups (Phase 2A) ───────────────────────────────
    # Requires full bearish EMA stack: e9 < e21 < e50 (price < e9 per ema_alignment)
    if e9 < e21 < e50:
        # Breakdown: price at or below support — bearish continuation entry
        if support > 0 and price <= support * 1.01 and 25 <= rsi <= 55:
            return "breakdown"
        # Failed breakout: price reversed from near resistance and is declining
        if resistance > 0 and price >= resistance * 0.93 and price <= resistance * 0.98 and 40 <= rsi <= 65:
            return "failed_breakout"
        # Trend rejection: price bounced into EMA9 overhead — short from resistance
        if price >= e9 * 0.97 and 45 <= rsi <= 65:
            return "trend_rejection"

    # ── Reversal (long bounce from oversold — long-side only) ─
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
    bias: str = "LONG",
) -> int:
    if bias == "SHORT":
        # Mirror of long-side scoring for bearish structure
        score = 0
        if price < e9:   score += 1   # price below EMA9
        if e9 < e21:     score += 1   # EMA9 below EMA21
        if e21 < e50:    score += 1   # full bearish stack
        if 35 <= rsi <= 55:              score += 2  # RSI has room to fall
        elif 25 <= rsi < 35 or 55 < rsi <= 65: score += 1
        if not last_candle_bullish:  score += 1   # bearish candle
        return score
    # LONG scoring (unchanged)
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

    # Bonus for clean setup type (long-side)
    if setup_type in ("trend", "pullback"):
        base += 1
    if setup_type == "breakout":
        base += 2
    # Bonus for clean setup type (short-side)
    if setup_type in ("breakdown", "trend_rejection"):
        base += 1
    if setup_type == "failed_breakout":
        base += 2

    # Penalty for mixed EMAs
    if alignment == "mixed":
        base -= 1

    return max(0, min(10, base))


def chart_grade(score: int) -> str:
    if score >= 5:  return "A"
    if score >= 3:  return "B"
    return "C"


# ── Stop logic thresholds (auditable defaults) ────────────────
_EMA_BUF_LONG  = 0.985   # 1.5 % below EMA anchor
_EMA_BUF_SHORT = 1.015   # 1.5 % above EMA anchor
_MIN_STOP_PCT  = 0.010   # minimum 1.0 % distance from entry (anti-noise floor)
_ATR_MULT      = 0.5     # minimum 0.5 × ATR distance from entry (volatility floor)

# EMA anchor selection by setup type (LONG side)
_LONG_ANCHOR = {
    "trend":    "e9",    # in a clean trend, a break of EMA9 is the first warning
    "breakout": "e9",    # breakout fails if price falls back under EMA9
    "pullback": "e21",   # pullback trade; EMA21 is the level being tested
    "reversal": "e50",   # deeper reversal; EMA50 is the structural anchor
    "none":     "e21",   # no clear structure; conservative default
}

# EMA anchor selection by setup type (SHORT side — stop is ABOVE price)
_SHORT_ANCHOR = {
    "breakdown":       "e9",    # rally back above EMA9 = breakdown failed
    "failed_breakout": "e21",   # reclaiming EMA21 = breakout was real after all
    "trend_rejection": "e9",    # break above EMA9 = rejection failed
    "none":            "e21",   # conservative default
}


def invalidation_level(
    bias: str,
    price: float,
    e9: float,
    e21: float,
    e50: float,
    setup_type: str,
    atr: float,
) -> float:
    """
    EMA-anchored invalidation with a strict 6-step stop hierarchy:

      1. Select EMA anchor from setup_type (see _LONG_ANCHOR map above)
      2. Apply EMA buffer (_EMA_BUF_*) to get the initial candidate stop
      3. Compute % floor: entry price × (1 ± _MIN_STOP_PCT)
      4. Compute ATR floor: entry price ± (_ATR_MULT × ATR)
      5. Final stop = most conservative candidate (widest stop wins)
         LONG:  min(ema_stop, pct_floor, atr_floor)  — lowest price wins
         SHORT: max(ema_stop, pct_floor, atr_floor)  — highest price wins
      6. compute_rr() is called with this value as invalidation

    This replaces the old 20-day-low anchor which created absurdly wide
    stops on extended moves and collapsed R:R to near-zero.
    """
    if bias == "LONG":
        anchor_key = _LONG_ANCHOR.get(setup_type, "e21")
        anchor     = {"e9": e9, "e21": e21, "e50": e50}[anchor_key]
        ema_stop   = anchor  * _EMA_BUF_LONG              # step 2
        pct_floor  = price   * (1 - _MIN_STOP_PCT)        # step 3
        atr_floor  = price   - _ATR_MULT * atr            # step 4
        return round(min(ema_stop, pct_floor, atr_floor), 2)  # step 5

    if bias == "SHORT":
        anchor_key = _SHORT_ANCHOR.get(setup_type, "e21")
        anchor    = {"e9": e9, "e21": e21, "e50": e50}[anchor_key]
        ema_stop  = anchor * _EMA_BUF_SHORT               # step 2
        pct_floor = price  * (1 + _MIN_STOP_PCT)          # step 3
        atr_floor = price  + _ATR_MULT * atr              # step 4
        return round(max(ema_stop, pct_floor, atr_floor), 2)  # step 5

    return round(e21, 2)  # NEUTRAL: reference level only, not traded


def compute_rr(
    bias: str,
    price: float,
    support: float,
    resistance: float,
    invalidation: float,
) -> float:
    """
    Risk/Reward ratio (reward ÷ risk).

    Long:  reward = resistance − price,  risk = price − invalidation
    Short: reward = price − support,     risk = invalidation − price

    Returns 0.0 when risk is zero or negative (undefined / invalid level).
    """
    if bias == "LONG":
        reward = resistance - price
        risk   = price - invalidation
    elif bias == "SHORT":
        reward = price - support
        risk   = invalidation - price
    else:
        return 0.0
    if risk <= 0:
        return 0.0
    return round(reward / risk, 2)
