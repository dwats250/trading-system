# ============================================================
# MACRO SUITE — Ticker Configuration
# ============================================================
# All tickers verified against Yahoo Finance.
# Grouped by theme for use in macro pulse, sniper, and
# the pre-market report.
# ============================================================

TICKERS = {
    "macro":         ["DX-Y.NYB", "^TNX", "^VIX", "ES=F", "NQ=F", "RTY=F", "HYG", "BTC-USD"],
    "metals":        ["GLD", "SLV", "GDX", "SILJ", "GC=F", "SI=F"],
    "oil_core":      ["USO", "CL=F", "BZ=F", "XLE", "OXY", "CVX", "XOM"],
    "oil_beta":      ["GUSH"],
    "energy_supply": ["LNG", "HAL", "SLB"],
    "fx":            ["UUP", "FXE", "JPY=X"],   # JPY=X = USD/JPY
    "equities":      ["SPY", "QQQ", "IWM", "SMCI", "AMD", "NVDA"],
    "commodities":   ["HG=F"],                  # Copper — growth proxy
}

# Flat list of all macro-relevant symbols for the regime scanner
MACRO_SYMBOLS = {
    "DXY":  ["DX-Y.NYB"],       # Dollar index
    "10Y":  ["^TNX"],           # US 10-year yield
    "VIX":  ["^VIX"],           # Volatility
    "ES":   ["ES=F"],           # S&P 500 futures
    "NQ":   ["NQ=F"],           # Nasdaq futures
    "RTY":  ["RTY=F"],          # Russell 2000 futures
    "HYG":  ["HYG"],            # High-yield bonds — credit risk
    "BTC":  ["BTC-USD"],        # Bitcoin — liquidity proxy
    "UJ":   ["JPY=X"],          # USD/JPY
    "WTI":  ["CL=F"],           # WTI crude
    "BRT":  ["BZ=F"],           # Brent crude
    "XAU":  ["GC=F"],           # Gold
    "XAG":  ["SI=F"],           # Silver
    "HG":   ["HG=F"],           # Copper
    "SPY":  ["SPY"],            # S&P 500 ETF
    "QQQ":  ["QQQ"],            # Nasdaq-100 ETF
}

# Tickers scanned by the Entry Sniper
SNIPER_SYMBOLS = {
    "XLE":  "XLE",
    "XOM":  "XOM",
    "OXY":  "OXY",
    "GUSH": "GUSH",
    "SPY":  "SPY",
    "QQQ":  "QQQ",
    "GDX":  "GDX",
    "SLV":  "SLV",
    "TLT":  "TLT",
    "UUP":  "UUP",
}
