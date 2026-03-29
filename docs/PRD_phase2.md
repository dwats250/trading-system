# PRD Addendum — Phase 2 System Expansion

## Objective

Evolve the current sniper system from a long-only filtering engine into a bidirectional, condition-aware, continuously validating decision engine while preserving strict guardrail integrity.

---

## Core Principles (Non-Negotiable)

* No setup may be promoted to a tradable state unless it passes all existing sniper guardrails
* The system must prefer no trades over low-quality trades
* The rescanner must never relax standards or manufacture urgency
* Watchlist setups are not tradable — they are conditional candidates only
* Maintain strict visual and logical separation between validated, watchlist, and rejected states
* Build features incrementally — do not combine phases into a single implementation

---

## Feature 1 — SHORT-Side Support (Phase 2A)

**Goal:** Allow the system to express high-quality bearish setups, especially in RISK OFF regimes.

### Short Setup Types to Detect

| Type | Condition |
|------|-----------|
| `breakdown` | Price breaks and holds below support |
| `failed_breakout` | Price rejected at resistance, reverses below |
| `trend_rejection` | Price tests resistance in downtrend, fails |
| `pullback_short` | Price bounces into EMA resistance in downtrend |

### Invalidation Logic (Mirror of Long Side)

Same 6-step hierarchy, applied above price:

1. Detect `setup_type`
2. Select EMA anchor — breakdown/trend_rejection → EMA9, pullback_short → EMA21, failed_breakout → EMA21
3. Apply 1.5% buffer above anchor
4. Apply 1% minimum stop floor above entry
5. Apply 0.5× ATR(14) floor above entry
6. Final stop = widest (most conservative) candidate

### Constraints

* R:R ≥ 2:1 (unchanged)
* Same A/B/C scoring system
* Same 5 hard guardrails (macro, liquidity, structure, grade, R:R)
* In RISK OFF regimes, shorts surface naturally as primary candidates
* No changes to long-side logic — mirror behavior, do not fork

---

## Feature 2 — Watchlist Trigger Conditions (Phase 2B)

**Goal:** Convert watchlist from passive display into an actionable conditional system.

### Trigger Condition Types

| Category | Example Conditions |
|----------|--------------------|
| Price action | Break and hold above resistance; breakdown below support; EMA21 retest holds |
| Structure | Grade upgrades from B → A |
| Risk | R:R improves above 2:1 |
| Macro | Regime conflict resolves |
| Options/liquidity | Volume or spread threshold met |

### Output Behavior

* One primary trigger per watchlist entry (low cognitive load)
* Label: **"Becomes valid if: [condition]"**
* Watchlist entries remain visually and semantically non-tradable

---

## Feature 3 — Validation Rescanner / Promotion Engine (Phase 2C)

**Goal:** Continuously evaluate watchlist setups and promote only when all conditions are met.

### Design Constraint

This is NOT a full re-scan engine. It is a targeted **candidate validation loop**.

### Scope

* Rescan: current watchlist setups + current validated trades (degradation checks only)
* Do NOT rescan full ticker universe every cycle

### Scan Intervals

| Mode | Interval | Scope |
|------|----------|-------|
| Default | 15 minutes | Full watchlist |
| Near-trigger | 5 minutes | Small subset approaching trigger |
| Hunt | 1 minute | Max 1–3 tickers, time-limited, manual or conditional |

### Per-Cycle Logic

For each candidate:

1. Refresh market data
2. Recompute: setup type, structure grade, invalidation (EMA + % floor + ATR floor), R:R
3. Re-run all sniper guardrails
4. Determine state transition:

| Outcome | Condition |
|---------|-----------|
| **Promote** | Passes all guardrails |
| **Retain** | Still watchlist-valid |
| **Demote** | Structure degraded |
| **Reject** | Fails key conditions |

### Critical Rule

A setup may only be promoted if it satisfies ALL existing guardrails.
No partial promotion. No inferred readiness.

---

## Enhanced Output Structure

| Section | Display Treatment |
|---------|-------------------|
| Validated Top Trades | Full card, ranked |
| Watchlist — Waiting on Trigger | Dimmed, no rank, shows trigger condition |
| Promoted This Cycle *(optional)* | Highlight badge |
| Lost Validity This Cycle *(optional)* | Muted warning |
| Not on Radar | Compact text only |

Visual hierarchy is non-negotiable: Validated = full card · Watchlist = dimmed · Not on radar = minimal text.

---

## Implementation Order (Strict)

1. **Phase 2A** — SHORT-side support
2. Compact + validate behavior
3. **Phase 2B** — Watchlist trigger conditions
4. Compact + validate behavior
5. **Phase 2C** — Rescanner / promotion engine
6. Compact + validate behavior

Do not combine phases.

---

## Recommended Defaults (Carry Forward from v1)

| Parameter | Value |
|-----------|-------|
| R:R minimum | 2.0 |
| EMA buffer | 1.5% |
| Min stop floor | 1.0% |
| ATR floor | 0.5× ATR(14) |
| Rescan interval | 15 min |
| Near-trigger interval | 5 min |
| Hunt mode interval | 1 min |

---

## Tradeoffs

* More frequent scans increase responsiveness but must not increase noise
* SHORT-side logic increases complexity but is required for full regime coverage
* Rescanner adds state management complexity — must remain deterministic and auditable

---

## Out of Scope (Phase 2)

* Alerts / notifications — only after rescanner is stable
* Position sizing engine
* Options strategy selection layer
* Backtesting / performance tracking

---

## End State

A system that:
* Filters aggressively
* Tracks conditional opportunities
* Promotes only when fully valid
* Operates correctly across both bullish and bearish regimes
