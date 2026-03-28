#!/usr/bin/env python3

import os
import sys
import requests
from typing import Optional

API_KEY = os.getenv("FMP_API_KEY", "").strip()
BASE_URL = "https://financialmodelingprep.com/api/v3"
TIMEOUT = 15


def masked_key(key: str) -> str:
    if not key:
        return "<missing>"
    if len(key) <= 8:
        return key
    return f"{key[:4]}...{key[-4:]}"


def require_api_key() -> None:
    if not API_KEY:
        print("ERROR: FMP_API_KEY is missing from environment.")
        print('Run: export FMP_API_KEY="YOUR_REAL_KEY"')
        sys.exit(1)


def fetch_json(url: str):
    r = requests.get(url, timeout=TIMEOUT)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} | {r.text[:300]}")
    return r.json()


def get_quote_change_pct(symbol: str) -> Optional[float]:
    url = f"{BASE_URL}/quote/{symbol}?apikey={API_KEY}"
    data = fetch_json(url)

    if not data or not isinstance(data, list):
        raise RuntimeError(f"No quote data: {str(data)[:200]}")

    row = data[0]
    price = row.get("price")
    prev_close = row.get("previousClose")

    if price is None or prev_close in (None, 0):
        raise RuntimeError(f"Missing price or previousClose: {row}")

    return ((float(price) - float(prev_close)) / float(prev_close)) * 100.0


def safe_get(symbol: str, label: str) -> Optional[float]:
    try:
        return get_quote_change_pct(symbol)
    except Exception as e:
        print(f"{label}: error ({e})")
        return None


def fmt_pct(x: Optional[float]) -> str:
    return f"{x:+.2f}%" if x is not None else "N/A"


def main() -> None:
    require_api_key()

    print("\n--- OIL SNIPER DEBUG ---")
    print(f"API key seen by script: {masked_key(API_KEY)}\n")

    gush = safe_get("GUSH", "GUSH")
    xle = safe_get("XLE", "XLE")
    oxy = safe_get("OXY", "OXY")
    xom = safe_get("XOM", "XOM")

    print("\n--- OIL SNIPER ---\n")
    print(f"GUSH: {fmt_pct(gush)}")
    print(f"XLE:  {fmt_pct(xle)}")
    print(f"OXY:  {fmt_pct(oxy)}")
    print(f"XOM:  {fmt_pct(xom)}\n")

    if None in [gush, xle]:
        print("⚠️ Incomplete data → skip trade")
    elif gush > 2 and xle > 0:
        print("🔥 STRONG MOMENTUM CONFIRMED")
        print("Top Play: GUSH continuation")
    elif gush < -2 and xle < 0:
        print("🔻 SHORT BIAS")
    else:
        print("😐 No clear edge")


if __name__ == "__main__":
    main()
