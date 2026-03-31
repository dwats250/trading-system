# ============================================================
# MACRO SUITE — Full Dashboard Build
# ============================================================
# Regenerates all four HTML dashboard pages in one pass.
# This is the canonical CI and GitHub Pages entrypoint.
#
# Local build (writes to reports/output/):
#   python -m reports.build_all
#
# Pages build (writes to _site/ for upload-pages-artifact):
#   python -m reports.build_all _site
#
# Pages generated:
#   index.html           — dashboard hub
#   macro_pulse.html     — macro instruments + regime
#   premarket.html       — morning brief + setups
#   options_sniper.html  — full pipeline + ranked trades
# ============================================================

from __future__ import annotations

import os
from pathlib import Path


def build_all(dest_dir: str = "reports/output") -> None:
    from config.tickers import MACRO_SYMBOLS
    from core.fetcher import fetch_all
    from outputs.html import save as _save_macro
    from outputs.index_html import save as _save_index
    from outputs.options_html import save as _save_options
    from outputs.premarket_html import save as _save_premarket

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    # Suppress Jekyll processing on GitHub Pages
    (dest / ".nojekyll").touch()

    print("Fetching macro data...", flush=True)
    data_map = fetch_all(MACRO_SYMBOLS)

    print("Building: Macro Pulse...", flush=True)
    _save_macro(path=str(dest / "macro_pulse.html"), data_map=data_map)

    print("Building: Pre-Market Report...", flush=True)
    _save_premarket(path=str(dest / "premarket.html"), data_map=data_map)

    print("Building: Options Sniper...", flush=True)
    _save_options(path=str(dest / "options_sniper.html"), data_map=data_map)

    print("Building: Dashboard Index...", flush=True)
    _save_index(path=str(dest / "index.html"), data_map=data_map)

    print(f"Done — all pages written to {dest}/", flush=True)


if __name__ == "__main__":
    import sys
    dest = sys.argv[1] if len(sys.argv) > 1 else "reports/output"
    build_all(dest_dir=dest)
