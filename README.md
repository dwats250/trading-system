Trading Projects

This repository contains my market-analysis and trading tools, built for speed, clarity, and real-time decision-making.

---

## Run

```bash
python main.py
```

---

## Phone Setup (Termux — first time only)

**Step 1 — Clone and install:**
```bash
git clone https://github.com/dwats250/trading-system.git
cd trading-system
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Step 2 — Set up the `macro` shortcut:**
```bash
echo 'alias macro="cd ~/trading-system && git pull && source .venv/bin/activate && python main.py"' >> ~/.bash_profile && source ~/.bash_profile
```

**Step 3 — Run it:**
```bash
macro
```

After setup, just type `macro` every time to pull latest and run.

---

## Structure

- `macro/` — Macro Pulse: regime, drivers, incidents
- `sniper/` — Entry Sniper: EMA/RSI trade setups
- `oil/` — Energy-specific tools
- `core/` — Shared utilities (fetcher, formatter, notifier)
- `config/` — Tickers and settings
- `outputs/` — HTML dashboard
- `docs/` — PRD and documentation
- `archive/` — Old versions

---

## Modules

**Macro Pulse** — real-time cross-asset regime scanner
- Regime: RISK ON / MIXED / RISK OFF
- Primary + secondary driver detection
- Incident alerts (rate spikes, oil shocks, vol spikes)
- Session awareness (Asia / London / NY)

**Entry Sniper** — ranked trade setup scanner
- EMA structure (9 / 21 / 50)
- RSI positioning
- Setup grades: IDEAL / FALLBACK / NO TRADE

---

## Version

v2.0 — Modular rebuild with Entry Sniper
