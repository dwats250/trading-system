# ============================================================
# MACRO SUITE — Approved Trading Universe
# ============================================================
# All tickers verified against Yahoo Finance.
#
# Groups:
#   MACRO       = regime detection only (NOT traded)
#   OIL_CORE    = primary trading universe
#   OIL_BETA    = momentum plays only
#   OIL_SUPPLY  = advanced / secondary
#   METALS      = core thesis
#   DOLLAR      = FX context (monitor, not primary)
#   EQUITIES    = secondary / context trades
#   MACRO_ALT   = optional confirmation signals
#
# EXCLUDED: low liquidity, meme stocks, penny stocks,
#           illiquid options chains, "cheap option" traps
# ============================================================

# ── Macro drivers — read-only, NOT traded ───────────────────
MACRO = {
    "DXY":  ["DX-Y.NYB"],   # Dollar index
    "10Y":  ["^TNX"],       # US 10-year yield
    "VIX":  ["^VIX"],       # Volatility
    "ES":   ["ES=F"],       # S&P 500 futures
    "NQ":   ["NQ=F"],       # Nasdaq futures
    "RTY":  ["RTY=F"],      # Russell 2000 futures
    "UJ":   ["JPY=X"],      # USD/JPY
}

# Keep MACRO_SYMBOLS as alias for backward compatibility
MACRO_SYMBOLS = {
    **MACRO,
    # Additional macro context signals
    "HYG":  ["HYG"],        # High-yield credit — risk proxy
    "BTC":  ["BTC-USD"],    # Bitcoin — liquidity proxy
    "WTI":  ["CL=F"],       # WTI crude
    "BRT":  ["BZ=F"],       # Brent crude
    "XAU":  ["GC=F"],       # Gold
    "XAG":  ["SI=F"],       # Silver
    "HG":   ["HG=F"],       # Copper
    "SPY":  ["SPY"],
    "QQQ":  ["QQQ"],
}

# ── Oil / Energy ─────────────────────────────────────────────
OIL_CORE = ["USO", "XLE", "OXY", "XOM", "CVX"]
OIL_BETA = ["GUSH"]
OIL_SUPPLY = ["LNG", "SLB", "HAL"]

# ── Metals ───────────────────────────────────────────────────
METALS = ["SLV", "GDX", "GLD", "SILJ"]

# ── Dollar / FX — context, not primary trades ───────────────
DOLLAR = ["UUP", "FXE"]

# ── Equities — secondary / context ──────────────────────────
EQUITIES = ["SPY", "QQQ", "IWM", "SMCI", "AMD", "NVDA"]

# ── Macro confirmation — optional signals, not primary trades
MACRO_ALT = ["TLT", "COPX", "DBA"]

# ── Tradeable universe (used by scanner) ────────────────────
# Only includes tickers with liquid options chains.
# MACRO, DOLLAR, MACRO_ALT are excluded — context only.
SNIPER_SYMBOLS = {t: t for t in OIL_CORE + OIL_BETA + OIL_SUPPLY + METALS + EQUITIES}

# ── Legacy TICKERS dict (used by focus router) ───────────────
TICKERS = {
    "oil_core":      OIL_CORE,
    "oil_beta":      OIL_BETA,
    "oil_supply":    OIL_SUPPLY,
    "metals":        METALS,
    "dollar":        DOLLAR,
    "equities":      EQUITIES,
    "macro_alt":     MACRO_ALT,
}
