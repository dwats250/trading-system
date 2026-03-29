#!/usr/bin/env python3
# ============================================================
# MACRO SUITE — Pre-Market Report
# ============================================================
# Runs at 6:00 AM PST on weekdays.
# Delivers a complete morning brief:
#   1. Overnight recap (futures + key macro)
#   2. Regime & drivers
#   3. Today's economic events
#   4. Top trade setups
#   5. Sector snapshot (metals, oil, equities)
# ============================================================

from __future__ import annotations

from datetime import datetime

from config.tickers import MACRO_SYMBOLS, SNIPER_SYMBOLS, TICKERS
from core.fetcher import fetch_all, fetch_label
from core.formatter import arrow, asset_line, divider, fmt_pct, fmt_price
from core.notifier import send
from macro.focus import format_focus, route
from macro.incidents import detect
from macro.playbook import format_playbook, generate
from macro.regime import classify, cross_asset_read, drivers
from outputs.premarket_html import save as save_html
from reports.calendar import format_events, get_events
from sniper.scanner import scan


# ── Section builders ─────────────────────────────────────────

def _overnight_recap(data_map: dict) -> list[str]:
    lines = ["OVERNIGHT RECAP"]

    # Futures first — these trade overnight and set the tone
    futures = [("ES", "S&P 500"), ("NQ", "Nasdaq"), ("RTY", "Russell")]
    for label, name in futures:
        d = data_map.get(label)
        if d:
            lines.append(f"  {label:<4} {arrow(d['pct'])} {fmt_pct(d['pct']):<10} @ {fmt_price(d['price'])}  ({name})")

    lines.append("")

    # Key macro context
    macro_items = [
        ("DXY", "Dollar"),
        ("10Y", "10Y Yield"),
        ("VIX", "Volatility"),
        ("UJ",  "USD/JPY"),
        ("XAU", "Gold"),
        ("WTI", "WTI Oil"),
    ]
    for label, name in macro_items:
        d = data_map.get(label)
        if d:
            lines.append(f"  {label:<4} {arrow(d['pct'])} {fmt_pct(d['pct']):<10} @ {fmt_price(d['price'])}  ({name})")

    return lines


def _regime_section(data_map: dict) -> list[str]:
    regime = classify(data_map)
    primary, secondary = drivers(data_map)
    incidents = detect(data_map)
    read = cross_asset_read(data_map)

    lines = ["MACRO REGIME"]
    lines.append(f"  {regime}")
    lines.append(f"  Primary:   {primary}")
    lines.append(f"  Secondary: {secondary}")

    if incidents:
        lines.append("")
        for inc in incidents:
            lines.append(f"  ⚠  {inc}")

    lines.append("")
    lines.append(f"  {read}")
    return lines


def _calendar_section() -> list[str]:
    events = get_events()
    lines = ["TODAY'S EVENTS  (UTC)"]
    for line in format_events(events):
        lines.append(f"  {line}")
    return lines


def _playbook_section(playbook: dict) -> list[str]:
    return format_playbook(playbook)


def _key_levels_section(setups: list, focus: dict) -> list[str]:
    setup_map = {s.ticker: s for s in setups}
    lines = [f"KEY LEVELS  [{focus['sub_regime']}]"]

    groups = [("Primary", focus["primary"]), ("Secondary", focus["secondary"])]
    any_found = False

    for group_name, tickers in groups:
        if not tickers:
            continue
        found = [(t, setup_map[t]) for t in tickers if t in setup_map]
        if not found:
            continue
        any_found = True
        lines.append(f"  {group_name}:")
        for ticker, s in found:
            setup_label = s.setup_type.title() if s.setup_type != "none" else "No setup"
            lines.append(
                f"    {ticker:<6} S {s.support:<8} R {s.resistance:<8}"
                f" — {setup_label:<12} Confidence {s.confidence}/10"
            )

    if not any_found:
        lines.append("  No focused tickers with data available")

    if focus.get("warning"):
        lines.append(f"  {focus['warning']}")

    return lines


