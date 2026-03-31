from __future__ import annotations


def _pct(data_map: dict, label: str) -> float:
    item = data_map.get(label)
    if not item:
        return 0.0
    return float(item.get("pct", 0.0))


def _level(data_map: dict, label: str) -> float:
    item = data_map.get(label)
    if not item:
        return 0.0
    return float(item.get("price", 0.0))


def _has_value(data_map: dict, label: str, field: str) -> bool:
    item = data_map.get(label)
    return bool(item) and item.get(field) is not None


def _volatility_component(data_map: dict) -> tuple[str, int]:
    if not _has_value(data_map, "VIX", "price") and not _has_value(data_map, "VIX", "pct"):
        return "unknown", 0

    vix_level = _level(data_map, "VIX")
    vix_pct = _pct(data_map, "VIX")

    if vix_level >= 24 or vix_pct >= 8:
        return "unstable", -2
    if vix_level >= 18 or vix_pct >= 3:
        return "elevated", -1
    return "stable", 1


def _trend_component(data_map: dict) -> tuple[str, int]:
    spy = _pct(data_map, "SPY")
    qqq = _pct(data_map, "QQQ")
    es = _pct(data_map, "ES")
    nq = _pct(data_map, "NQ")
    rty = _pct(data_map, "RTY")

    votes = [value for value in (spy, qqq, es, nq, rty) if value != 0.0]
    if not votes:
        return "mixed", 0
    if len(votes) < 3:
        return "mixed", 0

    positive = sum(1 for value in votes if value > 0)
    negative = sum(1 for value in votes if value < 0)

    if positive == len(votes) or negative == len(votes):
        return "aligned", 1
    if positive >= len(votes) - 1 or negative >= len(votes) - 1:
        return "mostly aligned", 1
    if positive == negative:
        return "conflicted", -1
    return "mixed", 0


def _cross_asset_component(data_map: dict) -> tuple[str, int]:
    spy = _pct(data_map, "SPY")
    qqq = _pct(data_map, "QQQ")
    hyg = _pct(data_map, "HYG")
    btc = _pct(data_map, "BTC")
    dxy = _pct(data_map, "DXY")
    tnx = _pct(data_map, "10Y")
    xau = _pct(data_map, "XAU")

    risk_on = sum(1 for value in (spy, qqq, hyg, btc) if value > 0)
    risk_off_pressure = sum(1 for value in (dxy, tnx) if value > 0)
    defensive_bid = 1 if xau > 0 else 0

    if risk_on >= 3 and risk_off_pressure == 0:
        return "coherent risk-on", 1
    if risk_on <= 1 and risk_off_pressure >= 1 and defensive_bid:
        return "coherent defensive", 1
    if risk_on >= 2 and risk_off_pressure >= 1:
        return "partially conflicted", -1
    if risk_on <= 1 and risk_off_pressure == 0 and defensive_bid == 0:
        return "unclear", 0
    return "mixed", 0


def _range_component(data_map: dict) -> tuple[str, int]:
    spy = _pct(data_map, "SPY")
    qqq = _pct(data_map, "QQQ")
    rty = _pct(data_map, "RTY")
    es = _pct(data_map, "ES")
    nq = _pct(data_map, "NQ")
    vix_pct = _pct(data_map, "VIX")

    moves = [abs(value) for value in (spy, qqq, rty, es, nq) if value != 0.0]
    if not moves:
        return "mixed", 0
    if len(moves) < 3:
        return "mixed", 0

    average_move = sum(moves) / len(moves)
    trend_label, trend_score = _trend_component(data_map)

    if trend_score > 0 and average_move >= 0.45 and _has_value(data_map, "VIX", "pct") and vix_pct <= 3:
        return "directional", 1
    if trend_label == "conflicted" or vix_pct >= 5:
        return "choppy", -1
    return "mixed", 0


def _minimum_evidence(data_map: dict) -> bool:
    core_labels = ("VIX", "SPY", "QQQ", "ES", "NQ", "RTY", "DXY", "10Y")
    present = sum(
        1
        for label in core_labels
        if _has_value(data_map, label, "pct") or _has_value(data_map, label, "price")
    )
    return present >= 5 and _has_value(data_map, "VIX", "price")


def _classification(score: int, volatility_state: str, range_behavior: str, has_minimum_evidence: bool) -> str:
    if volatility_state == "unstable" or score <= -2 or range_behavior == "choppy":
        return "CHAOTIC"
    if has_minimum_evidence and score >= 2 and volatility_state == "stable":
        return "CLEAN"
    return "MIXED"


def _execution_posture(classification: str) -> str:
    if classification == "CLEAN":
        return "normal"
    if classification == "CHAOTIC":
        return "defensive"
    return "selective"


def _summary(components: dict[str, str], classification: str) -> str:
    vol = components["volatility_state"]
    trend = components["trend_agreement"]
    cross = components["cross_asset_alignment"]
    range_behavior = components["range_behavior"]

    if classification == "CLEAN":
        return (
            f"Vol {vol}, index trends {trend}, cross-asset tone {cross}, "
            f"and price action looks {range_behavior}."
        )
    if classification == "CHAOTIC":
        return (
            f"Vol {vol}, trend agreement is {trend}, cross-asset tone is {cross}, "
            f"and the environment looks {range_behavior}."
        )
    return (
        f"Vol {vol}, trend agreement is {trend}, cross-asset tone is {cross}, "
        f"and conditions look {range_behavior}."
    )


def compute_market_quality(data_map: dict) -> dict:
    """Classify macro-level market quality for downstream posture decisions."""
    volatility_state, volatility_score = _volatility_component(data_map)
    trend_agreement, trend_score = _trend_component(data_map)
    cross_asset_alignment, cross_score = _cross_asset_component(data_map)
    range_behavior, range_score = _range_component(data_map)
    has_minimum_evidence = _minimum_evidence(data_map)

    components = {
        "volatility_state": volatility_state,
        "trend_agreement": trend_agreement,
        "cross_asset_alignment": cross_asset_alignment,
        "range_behavior": range_behavior,
    }
    score = volatility_score + trend_score + cross_score + range_score
    classification = _classification(score, volatility_state, range_behavior, has_minimum_evidence)

    return {
        "classification": classification,
        "score": score,
        "components": components,
        "summary": _summary(components, classification),
        "execution_posture": _execution_posture(classification),
    }
