#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

TIMEFRAME = "60m"
RANGE = "10d"


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"


@dataclass
class TickerPlan:
    symbol: str
    label: str
    role: str
    group: str
    ideal_pullback_low: Optional[float]
    ideal_pullback_high: Optional[float]
    breakout_level: Optional[float]
    stop_pullback: Optional[float]
    stop_breakout: Optional[float]
    target1: Optional[float]
    target2: Optional[float]
    notes: str


@dataclass
class QuoteInfo:
    symbol: str
    price: Optional[float]
    prev_close: Optional[float]
    change: Optional[float]
    pct_change: Optional[float]
    ema5: Optional[float]
    ema10: Optional[float]
    ema20: Optional[float]
    high: Optional[float]
    low: Optional[float]
    trend: str
    status: str
    location: str
    entry_bias: str
    error: Optional[str] = None


PLANS: Dict[str, TickerPlan] = {
    "CL=F": TickerPlan(
        symbol="CL=F",
        label="CL",
        role="Driver",
        group="DRIVER",
        ideal_pullback_low=94.8,
        ideal_pullback_high=95.2,
        breakout_level=96.5,
        stop_pullback=94.2,
        stop_breakout=95.8,
        target1=96.5,
        target2=98.0,
        notes="Everything starts here. No clean CL trend = no trade.",
    ),
    "XLE": TickerPlan(
        symbol="XLE",
        label="XLE",
        role="Structure Anchor",
        group="STRUCTURE",
        ideal_pullback_low=60.8,
        ideal_pullback_high=61.1,
        breakout_level=62.0,
        stop_pullback=60.2,
        stop_breakout=61.3,
        target1=62.0,
        target2=64.0,
        notes="Primary execution chart. If XLE is ugly, stand down.",
    ),
    "OILU": TickerPlan(
        symbol="OILU",
        label="OILU",
        role="Momentum",
        group="MOMENTUM",
        ideal_pullback_low=55.0,
        ideal_pullback_high=55.5,
        breakout_level=57.5,
        stop_pullback=54.0,
        stop_breakout=56.2,
        target1=58.5,
        target2=60.0,
        notes="High beta. Only trade when CL and XLE both confirm.",
    ),
    "UCO": TickerPlan(
        symbol="UCO",
        label="UCO",
        role="Momentum",
        group="MOMENTUM",
        ideal_pullback_low=40.0,
        ideal_pullback_high=40.5,
        breakout_level=42.0,
        stop_pullback=39.0,
        stop_breakout=40.8,
        target1=42.0,
        target2=44.0,
        notes="High beta crude ETF. Bad in chop.",
    ),
    "DIG": TickerPlan(
        symbol="DIG",
        label="DIG",
        role="Momentum",
        group="MOMENTUM",
        ideal_pullback_low=66.0,
        ideal_pullback_high=66.3,
        breakout_level=68.0,
        stop_pullback=64.5,
        stop_breakout=66.9,
        target1=69.0,
        target2=70.0,
        notes="Sector beta with leverage. Only for clean continuation.",
    ),
    "OXY": TickerPlan(
        symbol="OXY",
        label="OXY",
        role="Alpha",
        group="ALPHA",
        ideal_pullback_low=62.8,
        ideal_pullback_high=63.2,
        breakout_level=65.0,
        stop_pullback=62.0,
        stop_breakout=63.9,
        target1=65.0,
        target2=67.0,
        notes="High beta stock. Do not chase extended candles.",
    ),
    "XOM": TickerPlan(
        symbol="XOM",
        label="XOM",
        role="Alpha",
        group="ALPHA",
        ideal_pullback_low=164.0,
        ideal_pullback_high=164.5,
        breakout_level=167.0,
        stop_pullback=163.0,
        stop_breakout=165.5,
        target1=167.0,
        target2=170.0,
        notes="Cleaner, steadier, options-friendly energy name.",
    ),
    "PBR": TickerPlan(
        symbol="PBR",
        label="PBR",
        role="Alpha",
        group="ALPHA",
        ideal_pullback_low=20.0,
        ideal_pullback_high=20.1,
        breakout_level=20.6,
        stop_pullback=19.7,
        stop_breakout=20.15,
        target1=20.6,
        target2=21.2,
        notes="Slower mover. Better for cleaner holds than fast momentum.",
    ),
}

