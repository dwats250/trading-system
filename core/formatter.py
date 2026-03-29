# ============================================================
# MACRO SUITE — Terminal Formatter
# ============================================================
# Pure formatting helpers. No data fetching, no side effects.
# ============================================================

from __future__ import annotations

from typing import Optional


def arrow(pct: float) -> str:
    if pct > 0:
        return "↑"
    if pct < 0:
        return "↓"
    return "→"


def fmt_pct(pct: Optional[float]) -> str:
    if pct is None:
        return "n/a"
    return f"{pct:+.2f}%"


def fmt_price(price: Optional[float]) -> str:
    if price is None:
        return "n/a"
    if price >= 10_000:
        return f"{price:,.0f}"
    if price >= 1_000:
        return f"{price:,.2f}"
    return f"{price:.2f}"


def asset_line(label: str, data: Optional[dict]) -> str:
    """Format a single asset row: '10Y  ↑ +0.54%  @  4.44'"""
    tag = f"{label:<4}"
    if not data:
        return f"{tag} n/a"
    a = arrow(data["pct"])
    p = fmt_pct(data["pct"])
    v = fmt_price(data["price"])
    left = f"{tag} {a} {p}"
    return f"{left:<18} @  {v}"


def divider(char: str = "─", width: int = 40) -> str:
    return char * width
