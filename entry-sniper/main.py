import os
import time
import math
import requests
import select
import sys
import tty
import termios
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.rule import Rule

console = Console()
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

API_KEY = os.getenv("FMP_API_KEY")

APP_NAME = "Macro Pulse Entry Sniper"
APP_VERSION = "Beta 2.3"

TICKERS = [
    "SPY", "QQQ",
    "TSLA", "NVDA", "META", "GOOGL",
    "COIN", "MSTR", "PLTR", "AMD", "SMCI", "MU",
    "OXY", "GDX", "SLV", "UNG", "HYMC"
]

SECTORS = {
    "Tech": ["NVDA", "AMD", "SMCI", "MU"],
    "Big Tech": ["META", "GOOGL"],
    "High Beta": ["TSLA", "COIN", "MSTR", "PLTR"],
    "Energy": ["OXY"],
    "Metals": ["GDX", "SLV"],
    "Gas": ["UNG"],
    "Speculative": ["HYMC"]
}

OPTIONABLE = {
    "SPY", "QQQ", "TSLA", "NVDA", "META", "GOOGL",
    "COIN", "MSTR", "PLTR", "AMD", "SMCI", "MU",
    "OXY", "GDX", "SLV", "UNG"
}

QUOTE_URL = "https://financialmodelingprep.com/stable/quote"


def compute_change_pct(price, previous_close, open_price, api_change_pct):
    if previous_close and previous_close > 0:
        return ((price - previous_close) / previous_close) * 100.0
    if open_price and open_price > 0:
        return ((price - open_price) / open_price) * 100.0
    return api_change_pct or 0.0


def fetch_one(symbol):
    params = {"symbol": symbol, "apikey": API_KEY}
    r = session.get(QUOTE_URL, params=params, timeout=10)

    if r.status_code != 200:
        return None

    data = r.json()
    if not data or not isinstance(data, list):
        return None

    item = data[0]

    try:
        price = float(item.get("price", 0) or 0)
        api_change_pct = float(item.get("changesPercentage", 0) or 0)
        open_price = float(item.get("open", 0) or 0)
        prev_close = float(item.get("previousClose", 0) or 0)
        high = float(item.get("dayHigh", 0) or 0)
        low = float(item.get("dayLow", 0) or 0)
    except Exception:
        return None

    if price <= 0:
        return None

    change = compute_change_pct(price, prev_close, open_price, api_change_pct)
    range_pct = ((high - low) / open_price * 100) if open_price else 0
    dist_high = ((high - price) / high * 100) if high else 999
    dist_low = ((price - low) / low * 100) if low else 999

    return {
        "symbol": symbol,
        "price": price,
        "change": change,
        "range_pct": range_pct,
        "dist_high": dist_high,
        "dist_low": dist_low,
        "prev_close": prev_close,
        "open": open_price,
        "high": high,
        "low": low,
    }


def fetch_all():
    out = []
    for t in TICKERS:
        d = fetch_one(t)
        if d:
            out.append(d)
        time.sleep(0.12)
    return out


def color_pct(x):
    if x > 0:
        return f"[green]+{x:.2f}%[/green]"
    if x < 0:
        return f"[red]{x:.2f}%[/red]"
    return f"{x:.2f}%"


def build_header():
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    body = (
        f"[bold]{APP_NAME}[/bold]\n"
        f"Version: [cyan]{APP_VERSION}[/cyan]\n"
        f"Snapshot: [white]{ts}[/white]"
    )
    return Panel(body, title="Build", border_style="cyan")


def build_bias(data):
    avg = sum(x["change"] for x in data) / len(data)
    if avg > 0.5:
        txt = "[green]Bullish[/green]"
    elif avg < -0.5:
        txt = "[red]Bearish[/red]"
    else:
        txt = "[yellow]Mixed[/yellow]"
    return Panel(f"Market Bias:\n{txt}", title="Trade Signal")


def build_snapshot(data):
    half = math.ceil(len(data) / 2)
    left = data[:half]
    right = data[half:]

    def make_table(rows, title):
        t = Table(title=title)
        t.add_column("Ticker")
        t.add_column("Price", justify="right")
        t.add_column("%", justify="right")

        for x in rows:
            t.add_row(
                x["symbol"],
                f"{x['price']:.2f}",
                color_pct(x["change"])
            )
        return t

    return Columns(
        [make_table(left, "Market Snapshot"), make_table(right, "Market Snapshot")],
        expand=True,
        equal=True
    )


def build_leaders(data):
    ranked = sorted(data, key=lambda x: x["change"], reverse=True)

    top = Table(title="Top Movers")
    top.add_column("Ticker")
    top.add_column("%", justify="right")

    for x in ranked[:3]:
        top.add_row(x["symbol"], color_pct(x["change"]))

    lag = Table(title="Laggers")
    lag.add_column("Ticker")
    lag.add_column("%", justify="right")

    for x in ranked[-3:]:
        lag.add_row(x["symbol"], color_pct(x["change"]))

    return Columns([top, lag], expand=True, equal=True)