GROUP_ORDER = ["DRIVER", "STRUCTURE", "MOMENTUM", "ALPHA"]


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        val = float(value)
        if math.isnan(val):
            return None
        return val
    except Exception:
        return None


def fmt_price(x: Optional[float], digits: int = 2) -> str:
    return "--" if x is None else f"{x:.{digits}f}"


def fmt_pct(x: Optional[float]) -> str:
    if x is None:
        return "--"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:.2f}%"


def color_change(text: str, value: Optional[float]) -> str:
    if value is None:
        return text
    if value > 0:
        return f"{C.GREEN}{text}{C.RESET}"
    if value < 0:
        return f"{C.RED}{text}{C.RESET}"
    return f"{C.YELLOW}{text}{C.RESET}"


def emoji_status(status: str) -> str:
    return {
        "READY": "🟢",
        "WATCH": "🟡",
        "EXTENDED": "🟠",
        "AVOID": "🔴",
    }.get(status, "⚪")


def ema(values: List[float], span: int) -> Optional[float]:
    if not values:
        return None
    alpha = 2 / (span + 1)
    e = values[0]
    for v in values[1:]:
        e = alpha * v + (1 - alpha) * e
    return e


def classify_trend(
    price: Optional[float],
    ema5: Optional[float],
    ema10: Optional[float],
    ema20: Optional[float],
) -> str:
    if None in (price, ema5, ema10, ema20):
        return "Unknown"
    if price > ema5 > ema10 > ema20:
        return "Up"
    if price < ema5 < ema10 < ema20:
        return "Down"
    return "Mixed"


def classify_location(plan: TickerPlan, price: Optional[float]) -> str:
    if price is None:
        return "Unknown"

    if (
        plan.ideal_pullback_low is not None
        and plan.ideal_pullback_high is not None
        and plan.ideal_pullback_low <= price <= plan.ideal_pullback_high
    ):
        return "At ideal pullback"

    if (
        plan.ideal_pullback_low is not None
        and plan.ideal_pullback_high is not None
        and (plan.ideal_pullback_low - 0.35) <= price <= (plan.ideal_pullback_high + 0.35)
    ):
        return "Near pullback"

    if plan.breakout_level is not None:
        if price > plan.breakout_level:
            return "Above breakout"
        if abs(price - plan.breakout_level) <= max(0.15, plan.breakout_level * 0.002):
            return "Near breakout"

    return "Middle / extended"


def classify_status(plan: TickerPlan, price: Optional[float], trend: str) -> Tuple[str, str]:
    if price is None:
        return "AVOID", "No data"

    location = classify_location(plan, price)

    if trend == "Down":
        return "AVOID", location
    if location == "At ideal pullback" and trend in ("Up", "Mixed"):
        return "READY", location
    if location in ("Near pullback", "Near breakout") and trend in ("Up", "Mixed"):
        return "WATCH", location
    if location == "Above breakout" and trend == "Up":
        return "EXTENDED", location
    if trend == "Up":
        return "WATCH", location
    return "AVOID", location


def entry_bias_text(status: str) -> str:
    if status == "READY":
        return "Wait for A/B/C trigger"
    if status == "WATCH":
        return "Near zone; stay patient"
    if status == "EXTENDED":
        return "No chase; wait reset"
    return "No trade"


