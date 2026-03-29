# ============================================================
# MACRO SUITE — Sniper Analysis Engine
# ============================================================
# Pure math — no data fetching, no I/O.
# Input: list of OHLCV values (floats)
# Output: computed indicators used for setup scoring
# ============================================================

from __future__ import annotations

import statistics


# ── Exponential Moving Average ───────────────────────────────
# EMA gives more weight to recent prices than a simple average.
# period=9  → fast, tracks price closely
# period=21 → medium, filters out noise
# period=50 → slow, shows the macro trend

def ema(closes: list[float], period: int) -> list[float]:
    if len(closes) < period:
        return []
    k = 2 / (period + 1)
    result = [sum(closes[:period]) / period]  # seed with SMA
    for price in closes[period:]:
        result.append(price * k + result[-1] * (1 - k))
    return result


def latest_ema(closes: list[float], period: int) -> float | None:
    values = ema(closes, period)
    return values[-1] if values else None


# ── Relative Strength Index ──────────────────────────────────
# RSI measures momentum on a 0–100 scale.
# >70 = overbought (potential exhaustion)
# <30 = oversold (potential reversal)
# 45–65 = the "sweet spot" for momentum entries

def rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [abs(d) if d < 0 else 0.0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ── Support and Resistance ───────────────────────────────────
# Simple swing-level detection: look back over recent candles
# and find the most significant high (resistance) and low (support).

def support_resistance(
    highs: list[float],
    lows: list[float],
    lookback: int = 20,
) -> tuple[float, float]:
    """Return (support, resistance) as the recent swing low and high."""
    recent_highs = highs[-lookback:]
    recent_lows = lows[-lookback:]
    return min(recent_lows), max(recent_highs)


# ── EMA Alignment ────────────────────────────────────────────
# Checks whether the EMAs are stacked in bullish or bearish order.

def ema_alignment(price: float, e9: float, e21: float, e50: float) -> str:
    """
    Returns one of:
      'bullish'  — price > EMA9 > EMA21 > EMA50 (fully stacked up)
      'bearish'  — price < EMA9 < EMA21 < EMA50 (fully stacked down)
      'mixed'    — no clean alignment
    """
    if price > e9 > e21 > e50:
        return "bullish"
    if price < e9 < e21 < e50:
        return "bearish"
    return "mixed"


# ── Setup Score ──────────────────────────────────────────────
# Combines EMA alignment, RSI position, and momentum into a
# single 0–6 score used to rank trade candidates.

def setup_score(
    price: float,
    e9: float,
    e21: float,
    e50: float,
    rsi_val: float,
    last_candle_bullish: bool,
) -> int:
    score = 0

    # EMA alignment (0–3 points)
    if price > e9:
        score += 1
    if e9 > e21:
        score += 1
    if e21 > e50:
        score += 1

    # RSI positioning (0–2 points)
    if 45 <= rsi_val <= 65:
        score += 2   # sweet spot: momentum without overbought
    elif 35 <= rsi_val < 45 or 65 < rsi_val <= 72:
        score += 1   # acceptable but less ideal

    # Momentum (0–1 point)
    if last_candle_bullish:
        score += 1

    return score


def classify_setup(score: int) -> str:
    if score >= 5:
        return "IDEAL"
    if score >= 3:
        return "FALLBACK"
    return "NO TRADE"
