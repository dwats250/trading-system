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
echo "Done. Open in browser:"
echo "  premarket.html"
echo "  options_sniper.html"