def build_sector(data):
    table = Table(title="Sector Strength")
    table.add_column("Sector")
    table.add_column("Avg %", justify="right")

    for s, names in SECTORS.items():
        vals = [x["change"] for x in data if x["symbol"] in names]
        if vals:
            avg = sum(vals) / len(vals)
            table.add_row(s, color_pct(avg))

    return table


def score(x):
    move_score = abs(x["change"]) * 2
    range_score = x["range_pct"] * 0.6

    if x["change"] > 0:
        location_score = max(0, 2.5 - x["dist_high"])
    else:
        location_score = max(0, 2.5 - x["dist_low"])

    return move_score + range_score + location_score


def reason(x):
    bits = []

    if abs(x["change"]) >= 4:
        bits.append("big move")
    elif abs(x["change"]) >= 2:
        bits.append("solid momentum")

    if x["range_pct"] >= 2:
        bits.append("good range")

    if x["change"] > 0 and x["dist_high"] < 1.25:
        bits.append("near HOD")
    elif x["change"] < 0 and x["dist_low"] < 1.25:
        bits.append("near LOD")

    if not bits:
        bits.append("watch / building")

    return ", ".join(bits)


def rank_candidates(data):
    return sorted(data, key=score, reverse=True)


def build_candidates(data):
    ranked = rank_candidates(data)

    t = Table(title="Trade Candidates")
    t.add_column("Key")
    t.add_column("Ticker")
    t.add_column("Bias")
    t.add_column("Score")
    t.add_column("Reason")

    for idx, x in enumerate(ranked[:3], start=1):
        bias = "LONG" if x["change"] > 0 else "SHORT"
        color = "green" if bias == "LONG" else "red"

        t.add_row(
            str(idx),
            x["symbol"],
            f"[{color}]{bias}[/{color}]",
            f"{score(x):.1f}",
            reason(x)
        )

    return t


def build_optionable(data):
    ranked = [x for x in data if x["symbol"] in OPTIONABLE]
    ranked = sorted(ranked, key=score, reverse=True)

    t = Table(title="Optionable Momentum")
    t.add_column("Ticker")
    t.add_column("Bias")
    t.add_column("Move")
    t.add_column("Setup")

    for x in ranked[:5]:
        bias = "CALL" if x["change"] > 0 else "PUT"
        color = "green" if bias == "CALL" else "red"
        tier = "A-tier" if score(x) > 10 else "B-tier"

        t.add_row(
            x["symbol"],
            f"[{color}]{bias}[/{color}]",
            color_pct(x["change"]),
            tier
        )

    return t


def build_focus_from_item(x):
    bias = "CALL" if x["change"] > 0 else "PUT"

    if x["change"] > 0:
        loc = f"Distance from day high: {x['dist_high']:.2f}%"
        hunt = "→ Hunt continuation on strength"
    else:
        loc = f"Distance from day low: {x['dist_low']:.2f}%"
        hunt = "→ Hunt continuation on weakness"

    return Panel(
        f"{x['symbol']} | {bias}\n"
        f"Move: {color_pct(x['change'])} | Price: {x['price']:.2f}\n"
        f"Range: {x['range_pct']:.2f}%\n"
        f"{loc}\n"
        f"Reason: {reason(x)}\n"
        f"{hunt}",
        title="Top Trade Focus"
    )


def build_focus(data):
    ranked = [x for x in data if x["symbol"] in OPTIONABLE]
    ranked = sorted(ranked, key=score, reverse=True)

    if not ranked:
        return Panel("No trade", title="Top Trade Focus")

    return build_focus_from_item(ranked[0])


def build_warning(msg):
    return Panel(f"[red]{msg}[/red]", title="Warning")


def build_screen(data):
    return Group(
        build_header(),
        build_bias(data),
        build_snapshot(data),
        build_leaders(data),
        build_sector(data),
        build_candidates(data),
        build_optionable(data),
        build_focus(data)
    )


def print_cycle_header():
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    console.print(Rule(f"[bold cyan]{APP_NAME} | {APP_VERSION} | {ts}[/bold cyan]"))


def candidate_detail_panel(item, key_number):
    bias = "CALL" if item["change"] > 0 else "PUT"
    tier = "A-tier" if score(item) > 10 else "B-tier"

    if item["change"] > 0:
        location = f"Distance from HOD: {item['dist_high']:.2f}%"
        hunt_hint = "Watch for continuation, reclaim, or break."
    else:
        location = f"Distance from LOD: {item['dist_low']:.2f}%"
        hunt_hint = "Watch for continuation, rejection, or breakdown."

    body = (
        f"[bold]Candidate {key_number}: {item['symbol']}[/bold]\n"
        f"Bias: {bias}\n"
        f"Setup: {tier}\n"
        f"Price: {item['price']:.2f}\n"
        f"Move: {color_pct(item['change'])}\n"
        f"Range: {item['range_pct']:.2f}%\n"
        f"{location}\n"
        f"Score: {score(item):.1f}\n"
        f"Reason: {reason(item)}\n"
        f"Focus: Open chain for [bold]{item['symbol']}[/bold] and inspect near-the-money {bias.lower()}.\n"
        f"Hunt Hint: {hunt_hint}"
    )

    return Panel(body, title="Detailed Report", border_style="magenta")


