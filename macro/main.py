import json
import sys
import urllib.request
from urllib.parse import quote

macro_tickers = {
    "ES": "ES=F",
    "NDX": "^NDX",
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
    "USDJPY": "JPY=X",
    "US10Y": "^TNX",
    "XAU": "GC=F",
    "XAG": "SI=F",
    "USO": "CL=F",
    "HG": "HG=F",
}

watchlist_tickers = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "BZ": "BZ=F",
    "CL": "CL=F",
    "GDX": "GDX",
    "SLV": "SLV",
    "HYMC": "HYMC",
}


def fetch_quote(symbol: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}?interval=5m&range=1d"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    chart = data.get("chart", {})
    result_list = chart.get("result")
    if not result_list:
        return None

    result = result_list[0]
    indicators = result.get("indicators", {})
    quote_list = indicators.get("quote")
    if not quote_list:
        return None

    quote_data = quote_list[0]

    closes = [x for x in quote_data.get("close", []) if x is not None]
    opens = [x for x in quote_data.get("open", []) if x is not None]

    if not closes or not opens:
        return None

    current = float(closes[-1])
    session_open = float(opens[0])
    pct = ((current - session_open) / session_open) * 100.0

    if pct > 0:
        direction = "↑"
    elif pct < 0:
        direction = "↓"
    else:
        direction = "→"

    return {
        "price": current,
        "pct": pct,
        "direction": direction,
    }


def get_data(ticker_map: dict):
    results = {}
    for name, symbol in ticker_map.items():
        try:
            quote_data = fetch_quote(symbol)
            if quote_data:
                results[name] = quote_data
        except Exception:
            pass
    return results


def macro_banner(data: dict):
    ndx = data.get("NDX", {}).get("pct", 0)
    es = data.get("ES", {}).get("pct", 0)
    vix = data.get("VIX", {}).get("pct", 0)
    dxy = data.get("DXY", {}).get("pct", 0)
    us10y = data.get("US10Y", {}).get("pct", 0)
    uso = data.get("USO", {}).get("pct", 0)

    if (ndx > 0 or es > 0) and vix < 0:
        regime = "RISK ON"
    elif (ndx < 0 or es < 0) and vix > 0:
        regime = "RISK OFF"
    else:
        regime = "MIXED"

    def arrow(x):
        return "↑" if x > 0 else "↓" if x < 0 else "→"

    driver_line = f"DXY {arrow(dxy)}  Rates {arrow(us10y)}  Oil {arrow(uso)}"
    return regime, driver_line


def macro_read(data: dict):
    reads = []

    xau = data.get("XAU", {}).get("pct", 0)
    xag = data.get("XAG", {}).get("pct", 0)
    dxy = data.get("DXY", {}).get("pct", 0)
    us10y = data.get("US10Y", {}).get("pct", 0)
    hg = data.get("HG", {}).get("pct", 0)
    usdjpy = data.get("USDJPY", {}).get("pct", 0)

    if xau > 0 and xag > 0 and dxy < 0:
        reads.append("Metals supported by weaker dollar")
    elif xau > 0 and xag > 0 and us10y > 0:
        reads.append("Metals strong despite rising yields")
    elif xau < 0 and dxy > 0:
        reads.append("Gold pressured by stronger dollar")

    if hg > 0:
        reads.append("Copper: growth/cyclical bid")
    elif hg < 0:
        reads.append("Copper: softer growth signal")

    if usdjpy < 0:
        reads.append("Yen stronger / carry pressure")
    elif usdjpy > 0:
        reads.append("Yen weaker / carry supportive")

    return reads


def pair_line(data: dict, keys: list[str]) -> str:
    items = []
    for key in keys:
        if key in data:
            pct = data[key]["pct"]
            items.append(f"{key} {pct:+.1f}%")
    return "  ".join(items)


def build_phone_output(macro_data: dict, watchlist_data: dict) -> str:
    regime, drivers_line = macro_banner(macro_data)

    lines = [regime, drivers_line, ""]

    macro_pairs = [
        ["ES", "NDX"],
        ["VIX", "DXY"],
        ["USDJPY", "US10Y"],
        ["XAU", "XAG"],
        ["USO", "HG"],
    ]

    for pair in macro_pairs:
        line = pair_line(macro_data, pair)
        if line:
            lines.append(line)

    reads = macro_read(macro_data)
    if reads:
        lines.append("")
        for read in reads[:2]:
            lines.append(read)

    watch_pairs = [
        ["SPY", "QQQ"],
        ["CL", "BZ"],
        ["GDX", "SLV"],
        ["HYMC"],
    ]

    lines.append("")
    lines.append("Watch")

    for pair in watch_pairs:
        line = pair_line(watchlist_data, pair)
        if line:
            lines.append(line)

    return "\n".join(lines)


if __name__ == "__main__":
    macro_data = get_data(macro_tickers)
    watchlist_data = get_data(watchlist_tickers)
    print(build_phone_output(macro_data, watchlist_data))
