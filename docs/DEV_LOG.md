# Development Log

---

## 2026-03-31 — Macro Pulse and Dashboard live header cleanup

### What changed
- `outputs/html.py`: removed redundant top-row regime/driver duplication from Macro Pulse so the boxed summary card remains the only top summary surface and `MIXED` renders only in aligned stat cells
- `outputs/index_html.py`: replaced the Dashboard `report_header(...)` + boxed summary stack with one boxed summary card that owns title, metadata, navigation, and stat cells
- regenerated the real Pages deployment targets for both pages:
  - `_site/macro_pulse.html`
  - `_site/index.html`
  - `reports/output/macro_pulse.html`
  - `reports/output/index.html`

### Root cause
- Macro Pulse source had already been moved to a boxed summary card, but it still repeated regime/driver context in the top row outside the stat-cell layout
- Dashboard source still emitted two top surfaces in the actual render path: a shared `report_header(...)` followed by a second boxed summary card
- local preview files had previously lagged behind template changes, which made the stale top layout appear unchanged in browser checks

### Verification
- `python3 -m py_compile outputs/html.py outputs/index_html.py` passed
- Rebuilt actual deployment files with the live render path:
  - `.venv/bin/python - <<'PY' ... save_macro(path='_site/macro_pulse.html') ... save_index(path='_site/index.html') ... PY`
- Verified rendered deployment files directly:
  - `_site/macro_pulse.html`
    - `<div class="report-header">=0`
    - `<div class="surface-card summary-card">=1`
    - `<div class="summary-driver">=0`
    - `<div class="report-note">=0`
    - `<nav class="nav-bar">=0`
    - `<div class="nav-inline">=1`
    - `<div class="regime-pill mixed">MIXED</div>=0`
    - `<div class="stat-value">MIXED</div>=1`
  - `_site/index.html`
    - `<div class="report-header">=0`
    - `<div class="surface-card hub-summary-card">=1`
    - `<div class="hub-tagline">=0`
    - `<div class="hub-read">=0`
    - `<div class="meta-strip">=0`
    - `<div class="driver-text">=0`
    - `<div class="report-note">=0`
    - `<nav class="nav-bar">=0`
    - `<div class="nav-inline">=1`
    - `<div class="stat-value">MIXED</div>=1`

### Files changed
- `outputs/html.py`
- `outputs/index_html.py`
- `docs/DEV_LOG.md`

---

## 2026-03-31 — Pre-Market header sanity fix

### What changed
- `outputs/premarket_html.py`: audited the actual Pre-Market render path and confirmed the page was still stacking two top summary surfaces
- `outputs/premarket_html.py`: replaced the `report_header(...)` + `_daily_mission_html(...)` pair with one consolidated boxed summary block for the Pre-Market page only
- `outputs/premarket_html.py`: moved `MIXED` regime rendering onto shared `stat_block(...)` cells so it no longer uses the old inline `mission-value` layout path

### Root cause
- The prior UI polish pass cleaned up shared header usage, but Pre-Market still rendered its page-local `_daily_mission_html()` directly under the shared header
- That left two overlapping metadata surfaces on the actual page
- The `MIXED` label was still emitted by the old `.mission-value` inline row on Pre-Market, not by the aligned stat-cell layout

### Verification
- `python3 -m py_compile outputs/premarket_html.py` passed
- `python3 desktop/test_premarket_fixtures.py` passed
- Rebuilt a scoped sanity render to `artifacts/premarket_sanity.html` and confirmed:
  - `report_header_count=0`
  - `daily_mission_count=0`
  - `mission_value_mixed_count=0`
  - `stat_value_mixed_count=1`

### Files changed
- `outputs/premarket_html.py`
- `docs/DEV_LOG.md`

---

## 2026-03-31 — Final UI polish pass

### What changed
- `outputs/shared.py`: added inline header navigation support via `nav_links()` and `report_header(..., nav_html=...)` so page navigation now lives inside the header zone instead of above it
- `outputs/premarket_html.py`: removed the standalone top nav strip and integrated navigation into the report header; removed header helper copy while preserving existing content sections
- `outputs/options_html.py`: removed the standalone top nav strip, removed the supplemental explainer banner and header helper copy, and moved the pipeline bar below the header
- `outputs/html.py`: consolidated Macro Pulse into one stronger top summary block, removed the redundant header/banner pair, moved `Market Posture` and `What Matters Today` directly below the top block, and switched top metadata to aligned boxed cells
- `outputs/index_html.py`: removed the loose landing-page tagline/meta strip, removed driver text from the header area, integrated navigation into the main header, and converted the top summary into a compact boxed metadata grid

