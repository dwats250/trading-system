# ============================================================
# MACRO SUITE — Termux Notifier
# ============================================================
# Sends push notifications to Android via Termux API.
# Silently skips if termux-notification is not installed
# (e.g., when running on desktop).
# ============================================================

from __future__ import annotations

import shutil
import subprocess

from config.settings import SEND_TERMUX_NOTIFICATION


def _available() -> bool:
    return SEND_TERMUX_NOTIFICATION and shutil.which("termux-notification") is not None


def _build_body(full_text: str, max_lines: int = 12) -> str:
    """Strip the header line and return a compact notification body."""
    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    return "\n".join(lines[1:max_lines + 1])


def send(full_text: str, title: str = "Macro Pulse") -> None:
    """Send a Termux push notification. No-op on non-Termux environments."""
    if not _available():
        return

    body = _build_body(full_text)
    subprocess.run(
        [
            "termux-notification",
            "--id",       "macro-pulse",
            "--title",    title,
            "--content",  body,
            "--priority", "high",
        ],
        check=False,
    )
