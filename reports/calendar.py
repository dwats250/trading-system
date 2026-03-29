# ============================================================
# MACRO SUITE — Economic Calendar
# ============================================================
# Fetches today's economic events from the Nasdaq free API.
# No API key required.
# ============================================================

from __future__ import annotations

from datetime import date
from typing import Optional

import requests

_URL = "https://api.nasdaq.com/api/calendar/economicevents"
_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Events with these keywords are flagged as high impact
_HIGH_IMPACT_KEYWORDS = [
    "CPI", "PCE", "NFP", "Nonfarm", "FOMC", "Fed ", "Interest Rate",
    "GDP", "Unemployment", "Inflation", "Retail Sales", "PMI",
    "Consumer Price", "Producer Price", "Jobs",
]

# Only show US and Euro Zone events (filter noise)
_COUNTRIES = {"United States", "Euro Zone", "United Kingdom"}


def _impact(event_name: str) -> str:
    name_upper = event_name.upper()
    for kw in _HIGH_IMPACT_KEYWORDS:
        if kw.upper() in name_upper:
            return "HIGH"
    return "MED"


def get_events(target_date: Optional[date] = None) -> list[dict]:
    """
    Return today's economic events as a list of dicts:
    {time, country, event, impact, consensus, previous}
    """
    if target_date is None:
        target_date = date.today()

    try:
        r = requests.get(
            _URL,
            params={"date": target_date.isoformat(), "daterange": "day"},
            headers=_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json().get("data", {}).get("rows", [])
    except Exception:
        return []

    events = []
    for row in rows:
        country = row.get("country", "").strip()
        if country not in _COUNTRIES:
            continue

        name = row.get("eventName", "").strip()
        time = row.get("gmt", "").strip()
        consensus = row.get("consensus", "").strip().replace("&nbsp;", "").strip()
        previous  = row.get("previous",  "").strip().replace("&nbsp;", "").strip()

        events.append({
            "time":      time,
            "country":   country,
            "event":     name,
            "impact":    _impact(name),
            "consensus": consensus or "—",
            "previous":  previous  or "—",
        })

    # Sort by impact (HIGH first) then time
    events.sort(key=lambda e: (0 if e["impact"] == "HIGH" else 1, e["time"]))
    return events


def format_events(events: list[dict]) -> list[str]:
    """Format events as terminal-ready lines."""
    if not events:
        return ["No major events today"]

    lines = []
    for e in events:
        flag = "!" if e["impact"] == "HIGH" else " "
        consensus = f"  Est: {e['consensus']}" if e["consensus"] != "—" else ""
        lines.append(f"{flag} {e['time']} UTC  {e['event']}{consensus}")
    return lines
