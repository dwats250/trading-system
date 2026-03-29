# ============================================================
# MACRO SUITE — Playbook Generator
# ============================================================
# Transforms macro regime + drivers into plain-English action
# guidance. This is the "what to do" layer — it sits between
# regime detection and trade selection.
#
# Core reasoning: every macro environment has a different
# optimal posture. The playbook makes that explicit so the
# trader doesn't have to re-derive it each morning.
# ============================================================

from __future__ import annotations


# ── Position size guidance ────────────────────────────────────
# RISK OFF = reduce size to limit exposure during uncertainty
# MIXED    = selective sizing, only A setups warrant full size
# RISK ON  = normal sizing, environment supports participation

_SIZE_GUIDANCE = {
    "RISK OFF": "Reduce position size (25–50% of normal)",
    "MIXED":    "Selective sizing — full size only on A setups",
    "RISK ON":  "Normal position sizing — environment is supportive",
}

# ── Bias guidance ─────────────────────────────────────────────
_BIAS_GUIDANCE = {
    "RISK OFF": "Favor defensive, short bias, or cash",
    "MIXED":    "No strong directional bias — wait for clarity",
    "RISK ON":  "Favor long bias, growth, and momentum",
}

# ── Driver-specific focus rules ───────────────────────────────
# When a specific driver is dominant, route attention accordingly.
# Each driver maps to: focus sectors, avoid sectors, and a note.

_DRIVER_RULES: dict[str, dict] = {
    "Vol spike": {
        "focus":  [],
        "avoid":  ["Tech longs", "Momentum breakouts", "Levered longs"],
        "note":   "VIX elevated — wait for volatility to contract before entering",
    },
    "Vol compression": {
        "focus":  ["Breakout setups", "Trend continuations"],
        "avoid":  [],
        "note":   "VIX falling — improving environment for directional trades",
    },
    "Oil bid": {
        "focus":  ["Energy (XLE, OXY, XOM, USO, GUSH)"],
        "avoid":  ["Consumer discretionary", "Airlines"],
        "note":   "Oil strength creates energy sector leadership",
    },
    "Oil selling": {
        "focus":  ["Airlines", "Consumer discretionary", "Short energy"],
        "avoid":  ["Energy longs"],
        "note":   "Oil weakness — pressure on energy sector",
    },
    "Dollar strength": {
        "focus":  ["UUP long", "USD pairs"],
        "avoid":  ["Gold longs", "Emerging markets", "Commodities"],
        "note":   "Strong dollar headwind for commodities and risk assets",
    },
    "Dollar weakness": {
        "focus":  ["Gold (GLD, GDX)", "Silver (SLV)", "Commodities"],
        "avoid":  ["UUP long"],
        "note":   "Weak dollar tailwind for metals and commodities",
    },
    "Rates rising": {
        "focus":  ["Financials", "Short TLT"],
        "avoid":  ["Tech longs", "Growth", "TLT long"],
        "note":   "Rising rates pressure growth/tech valuations",
    },
    "Rates falling": {
        "focus":  ["TLT long", "Tech", "Growth"],
        "avoid":  ["Financials", "Short TLT"],
        "note":   "Falling rates supportive for growth and duration",
    },
    "Gold bid": {
        "focus":  ["GLD", "GDX", "SILJ", "SLV"],
        "avoid":  [],
        "note":   "Gold bid signals monetary stress or safe-haven demand",
    },
    "Equity rally": {
        "focus":  ["SPY", "QQQ", "IWM", "Growth names"],
        "avoid":  ["Defensive shorts"],
        "note":   "Broad equity strength — trend-following environment",
    },
    "Equity selloff": {
        "focus":  ["Short SPY/QQQ", "Defensive sectors"],
        "avoid":  ["Tech longs", "Small cap longs"],
        "note":   "Equity weakness — reduce long exposure",
    },
    "Credit bid": {
        "focus":  ["Risk assets", "HYG"],
        "avoid":  [],
        "note":   "Credit bid signals improving risk appetite",
    },
    "Credit selling": {
        "focus":  ["Defensive", "Cash"],
        "avoid":  ["High beta", "Levered longs"],
        "note":   "Credit selling often leads equity weakness",
    },
}


def _match_rule(driver_str: str) -> dict | None:
    """Match a driver string against known rules (partial match)."""
    for key, rule in _DRIVER_RULES.items():
        if key.lower() in driver_str.lower():
            return rule
    return None


def generate(regime: str, primary_driver: str, secondary_driver: str) -> dict:
    """
    Generate a playbook dict from regime and driver strings.

    Returns:
    {
        "size":    str,
        "bias":    str,
        "focus":   list[str],
        "avoid":   list[str],
        "notes":   list[str],
    }
    """
    size   = _SIZE_GUIDANCE.get(regime, "Use judgment")
    bias   = _BIAS_GUIDANCE.get(regime, "")
    focus  = []
    avoid  = []
    notes  = []

    for driver in [primary_driver, secondary_driver]:
        rule = _match_rule(driver)
        if rule:
            focus.extend(rule.get("focus", []))
            avoid.extend(rule.get("avoid", []))
            if rule.get("note"):
                notes.append(rule["note"])

    # Deduplicate
    focus = list(dict.fromkeys(focus))
    avoid = list(dict.fromkeys(avoid))

    return {
        "size":  size,
        "bias":  bias,
        "focus": focus,
        "avoid": avoid,
        "notes": notes,
    }


def format_playbook(playbook: dict) -> list[str]:
    """Format playbook as terminal-ready lines."""
    lines = ["PLAYBOOK"]
    lines.append(f"  Size:  {playbook['size']}")
    lines.append(f"  Bias:  {playbook['bias']}")

    if playbook["focus"]:
        lines.append(f"  Focus: {', '.join(playbook['focus'])}")
    if playbook["avoid"]:
        lines.append(f"  Avoid: {', '.join(playbook['avoid'])}")
    for note in playbook["notes"]:
        lines.append(f"  ~  {note}")

    return lines
