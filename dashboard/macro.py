#!/usr/bin/env python3
# ============================================================
# MACRO SUITE — Dashboard CLI Entry Point
# ============================================================
# Usage:
#   python -m dashboard.macro
#   python -m dashboard.macro --serve
#   python -m dashboard.macro --mobile
#   python -m dashboard.macro --serve --mobile --refresh 60
# ============================================================

from __future__ import annotations

import argparse
import os
import shutil
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from dashboard.render import render_macro_html
from dashboard.server import serve_directory
from macro.pulse import run

# ── Paths ────────────────────────────────────────────────────

_REPO_ROOT    = Path(__file__).resolve().parents[1]
_ARTIFACTS    = _REPO_ROOT / "artifacts"
_SITE         = _REPO_ROOT / "site"
_DASHBOARD    = "macro_dashboard.html"

_TERMUX_DOCS  = Path.home() / "storage" / "shared" / "Documents"


# ── Helpers ──────────────────────────────────────────────────

def _is_termux() -> bool:
    """Detect Termux environment without Android-specific commands."""
    return (
        "com.termux" in os.environ.get("PREFIX", "")
        or Path("/data/data/com.termux").exists()
    )


def _export_mobile(src: Path) -> None:
    """Copy dashboard HTML to Termux Documents folder if available."""
    if not _is_termux():
        print("  [mobile] Not running in Termux — skipping mobile export.")
        return
    if not _TERMUX_DOCS.exists():
        print(
            "  [mobile] ~/storage/shared/Documents not found.\n"
            "           Run: termux-setup-storage  then retry."
        )
        return
    dest = _TERMUX_DOCS / _DASHBOARD
    shutil.copy2(src, dest)
    print(f"  Mobile:    {dest}")


# ── Main flow ────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a styled macro pulse HTML dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start a local HTTP server and open dashboard in browser.",
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="(Termux) Copy dashboard to ~/storage/shared/Documents.",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=None,
        metavar="N",
        help="Add auto-refresh meta tag every N seconds.",
    )
    args = parser.parse_args()

    # 1. Fetch macro data and build text
    print("Fetching macro data...", end=" ", flush=True)
    text = run()
    print("done.")

    # 2. Render HTML (single render, written to both output locations)
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    html_content = render_macro_html(
        text,
        title="Macro Pulse",
        refresh_seconds=args.refresh,
        footer=f"Generated {generated_at} · dwats250/trading-system",
    )

    # 3a. Write to artifacts/
    _ARTIFACTS.mkdir(exist_ok=True)
    html_path = _ARTIFACTS / _DASHBOARD
    html_path.write_text(html_content, encoding="utf-8")
    print(f"  Generated: {html_path}")

    # 3b. Write to site/ (GitHub Pages deploy target)
    _SITE.mkdir(exist_ok=True)
    (_SITE / ".nojekyll").touch()          # prevent Jekyll processing on Pages
    site_path = _SITE / "index.html"
    site_path.write_text(html_content, encoding="utf-8")
    print(f"  Site:      {site_path}")

    # 4. Optional mobile export
    if args.mobile:
        _export_mobile(html_path)

    # 5. Optional local server + browser
    if args.serve:
        url = serve_directory(_ARTIFACTS)
        print(f"  Serving:   {url}")
        webbrowser.open(url)
        print("  Press Ctrl-C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  Server stopped.")


if __name__ == "__main__":
    main()
