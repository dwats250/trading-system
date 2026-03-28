Trading Projects

This repository contains my market-analysis and trading tools, built for speed, clarity, and real-time decision-making.

---

🚀 Active Tools

macro/

- Macro Pulse
  - Real-time macro regime scanner
  - Mobile-first (Termux + notifications)
  - Tracks cross-asset flows:
    - Rates (10Y)
    - Dollar (DXY, UJ)
    - Volatility (VIX)
    - Energy (WTI, Brent)
    - Equities (SPY, QQQ)
    - Metals (XAU, XAG)
    - Crypto (BTC)

---

sniper/

- Entry Sniper (in progress)
- Focus: high-probability setups and execution

---

oil/

- Energy-specific macro + trade tools

---

📊 Macro Pulse Output (v1.0)

Each run produces:

- Timestamp
- Regime (RISK ON / OFF / MIXED)
- Primary drivers
- Cross-asset snapshot
  - Direction (↑ ↓)
  - % change
  - Current price
- Summary line

Example:
10Y ↑ +0.54% @ 4.44
DXY ↑ +0.29% @ 100.19

---

⚙️ Workflow

- Edit locally in Termux
- Run script:
  python main.py
- Sync changes:
  sync-macro

---

📁 Structure

- "macro/" → Macro Pulse + regime tools
- "sniper/" → trade setup tools
- "oil/" → energy-focused analysis

---

📏 Rules

- Keep repo focused on tools, signals, and macro analysis
- No financial tracking or tax records here
- Archive experiments instead of cluttering active tools

---

🏷️ Version

v1.0 — Stable Baseline

- Clean output formatting
- Notification-ready
- Auto-sync enabled
- Mobile optimized

---

🔄 Next Up

- Signal layer (bias per asset)
- Sniper integration
- Event-driven alerts
