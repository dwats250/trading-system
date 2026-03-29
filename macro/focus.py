# ============================================================
# MACRO SUITE — Focus Router
# ============================================================
# Narrows the trading universe based on playbook guidance.
# Rather than scanning 40 tickers, we focus on the 3-5 most
# relevant given the current macro environment.
#
# Core reasoning: attention is a limited resource. The focus
# router prevents "scanning everything and trading nothing."
# ============================================================

from __future__ import annotations

from config.tickers import TICKERS


# ── Driver → ticker group mapping ────────────────────────────
# Maps driver keywords to groups in TICKERS config.
# Primary = scan first. Secondary = scan if no A setups in primary.

_DRIVER_FOCUS_MAP: dict[str, dict[str, list[str]]] = {
    "oil bid":          {"primary": ["oil_core", "oil_beta"], "secondary": ["energy_supply"]},
    "oil selling":      {"primary": ["oil_core"],             "secondary": []},
    "brent bid":        {"primary": ["oil_core", "oil_beta"], "secondary": []},
    "dollar strength":  {"primary": ["fx"],                   "secondary": []},
    "dollar weakness":  {"primary": ["metals"],               "secondary": ["fx"]},
    "gold bid":         {"primary": ["metals"],               "secondary": []},
    "gold selling":     {"primary": [],                       "secondary": ["metals"]},
    "equity rally":     {"primary": ["equities"],             "secondary": []},
    "equity selloff":   {"primary": ["equities"],             "secondary": []},
    "vol spike":        {"primary": [],                       "secondary": []},   # wait
    "vol compression":  {"primary": ["equities"],             "secondary": ["metals"]},
    "rates rising":     {"primary": ["equities"],             "secondary": []},
    "rates falling":    {"primary": ["equities"],             "secondary": ["metals"]},
    "credit bid":       {"primary": ["equities"],             "secondary": []},
    "credit selling":   {"primary": [],                       "secondary": []},
}

# Default focus when no driver match: scan equities + oil
_DEFAULT_FOCUS = {"primary": ["equities", "oil_core"], "secondary": ["metals"]}


def _match(driver_str: str) -> dict:
    dl = driver_str.lower()
    for key, mapping in _DRIVER_FOCUS_MAP.items():
        if key in dl:
            return mapping
    return _DEFAULT_FOCUS


def _group_to_tickers(groups: list[str]) -> list[str]:
    result = []
    for group in groups:
        result.extend(TICKERS.get(group, []))
    return list(dict.fromkeys(result))  # deduplicate, preserve order


def route(primary_driver: str, secondary_driver: str) -> dict:
    """
    Return focused ticker lists based on the dominant drivers.

    Returns:
    {
        "primary":   list[str],   # scan these first
        "secondary": list[str],   # scan if no A setups in primary
        "avoid":     list[str],   # labels to skip
    }
    """
    p_map = _match(primary_driver)
    s_map = _match(secondary_driver)

    primary   = _group_to_tickers(p_map.get("primary", []))
    secondary = _group_to_tickers(
        [g for g in s_map.get("primary", []) if g not in p_map.get("primary", [])]
    )

    # Vol spike = don't trade anything
    if "vol spike" in primary_driver.lower():
        return {"primary": [], "secondary": [], "avoid": ["everything — wait for VIX to settle"]}

    return {
        "primary":   primary[:6],    # cap at 6 primary tickers
        "secondary": secondary[:4],
        "avoid":     [],
    }


def format_focus(focus: dict) -> list[str]:
    lines = ["FOCUS"]
    if not focus["primary"] and not focus["secondary"]:
        lines.append("  No clear focus — stay in cash")
        return lines
    if focus["primary"]:
        lines.append(f"  Primary:   {', '.join(focus['primary'])}")
    if focus["secondary"]:
        lines.append(f"  Secondary: {', '.join(focus['secondary'])}")
    if focus["avoid"]:
        lines.append(f"  Avoid:     {', '.join(focus['avoid'])}")
    return lines
