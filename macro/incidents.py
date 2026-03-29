# ============================================================
# MACRO SUITE — Incident Detection
# ============================================================
# Watches for abnormal moves that warrant an alert:
#   • Rate spike (10Y)
#   • Dollar breakout (DXY)
#   • Oil shock (WTI or Brent)
#   • Vol spike (VIX)
#
# Returns a list of incident strings (empty = no incidents).
# ============================================================

from __future__ import annotations

from config.settings import INCIDENT_THRESHOLDS


def _pct(data_map: dict, label: str) -> float:
    item = data_map.get(label)
    return float(item["pct"]) if item else 0.0


def detect(data_map: dict) -> list[str]:
    """Return a list of active incident descriptions."""
    t = INCIDENT_THRESHOLDS
    incidents: list[str] = []

    tnx = _pct(data_map, "10Y")
    if abs(tnx) >= t["rate_spike"]:
        direction = "spiking" if tnx > 0 else "collapsing"
        incidents.append(f"Rate {direction}: 10Y {tnx:+.2f}%")

    dxy = _pct(data_map, "DXY")
    if abs(dxy) >= t["dollar_breakout"]:
        direction = "breakout" if dxy > 0 else "breakdown"
        incidents.append(f"Dollar {direction}: DXY {dxy:+.2f}%")

    wti = _pct(data_map, "WTI")
    brt = _pct(data_map, "BRT")
    oil_move = wti if abs(wti) >= abs(brt) else brt
    oil_label = "WTI" if abs(wti) >= abs(brt) else "Brent"
    if abs(oil_move) >= t["oil_shock"]:
        direction = "shock up" if oil_move > 0 else "shock down"
        incidents.append(f"Oil {direction}: {oil_label} {oil_move:+.2f}%")

    vix = _pct(data_map, "VIX")
    if vix >= t["vol_spike"]:
        incidents.append(f"Vol spike: VIX {vix:+.2f}%")

    return incidents