def _setups_section(data_map: dict, setups: list | None = None) -> list[str]:
    regime = classify(data_map)
    regime_notes = {
        "RISK OFF": "⚠  RISK OFF — reduce size, favor shorts or cash",
        "MIXED":    "~  Mixed — be selective, wait for clarity",
        "RISK ON":  "✓  RISK ON — favorable for longs",
    }

    lines = ["TOP SETUPS"]
    lines.append(f"  {regime_notes.get(regime, regime)}")
    lines.append("")

    if setups is None:
        setups = scan(SNIPER_SYMBOLS)
    tradeable = [s for s in setups if s.grade != "NO TRADE"]
    no_trade  = [s for s in setups if s.grade == "NO TRADE"]

    if tradeable:
        for i, s in enumerate(tradeable[:3], 1):
            lines.append(f"  {i}. {s.ticker}  —  {s.bias}  [{s.grade}]")
            lines.append(f"     Price {s.price}  RSI {s.rsi_val}  EMA {s.alignment}")
            lines.append(f"     {s.entry_note}")
            lines.append("")
    else:
        lines.append("  No clean setups — stay flat")
        lines.append("")

    if no_trade:
        lines.append(f"  Skip: {', '.join(s.ticker for s in no_trade)}")

    return lines


def _sector_snapshot(data_map: dict) -> list[str]:
    lines = ["SECTOR SNAPSHOT"]

    sections = [
        ("Metals",   ["XAU", "XAG", "GDX"]),
        ("Oil",      ["WTI", "BRT", "XLE"]),
        ("Equities", ["SPY", "QQQ", "IWM"]),
        ("Credit",   ["HYG", "BTC"]),
    ]

    # Fetch extra tickers not in base macro map
    extra_symbols = {
        "GDX": ["GDX"],
        "IWM": ["IWM"],
    }
    extra = fetch_all(extra_symbols)
    combined = {**data_map, **extra}

    for section_name, labels in sections:
        parts = []
        for label in labels:
            d = combined.get(label)
            if d:
                parts.append(f"{label} {arrow(d['pct'])} {fmt_pct(d['pct'])}")
        if parts:
            lines.append(f"  {section_name:<10} {'  '.join(parts)}")

    return lines


# ── Main report builder ──────────────────────────────────────

def build_report() -> str:
    now = datetime.now().strftime("%Y-%m-%d  %I:%M %p PST")

    print("Fetching market data...", flush=True)
    data_map = fetch_all(MACRO_SYMBOLS)

    # Pre-compute shared state so sections don't re-derive it
    regime   = classify(data_map)
    primary, secondary = drivers(data_map)
    playbook = generate(regime, primary, secondary)
    focus    = route(primary, secondary, regime)

    print("Scanning setups...", flush=True)
    setups = scan(SNIPER_SYMBOLS)

    lines: list[str] = []
    lines.append("PRE-MARKET REPORT")
    lines.append(now)
    lines.append(divider("═"))

    lines.append("")
    lines.extend(_overnight_recap(data_map))

    lines.append("")
    lines.append(divider())
    lines.extend(_regime_section(data_map))

    lines.append("")
    lines.append(divider())
    lines.extend(_playbook_section(playbook))

    lines.append("")
    lines.extend(format_focus(focus))

    lines.append("")
    lines.append(divider())
    lines.extend(_calendar_section())

    lines.append("")
    lines.append(divider())
    lines.extend(_setups_section(data_map, setups))

    lines.append("")
    lines.append(divider())
    lines.extend(_key_levels_section(setups, focus))

    lines.append("")
    lines.append(divider())
    lines.extend(_sector_snapshot(data_map))

    lines.append("")
    lines.append(divider("═"))

    return "\n".join(lines)


def run() -> None:
    report = build_report()
    print(report)
    send(report, title="Pre-Market Report")
    save_html()


if __name__ == "__main__":
    run()