### What was preserved
- Report logic and data derivation — unchanged
- Scanner / scoring / event logic — unchanged
- Shared theme and deployment path — preserved
- Existing page roles and section content — preserved outside the scoped layout cleanup

### Verification
- `python3 -m py_compile outputs/shared.py outputs/html.py outputs/index_html.py outputs/options_html.py outputs/premarket_html.py` passed
- Searched renderers to confirm standalone top-nav calls and the removed helper copy are no longer used in the affected pages

### Files changed
- `outputs/shared.py`
- `outputs/premarket_html.py`
- `outputs/options_html.py`
- `outputs/html.py`
- `outputs/index_html.py`
- `docs/DEV_LOG.md`

---

## 2026-03-31 — Lean Pre-Market robustness pass

### What changed
- `outputs/premarket_html.py`: tightened fallback handling for the Daily Mission, Events, Overnight Narrative, and Trade Funnel sections so the page keeps rendering cleanly with partial or thin data
- `outputs/premarket_html.py`: added safe normalization helpers for missing regime, session, and driver values
- `outputs/premarket_html.py`: refined event annotation logic so `HIGH`, `MED`, and `LOW` impact rows always show a volatility note and trade implication
- `outputs/premarket_html.py`: upgraded the Trade Funnel to render all tiers independently with explicit empty-state behavior:
  - Tier 1 `Validated`
  - Tier 2 `Partially Qualified`
  - Tier 3 `Watchlist`
  - Tier 4 `Rejected`
- `outputs/premarket_html.py`: replaced the old compact off-radar line with a proper rejected tier carrying a brief reason
- `outputs/premarket_html.py`: added a derived 0–100 watchlist score display from the existing scanner raw score for lightweight comparability only
- `outputs/premarket_html.py`: made `build_premarket_html()` accept optional `events` input so the renderer can be exercised without a live calendar fetch
- `desktop/test_premarket_fixtures.py`: added five static fixture scenarios covering bullish calm, risk-off spike, major event day, no validated setups, and thin data

### What was preserved
- Report logic and scoring — unchanged
- Scanner pipeline and setup generation — unchanged
- Options Context embedding — unchanged
- Shared page shell and deployment path — unchanged

### Verification
- `python3 -m py_compile outputs/premarket_html.py desktop/test_premarket_fixtures.py` passed
- `python3 desktop/test_premarket_fixtures.py` passed

### Files changed
- `outputs/premarket_html.py`
- `desktop/test_premarket_fixtures.py`
- `docs/DEV_LOG.md`

---

## 2026-03-31 — Phase 5: rendering system unification

### What changed
- `outputs/shared.py`: expanded the shared rendering layer beyond nav/header/footer to include reusable UI primitives:
  - `card_block()`
  - `section_block()`
  - `info_chip()`
  - `stat_block()`
- `outputs/shared.py`: centralized more cross-page CSS for shared cards, chips, stat blocks, section headers, and banner-style CTA rows
- `outputs/shared.py`: extended `report_header()` with optional `note_text` so page role copy no longer needs page-local header variants
- `outputs/premarket_html.py`: migrated the page off standalone HTML scaffolding onto `page_shell()`, `nav_bar()`, `report_header()`, and `footer()`
- `outputs/options_html.py`: migrated the page off standalone HTML scaffolding onto the same shared shell and header/footer helpers, while preserving Chart.js script injection through `extra_head`
- `outputs/html.py`: refactored page sections to use shared helper components instead of page-local card/chip/stat wrappers

### Duplication removed
- Standalone full-document HTML wrappers in Pre-Market and Advanced Options
- Duplicated nav shell / page container / report header / footer ownership in page-local builders
- Repeated chip/stat/banner markup in Macro Pulse
- Repeated card/section wrapper markup patterns across report pages

### What was preserved
- Report logic and scoring — unchanged
- Data pipelines and fetch paths — unchanged
- Pages deployment path — unchanged
- Chart/script wiring for Advanced Options — unchanged
- Existing page-specific content structure where it remains distinct and useful