def fetch_chart(symbol: str) -> Dict:
    encoded = urllib.parse.quote(symbol, safe="")
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{encoded}?range={RANGE}&interval={TIMEFRAME}&includePrePost=true"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 EnergySniper/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_chart(symbol: str, payload: Dict) -> QuoteInfo:
    plan = PLANS[symbol]
    try:
        result = payload["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]

        closes = [safe_float(x) for x in quote.get("close", [])]
        highs = [safe_float(x) for x in quote.get("high", [])]
        lows = [safe_float(x) for x in quote.get("low", [])]

        closes = [x for x in closes if x is not None]
        highs = [x for x in highs if x is not None]
        lows = [x for x in lows if x is not None]

        if not closes:
            raise ValueError("No close data")

        price = closes[-1]
        prev_close = closes[-2] if len(closes) >= 2 else None
        change = price - prev_close if prev_close is not None else None
        pct_change = ((change / prev_close) * 100) if (change is not None and prev_close not in (None, 0)) else None

        ema5 = ema(closes[-30:], 5)
        ema10 = ema(closes[-40:], 10)
        ema20 = ema(closes[-60:], 20)
        high = highs[-1] if highs else None
        low = lows[-1] if lows else None

        trend = classify_trend(price, ema5, ema10, ema20)
        status, location = classify_status(plan, price, trend)
        entry_bias = entry_bias_text(status)

        return QuoteInfo(
            symbol=symbol,
            price=price,
            prev_close=prev_close,
            change=change,
            pct_change=pct_change,
            ema5=ema5,
            ema10=ema10,
            ema20=ema20,
            high=high,
            low=low,
            trend=trend,
            status=status,
            location=location,
            entry_bias=entry_bias,
            error=None,
        )
    except Exception as e:
        return QuoteInfo(
            symbol=symbol,
            price=None,
            prev_close=None,
            change=None,
            pct_change=None,
            ema5=None,
            ema10=None,
            ema20=None,
            high=None,
            low=None,
            trend="Unknown",
            status="AVOID",
            location="No data",
            entry_bias="No trade",
            error=str(e),
        )


def fetch_quote(symbol: str) -> QuoteInfo:
    try:
        payload = fetch_chart(symbol)
        return parse_chart(symbol, payload)
    except Exception as e:
        return QuoteInfo(
            symbol=symbol,
            price=None,
            prev_close=None,
            change=None,
            pct_change=None,
            ema5=None,
            ema10=None,
            ema20=None,
            high=None,
            low=None,
            trend="Unknown",
            status="AVOID",
            location="Fetch error",
            entry_bias="No trade",
            error=str(e),
        )


def banner() -> str:
    return "\n".join([
        f"{C.BOLD}{C.BRIGHT_CYAN}ENERGY SNIPER{C.RESET}",
        f"{C.DIM}{now_str()}  |  1H structure + live prep{C.RESET}",
        "",
        f"{C.BOLD}Process:{C.RESET} CL trend → XLE structure → A/B/C → choose instrument → set stop/target",
        f"{C.BOLD}Weekend:{C.RESET} Default = no hold. Only hold small winners in strong trend.",
        f"{C.BOLD}Hard rules:{C.RESET} No CL trend = no trade | No XLE structure = no trade | No chase",
    ])


def render_quote_line(q: QuoteInfo, plan: TickerPlan) -> str:
    pct_col = color_change(fmt_pct(q.pct_change), q.pct_change)
    return (
        f"{emoji_status(q.status)} "
        f"{C.BOLD}{plan.label:<5}{C.RESET} "
        f"{fmt_price(q.price):>7} "
        f"{pct_col:>10} "
        f"{C.DIM}{q.trend:<7}{C.RESET} "
        f"{C.YELLOW}{q.status:<8}{C.RESET} "
        f"{C.DIM}{q.location}{C.RESET}"
    )


def render_group_table(group_name: str, quotes: Dict[str, QuoteInfo]) -> str:
    lines = [f"{C.BOLD}{C.CYAN}{group_name}{C.RESET}"]
    for symbol, plan in PLANS.items():
        if plan.group == group_name:
            lines.append(render_quote_line(quotes[symbol], plan))
    return "\n".join(lines)


def render_best_candidates(quotes: Dict[str, QuoteInfo]) -> str:
    scored: List[Tuple[int, str]] = []
    for symbol, q in quotes.items():
        score = 0
        if q.status == "READY":
            score += 100
        elif q.status == "WATCH":
            score += 70
        elif q.status == "EXTENDED":
            score += 40

        if q.trend == "Up":
            score += 20
        elif q.trend == "Mixed":
            score += 5

        if q.location == "At ideal pullback":
            score += 25
        elif q.location == "Near pullback":
            score += 15
        elif q.location == "Near breakout":
            score += 10
        elif q.location == "Above breakout":
            score -= 10

        scored.append((score, symbol))

    scored.sort(reverse=True)
    lines = [f"{C.BOLD}{C.MAGENTA}BEST CANDIDATES{C.RESET}"]
    for _, symbol in scored[:3]:
        q = quotes[symbol]
        plan = PLANS[symbol]
        lines.append(f"{emoji_status(q.status)} {plan.label:<5} {q.status:<8} | {q.location:<18} | {q.entry_bias}")
    return "\n".join(lines)


def render_process_reminder() -> str:
    return "\n".join([
        f"{C.BOLD}{C.BRIGHT_YELLOW}QUICK PRIMER{C.RESET}",
        "1. Check CL first",
        "2. Check XLE second",
        "3. Only trade names aligned with both",
        "4. Entry = location + A/B/C behavior",
        "5. Set stop immediately",
        "6. No revenge trades",
        "7. If extended, wait",
    ])


def render_weekend_rules() -> str:
    return "\n".join([
        f"{C.BOLD}{C.BRIGHT_YELLOW}WEEKEND RULES{C.RESET}",
        "Default: do not hold energy over weekend",
        "Only hold if trend is strong, trade is green, size is small",
        "If you would hate a gap against you, close it",
    ])


def render_detailed_plans(quotes: Dict[str, QuoteInfo]) -> str:
    lines = [f"{C.BOLD}{C.BRIGHT_GREEN}LEVEL MAP / GAME PLAN{C.RESET}"]
    for group_name in GROUP_ORDER:
        lines.append(f"\n{C.BOLD}{group_name}{C.RESET}")
        for symbol, plan in PLANS.items():
            if plan.group != group_name:
                continue
            q = quotes[symbol]
            pullback = (
                f"{fmt_price(plan.ideal_pullback_low)}-{fmt_price(plan.ideal_pullback_high)}"
                if plan.ideal_pullback_low is not None and plan.ideal_pullback_high is not None
                else "--"
            )
            lines.append(f"{C.BOLD}{plan.label} — {plan.role}{C.RESET}")
            lines.append(
                f"Price: {fmt_price(q.price)} | Trend: {q.trend} | Status: {q.status} | Bias: {q.entry_bias}"
            )
            lines.append(
                f"Ideal pullback: {pullback} | Breakout: > {fmt_price(plan.breakout_level)}"
            )
            lines.append(
                f"Stop pb: {fmt_price(plan.stop_pullback)} | Stop bo: {fmt_price(plan.stop_breakout)} | "
                f"T1: {fmt_price(plan.target1)} | T2: {fmt_price(plan.target2)}"
            )
            lines.append(f"Note: {plan.notes}")
            lines.append("")
    return "\n".join(lines).rstrip()


def render_errors(quotes: Dict[str, QuoteInfo]) -> str:
    bad = [q for q in quotes.values() if q.error]
    if not bad:
        return ""
    lines = [f"{C.BOLD}{C.BRIGHT_RED}DATA WARNINGS{C.RESET}"]
    for q in bad:
        lines.append(f"{q.symbol}: {q.error}")
    return "\n".join(lines)


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def render_dashboard() -> str:
    quotes = {symbol: fetch_quote(symbol) for symbol in PLANS}
    parts = [
        banner(),
        "",
        render_group_table("DRIVER", quotes),
        "",
        render_group_table("STRUCTURE", quotes),
        "",
        render_group_table("MOMENTUM", quotes),
        "",
        render_group_table("ALPHA", quotes),
        "",
        render_best_candidates(quotes),
        "",
        render_process_reminder(),
        "",
        render_weekend_rules(),
        "",
        render_detailed_plans(quotes),
    ]
    err_block = render_errors(quotes)
    if err_block:
        parts.extend(["", err_block])
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Energy Sniper Dashboard")
    parser.add_argument("--loop", type=int, default=0, help="Refresh every N seconds")
    args = parser.parse_args()

    if args.loop > 0:
        while True:
            clear_screen()
            print(render_dashboard())
            time.sleep(args.loop)
    else:
        print(render_dashboard())


if __name__ == "__main__":
    main()
