# Next Steps

---

## Current state
- **Phase 2A** — Complete and stable (SHORT-side detection, scoring, invalidation, HTML)
- **Phase 2B** — Complete and reconciled (trigger conditions on all Tier 2 watchlist entries)
- **Phase 2C** — Complete (trigger_type backend, rescanner module, run() wiring, scope reconciliation)

---

## Phase 2C — Rescanner / Promotion Engine

**Complete.**

### Completed
- `trigger_type: str = ""` on `TradeIdea` — backend metadata only, no rendering
- `_b_grade_trigger_type(setup, opts, regime)` — sole authoritative path, populates trigger_type for B-grade entries in `build_report()`
- `sniper/rescanner.py` — `run_cycle`, `run_loop`, `CycleResult`, interval constants
- State transitions: Promote / Retain / Demote / Reject — full guardrail pass required for Promote
- Scope reconciliation: removed `_classify_trigger_type` (unused), removed trigger HTML/CSS from both output files
- `run()` wired: `rescan=False` default unchanged; `run(rescan=True)` seeds `run_loop()` from `build_report()` ideas list

### Deferred
- Badge surfacing in HTML output (`"Promoted This Cycle"` / `"Lost Validity This Cycle"`) — exists on `CycleResult`, not rendered
- Near-trigger / Hunt automatic interval switching — currently caller-controlled only

---