### Remaining inconsistencies
- Some page-specific content CSS still lives locally in `outputs/premarket_html.py` and `outputs/options_html.py` because the setup cards and chart-heavy drilldown layouts are still unique enough to justify local styling
- `outputs/index_html.py` still has some homepage-specific card styling, but it already uses the shared shell and does not duplicate full layout scaffolding

### Verification
- `python3 -m py_compile outputs/shared.py outputs/html.py outputs/premarket_html.py outputs/options_html.py outputs/index_html.py` passed

### Files changed
- `outputs/shared.py`
- `outputs/html.py`
- `outputs/premarket_html.py`
- `outputs/options_html.py`
- `docs/DEV_LOG.md`

---

## 2026-03-31 — Phase 4: product rationalization and navigation unification

### What changed
- `outputs/shared.py`: reordered primary shared navigation so `Pre-Market` now sits ahead of `Macro Pulse`, and relabeled `Options Sniper` to `Advanced Options`
- `outputs/shared.py`: added nav emphasis classes so `Pre-Market` reads as the primary destination and `Advanced Options` reads as a lower-emphasis secondary path
- `outputs/index_html.py`: reordered homepage cards to make `Pre-Market Report` the first and most prominent card, reframed `Macro Pulse` as context, and reframed `Advanced Options` as supplemental drilldown
- `outputs/index_html.py`: added a workflow line in the hero: `Macro Pulse → Pre-Market → Embedded Options Context`
- `outputs/html.py`: added explicit handoff copy and CTA from `Macro Pulse` into `Pre-Market`, clarifying Macro Pulse as the context/regime page rather than a competing execution page
- `outputs/premarket_html.py`: added a lightweight top workflow bar and execution-role copy so Pre-Market now presents itself as the flagship execution surface
- `outputs/options_html.py`: added shared-style navigation, renamed the page UI/title to `Advanced Options Drilldown`, added a contextual banner pointing users back to Pre-Market, and clarified the page as secondary analysis

### Why
After embedding Options Context into Pre-Market, the Pages experience still treated Macro Pulse, Pre-Market, and Options Sniper too evenly. Phase 4 tightened the suite into one product flow:
- Macro Pulse = context
- Pre-Market = flagship execution plan
- Advanced Options = optional drilldown

### What was preserved
- No report-generation logic was removed
- No standalone page was deleted
- Existing build/deploy paths remain intact
- CLI dashboard remains untouched
- Options Sniper functionality is preserved; only its position and labeling were demoted

### Verification
- `python3 -m py_compile outputs/shared.py outputs/index_html.py outputs/html.py outputs/premarket_html.py outputs/options_html.py` passed

### Files changed
- `outputs/shared.py`
- `outputs/index_html.py`
- `outputs/html.py`
- `outputs/premarket_html.py`
- `outputs/options_html.py`
- `docs/DEV_LOG.md`

---

## 2026-03-31 — Phase 3: Embedded options context in Pre-Market validated trades

### What changed
- `outputs/premarket_html.py`: replaced the validated-trade `Options Context` placeholder with a compact live section embedded at the bottom of each validated setup card
- `outputs/premarket_html.py`: reused existing `options.chain.analyze()` output when available to surface:
  - implied volatility
  - volume
  - open interest
  - spread width proxy (`spread_pct`)
  - liquidity tier
- `outputs/premarket_html.py`: added lightweight expression logic for validated trades only:
  - `Calls` / `Puts`
  - `Debit Call/Put Spread`
  - `Credit Put/Call Spread`
  - `Short` / `Medium` / `Longer` expiry band
- `outputs/premarket_html.py`: added 1–2 line interpretation layer for premium state and trade suitability
- `outputs/premarket_html.py`: changed options fetching to lazy-import inside `save()` so the page builder still renders if options dependencies are missing; unavailable data degrades to `Options data unavailable`

### Why
Phase 3 required a decision-focused options expression layer inside the existing Pre-Market validated trade cards, without reintroducing a separate standalone options workflow or adding chain tables.

### What was preserved
- Pre-Market page structure — unchanged outside the validated trade card bottom pane
- Watchlist card structure — unchanged
- `sniper/scanner.py` chart/setup logic — unchanged
- Standalone Options Sniper page — unchanged
- No fabricated options values; if chain data is unavailable, the pane explicitly says so

