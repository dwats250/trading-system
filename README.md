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

Every push to `main` automatically builds and deploys the full dashboard suite to GitHub Pages.

**Workflow:** `.github/workflows/deploy-dashboard.yml`
- Triggers on push to `main` and `workflow_dispatch`
- `build` job: runs `python -m reports.build_all _site`, uploads `_site/` as Pages artifact
- `deploy` job: depends on `build`, deploys via `actions/deploy-pages`

**Build locally (all four pages → `reports/output/`):**
```bash
python -m reports.build_all
```

**Build to a custom directory:**
```bash
python -m reports.build_all _site
```

**Pages output directory:** `_site/` (gitignored — built by CI, never committed)

**Site pages:**
- `index.html` — landing hub with links to all reports
- `macro_pulse.html` — cross-asset regime dashboard
- `premarket.html` — morning brief + setups
- `options_sniper.html` — full pipeline + ranked trades

**Hosted URL:**
```
https://dwats250.github.io/trading-system/
```
Exact URL shown under **Settings → Pages** after first deploy.

**One-time repo setup (manual):**
Go to **Settings → Pages → Source** and select **GitHub Actions**.

**Phone workflow:**
Open the Pages URL in Chrome. No local server, no SSH, no Termux required.

> ⚠️ GitHub Pages is public. Do not push API keys, private tickers, or sensitive position data into the generated output.

---

## Version

v2.0 — Modular rebuild with Entry Sniper
