#!/usr/bin/env python3
# ============================================================
# MACRO SUITE — Root Runner
# Run from project root:  python main.py
#
# Runs in order:
#   1. Macro Pulse  — regime, drivers, incidents
#   2. Entry Sniper — ranked trade setups
#   3. HTML output  — saves macro_pulse.html
# ============================================================

from config.tickers import MACRO_SYMBOLS
from core.fetcher import fetch_all
from macro.pulse import build_text
from outputs.html import save
from sniper.main import run as run_sniper

if __name__ == "__main__":
    macro_data = fetch_all(MACRO_SYMBOLS)
    print(build_text(macro_data))
    print()
    run_sniper(macro_data)
    save(data_map=macro_data)
