# Development Log

---

## 2026-03-29 — Timestamp clarity patch: local time + UTC in header

### What changed
- `reports/options_sniper.py`: replaced hardcoded `PST` string with `datetime.now().astimezone()` → `%Z`; added `utc_str = datetime.now(timezone.utc).strftime("%H:%M UTC")`; header line now reads `Generated: [local time TZ]  |  Market ref: [UTC]  |  [session] Session`
- `outputs/options_html.py`: same local+UTC split; added `from macro.session import current_session`; `report-meta` div now reads `Generated: [local time TZ] · Market ref: [UTC] · [session] Session`
- `outputs/premarket_html.py`: identical changes to options_html.py

### Why
Hardcoded `PST` in `strftime` was always wrong for any non-PST host and showed no UTC reference for cross-timezone readers. Session label alone was insufficient to anchor market time unambiguously.

### What was preserved
- Session classification logic in `macro/session.py` — unchanged
- All scoring, guardrails, ranking, rendering structure — unchanged
- `session` variable and label — unchanged, now displayed in all three surfaces

### Files changed
- `reports/options_sniper.py` — 4-line diff (import timezone, split now/utc_str, update header line)
- `outputs/options_html.py` — 6-line diff (import timezone + current_session, split now/utc_str/session, update report-meta)
- `outputs/premarket_html.py` — 6-line diff (same as options_html.py)

---

## 2026-03-29 — Fix: circular import between options_sniper and rescanner

### What changed
- `reports/options_sniper.py`: removed top-level `from sniper import rescanner as _rescanner` and `from sniper.rescanner import INTERVAL_DEFAULT` imports
- `reports/options_sniper.py`: deferred rescanner import to inside `run()` body — `from sniper import rescanner as _rescanner`
- `reports/options_sniper.py`: `interval` parameter changed from `int = INTERVAL_DEFAULT` to `int | None = None`; resolved inside body via `interval if interval is not None else _rescanner.INTERVAL_DEFAULT`

### Why
`options_sniper` imported `rescanner` at top level; `rescanner` imported `TradeIdea` and helpers from `options_sniper` at top level — mutual dependency at module load time. Deferred import in `run()` breaks the cycle with minimal surface area.

### What was preserved
- All behavior unchanged: `run()` signature is compatible (callers passing `interval` explicitly continue to work; callers using the default continue to get `INTERVAL_DEFAULT`)
- No changes to scoring, guardrails, rendering, output, state-transition logic, or any v1 freeze items

### Files changed
- `reports/options_sniper.py` — 4-line diff (remove 2 imports, change default, defer import + inline resolve)

---

## 2026-03-29 — Phase 2C Reconciliation: trigger_type scope cleanup

### What changed
- `reports/options_sniper.py`: removed `_classify_trigger_type()` — unused parallel classification path; `_b_grade_trigger_type()` is the only authoritative path and remains unchanged
- `outputs/options_html.py`: removed `trigger_html` variable, its `{trigger_html}` render slot, and `.watch-trigger` CSS rule
- `outputs/premarket_html.py`: removed `from reports.options_sniper import _derive_trigger` import, `trigger = _derive_trigger(reasons)` call, `watchlist-trigger` HTML div, and `.watchlist-trigger` CSS rule

### Why
trigger_type patch drifted into HTML rendering. Intended scope was backend metadata only: field exists on TradeIdea, populated for B-grade entries in build_report(), no user-visible output.

### What was preserved
- `trigger_type` field on `TradeIdea` — unchanged
- `trigger_condition` field and its population — unchanged
- `_b_grade_trigger_type()` — authoritative path, unchanged
- `_b_grade_trigger()` and `_derive_trigger()` — used for trigger_condition, unchanged
- All scoring, guardrail, and v1 freeze items — unchanged

---

## 2026-03-29 — Phase 2C (Step 3): Wire rescanner into options_sniper.run()

### What changed
- `reports/options_sniper.py`: added `rescan`, `interval`, `max_cycles` params to `run()`
- `reports/options_sniper.py`: imported `sniper.rescanner` and `INTERVAL_DEFAULT`
- After report print + send, if `rescan=True` and ideas exist, calls `_rescanner.run_loop(ideas, interval, max_cycles)`

### Behavior
- Default call (`run()`) is unchanged — no rescanner starts
- `run(rescan=True)` seeds the loop with all TradeIdea produced by `build_report()` (B watchlist + A/A+ validated) and runs at 15 min default interval
- Interval and cycle cap are overridable: `run(rescan=True, interval=INTERVAL_NEAR_TRIGGER, max_cycles=10)`
- Candidates are scoped to the ideas list — full ticker universe is never rescanned

### Files changed
- `reports/options_sniper.py` — 5-line diff (import + run signature + loop call)

### Not touched
- `sniper/rescanner.py` — no changes
- `sniper/scanner.py`, `sniper/analysis.py` — no changes
- All v1 stable freeze items unchanged

---

## 2026-03-29 — Phase 2C (Step 2): Rescanner / Promotion Engine

### What changed
- Created `sniper/rescanner.py` — targeted candidate validation loop

