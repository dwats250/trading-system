# Macro Suite – Product Requirements Document (PRD)

## 1. Overview

Macro Suite is a modular trading intelligence system designed to:

- Monitor global macro conditions in real time
- Identify regime shifts across markets
- Track cross-asset relationships (DXY, rates, oil, equities, metals)
- Surface high-probability trade opportunities
- Provide actionable insights via terminal and mobile environments

The system is built primarily for fast decision-making, not data overload.

---

## 2. Core Philosophy

- Macro → Fundamentals → Technicals
- Focus on drivers, not noise
- Clarity over complexity
- Only act on high-quality setups
- Mobile-first usability (Termux + notifications)
- Reduce emotional trading through structured outputs

---

## 3. Core Modules

### 3.1 Macro Pulse

**Purpose:** Real-time macro awareness

**Tracks:**
- DXY (Dollar strength)
- US10Y (rates / liquidity)
- Oil (inflation / geopolitical driver)
- VIX (risk sentiment)
- SPY / NDX (equity direction)
- Gold / Silver (monetary stress)

**Outputs:**
- Regime classification (risk-on / risk-off / mixed)
- Primary driver
- Secondary driver
- Directional bias

**Features:**
- Hourly updates
- Session awareness (Asia / London / NY)
- Incident detection:
  - Rate spikes
  - Dollar breakouts
  - Oil shocks
- Follow-up tracking during events

---

### 3.2 Entry Sniper

**Purpose:** Identify high-quality trade setups

**Analyzes:**
- EMA structure (trend alignment)
- Momentum shifts
- RSI positioning
- Support / resistance
- Intraday structure

**Outputs:**
- Top 1–3 trade candidates
- Entry conditions
- Ideal setup vs fallback setup
- Explicit "no trade" signal when setups are weak

**Goal:**
Eliminate low-quality trades and enforce discipline

---

### 3.3 Trade Tracker

**Purpose:** Improve execution and long-term performance

**Tracks:**
- Trade entries and exits
- Strategy type (spread, directional, etc.)
- Profit and loss
- Execution quality

**Future Enhancements:**
- Performance analytics
- Strategy breakdown
- Behavioral tracking
- Mistake identification

---

### 3.4 Macro Intelligence Layer (Future)

**Goal:** Move beyond manual interpretation

**Planned Features:**
- Pattern recognition across regimes
- Historical behavior mapping (tickers vs macro states)
- Adaptive strategy suggestions
- ML-assisted signal weighting

---

## 4. System Architecture

### Current Structure

trading-projects/
├── macro/
├── sniper/
├── oil/
├── core/
├── config/
├── outputs/
├── docs/

### Design Principles

- Modular architecture (independent but connected components)
- Lightweight API usage
- Terminal-first output
- Mobile-friendly formatting
- Expandable to web/dashboard interface

---

## 5. Output Design

### Requirements

- Clean, readable formatting
- Minimal noise
- Strong signal hierarchy:
  - Timestamp
  - Regime
  - Primary driver
  - Secondary driver
  - Key levels

### UX Goals

- Fast scanning
- No clutter
- Clear directional bias
- Consistent formatting across tools

---

## 6. Automation

### Current

- Manual or scheduled macro updates

### Planned

- Pre-market report (6:00 AM)
- Pre-market trade setup scan (6:30 AM)
- Intraday macro pulse updates
- Incident-triggered alerts
- Notification system (phone + watch)

---

## 7. Roadmap

### Phase 1 (Current)

- Stabilize Macro Pulse
- Improve output clarity
- Define core ticker set

### Phase 2

- Entry Sniper integration
- Trade candidate system
- Watchlist refinement

### Phase 3

- Trade Tracker implementation
- Performance logging system

### Phase 4

- Machine learning integration
- Adaptive strategy layer
- Automated insights

---

## 8. Long-Term Vision

Macro Suite evolves into a **personal trading operating system** that:

- Understands macro regimes in real time
- Identifies opportunities automatically
- Adapts strategies based on performance
- Minimizes emotional decision-making
- Provides a complete trading feedback loop

End goal:
A disciplined, data-driven trading system built around clarity, consistency, and edge.