def read_key_nonblocking():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if not dr:
        return None

    ch = sys.stdin.read(1)

    if ch == "\x1b":
        while True:
            dr2, _, _ = select.select([sys.stdin], [], [], 0)
            if not dr2:
                break
            sys.stdin.read(1)
        return None

    return ch.lower()


def run_hunt(item):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setcbreak(fd)

        console.print(Rule(f"[bold yellow]Hunt Mode: {item['symbol']}[/bold yellow]"))
        console.print(Panel(
            f"Watching [bold]{item['symbol']}[/bold] for 5 minutes.\n"
            f"1 check per minute.\n"
            f"Press [bold]S[/bold] to stop hunting early.",
            title="Hunt Started",
            border_style="yellow"
        ))

        history = []

        for minute in range(1, 6):
            fresh = fetch_one(item["symbol"])
            ts = time.strftime("%H:%M:%S")

            if not fresh:
                console.print(Panel(f"[red]Minute {minute}: No data[/red]", title=f"Hunt Check {minute}"))
            else:
                history.append(fresh)

                direction = "CALL" if fresh["change"] > 0 else "PUT"
                direction_color = "green" if direction == "CALL" else "red"

                if fresh["change"] > 0:
                    location = f"Dist from HOD: {fresh['dist_high']:.2f}%"
                else:
                    location = f"Dist from LOD: {fresh['dist_low']:.2f}%"

                body = (
                    f"Time: {ts}\n"
                    f"Bias: [{direction_color}]{direction}[/{direction_color}]\n"
                    f"Price: {fresh['price']:.2f}\n"
                    f"Move: {color_pct(fresh['change'])}\n"
                    f"Range: {fresh['range_pct']:.2f}%\n"
                    f"{location}\n"
                    f"Reason: {reason(fresh)}\n"
                    f"Score: {score(fresh):.1f}"
                )

                console.print(Panel(body, title=f"Hunt Check {minute}/5", border_style="yellow"))

            if minute < 5:
                console.print(Panel("Hunt waiting... Press S to stop early.", border_style="dim"))
                start_wait = time.time()
                while time.time() - start_wait < 60:
                    key = read_key_nonblocking()
                    if key == "s":
                        console.print(Panel("[yellow]Hunt stopped by user.[/yellow]", title="Hunt"))
                        minute = 99
                        break
                    time.sleep(0.1)
                if minute == 99:
                    break

        if history:
            start = history[0]
            end = history[-1]
            delta = end["price"] - start["price"]
            delta_pct = ((end["price"] - start["price"]) / start["price"] * 100) if start["price"] else 0

            summary = (
                f"Start Price: {start['price']:.2f}\n"
                f"End Price: {end['price']:.2f}\n"
                f"Net Move: {delta:+.2f} ({delta_pct:+.2f}%)\n"
                f"Start Score: {score(start):.1f}\n"
                f"End Score: {score(end):.1f}\n"
                f"Start Reason: {reason(start)}\n"
                f"End Reason: {reason(end)}"
            )
            console.print(Panel(summary, title="Hunt Summary", border_style="green"))

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main():
    try:
        while True:
            print_cycle_header()

            data = fetch_all()

            if not data:
                console.print(build_warning("No data"))
                console.print(Panel("Press R to retry | Press Q to exit", border_style="dim"))
                cmd = input("> ").strip().lower()
                if cmd == "q":
                    break
                continue

            console.print(build_screen(data))
            console.print(Panel(
                "Press R to refresh | Enter 1/2/3 for detailed report + hunt | Press Q to exit",
                border_style="dim"
            ))

            cmd = input("> ").strip().lower()

            if cmd == "q":
                break

            if cmd == "r" or cmd == "":
                continue

            if cmd in {"1", "2", "3"}:
                ranked = rank_candidates(data)
                idx = int(cmd) - 1

                if idx < len(ranked):
                    selected = ranked[idx]
                    console.print(candidate_detail_panel(selected, cmd))
                    console.print(Panel(
                        f"Starting 5-minute hunt for [bold]{selected['symbol']}[/bold]...",
                        title="Hunt",
                        border_style="yellow"
                    ))
                    run_hunt(selected)
                    console.print(Panel(
                        "Hunt complete. Press R to refresh, 1/2/3 for another candidate, or Q to exit.",
                        border_style="dim"
                    ))
                    post_cmd = input("> ").strip().lower()
                    if post_cmd == "q":
                        break
                    else:
                        continue

            console.print(Panel("Unknown command. Press R, 1, 2, 3, or Q.", border_style="red"))

    except KeyboardInterrupt:
        console.print("\n[bold]Exited.[/bold]")


if __name__ == "__main__":
    main()
