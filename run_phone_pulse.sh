#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$HOME/trading-system"
git pull --ff-only
source .venv/bin/activate
python3 -c "from macro.pulse import run; run()"
