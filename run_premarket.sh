#!/bin/bash
cd /home/dustin/trading-system
.venv/bin/python -c "from reports.premarket import run; run()"