### What it does
- `run_cycle(candidates, macro_data)` — one full rescan pass over provided TradeIdea list; returns `list[CycleResult]`
- `run_loop(candidates, interval, max_cycles, on_cycle)` — timed loop using `INTERVAL_DEFAULT` (15 min), `INTERVAL_NEAR_TRIGGER` (5 min), or `INTERVAL_HUNT` (1 min)
- Per-cycle per-ticker: re-fetch via `scan({ticker: ticker})` → recompute score → re-run all guardrails → state transition
- State transitions: **Promote** (B → A/A+, passes all guardrails), **Retain** (same tier, still valid), **Demote** (A/A+ → B, degraded), **Reject** (fails guardrails or score < 60)
- Badges emitted: `"Promoted This Cycle"` / `"Lost Validity This Cycle"`
- Rejected candidates drop from the active list; loop stops when no candidates remain

### Critical rule enforced
Promotion only on full guardrail pass (`_hard_guardrails` returns empty + score ≥ 80). No partial promotion.

### Files changed
- `sniper/rescanner.py` — new file

### Not touched
- `reports/options_sniper.py` — no changes; rescanner imports its evaluation functions directly
- `sniper/scanner.py` — no changes
- All v1 stable freeze items unchanged

---

## 2026-03-29 — Phase 2C: NEXT_STEPS.md reconciliation

### What happened
`docs/NEXT_STEPS.md` was found to contain a stale task definition that did not match the actual code state. Specifically:
- It described adding `trigger_type` to `TradeIdea` as a pending task — but the field was already implemented
- It specified a string-matching derivation from `trigger_condition` values — but the actual implementation uses direct branch mirroring via `_b_grade_trigger_type()`
- It listed `reports/premarket.py` as the target file — but that file has no B-grade or `TradeIdea` logic

### Correction
`docs/NEXT_STEPS.md` rewritten to reflect actual code state. No code was changed. DEV_LOG updated to record the mismatch.

### Current Phase 2C state (verified)
- `trigger_type: str = ""` exists on `TradeIdea` (options_sniper.py:57)
- `_classify_trigger_type(reasons)` — keyword classifier (options_sniper.py:200)
- `_b_grade_trigger_type(setup, opts, regime)` — branch-mirroring derivation (options_sniper.py:219)
- `trigger_type` populated for all B-grade entries in `build_report()` (options_sniper.py:390)
- `""` returned for the "Composite score reaches 80" fallback — no type category assigned (deferred)

---

## 2026-03-29 — Phase 2C (Step 1): trigger_type field

### What changed
- Added `trigger_type: str = ""` to `TradeIdea` dataclass
- Added `_classify_trigger_type(reasons: list[str]) -> str` — keyword classifier mapping blocking reason strings to type categories (`rr` / `grade` / `regime` / `liquidity` / `""`)
- Added `_b_grade_trigger_type(setup, opts, regime) -> str` — mirrors `_b_grade_trigger` branches exactly, returns type string instead of label
- In `build_report()`, B-grade `TradeIdea` creation now also sets `trigger_type=_b_grade_trigger_type(s, opts, regime)`

### Why
Phase 2C foundation: downstream rescanner and promotion logic needs a stable, classified type for each Tier 2 blocking reason to route state transitions correctly. Adding the field now keeps data and derivation in one place before the loop is wired.

### Expected impact
- No change to output rendering, scoring, ranking, or filtering
- Every Tier 2 `TradeIdea` carries a `trigger_type` string alongside `trigger_condition`
- Tier 1, Tier 3, and HTML layers untouched
- `""` for the "Composite score reaches 80" fallback case (no single blocking category — deferred)

---

## 2026-03-29 — Phase 2B: Watchlist Trigger Conditions

### What changed
- Added `trigger_condition: str = ""` to `TradeIdea` dataclass
- Added `_derive_trigger(reasons: list[str]) -> str` — single-source trigger mapper in `reports/options_sniper.py`
- Added `_b_grade_trigger(setup, opts, regime) -> str` — sniper-specific wrapper; synthesizes soft-blocking reason and delegates to `_derive_trigger`
- Populated `trigger_condition` for Tier 2 (B-grade) entries only in `build_report()`
- Both HTML outputs render `Becomes valid if: [trigger_condition]` as one muted line in Tier 2 cards
- Removed duplicate `_trigger_from_failure` from `outputs/premarket_html.py`; premarket now imports `_derive_trigger` from `reports.options_sniper`

### Reconciliation pass (same date)
- Identified drift: `_trigger_from_failure` in `premarket_html.py` was an independent copy of trigger derivation logic
- Corrected: moved to single-source `_derive_trigger` in `options_sniper.py`
- `_b_grade_trigger` now delegates to `_derive_trigger` for the liquidity case
- Premarket imports and calls `_derive_trigger` directly — no local derivation in render layer

### Why
Phase 2B PRD: each Tier 2 watchlist entry must display exactly one forward-looking trigger condition derived from the primary blocking failure.

### Expected impact
- Tier 2 cards in both dashboards now show "Becomes valid if: [condition]"
- Trigger text is authoritative and single-sourced
- No change to Tier 1, Tier 3, scoring, ranking, or Phase 2A logic

---