### Verification
- `python3 -m py_compile outputs/premarket_html.py` passed
- Stubbed HTML render validated the embedded pane layout and text flow without relying on live chain access
- Live options-chain verification was not completed in this environment because `yfinance` is not installed locally

### Files changed
- `outputs/premarket_html.py` — embedded options context layer
- `docs/DEV_LOG.md` — this entry

---

## 2026-03-31 — Phase 1: Macro Pulse UI + structure revamp

### What changed
- `outputs/html.py`: rebuilt the Macro Pulse HTML page on top of `outputs.shared.page_shell()`, `nav_bar()`, `report_header()`, and `footer()` so it now uses the same Tilix-style visual system as the newer Pages output
- `outputs/html.py`: replaced the old single-grid macro page with explicit sections for header context, macro dashboard, market posture, what-matters-today, incidents, and watchlist preview
- `outputs/html.py`: reused existing macro functions only for page content derivation:
  - `classify()` for regime
  - `drivers()` for primary / secondary drivers
  - `cross_asset_read()` for cross-asset summary
  - `detect()` for incidents
  - `route()` for watchlist preview tickers
  - `generate()` for short focus / posture text support
- `outputs/html.py`: added asset-level status badges and responsive card layout for DXY, 10Y, WTI, XAU, XAG, SPY, ES, QQQ, NQ, and VIX when those quotes are present
- `reports/output/macro_pulse.html`: regenerated locally with a controlled sample data map to verify structure and responsive card rendering without changing fetch logic

### Why
Macro Pulse was still using an older standalone HTML structure and theme. Phase 1 required aligning it with the newer shared Pages styling while keeping the existing build path and macro data model intact.

### What was preserved
- `macro/pulse.py` — unchanged
- CLI dashboard / terminal renderer — unchanged
- `outputs/shared.py` shared theme contract — reused, not replaced
- Fetching / regime / driver / incident logic — unchanged
- No new external data sources, no live browser refresh behavior, no build pipeline changes

### Limitations / deliberate omissions
- Key levels section was not added because current macro quote data only exposes `price`, `pct`, `change`, and `as_of`; there is no support / resistance / key level data for macro instruments in the existing Macro Pulse pipeline
- Watchlist preview uses existing focus routing output, not a new scanner pass; it intentionally stays lightweight and links the user to `premarket.html` for trade-level detail

### Files changed
- `outputs/html.py` — Macro Pulse HTML refactor
- `docs/DEV_LOG.md` — this entry

---

## 2026-03-29 — Data freshness clarity patch: prices as-of timestamp

### What changed
- `core/fetcher.py`: added `timezone` to import; `fetch_symbol()` now extracts `meta["regularMarketTime"]` (Unix timestamp) and converts it to `"%H:%M UTC"` string stored as `"as_of"` key in the returned dict; `None` if the field is absent
- `reports/options_sniper.py`: added `_as_of_raw` extraction after `macro_data` is ready; `data_as_of` string forwarded to report header line — now reads `Generated: ... | Market ref: ... | Prices as of HH:MM UTC | ... Session`
- `outputs/options_html.py`: same `_as_of_raw` / `data_as_of` extraction in `build_options_html()`; `report-meta` div updated with the new field
- `outputs/premarket_html.py`: identical changes to `options_html.py`

### Why
Dashboard showed no indication of when Yahoo last updated the displayed prices. `regularMarketTime` is already in the Yahoo v8 API response — no additional fetch needed. Surfacing it makes stale/previous-session data obvious without changing any price-fetching logic.

### What was preserved
- Price-fetching logic — unchanged (`fetch_symbol`, `fetch_label`, `fetch_all`)
- Scoring, guardrails, setup logic — unchanged
- Session classification — unchanged
- `as_of` is additive to the return dict; no existing callers break (they access `price`/`pct`/`change` by key)

### Files changed
- `core/fetcher.py` — 5-line diff (import timezone, extract market_time/as_of, add to return)
- `reports/options_sniper.py` — 3-line diff (extract data_as_of, extend header line)
- `outputs/options_html.py` — 3-line diff (extract data_as_of, extend report-meta)
- `outputs/premarket_html.py` — 3-line diff (same as options_html.py)

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
