# Macro Suite – Product Requirements Document (PRD)

## 1. Overview

Macro Suite is a modular trading intelligence system designed to:

- Monitor global macro conditions in real time
- Identify regime shifts across markets
- Track cross-asset relationships (DXY, rates, oil, equities, metals)
- Surface high-probability trade opportunities
- Provide actionable insights via terminal and mobile environments

---

## 2. Core Philosophy

- Macro → Fundamentals → Technicals
- Focus on drivers, not noise
- Lightweight, fast, and readable outputs
- Built for decision clarity, not data overload
- Mobile-first usability (Termux + notifications)

---

## 3. Core Modules

### 3.1 Macro Pulse

Purpose: Real-time macro awareness

Tracks:
- DXY (Dollar strength)
- US10Y (rates / liquidity)
- Oil (inflation / geopolitical driver)
- VIX (risk sentiment)
- SPY / NDX (equity direction)
- Gold / Silver (monetary stress)

Outputs:
- Regime classification (risk-on / risk-off / mixed)
- Primary driver
- Secondary driver
- Directional bias

Features:
- Hourly updates
- Session awareness (Asia / London / NY)
- Incident detection for large moves

---### 3.2 Entry Sniper

Purpose: Identify high-quality trade setups

Analyzes:
- EMA structure (trend alignment)
- Momentum shifts
- RSI positioning
- Support / resistance
- Intraday structure

Outputs:
- Top 1–3 trade candidates
- Entry conditions
- Ideal setup vs fallback setup
- “Do nothing” signal if no A+ setups

Design goal:
Eliminate low-quality trades and enforce discipline

---

### 3.3 Trade Tracker

Purpose: Improve execution and performance

Tracks:
- Trade entries and exits
- Strategy type (spread, directional, etc.)
- Profit and loss
- Execution quality

Future:
- Performance analytics
- Strategy breakdown
- Pattern recognition

---

### 3.4 Macro Intelligence Layer (Future)

Goal: Evolve beyond manual interpretation

Planned features:
- Pattern recognition across regimes
- Historical behavior tracking
- Adaptive strategy suggestions
- ML-assisted signal weighting

---## 4. System Architecture

Structure:

trading-projects/
├── macro/
├── sniper/
├── oil/
├── core/
├── config/
├── outputs/
├── docs/

Design Principles:
- Modular architecture
- Lightweight API usage
- Terminal-first output
- Expandable to web/dashboard

---

## 5. Output Design

Requirements:
- Clean, readable formatting
- Minimal noise
- Strong signal hierarchy:
  - Timestamp
  - Regime
  - Drivers
  - Key levels
- Visual clarity (spacing, alignment)

---

## 6. Automation

Current:
- Hourly macro updates

Planned:
- Pre-market report (6:00 AM)
- Trade scan (6:30 AM)
- Intraday updates
- Incident-triggered alerts

---

## 7. Roadmap

Phase 1:
- Stabilize Macro Pulse
- Improve formatting and clarity

Phase 2:
- Entry Sniper integration
- Watchlist refinement

Phase 3:
- Trade Tracker system
- Performance logging

Phase 4:
- Machine learning integration
- Adaptive strategies
