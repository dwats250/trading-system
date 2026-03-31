#!/data/data/com.termux/files/usr/bin/bash
cd ~/trading-system || exit 1

source .venv/bin/activate
export PYTHONPATH="$PWD"

python3 - <<'PY'
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import html

from macro.pulse import run

buf = StringIO()
with redirect_stdout(buf):
    run()

clean = buf.getvalue().strip()
if not clean:
    clean = "Macro pulse returned no stdout."

out = Path.home() / "storage" / "shared" / "Documents" / "macro_pulse.html"
out.parent.mkdir(parents=True, exist_ok=True)

page = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Macro Pulse</title>
<style>
:root {{
  --bg: #2b2f3a;
  --panel: #313644;
  --text: #d8dee9;
  --border: #4c566a;
  --accent: #88c0d0;
}}
body {{
  margin: 0;
  padding: 20px;
  background: var(--bg);
  color: var(--text);
  font-family: monospace;
  font-size: 18px;
  line-height: 1.6;
}}
.card {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px;
}}
.header {{
  color: var(--accent);
  font-weight: bold;
  font-size: 1.15rem;
  margin-bottom: 12px;
}}
pre {{
  white-space: pre-wrap;
  margin: 0;
  font-size: 17px;
  line-height: 1.65;
}}
</style>
</head>
<body>
<div class="card">
  <div class="header">Macro Pulse</div>
  <pre>{html.escape(clean)}</pre>
</div>
</body>
</html>
"""
out.write_text(page, encoding="utf-8")
print(out)
PY

pkill -f "http.server 8765" 2>/dev/null || true
cd "$HOME/storage/shared/Documents" || exit 1
nohup python3 -m http.server 8765 >/dev/null 2>&1 &
sleep 2

am start -n com.android.chrome/com.google.android.apps.chrome.Main \
-a android.intent.action.VIEW \
-d "http://127.0.0.1:8765/macro_pulse.html" >/dev/null 2>&1 || true
