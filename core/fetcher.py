# ============================================================
# MACRO SUITE — Market Data Fetcher
# ============================================================
# Single source for all Yahoo Finance data.
# Returns a consistent dict: {"price": float, "pct": float}
# pct = % change from previous close to current price.
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone
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

        pct    = ((price - prev_close) / prev_close) * 100.0
        change = price - prev_close
        market_time = meta.get("regularMarketTime")
        as_of = (
            datetime.fromtimestamp(market_time, tz=timezone.utc).strftime("%H:%M UTC")
            if market_time else None
        )
        return {"price": float(price), "pct": float(pct), "change": float(change), "as_of": as_of}

    except Exception:
        return None


def fetch_label(symbols: list[str]) -> Optional[dict]:
    """Try each symbol in the list and return the first successful result."""
    for sym in symbols:
        data = fetch_symbol(sym)
        if data is not None:
            return data
    return None


def fetch_ohlcv(symbol: str, range_: str = "3mo") -> list[dict]:
    """Fetch daily OHLCV bars. Returns [{date, open, high, low, close}]."""
    try:
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{quote(symbol, safe='')}?range={range_}&interval=1d"
        )
        resp = requests.get(url, headers=_HEADERS, timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        timestamps = result.get("timestamp", [])
        q = result["indicators"]["quote"][0]
        opens  = q.get("open",  [])
        highs  = q.get("high",  [])
        lows   = q.get("low",   [])
        closes = q.get("close", [])
        bars = []
        for i, ts in enumerate(timestamps):
            if i >= len(closes) or closes[i] is None:
                continue
            bars.append({
                "date":  datetime.fromtimestamp(ts).strftime("%m/%d"),
                "open":  opens[i],
                "high":  highs[i],
                "low":   lows[i],
                "close": closes[i],
            })
        return bars
    except Exception:
        return []


def fetch_all(symbol_map: dict[str, list[str]]) -> dict[str, Optional[dict]]:
    """
    Fetch all labels in symbol_map.
    Returns {label: {"price": float, "pct": float} | None}
    """
    return {label: fetch_label(symbols) for label, symbols in symbol_map.items()}
