# ============================================================
# MACRO SUITE — Regime Classifier
# ============================================================
# Scores market data into RISK ON / MIXED / RISK OFF.
# Also identifies the primary and secondary macro driver —
# the assets with the largest weighted move that explain
# why the regime is what it is.
# ============================================================

from __future__ import annotations

from typing import Optional


# ── Regime Scoring ──────────────────────────────────────────
# Each asset votes +1 (risk-on signal) or -1 (risk-off signal).
# Score >= +2 → RISK ON, <= -2 → RISK OFF, else MIXED.

def _pct(data_map: dict, label: str) -> float:
    item = data_map.get(label)
    return float(item["pct"]) if item else 0.0


def classify(data_map: dict) -> str:
    score = 0
    score += 1 if _pct(data_map, "SPY") > 0 else -1
    score += 1 if _pct(data_map, "QQQ") > 0 else -1
    score += 1 if _pct(data_map, "HYG") > 0 else -1
    score += 1 if _pct(data_map, "BTC") > 0 else -1
    score -= 1 if _pct(data_map, "VIX") > 0 else -1   # VIX up = risk-off
    score -= 1 if _pct(data_map, "DXY") > 0 else -1   # Dollar up = risk-off pressure
    score -= 1 if _pct(data_map, "10Y") > 0 else -1   # Rates up = risk-off pressure

    if score >= 2:
        return "RISK ON"
    if score <= -2:
        return "RISK OFF"
    return "MIXED"


# ── Driver Detection ────────────────────────────────────────
# Each asset has a weight reflecting how "loud" its signal is.
# Primary driver = highest weighted absolute move.
# Secondary driver = second highest.

_DRIVER_WEIGHTS: dict[str, float] = {
    "VIX":  3.0,   # Vol is the loudest macro signal
    "10Y":  2.5,   # Rates drive everything
    "DXY":  2.0,   # Dollar sets the tone
    "WTI":  1.5,   # Oil is inflationary / geopolitical
    "BRT":  1.5,
    "XAU":  1.2,   # Gold as monetary stress indicator
    "SPY":  1.0,
    "QQQ":  1.0,
    "HYG":  1.0,
    "BTC":  0.8,
}

_DRIVER_LABELS: dict[str, tuple[str, str]] = {
    # label: (label when positive, label when negative)
    "VIX":  ("Vol spike",          "Vol compression"),
    "10Y":  ("Rates rising",       "Rates falling"),
    "DXY":  ("Dollar strength",    "Dollar weakness"),
    "WTI":  ("Oil bid",            "Oil selling"),
    "BRT":  ("Brent bid",          "Brent selling"),
    "XAU":  ("Gold bid",           "Gold selling"),
    "SPY":  ("Equity rally",       "Equity selloff"),
    "QQQ":  ("Tech rally",         "Tech selloff"),
    "HYG":  ("Credit bid",        "Credit selling"),
    "BTC":  ("Crypto bid",         "Crypto selling"),
}


def _driver_score(label: str, pct: float) -> float:
    weight = _DRIVER_WEIGHTS.get(label, 1.0)
    return abs(pct) * weight


def _driver_label(label: str, pct: float) -> str:
    pos, neg = _DRIVER_LABELS.get(label, (label, label))
    detail = f"({pct:+.2f}% {label})"
    return f"{pos if pct >= 0 else neg} {detail}"


def drivers(data_map: dict) -> tuple[str, str]:
    """Return (primary_driver, secondary_driver) as descriptive strings."""
    scored = []
    for label in _DRIVER_WEIGHTS:
        pct = _pct(data_map, label)
        if pct != 0.0:
            scored.append((label, pct, _driver_score(label, pct)))

    scored.sort(key=lambda x: x[2], reverse=True)

    def label_or_none(rank: int) -> str:
        if rank < len(scored):
            return _driver_label(scored[rank][0], scored[rank][1])
        return "─"

    return label_or_none(0), label_or_none(1)


# ── Cross-Asset Read ─────────────────────────────────────────
# A one-line human interpretation of what the data is saying.

def cross_asset_read(data_map: dict) -> str:
    dxy = _pct(data_map, "DXY")
    xau = _pct(data_map, "XAU")
    xag = _pct(data_map, "XAG")
    spy = _pct(data_map, "SPY")
    qqq = _pct(data_map, "QQQ")
    vix = _pct(data_map, "VIX")
    btc = _pct(data_map, "BTC")
    hyg = _pct(data_map, "HYG")
    wti = _pct(data_map, "WTI")
    tnx = _pct(data_map, "10Y")
    hg  = _pct(data_map, "HG")
    uj  = _pct(data_map, "UJ")

    if vix > 5 and spy < 0 and qqq < 0:
        return "Vol spike driving broad risk-off — defensive posture"
    if dxy > 0.5 and xau < 0 and tnx > 0:
        return "Dollar + rates rising — headwind for risk and metals"
    if dxy > 0 and xau < 0:
        return "Gold pressured by firm USD"
    if xau > 0 and xag > 0 and dxy < 0:
        return "Metals supported by weaker dollar"
    if xau > 0 and xag > 0 and tnx > 0:
        return "Metals strong despite rising yields — monetary stress bid"
    if btc > 0 and hyg > 0 and spy >= 0:
        return "Liquidity tone improving — risk appetite returning"
    if wti > 2 and spy < 0:
        return "Oil shock weighing on risk — stagflation concern"
    if hg > 0 and spy > 0:
        return "Copper + equities — growth narrative intact"
    if uj < 0:
        return "Yen strengthening — carry trades under pressure"
    return "Cross-asset tone mixed — no dominant theme"
