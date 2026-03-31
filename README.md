# trading-system

A macro-aware options decision engine. Reads cross-asset regime, scores trade setups through a strict pipeline, and rejects more trades than it accepts.

---

## What it does

The system runs a full pipeline on every execution:

```
MACRO → REGIME → PLAYBOOK → FOCUS → CHART → OPTIONS → VALIDATE → RANK → OUTPUT
```

- **Macro Pulse** — cross-asset regime scanner (RISK ON / MIXED / RISK OFF), primary and secondary driver detection, incident alerts, session awareness
- **Pre-Market Report** — overnight futures, macro snapshot, economic calendar, three-tier setup classification
- **Options Sniper** — full pipeline report with composite scoring (0–100), hard guardrail enforcement, options chain analysis, ranked trade ideas
- **Dashboard Hub** — landing page linking all three reports

---

## Live dashboard

Deployed automatically to GitHub Pages on every push to `main`.

```
https://dwats250.github.io/trading-system/
```

Open in any browser. No local server, no SSH, no Termux required.

**One-time setup:** Settings → Pages → Source → **GitHub Actions**

---

## Local usage

**Run all reports (writes to `reports/output/`):**
```bash
python -m reports.build_all
```

**Individual reports:**
```bash
python -m macro.pulse           # macro pulse terminal output
python -m reports.premarket     # pre-market report
python -m reports.options_sniper  # options sniper report
```

**Quick macro dashboard (local preview with optional server):**
```bash
python -m dashboard.macro
python -m dashboard.macro --serve
python -m dashboard.macro --serve --refresh 60
```

---

## System doctrine

- No trade without macro context
- No trade without defined invalidation
- No trade below R:R 2:1 minimum
- Prefer WAIT over weak setups
- The system must reject more trades than it accepts

**Hard guardrails** (any failure → rejected):
- R:R < 2:1
- Chart grade not A
- Options liquidity insufficient
- Structure unclear
- Trade conflicts with macro regime

---

## Scoring

Each setup is scored 0–100 across five dimensions:

| Category         | Weight |
|------------------|--------|
| Regime Alignment | 25     |
| Chart Quality    | 25     |
| Risk/Reward      | 20     |
| Options Quality  | 20     |
| Clarity          | 10     |

| Score  | Grade | Treatment        |
|--------|-------|------------------|
| 80–100 | A/A+  | Tradeable        |
| 60–79  | B     | Watch            |
| < 60   | C     | Reject           |

---

## Project structure

```
dashboard/        CLI entry point for quick macro dashboard
  macro.py        python -m dashboard.macro
  render.py       text → HTML renderer
  server.py       local HTTP server utility

macro/            Macro pulse engine
  pulse.py        regime, drivers, incidents, cross-asset read
  regime.py       RISK ON / MIXED / RISK OFF classifier
  playbook.py     regime-specific trade playbook
  focus.py        focus ticker routing

sniper/           Chart quality engine
  scanner.py      scan() → list[Setup]
  analysis.py     EMA alignment, RSI, ATR, setup scoring

options/          Options chain analysis
  chain.py        analyze() → OptionsAnalysis

reports/          Report builders
  options_sniper.py   full pipeline report
  premarket.py        morning brief
  build_all.py        builds all four HTML pages

outputs/          HTML renderers
  html.py             macro pulse page
  premarket_html.py   pre-market page
  options_html.py     options sniper page
  index_html.py       landing hub
  shared.py           shared CSS tokens, nav, page shell

config/           Tickers and settings
core/             Shared utilities (fetcher, formatter, notifier)
docs/             PRD and documentation
```

---

## GitHub Actions workflows

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `deploy-dashboard.yml` | push to main, manual | Builds `_site/` via `build_all`, deploys to GitHub Pages |
| `build-dashboard.yml`  | schedule (30 min), manual | Builds all reports and commits HTML output |

**Pages build directory:** `_site/` — gitignored, built by CI only, never committed.

---

## Tech stack

- Python 3.11
- yfinance — market data
- pandas / pandas-ta-classic — indicators
- GitHub Pages — static site hosting
- No external JS/CSS frameworks — all HTML is self-contained

---

> ⚠️ GitHub Pages is public. Do not push API keys, private tickers, or sensitive position data into generated output.
