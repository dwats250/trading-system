# 📘 CLAUDE.md

## Macro Sniper – AI Operating Guidelines

---

# 🎯 PURPOSE

This repository contains a **macro-aware options decision engine**.

The system is designed to:

* Identify high-quality trade setups
* Enforce strict risk discipline
* Reject low-quality trades
* Output only clear, actionable opportunities

---

# 🧠 CORE PRINCIPLE

> The system must reject more trades than it accepts.

If a setup is not clearly valid:
→ **DO NOT TRADE**

---

# ⚙️ SYSTEM FLOW

```text
MACRO → REGIME → PLAYBOOK → FOCUS → CHART → OPTIONS → VALIDATE → RANK → OUTPUT
```

---

# 🧭 SYSTEM DOCTRINE (NON-NEGOTIABLE)

* No trade without macro context
* No trade without defined invalidation
* No trade below minimum R:R
* No trade with poor liquidity
* No forced trades
* No A+ label unless all checklist items pass
* Prefer "WAIT" over weak setups
* **No setup may be presented as a top trade unless it has passed the same guardrails used for execution-level validation**

---

# 🔒 HARD GUARDRAILS

Reject any trade if ANY of the following fail:

* Risk/Reward < 2:1
* Chart quality not A-level
* Options liquidity insufficient
* Structure unclear
* Trade conflicts with macro regime

These guardrails apply equally to all output surfaces. A setup surfaced in the pre-market report, sniper report, or any ranked list must have passed all of the above. No surface may present a setup as tradeable that would be rejected at execution.

---

# 📊 SCORING SYSTEM

Each trade is scored (0–100):

| Category         | Weight |
| ---------------- | ------ |
| Regime Alignment | 25     |
| Chart Quality    | 25     |
| Risk/Reward      | 20     |
| Options Quality  | 20     |
| Clarity          | 10     |

---

### Score Thresholds

* 80–100 → A (tradable)
* 60–79 → B (watch)
* <60 → C (reject)

---

# 🧠 A+ CHECKLIST (REQUIRED)

A trade is A+ ONLY if ALL are true:

* Clear structure
* Clean support/resistance levels
* Regime aligned
* R:R ≥ 2:1
* Not extended
* Momentum confirmation
* Liquid options chain
* Entry and invalidation clearly defined

If ANY fail:
→ NOT A+

---

# ⚙️ OPTIONS STRUCTURE RULES

* Strong trend + normal IV → Long call/put
* Strong trend + high IV → Debit spread
* Weak clarity → No trade

Outputs must include:

* Structure type
* Suggested DTE
* Delta range

---

# 🚫 REJECTION ENGINE

The system must explicitly list rejected setups.

Purpose:

* Reinforce discipline
* Prevent impulsive trades

---

# 🧾 OUTPUT REQUIREMENTS

---

## A Setup (Only if valid)

* Ticker
* Score
* Why
* Structure
* Entry
* Invalidation
* Options suggestion
* Risk/Reward

---

## WATCH

* Not actionable
* Waiting for structure

---

## REJECT

* Clear reason
* No ambiguity

---

## CONCLUSION

The system MUST be able to output:

```text
No A+ setups → WAIT
```

---

# 🧠 ARCHITECTURE (EXPECTED MODULES)

* macro_engine
* regime_router
* chart_scorer
* a_plus_validator
* options_engine
* trade_ranker
* rejection_engine
* report_builder

---

# 🧪 VALIDATION REQUIREMENTS

The system must be:

* Explainable
* Testable
* Consistent

Maintain:

* Sample trade library (good / bad / rejected)
* Regular review of outputs
* Tracking of false positives

---

# 🔄 VERSION CONTROL RULES

All logic changes must include:

* What changed
* Why
* Expected impact

No silent logic changes.

---

# 🤖 MACHINE LEARNING POLICY

Machine learning is NOT used for trade generation.

Allowed uses:

* Ranking refinement
* Pattern clustering
* Trade outcome analysis

NOT allowed:

* Overriding rules
* Replacing checklist
* Generating trades independently

---

# 🗂️ FILE MAP (Read this before opening files)

## Key Logic — Where to Find Things

