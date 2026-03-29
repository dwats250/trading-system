# ============================================================
# MACRO SUITE — Options Chain Engine
# ============================================================
# Evaluates whether a ticker's options are worth trading.
#
# Core reasoning: a great chart with terrible options liquidity
# is still a bad trade. Wide spreads, low OI, and high IV
# all erode edge before you even enter. This layer filters
# those out and suggests the most appropriate structure.
#
# Data source: yfinance (free, no API key needed)
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import yfinance as yf


# ── Liquidity thresholds ──────────────────────────────────────
# These are conservative — we'd rather miss a trade than enter
# with bad fills.

_LIQ_HIGH   = {"volume": 100, "oi": 500,  "spread_pct": 0.05}
_LIQ_MEDIUM = {"volume": 20,  "oi": 100,  "spread_pct": 0.12}


@dataclass
class OptionsAnalysis:
    ticker:          str
    expiry:          str           # e.g. "2026-04-24"
    dte:             int           # days to expiry
    atm_strike:      float
    liquidity:       str           # High / Medium / Low
    iv:              float         # implied volatility (0-1 scale, e.g. 0.35 = 35%)
    iv_pct:          str           # human-readable e.g. "35%"
    bid:             float
    ask:             float
    spread_pct:      float         # (ask-bid)/mid — lower is better
    volume:          int
    open_interest:   int
    suggested_structure: str       # Long Call / Debit Call Spread / Long Put / etc.
    structure_reason:    str       # why this structure was chosen
    contract_note:       str       # e.g. "Apr 24 $63 Call"
    delta_guidance:      str       # recommended delta range + rationale


def _find_expiry(expirations: tuple, target_dte_min: int = 25, target_dte_max: int = 50) -> str | None:
    """Find the expiration closest to 30-45 DTE."""
    today = date.today()
    best = None
    best_dte = 9999
    for exp in expirations:
        d = datetime.strptime(exp, "%Y-%m-%d").date()
        dte = (d - today).days
        if target_dte_min <= dte <= target_dte_max:
            if abs(dte - 37) < abs(best_dte - 37):   # closest to ideal 37 DTE
                best = exp
                best_dte = dte
    return best


def _liquidity_score(volume: float, oi: float, spread_pct: float) -> str:
    vol = int(volume or 0)
    oi  = int(oi or 0)
    if vol >= _LIQ_HIGH["volume"] and oi >= _LIQ_HIGH["oi"] and spread_pct <= _LIQ_HIGH["spread_pct"]:
        return "High"
    if vol >= _LIQ_MEDIUM["volume"] and oi >= _LIQ_MEDIUM["oi"] and spread_pct <= _LIQ_MEDIUM["spread_pct"]:
        return "Medium"
    return "Low"


def _suggest_structure(bias: str, iv: float, liquidity: str) -> tuple[str, str]:
    """
    Suggest an options structure based on directional bias and IV environment.

    Core logic:
    - Low IV  → buy options outright (cheap premium)
    - High IV → use spreads to reduce premium cost
    - Low liquidity → always use spreads (defined risk, easier to fill)
    """
    high_iv  = iv > 0.45   # above 45% IV is expensive for most ETFs
    poor_liq = liquidity == "Low"

    if bias == "LONG":
        if high_iv or poor_liq:
            return "Debit Call Spread", "IV elevated or liquidity thin — spread reduces cost and risk"
        return "Long Call", "Clean bullish setup with reasonable IV"

    if bias == "SHORT":
        if high_iv or poor_liq:
            return "Debit Put Spread", "IV elevated or liquidity thin — spread reduces cost and risk"
        return "Long Put", "Clean bearish setup with reasonable IV"

    return "No position", "No clear directional bias"


def _delta_guidance(iv: float, structure: str) -> str:
    """
    Recommend a delta range based on IV environment and chosen structure.

    Outright options (Long Call/Put):
      - Normal IV → ATM (0.45–0.55) gives best directional response per dollar
      - High IV   → near-ATM (0.40–0.50) to limit premium while staying responsive

    Spreads (Debit Spread):
      - Long leg slightly OTM keeps net debit lower
      - High IV spreads → go further OTM to stay under 33% of spread width in cost
    """
    is_spread = "Spread" in structure
    high_iv   = iv > 0.45

    if is_spread:
        if high_iv:
            return "0.30–0.40 (OTM long leg) — IV elevated, spread limits premium cost"
        return "0.35–0.45 (slight OTM long leg) — defined risk, balance cost vs. delta"

    if high_iv:
        return "0.40–0.50 (near ATM) — IV elevated, stay ATM to minimize overpay"
    return "0.45–0.55 (ATM) — clean setup, maximize directional exposure"


def analyze(ticker: str, bias: str, current_price: float) -> OptionsAnalysis | None:
    """
    Fetch and analyze the options chain for a ticker.
    Returns None if no suitable expiry or data is unavailable.
    """
    try:
        t = yf.Ticker(ticker)
        expirations = t.options
        if not expirations:
            return None

        expiry = _find_expiry(expirations)
        if not expiry:
            return None

        dte = (datetime.strptime(expiry, "%Y-%m-%d").date() - date.today()).days
        chain = t.option_chain(expiry)

        # Choose calls or puts based on bias
        df = chain.calls if bias in ("LONG", "NEUTRAL") else chain.puts

        if df.empty:
            return None

        # Find ATM strike (closest to current price)
        df = df.copy()
        df["dist"] = (df["strike"] - current_price).abs()
        atm = df.sort_values("dist").iloc[0]

        strike      = float(atm["strike"])
        bid         = float(atm.get("bid", 0) or 0)
        ask         = float(atm.get("ask", 0) or 0)
        volume      = int(atm.get("volume", 0) or 0)
        oi          = int(atm.get("openInterest", 0) or 0)
        iv          = float(atm.get("impliedVolatility", 0) or 0)

        mid = (bid + ask) / 2 if (bid + ask) > 0 else 1
        spread_pct = round((ask - bid) / mid, 3) if mid > 0 else 1.0

        liquidity = _liquidity_score(volume, oi, spread_pct)
        structure, reason = _suggest_structure(bias, iv, liquidity)
        delta_guide = _delta_guidance(iv, structure)

        exp_label = datetime.strptime(expiry, "%Y-%m-%d").strftime("%b %d")
        option_type = "Call" if bias in ("LONG", "NEUTRAL") else "Put"
        contract_note = f"{exp_label} ${strike:.0f} {option_type}"

        return OptionsAnalysis(
            ticker=ticker,
            expiry=expiry,
            dte=dte,
            atm_strike=strike,
            liquidity=liquidity,
            iv=round(iv, 3),
            iv_pct=f"{iv * 100:.0f}%",
            bid=round(bid, 2),
            ask=round(ask, 2),
            spread_pct=round(spread_pct, 3),
            volume=volume,
            open_interest=oi,
            suggested_structure=structure,
            structure_reason=reason,
            contract_note=contract_note,
            delta_guidance=delta_guide,
        )

    except Exception:
        return None
