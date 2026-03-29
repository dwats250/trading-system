# 📘 PRODUCT REQUIREMENTS DOCUMENT (PRD)

## Macro-Aware Options Sniper (Decision Engine)

---

# 1. 🎯 PURPOSE

Build a **macro-aware decision engine** that identifies high-quality options trades by:

1. Detecting the current **market regime**
2. Routing attention to the correct **sector/tickers**
3. Evaluating **chart structure quality**
4. Evaluating **options chain viability**
5. Producing **ranked, actionable trade ideas**

---

## ❗ Core Philosophy

This system is NOT a signal generator.

It is a **trade triage engine** designed to:

* Reduce bad trades
* Improve decision clarity
* Reinforce disciplined execution
* Surface only high-quality opportunities

---

# 2. 🧠 SYSTEM ARCHITECTURE

The system follows a strict pipeline:

```
MACRO → REGIME → PLAYBOOK → FOCUS → CHART → OPTIONS → RANK → OUTPUT
```

---

# 3. 📊 CORE MODULES

---

## 3.1 MACRO REGIME ENGINE

### Inputs:

* DXY
* US10Y Yield (^TNX)
* VIX
* ES / NQ / RTY futures
* Oil (WTI / Brent)
* Gold / Silver
* USDJPY (optional)

### Output:

```
Regime: OIL-DRIVEN RISK OFF
Primary Driver: VIX spike (+13%)
Secondary Driver: Oil +5.4%
Rates: Rising
Dollar: Strong
```

---

## 3.2 PLAYBOOK GENERATOR

Transforms macro into action bias.

### Output Example:

```
PLAYBOOK:
- Reduce position size
- Favor defensive / short bias
- Focus: Energy strength
- Avoid: Tech longs, weak breakouts
```

---

## 3.3 FOCUS ROUTER

Narrows universe to relevant tickers.

### Example Output:

```
FOCUS:
Primary: Energy → XLE, OXY, XOM, USO
Secondary: Dollar → UUP
Avoid: QQQ, SPY, growth
```

---

## 3.4 CHART QUALITY ENGINE

Evaluates underlying before options.

### Inputs:

* Price structure
* EMA alignment
* RSI
* Support/resistance
* Trend strength
* Volatility expansion

### Output:

```
Score: A / B / C
Confidence: 0–10
Setup Type: breakout / pullback / trend / none
```

### Rules:

* Only A setups proceed to options layer
* B = watchlist
* C = discard

---

## 3.5 OPTIONS CHAIN ENGINE

Evaluates viability of trading contracts.

### Inputs:

* Volume
* Open interest
* Bid/ask spread
* Delta
* Expiry
* Implied volatility

### Output:

```
Liquidity Score: High / Medium / Low
Suggested Structure:
- Long Call
- Debit Spread
- Put
- Put Spread
```

---

## 3.6 TRADE CONSTRUCTION ENGINE

Builds trade idea.

### Output Example:

```
Ticker: UUP
Direction: Long
Setup: Trend continuation

Entry: Pullback to EMA9 or break above 27.91
Invalidation: Below 27.28

Options:
- ITM Call
- 30–45 DTE

Reason:
- Dollar strength + risk-off alignment
```

---

## 3.7 RANKING ENGINE

Ranks top opportunities.

### Criteria:

* Regime alignment
* Chart quality score
* Options liquidity
* Clarity of setup

### Output:

Top 3 setups only.

---

## 3.8 INCIDENT DETECTION ENGINE

Detects major macro moves.

### Example:

```
⚠️ INCIDENT: OIL SHOCK
WTI +5.46%

Implications:
- Inflation pressure
- Energy leadership likely
- Risk assets vulnerable
```

---

# 4. 🖥️ UI / OUTPUT STRUCTURE

---

## 4.1 HEADER

```
PRE-MARKET REPORT
Time / Session
REGIME (large, visible)
```

---

## 4.2 PLAYBOOK (NEW — CRITICAL)

Placed directly under regime.

---

## 4.3 INCIDENTS (if present)

---

## 4.4 FOCUS SECTION

Clearly shows where to trade.

---

## 4.5 TOP SETUPS (PRIORITY SECTION)

**Guardrail requirement:** A setup may only appear in Top Setups if it has passed all execution-level hard guardrails (R:R ≥ 2:1, chart grade A, regime-aligned, options liquid, structure clear). Setups that fail any guardrail must not be ranked — they are either demoted to a watchlist section or excluded entirely. This rule applies to every output surface that ranks or presents setups, including the pre-market report.

Format:

---

### 🥇 #1 TICKER — LONG / SHORT (A SETUP)

* Why
* Entry
* Invalidation
* Structure
* Options idea

---

### 🟡 #2 WATCH (NOT READY)

---

### ⚪ #3 PASS / FALLBACK

---

## 4.6 CONCLUSION (NEW)

```
CONCLUSION:
No A+ setups → WAIT
```

---

## 4.7 MACRO SNAPSHOT

Include interpretation tags:

```
DXY ↑ (pressure on risk)
VIX ↑ (volatility expansion)
WTI ↑ (inflation impulse)
```

---

# 5. ⚙️ FUNCTIONAL REQUIREMENTS

---

## Must Have (Phase 1)

* Macro regime detection
* Playbook generation
* Focus routing
* Chart scoring
* Top 3 ranked setups
* Basic options suggestions

---

## Phase 2

* Options liquidity scoring
* Delta-based contract selection
* Expiration logic
* Spread recommendations

---

## Phase 3

* Entry trigger logic
* Follow-up alerts
* Incident monitoring updates

---

## Phase 4 (Future)

* Trade tracking
* Performance feedback loop
* Adaptive ranking (ML optional)

---

# 6. 🚫 NON-GOALS

Do NOT build:

* Signal spam system
* Random options screener
* ML-first system
* Overly complex dashboard
* Prediction engine

---

# 7. 🧭 DESIGN PRINCIPLES

* Clarity over complexity
* Fewer, better trades
* Bias toward "no trade"
* Explain reasoning
* Align with trader behavior (not generic users)

---

# 8. 🧠 SUCCESS METRICS

The system is successful if:

* It reduces impulsive trades
* It frequently outputs "WAIT"
* It surfaces only clean setups
* It improves trade selection consistency
* It aligns with macro conditions

---

# 9. 🔥 CORE STATEMENT (FOR DEVELOPER)

> This system is not meant to replace the trader.
> It is meant to sharpen decision-making, filter noise, and align trades with macro context and structure quality.
