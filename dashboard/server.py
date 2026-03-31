# ============================================================
# MACRO SUITE — Dashboard Local HTTP Server
# ============================================================
# Starts a background SimpleHTTPRequestHandler for a given
# directory.  Returns the URL so the caller can open it.
# ============================================================

from __future__ import annotations

import http.server
import threading
from pathlib import Path


def serve_directory(directory: Path, port: int = 8765) -> str:
    """
    Serve *directory* over localhost on *port* in a daemon thread.

    Returns the URL to the macro_dashboard.html page.
    The server runs until the process exits (daemon=True).
    """
    directory = Path(directory).resolve()

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, fmt, *args):  # silence per-request logs
            pass

    httpd = http.server.HTTPServer(("127.0.0.1", port), _Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return f"http://127.0.0.1:{port}/macro_dashboard.html"
