Trading Projects

This repository contains my market-analysis and trading tools, built for speed, clarity, and real-time decision-making.

---

## Run

```bash
python main.py
```

---

## Phone Setup (Termux — first time only)

**Step 1 — Set up the `laptop` shortcut** (connect to your laptop via SSH):
```bash
echo 'alias laptop="ssh dustin@192.168.0.69"' >> ~/.bash_profile && source ~/.bash_profile
```

**Step 2 — Connect to your laptop:**
```bash
laptop
```

**Step 3 — Set up the `macro` shortcut** (run once after connecting):
```bash
echo 'alias macro="cd ~/trading-system && source .venv/bin/activate && python main.py"' >> ~/.bash_profile && source ~/.bash_profile
```

**After setup, daily use:**
```bash
laptop      # connect to laptop from Termux
macro       # run macro pulse + entry sniper
premarket   # run full pre-market report
```

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

## GitHub Pages Dashboard

Every push to `main` automatically builds and deploys the macro dashboard to GitHub Pages.

**Build locally:**
```bash
python -m dashboard.macro
```
Writes `artifacts/macro_dashboard.html` and `site/index.html`.

**Hosted dashboard:**
Go to **Settings → Pages** in the GitHub repo. The URL will be shown there after the first deploy (format: `https://<user>.github.io/<repo>/`).

**Phone workflow:**
Open the Pages URL in Chrome. No local server, no SSH, no Termux required.

> ⚠️ GitHub Pages is public. Do not push API keys, private tickers, or sensitive position data into the generated output.

---

## Version

v2.0 — Modular rebuild with Entry Sniper
