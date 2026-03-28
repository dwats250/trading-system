#!/usr/bin/env python3
import yfinance as yf
from datetime import datetime

TICKERS = ["GUSH", "XLE", "OXY", "XOM"]


def banner():
    print("\n" + "=" * 60)
    print(f"MACRO PULSE ENTRY SNIPER | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def fetch(symbol):
    try:
        data = yf.Ticker(symbol)
        hist = data.history(period="2d")

        if len(hist) < 2:
            return None

        prev_close = hist["Close"].iloc[-2]
        last = hist["Close"].iloc[-1]

        change = last - prev_close
        pct = (change / prev_close) * 100

        return {
            "symbol": symbol,
            "price": last,
            "change": change,
            "pct": pct,
        }

    except Exception as e:
        print(f"{symbol} error: {e}")
        return None


def main():
    banner()

    results = []

    for t in TICKERS:
        r = fetch(t)
        if r:
            results.append(r)

    if not results:
        print("\n❌ No data (all fetches failed)")
        return

    print("\n--- OIL SNIPER ---\n")

    for r in results:
        print(
            f"{r['symbol']}: "
            f"{r['price']:.2f} | "
            f"{r['change']:+.2f} | "
            f"{r['pct']:+.2f}%"
        )

    print("\n✅ Data stable (yfinance)\n")


if __name__ == "__main__":
    main()
