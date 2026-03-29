#!/data/data/com.termux/files/usr/bin/bash
# Macro Suite — Termux Setup
pkg install python -y
pip install requests yfinance
echo 'alias macro="cd ~/trading-system && git pull && python main.py"' >> ~/.bash_profile
source ~/.bash_profile
echo "Done. Type: macro"
