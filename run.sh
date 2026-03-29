#!/bin/bash
# Macro Suite — Main launcher
# Usage: ./run.sh  or  bash run.sh

cd /home/dustin/trading-system
source .venv/bin/activate

echo "==> Pre-market report..."
python3 -c "from outputs.premarket_html import save; save()"

echo "==> Options sniper..."
python3 -c "from outputs.options_html import save; save()"

echo ""
echo "==> Publishing to GitHub Pages..."
git add premarket.html options_sniper.html macro_pulse.html
git commit -m "Update dashboards $(date '+%Y-%m-%d %H:%M')" --quiet
git push origin main --quiet && echo "Done. Live at: https://dwats250.github.io/trading-system" || echo "Push failed — check connection."
