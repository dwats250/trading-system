#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$HOME/trading-system"
git pull --ff-only
source .venv/bin/activate
python3 - <<'PY'
from macro.pulse import run as run_macro
from outputs.premarket_html import save as save_premarket

data_map = run_macro()
save_premarket(data_map=data_map)
PY

if command -v am >/dev/null 2>&1; then
  am start \
    -n com.android.chrome/com.google.android.apps.chrome.Main \
    -a android.intent.action.VIEW \
    -d "file://$PWD/premarket.html" >/dev/null 2>&1 || true
fi

if command -v termux-open >/dev/null 2>&1; then
  termux-open "$PWD/premarket.html" >/dev/null 2>&1 || true
fi
