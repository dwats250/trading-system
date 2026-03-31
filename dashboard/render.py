# ============================================================
# MACRO SUITE — Dashboard HTML Renderer
# ============================================================
# Converts formatted macro text into a styled HTML page.
# No external CSS/JS dependencies — self-contained output.
# ============================================================

from __future__ import annotations

import html
import re

_RISK_ON  = re.compile(r"\bRISK ON\b")
_RISK_OFF = re.compile(r"\bRISK OFF\b")
_MIXED    = re.compile(r"\bMIXED\b")
_PRIMARY  = re.compile(r"^(Primary|Secondary):")
_WARNING  = re.compile(r"^⚠")
_DIVIDER  = re.compile(r"^─{5,}")


def _highlight_line(line: str) -> str:
    """Apply inline span highlights to a single text line."""
    escaped = html.escape(line)

    if _WARNING.match(line):
        return f'<span class="warn">{escaped}</span>'
    if _DIVIDER.match(line):
        return f'<span class="div">{escaped}</span>'
    if _PRIMARY.match(line):
        return f'<span class="driver">{escaped}</span>'

    # Inline regime highlights (may appear mid-line)
    escaped = _RISK_ON.sub('<span class="risk-on">RISK ON</span>', escaped)
    escaped = _RISK_OFF.sub('<span class="risk-off">RISK OFF</span>', escaped)
    escaped = _MIXED.sub('<span class="mixed">MIXED</span>', escaped)
    return escaped


def render_macro_html(
    text: str,
    title: str = "Macro Pulse",
    refresh_seconds: int | None = None,
) -> str:
    """
    Convert macro pulse text to a dark-themed, mobile-friendly HTML dashboard.

    Args:
        text:            The formatted macro pulse string.
        title:           Page/card title shown in the header.
        refresh_seconds: If set, adds a <meta http-equiv="refresh"> tag.

    Returns:
        Complete HTML document string.
    """
    refresh_meta = (
        f'  <meta http-equiv="refresh" content="{refresh_seconds}">\n'
        if refresh_seconds
        else ""
    )

    body = "\n".join(_highlight_line(ln) for ln in text.split("\n"))
    safe_title = html.escape(title)

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
{refresh_meta}  <title>{safe_title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      padding: 16px;
      background: #0d1117;
      color: #c9d1d9;
      font-family: 'JetBrains Mono', 'Fira Mono', 'Menlo', 'Courier New', monospace;
      font-size: 15px;
      line-height: 1.65;
    }}

    .card {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 22px 28px;
      max-width: 820px;
      margin: 0 auto;
      box-shadow: 0 4px 24px rgba(0,0,0,.5);
    }}

    .card-title {{
      font-size: 10px;
      letter-spacing: .12em;
      text-transform: uppercase;
      color: #6e7681;
      margin-bottom: 14px;
    }}

    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
    }}

    /* regime */
    .risk-on  {{ color: #3fb950; font-weight: bold; }}
    .risk-off {{ color: #f85149; font-weight: bold; }}
    .mixed    {{ color: #d29922; font-weight: bold; }}

    /* structural */
    .driver {{ color: #79c0ff; }}
    .warn   {{ color: #ffa657; }}
    .div    {{ color: #21262d; }}

    @media (max-width: 600px) {{
      body  {{ font-size: 13px; padding: 10px; }}
      .card {{ padding: 14px 16px; border-radius: 8px; }}
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="card-title">{safe_title}</div>
    <pre>{body}</pre>
  </div>
</body>
</html>
"""
