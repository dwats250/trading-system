# ============================================================
# MACRO SUITE — Session Detection
# ============================================================
# Returns the current trading session based on UTC time.
# Windows overlap (e.g., London/NY overlap 13:00–16:00 UTC)
# — we return the primary active session.
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone


def current_session() -> str:
    """Return the current trading session name based on UTC hour."""
    utc_hour = datetime.now(timezone.utc).hour

    if 13 <= utc_hour < 20:
        return "NY"
    if 7 <= utc_hour < 13:
        return "London"
    if 0 <= utc_hour < 7:
        return "Asia"
    return "After Hours"
