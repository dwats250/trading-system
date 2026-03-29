# ============================================================
# MACRO SUITE — Ticker Configuration
# ============================================================
# Each key is a human label. Values are Yahoo Finance symbols
# listed in priority order — the fetcher tries each in turn
# and uses the first one that returns data.
# ============================================================

MACRO_SYMBOLS = {
    "10Y":  ["^TNX"],           # US 10-Year yield
    "DXY":  ["DX-Y.NYB", "UUP"], # Dollar index (UUP ETF as fallback)
    "UJ":   ["JPY=X"],          # USD/JPY — yen carry proxy
    "VIX":  ["^VIX"],           # Volatility index
    "WTI":  ["CL=F"],           # WTI crude oil futures
    "BRT":  ["BZ=F"],           # Brent crude oil futures
    "SPY":  ["SPY"],            # S&P 500 ETF
    "QQQ":  ["QQQ"],            # Nasdaq-100 ETF
    "NDX":  ["^NDX"],           # Nasdaq-100 index
    "XAU":  ["GC=F"],           # Gold futures
    "XAG":  ["SI=F"],           # Silver futures
    "HG":   ["HG=F"],           # Copper futures — growth proxy
    "HYG":  ["HYG"],            # High-yield bonds — credit risk proxy
    "BTC":  ["BTC-USD"],        # Bitcoin — risk/liquidity proxy
}

# Tickers scanned by the Entry Sniper
# Grouped by theme — sniper scores all and surfaces the best setups
SNIPER_SYMBOLS = {
    # Energy
    "XLE":  "XLE",    # Energy sector ETF
    "XOM":  "XOM",    # ExxonMobil
    "OXY":  "OXY",    # Occidental Petroleum
    "GUSH": "GUSH",   # 2x leveraged oil & gas ETF
    # Equities
    "SPY":  "SPY",    # S&P 500
    "QQQ":  "QQQ",    # Nasdaq-100
    # Metals
    "GDX":  "GDX",    # Gold miners ETF
    "SLV":  "SLV",    # Silver ETF
    # Volatility / Macro plays
    "TLT":  "TLT",    # 20Y Treasury ETF — rates play
    "UUP":  "UUP",    # Dollar ETF
}

# Tickers used by the Oil module
OIL_SYMBOLS = {
    "GUSH": ["GUSH"],
    "XLE":  ["XLE"],
    "OXY":  ["OXY"],
    "XOM":  ["XOM"],
}