| What | File | Functions |
|------|------|-----------|
| Composite scoring | `reports/options_sniper.py` | `_composite_score`, `_hard_guardrails`, `_aplus_checklist` |
| Chart grading | `sniper/analysis.py` | `chart_grade`, `setup_score`, `compute_rr` |
| Setup detection | `sniper/analysis.py` | `detect_setup_type`, `ema_alignment`, `invalidation_level` |
| Scanner loop | `sniper/scanner.py` | `scan` |
| Options analysis | `options/chain.py` | `analyze`, `_suggest_structure`, `_delta_guidance` |
| HTML output | `outputs/options_html.py` | `build_options_html`, `save` |
| Pre-market report | `reports/premarket.py` | `build_report` |
| Sniper report | `reports/options_sniper.py` | `build_report`, `run` |
| Regime/drivers | `macro/regime.py` | `classify`, `drivers`, `cross_asset_read` |
| Playbook | `macro/playbook.py` | `generate`, `format_playbook` |
| Focus/routing | `macro/focus.py` | `route`, `format_focus` |
| Tickers config | `config/tickers.py` | `MACRO_SYMBOLS`, `SNIPER_SYMBOLS` |

---

## Setup Dataclass Fields (`sniper/scanner.py`)

```python
ticker, price, e9, e21, e50,
rsi_val, alignment,          # alignment: bullish / bearish / mixed
support, resistance,
score,                        # raw 0-6
grade,                        # A / B / C
confidence,                   # 0-10
setup_type,                   # trend / pullback / breakout / reversal / none
bias,                         # LONG / SHORT / NEUTRAL
entry_note, invalidation,     # invalidation is a float price level
rr                            # float risk/reward ratio
```

## OptionsAnalysis Dataclass Fields (`options/chain.py`)

```python
ticker, expiry, dte, atm_strike,
liquidity,                    # High / Medium / Low
iv, iv_pct,
bid, ask, spread_pct,
volume, open_interest,
suggested_structure,          # Long Call / Debit Call Spread / Long Put / Debit Put Spread
structure_reason, contract_note,
delta_guidance
```

## TradeIdea / Rejection (`reports/options_sniper.py`)

```python
# TradeIdea
setup, options, rank, why,
score,                        # composite 0-100
composite_grade,              # A+ / A / B
failures                      # A+ checklist gaps

# Rejection
ticker, chart_grade, score, reasons
```

## build_report() Return Types
- `reports/options_sniper.py`: returns `(str, list[TradeIdea], list[Rejection])`
- `reports/premarket.py`: returns `str`

---

## Stable Files — Do Not Read Unless Directly Relevant

* `core/fetcher.py`
* `core/formatter.py`
* `core/notifier.py`
* `macro/regime.py`
* `macro/session.py`
* `macro/incidents.py`

---

# 🗺️ ROADMAP

Phase 2 PRD is at `docs/PRD_phase2.md`. Implementation order is strict:
* **2A** — SHORT-side setup detection (first)
* **2B** — Watchlist trigger conditions
* **2C** — Rescanner / promotion engine

Do not begin any phase without explicit instruction. Do not combine phases.

---

# 🔒 V1 STABLE FREEZE

The following behaviors are frozen as of v1 stable. Do not modify unless explicitly requested by the user.

* **3-tier output** — Validated Top Trades / Watchlist Setups (Good Structure, Not Trade-Ready) / Not on radar
* **EMA + ATR stop logic** — 6-step hierarchy in `sniper/analysis.py → invalidation_level()`
* **Guardrail enforcement** — All output surfaces (premarket + sniper) apply the same hard guardrails before ranking any setup

Any change to these three systems requires explicit user instruction. Proposing unsolicited modifications to them is not permitted.

---

# ⚠️ CLAUDE CODE OPERATING RULES (CRITICAL)

---

## 🔹 Token Efficiency

* Read only necessary files
* Do not scan entire repo unless required
* Do not restate context unnecessarily
* Prefer minimal diffs over full rewrites

---

## 🔹 Code Changes

* Modify only relevant modules
* Avoid refactoring unless explicitly requested
* Preserve architecture
* Make smallest valid change

---

## 🔹 Output Format

Default response must be:

* Goal
* Files touched
* Minimal patch/snippet
* Brief rationale

---

## 🔹 Scope Control

Claude MUST NOT:

* Expand ticker universe
* Add features outside PRD
* Introduce new systems without request
* Increase complexity unnecessarily

---

## 🔹 Decision Discipline

Claude MUST:

* Enforce all guardrails
* Prefer rejecting trades over approving weak ones
* Never force outputs
* Always align with system doctrine

---

# 🔥 FINAL DIRECTIVE

> This is a professional decision engine.

> If a trade cannot be clearly justified, it must be rejected.

---
