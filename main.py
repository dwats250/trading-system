#!/usr/bin/env python3
# ============================================
# MACRO PULSE SYSTEM v1
# ============================================

from __future__ import annotations

import requests
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import quote


# ============================================
# CONFIG / SETTINGS
# ============================================

TIMEOUT = 8
SEND_TERMUX_NOTIFICATION = True


# ============================================
# TICKERS
# ============================================

SYMBOLS = {
    "10Y": ["^TNX"],
    "DXY": ["DX-Y.NYB", "UUP"],
    "UJ": ["JPY=X"],
    "VIX": ["^VIX"],
    "WTI": ["CL=F"],
    "BRT": ["BZ=F"],
    "SPY": ["SPY"],
    "QQQ": ["QQQ"],
    "XAU": ["GC=F"],
    "XAG": ["SI=F"],
    "HYG": ["HYG"],
    "BTC": ["BTC-USD"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# ============================================
# DATA FETCHING
# ============================================

def yahoo_chart_url(symbol: str) -> str:
    return f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='')}?range=5d&interval=1d"


def fetch_symbol(symbol: str) -> Optional[Dict[str, float]]:
    try:
        resp = requests.get(yahoo_chart_url(symbol), headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()

        result = payload["chart"]["result"][0]
        meta = result.get("meta", {})
        closes = result["indicators"]["quote"][0].get("close", [])
        valid_closes = [c for c in closes if c is not None]

        if len(valid_closes) < 2:
            return None

        prev_close = valid_closes[-2]
        last_close = valid_closes[-1]
        price = meta.get("regularMarketPrice", last_close)

        if price is None or prev_close in (None, 0):
            return None

        pct = ((price - prev_close) / prev_close) * 100.0
        return {"price": float(price), "pct": float(pct)}
    except Exception:
        return None


def get_data(label: str) -> Optional[Dict[str, float]]:
    for sym in SYMBOLS[label]:
        data = fetch_symbol(sym)
        if data is not None:
            return data
    return None


# ============================================
# FORMAT HELPERS
# ============================================

def pct_of(data_map: Dict[str, Optional[Dict[str, float]]], label: str) -> float:
    item = data_map.get(label)
    if not item:
        return 0.0
    return float(item.get("pct", 0.0))


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
    if price > 1000:
        return f"{price:.0f}"
    return f"{price:.2f}"


def part(label: str, data: Optional[Dict[str, float]]) -> str:
    label_fmt = f"{label:<3}"

    if not data:
        left = f"{label_fmt} n/a"
        return f"{left:<14} @  n/a"

    left = f"{label_fmt} {arrow(data['pct'])} {fmt_pct(data['pct'])}"
    return f"{left:<14} @  {fmt_price(data['price'])}"


# ============================================
# MACRO LOGIC
# ============================================

def regime(data_map: Dict[str, Optional[Dict[str, float]]]) -> str:
    score = 0
    score += 1 if pct_of(data_map, "SPY") > 0 else -1
    score += 1 if pct_of(data_map, "QQQ") > 0 else -1
    score += 1 if pct_of(data_map, "HYG") > 0 else -1
    score += 1 if pct_of(data_map, "BTC") > 0 else -1
    score -= 1 if pct_of(data_map, "VIX") > 0 else -1
    score -= 1 if pct_of(data_map, "DXY") > 0 else -1
    score -= 1 if pct_of(data_map, "10Y") > 0 else -1

    if score <= -2:
        return "RISK OFF"
    if score >= 2:
        return "RISK ON"
    return "MIXED"


def dollar_line(data_map: Dict[str, Optional[Dict[str, float]]]) -> str:
    return "Dollar firm" if pct_of(data_map, "DXY") > 0 else "Dollar soft"


def rates_oil_line(data_map: Dict[str, Optional[Dict[str, float]]]) -> str:
    rates = "10Y up" if pct_of(data_map, "10Y") > 0 else "10Y down"
    oil = "Oil bid" if (pct_of(data_map, "WTI") > 0 or pct_of(data_map, "BRT") > 0) else "Oil soft"
    return f"{rates} | {oil}"


def takeaway(data_map: Dict[str, Optional[Dict[str, float]]]) -> str:
    dxy = pct_of(data_map, "DXY")
    xau = pct_of(data_map, "XAU")
    spy = pct_of(data_map, "SPY")
    qqq = pct_of(data_map, "QQQ")
    vix = pct_of(data_map, "VIX")
    btc = pct_of(data_map, "BTC")
    hyg = pct_of(data_map, "HYG")
    wti = pct_of(data_map, "WTI")

    if dxy > 0 and xau < 0:
        return "Gold pressured by firm USD"
    if vix > 0 and spy < 0 and qqq < 0:
        return "Vol up with equities weak"
    if btc > 0 and hyg > 0 and spy >= 0:
        return "Liquidity tone improving"
    if wti > 0 and spy < 0:
        return "Oil shock weighing on risk"
    return "Cross-asset tone mixed"


# ============================================
# OUTPUT BUILDER
# ============================================

def build_output() -> str:
    data_map: Dict[str, Optional[Dict[str, float]]] = {}
    for label in SYMBOLS:
        data_map[label] = get_data(label)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append("MACRO PULSE")
    lines.append(now)
    lines.append("")
    lines.append(regime(data_map))
    lines.append(dollar_line(data_map))
    lines.append(rates_oil_line(data_map))
    lines.append("")

    for label in SYMBOLS:
        lines.append(part(label, data_map[label]))

    lines.append("")
    lines.append(takeaway(data_map))
    return "\n".join(lines)


# ============================================
# NOTIFICATIONS
# ============================================

def build_notification_text(full_text: str) -> str:
    lines = full_text.splitlines()
    body_lines = []
    for line in lines[1:]:
        if line.strip():
            body_lines.append(line.strip())
    return "\n".join(body_lines[:12])


def send_notification(full_text: str) -> None:
    if not SEND_TERMUX_NOTIFICATION:
        return
    if shutil.which("termux-notification") is None:
        return

    body = build_notification_text(full_text)

    subprocess.run(
        [
            "termux-notification",
            "--id", "macro-pulse",
            "--title", "Macro Pulse",
            "--content", body,
            "--priority", "high",
        ],
        check=False,
    )


# ============================================
# MAIN ENTRY
# ============================================

def main() -> None:
    output = build_output()
    print(output)
    send_notification(output)


if __name__ == "__main__":
    main()