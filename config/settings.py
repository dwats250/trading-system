# ============================================================
# MACRO SUITE — Global Settings
# ============================================================

# HTTP timeout for all market data requests (seconds)
FETCH_TIMEOUT = 8

# Send push notifications to phone via Termux
# Set to False when testing on desktop
SEND_TERMUX_NOTIFICATION = True

# ── Incident Detection Thresholds ──────────────────────────
# A move beyond these levels triggers an incident alert

INCIDENT_THRESHOLDS = {
    "rate_spike":       1.0,   # 10Y yield daily % change
    "dollar_breakout":  0.5,   # DXY daily % change
    "oil_shock":        2.0,   # WTI or Brent daily % change (abs)
    "vol_spike":        15.0,  # VIX daily % change
}

# ── Session Windows (UTC hours) ─────────────────────────────
SESSION_WINDOWS = {
    "Asia":       (0,  8),
    "London":     (7,  13),
    "NY":         (13, 20),
    "After Hours":(20, 24),
}
