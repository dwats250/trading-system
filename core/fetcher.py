# ============================================================
# MACRO SUITE — Market Data Fetcher
# ============================================================
# Single source for all Yahoo Finance data.
# Returns a consistent dict: {"price": float, "pct": float}
# pct = % change from previous close to current price.
# ============================================================

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

import requests

from config.settings import FETCH_TIMEOUT

_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def _yahoo_url(symbol: str) -> str:
    return (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{quote(symbol, safe='')}?range=5d&interval=1d"
    )


def fetch_symbol(symbol: str) -> Optional[dict]:
    """Fetch price + daily % change for a single Yahoo Finance symbol."""
    try:
        resp = requests.get(_yahoo_url(symbol), headers=_HEADERS, timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()

        result = payload["chart"]["result"][0]
        meta = result.get("meta", {})
        closes = result["indicators"]["quote"][0].get("close", [])
        valid = [c for c in closes if c is not None]

        if len(valid) < 2:
            return None

        prev_close = valid[-2]
        last_close = valid[-1]
        price = meta.get("regularMarketPrice", last_close)

        if price is None or prev_close in (None, 0):
            return None

        pct = ((price - prev_close) / prev_close) * 100.0
        return {"price": float(price), "pct": float(pct)}

    except Exception:
        return None


def fetch_label(symbols: list[str]) -> Optional[dict]:
    """Try each symbol in the list and return the first successful result."""
    for sym in symbols:
        data = fetch_symbol(sym)
        if data is not None:
            return data
    return None


def fetch_all(symbol_map: dict[str, list[str]]) -> dict[str, Optional[dict]]:
    """
    Fetch all labels in symbol_map.
    Returns {label: {"price": float, "pct": float} | None}
    """
    return {label: fetch_label(symbols) for label, symbols in symbol_map.items()}
