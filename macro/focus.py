# ============================================================
# MACRO SUITE — Focus Router
# ============================================================
# Routes attention to the correct group based on regime.
# Mirrors the approved trading universe routing table exactly:
#
#   Oil-driven      → OIL_CORE, OIL_SUPPLY
#   Metals-driven   → METALS
#   Dollar move     → DOLLAR
#   Risk-on         → EQUITIES
#   Mixed / unclear → Reduce scope
#
# Core reasoning: scan ONLY the active group. Scanning
# everything and trading nothing is the enemy of edge.
# ============================================================

from __future__ import annotations

from config.tickers import DOLLAR, EQUITIES, METALS, OIL_CORE, OIL_SUPPLY


# ── Sub-regime detection ──────────────────────────────────────
# Translates the raw regime + primary driver into a specific
# sub-regime that maps directly to a ticker group.

def detect_sub_regime(regime: str, primary_driver: str, secondary_driver: str) -> str:
    """
    Returns one of:
      OIL-DRIVEN | METALS-DRIVEN | DOLLAR-MOVE | RISK-ON | MIXED
    """
    p = primary_driver.lower()
    s = secondary_driver.lower()

    if any(kw in p for kw in ["oil bid", "brent bid", "oil shock"]):
        return "OIL-DRIVEN"
    if any(kw in p for kw in ["gold bid", "gold", "silver"]):
        return "METALS-DRIVEN"
    if any(kw in p for kw in ["dollar strength", "dollar breakout"]):
        return "DOLLAR-MOVE"
    if regime == "RISK ON":
        return "RISK-ON"

    # Check secondary if primary wasn't definitive
    if any(kw in s for kw in ["oil bid", "brent bid"]):
        return "OIL-DRIVEN"
    if any(kw in s for kw in ["gold bid"]):
        return "METALS-DRIVEN"

    return "MIXED"


# ── Routing table ─────────────────────────────────────────────

_ROUTING: dict[str, dict] = {
    "OIL-DRIVEN": {
        "primary":   OIL_CORE,
        "secondary": OIL_SUPPLY,
        "warning":   "",
    },
    "METALS-DRIVEN": {
        "primary":   METALS,
        "secondary": [],
        "warning":   "",
    },
    "DOLLAR-MOVE": {
        "primary":   DOLLAR,
        "secondary": [],
        "warning":   "Dollar group has thin options — monitor, not primary trade",
    },
    "RISK-ON": {
        "primary":   EQUITIES,
        "secondary": OIL_CORE[:3],  # SPY/QQQ/IWM + top oil names
        "warning":   "",
    },
    "MIXED": {
        "primary":   [],
        "secondary": [],
        "warning":   "No clear regime — reduce scope, wait for clarity",
    },
}


def route(primary_driver: str, secondary_driver: str, regime: str = "MIXED") -> dict:
    """
    Return focused ticker lists based on sub-regime.

    Returns:
    {
        "sub_regime": str,
        "primary":    list[str],
        "secondary":  list[str],
        "warning":    str,
    }
    """
    sub_regime = detect_sub_regime(regime, primary_driver, secondary_driver)
    mapping = _ROUTING.get(sub_regime, _ROUTING["MIXED"])

    # VIX spike adds a warning on top of whatever group we're in
    vol_warning = ""
    if "vol spike" in primary_driver.lower():
        vol_warning = "⚠ VIX elevated — reduced size only, wait for vol to contract"

    warning = vol_warning or mapping["warning"]

    return {
        "sub_regime": sub_regime,
        "primary":    mapping["primary"],
        "secondary":  mapping["secondary"],
        "warning":    warning,
    }


def format_focus(focus: dict) -> list[str]:
    lines = [f"FOCUS  [{focus['sub_regime']}]"]
    if not focus["primary"] and not focus["secondary"]:
        lines.append("  No clear focus — stay in cash")
    if focus["primary"]:
        lines.append(f"  Primary:   {', '.join(focus['primary'])}")
    if focus["secondary"]:
        lines.append(f"  Secondary: {', '.join(focus['secondary'])}")
    if focus["warning"]:
        lines.append(f"  {focus['warning']}")
    return lines
