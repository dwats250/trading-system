# ============================================================
# MACRO SUITE — Macro Pulse Orchestrator
# ============================================================
# Brings together: fetch → session → regime → incidents →
# drivers → cross-asset read → terminal output.
# ============================================================

from __future__ import annotations

from datetime import datetime

from config.tickers import MACRO_SYMBOLS
from core.fetcher import fetch_all
from core.formatter import asset_line, divider
from core.notifier import send
from macro.incidents import detect
from macro.regime import classify, cross_asset_read, drivers
from macro.session import current_session

# Display order for the asset table
_ASSET_ORDER = [
    "10Y", "DXY", "UJ",
    "VIX",
    "WTI", "BRT",
    "SPY", "QQQ",
    "XAU", "XAG", "HG",
    "HYG", "BTC",
]



def run() -> dict:
    """Run the macro pulse. Returns the raw data map for use by other modules."""
    data_map = fetch_all(MACRO_SYMBOLS)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    session = current_session()
    regime = classify(data_map)
    primary, secondary = drivers(data_map)
    incidents = detect(data_map)
    read = cross_asset_read(data_map)

    lines: list[str] = []
    lines.append("MACRO PULSE")
    lines.append(f"{now}  |  {session} Session")
    lines.append(divider())
    lines.append(regime)
    lines.append(f"Primary:    {primary}")
    lines.append(f"Secondary:  {secondary}")

    if incidents:
        lines.append("")
        for inc in incidents:
            lines.append(f"⚠  {inc}")

    lines.append(divider())

    for label in _ASSET_ORDER:
        lines.append(asset_line(label, data_map.get(label)))

    lines.append(divider())
    lines.append(read)

    output = "\n".join(lines)
    print(output)
    send(output)
    return data_map
