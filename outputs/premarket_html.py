# ============================================================
# MACRO SUITE — Pre-Market HTML Dashboard
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone

from core.formatter import arrow, fmt_pct, fmt_price
from macro.incidents import detect
from macro.regime import classify, cross_asset_read, drivers
from macro.session import current_session
from outputs.shared import card_block, footer, nav_bar, page_shell, report_header, section_block
from reports.calendar import get_events, get_month_events

# ── Helpers ──────────────────────────────────────────────────


# ── Helpers ──────────────────────────────────────────────────

def _cls(pct: float) -> str:
    if pct > 0: return "up"
    if pct < 0: return "dn"
    return "flat"


def _fmt_change(change: float) -> str:
    sign = "+" if change >= 0 else ""
    if abs(change) >= 1000:
        return f"{sign}{change:,.0f}"
    return f"{sign}{change:.2f}"


def _regime_cls(regime: str) -> str:
    if regime == "RISK ON":  return "regime-on"
    if regime == "RISK OFF": return "regime-off"
    return "regime-mixed"


def _safe_regime(regime: str | None) -> str:
    value = (regime or "").strip().upper()
    return value if value in {"RISK ON", "RISK OFF", "MIXED"} else "NEUTRAL"


def _safe_session(session: str | None) -> str:
    value = (session or "").strip()
    return value if value else "Unknown session"


def _safe_driver(driver: str | None) -> str:
    value = (driver or "").strip()
    return value if value else "No dominant driver"


def _execution_plan(regime: str | None) -> str:
    plan_map = {
        "RISK ON": "Risk-on -> favor calls or long breakouts, size normally when structure is clean.",
        "RISK OFF": "Risk-off -> favor puts or defensive shorts, reduce size and respect failed bounces.",
        "MIXED": "Mixed regime -> stay selective, wait for confirmation, keep risk tight.",
    }
    return plan_map.get(_safe_regime(regime), "Neutral / Mixed - stay reactive")


def _setup_score_pct(setup) -> int:
    raw = max(0, min(int(getattr(setup, "score", 0) or 0), 6))
    return round((raw / 6) * 100)


def _rejected_reasons(setup, failures: list[str]) -> list[str]:
    reasons = list(failures)
    if getattr(setup, "grade", "") == "C":
        reasons.append("Chart quality below tradeable threshold")
    if getattr(setup, "setup_type", "") == "none":
        reasons.append("No clear setup structure")
    if getattr(setup, "bias", "") == "NEUTRAL":
        reasons.append("Directional bias is mixed / indecisive")
    deduped = []
    seen = set()
    for reason in reasons:
        if reason not in seen:
            deduped.append(reason)
            seen.add(reason)
    return deduped or ["Failed setup qualification"]


# ── Section builders ─────────────────────────────────────────

def _futures_cards(data_map: dict) -> str:
    futures = [("ES", "S&P 500 Fut"), ("NQ", "Nasdaq Fut"), ("RTY", "Russell Fut")]
    cards = []
    for label, name in futures:
        d = data_map.get(label)
        if not d:
            continue
        cls = _cls(d["pct"])
        cards.append(f"""
        <div class="fut-card">
            <div class="fut-name">{name}</div>
            <div class="fut-price">{fmt_price(d['price'])}</div>
            <div class="fut-change {cls}">{arrow(d['pct'])} {fmt_pct(d['pct'])}</div>
        </div>""")
    return "".join(cards)


def _macro_rows(data_map: dict) -> str:
    items = [
        ("DXY", "Dollar (DXY)"),
        ("10Y", "10Y Yield"),
        ("VIX", "VIX"),
        ("UJ",  "USD/JPY"),
        ("XAU", "Gold"),
        ("XAG", "Silver"),
        ("WTI", "WTI Oil"),
        ("BRT", "Brent Oil"),
        ("HYG", "HYG Credit"),
        ("BTC", "Bitcoin"),
        ("HG",  "Copper"),
    ]
    rows = []
    for label, name in items:
        d = data_map.get(label)
        if not d:
            continue
        cls = _cls(d["pct"])
        change     = d.get("change")
        change_html = f'<span class="row-change-dollar {cls}">{_fmt_change(change)}</span>' if change is not None else ""
        rows.append(f"""
        <tr>
            <td class="row-label">{name}</td>
            <td class="row-price">{fmt_price(d['price'])}</td>
            <td class="row-dollar">{change_html}</td>
            <td class="row-change {cls}">{arrow(d['pct'])} {fmt_pct(d['pct'])}</td>
        </tr>""")
    return "".join(rows)


def _calendar_rows(events: list[dict]) -> str:
    if not events:
        return '<tr><td colspan="4" class="no-events">No major events today</td></tr>'
    rows = []
    for e in events:
        impact = e.get("impact", "LOW")
        impact_cls = "impact-high" if impact == "HIGH" else ("impact-med" if impact == "MED" else "impact-low")
        url = e.get("url", "#")
        vol = _vol_note(e)
        trade = _trade_implication(e)
        rows.append(f"""
        <tr>
            <td class="ev-time">{e.get('time', '--:--')} UTC</td>
            <td><span class="impact-badge {impact_cls}">{impact}</span></td>
            <td class="ev-name">
                <a href="{url}" target="_blank" rel="noopener">{e.get('event', e.get('name', 'Unnamed event'))}</a>
                <div class="ev-vol-note">{vol}</div>
                <div class="ev-trade-note">{trade}</div>
            </td>
            <td class="ev-est">{e.get('consensus', '—')}</td>
        </tr>""")
    return "".join(rows)


def _primary_disqualifier(reasons: list[str]) -> str:
    """Single most important failure reason for trader-facing display."""
    checks = [
        ("regime",          "Conflicts with current macro regime"),
        ("R:R",             "R:R below 2:1 — risk not justified"),
        ("Chart grade",     "Chart not A-grade yet"),
        ("No clear chart",  "No clear setup structure"),
        ("liquidity",       "Options liquidity insufficient"),
    ]
    for keyword, label in checks:
        for r in reasons:
            if keyword.lower() in r.lower():
                return label
    return reasons[0] if reasons else "Failed guardrails"


def _structural_guardrails(setup, regime: str) -> list[str]:
    """
    Structural guardrail check applicable without options data.
    Mirrors the execution-level hard guardrails except for options liquidity,
    which requires the full sniper pipeline. Any setup failing here must not
    be ranked — it is demoted to the watchlist.
    """
    failures = []
    if setup.rr < 2.0:
        failures.append(f"R:R {setup.rr:.1f} — below 2:1 minimum")
    if setup.grade != "A":
        failures.append(f"Chart grade {setup.grade} — A required")
    if setup.setup_type == "none":
        failures.append("No clear chart structure")
    if (regime == "RISK ON"  and setup.bias == "SHORT") or \
       (regime == "RISK OFF" and setup.bias == "LONG"):
        failures.append(f"Direction conflicts with {regime}")
    return failures


def _alignment_label(alignment: str) -> str:
    if alignment == "bullish":
        return "Bullish stack — price > EMA9 > EMA21 > EMA50"
    if alignment == "bearish":
        return "Bearish stack — price < EMA9 < EMA21 < EMA50"
    return "Mixed / conflicted EMAs"


def _atr_interp(atr: float, price: float, support: float, resistance: float, bias: str) -> str:
    room = (resistance - price) if bias == "LONG" else (price - support)
    atr_pct = (atr / price) * 100
    if atr_pct < 1.0:
        return "Compressed — low volatility"
    if room >= atr * 1.5:
        return "Enough room to target"
    if room < atr * 0.5:
        return "Extended — most move may be in"
    return "Normal range"


def _confirms_note(s) -> str:
    t, b = s.setup_type, s.bias
    if b == "LONG":
        if t == "breakout":    return f"Hold above {s.resistance:.2f} on close"
        if t == "pullback":    return f"Hold EMA21 ({s.e21:.2f}) — RSI stays above 50"
        if t == "trend":       return f"Hold EMA9 ({s.e9:.2f}) on any pullback"
        if t == "reversal":    return f"Green candle above EMA9 ({s.e9:.2f}) after bounce"
        return f"Price stays above EMA9 ({s.e9:.2f})"
    if b == "SHORT":
        if t == "breakdown":        return f"Fail to reclaim support ({s.support:.2f})"
        if t == "trend_rejection":  return f"Rejection at EMA9 ({s.e9:.2f}) holds — RSI fading"
        if t == "failed_breakout":  return f"Unable to reclaim {s.resistance:.2f} — selling continues"
        return f"Price stays below EMA9 ({s.e9:.2f})"
    return "Wait for directional confirmation"


def _avoid_if_top(s) -> str:
    if s.bias == "LONG":
        return f"Opening gap > ATR, or price loses EMA21 ({s.e21:.2f})"
    if s.bias == "SHORT":
        return f"Gap up at open, or price reclaims EMA9 ({s.e9:.2f})"
    return "Structure breaks before entry"


def _wl_look_for(s) -> str:
    t, b = s.setup_type, s.bias
    if t == "breakout"        and b == "LONG":  return f"Break and close above {s.resistance:.2f}"
    if t == "pullback"        and b == "LONG":  return f"Dip to EMA9 ({s.e9:.2f})–EMA21 ({s.e21:.2f}) and bounce"
    if t == "trend"           and b == "LONG":  return f"Hold EMA9 ({s.e9:.2f}) and resume trend"
    if t == "reversal"        and b == "LONG":  return f"Green candle above EMA9 ({s.e9:.2f}) from oversold"
    if t == "breakdown"       and b == "SHORT": return f"Lose and fail to reclaim support ({s.support:.2f})"
    if t == "trend_rejection" and b == "SHORT": return f"Rejection at EMA9 ({s.e9:.2f}) — fade the bounce"
    if t == "failed_breakout" and b == "SHORT": return f"Fail to hold above {s.resistance:.2f} — confirm follow-through"
    return "Wait for directional break and confirmation"


def _wl_upgrades(failures: list[str], s) -> str:
    upgrades = []
    for f in failures:
        if "R:R" in f:
            upgrades.append(f"Pullback to EMA21 ({s.e21:.2f}) improves R:R")
        elif "grade" in f.lower() or "chart" in f.lower():
            upgrades.append("One more confirming candle")
        elif "regime" in f.lower():
            upgrades.append("Wait for regime shift")
        elif "structure" in f.lower():
            upgrades.append("Wait for clean setup to form")
    return " / ".join(upgrades) if upgrades else "Improve setup quality across dimensions"


def _wl_avoid(s) -> str:
    if s.bias == "LONG":
        return f"Loses EMA21 ({s.e21:.2f}) or breaks support ({s.support:.2f})"
    if s.bias == "SHORT":
        return f"Reclaims EMA9 ({s.e9:.2f}) or breaks above resistance ({s.resistance:.2f})"
    return "Structure invalidates before entry"


def _vol_note(event: dict) -> str:
    """Derive volatility expectation from event name and impact."""
    name   = (event.get("event") or event.get("name") or "").upper()
    impact = event.get("impact", "LOW")
    if impact == "HIGH":
        keywords = {
            "CPI":        "Inflation print — sharp DXY and rate-sensitive reaction expected",
            "PCE":        "Fed's preferred inflation gauge — rate and equity sensitivity",
            "PPI":        "Producer prices — precursor to CPI; high directional risk",
            "FOMC":       "Fed decision — potentially the largest mover of the session",
            "POWELL":     "Fed commentary — watch for policy shift signals",
            "NFP":        "Jobs report — broad market volatility across all asset classes",
            "EMPLOYMENT": "Labor data — rate and equity sensitivity",
            "NONFARM":    "Jobs report — broad market volatility across all asset classes",
            "GDP":        "Growth data — risk-on / risk-off tone setter",
            "PMI":        "Activity data — moderate to high cross-asset impact",
            "RETAIL":     "Consumer spending — moderate equity and rate impact",
            "HOUSING":    "Rate-sensitive sectors at risk",
            "INFLATION":  "Inflation data — DXY and bond market reaction likely",
        }
        for key, note in keywords.items():
            if key in name:
                return note
        return "High-impact release — expect elevated intraday volatility"
    if impact == "MED":
        return "Expect moderate volatility"
    return "Minimal impact expected"


def _trade_implication(event: dict) -> str:
    """Derive trade implication from event — conservative, no fabrication."""
    impact = event.get("impact", "LOW")
    name   = (event.get("event") or event.get("name") or "").upper()
    if impact == "HIGH":
        return "Avoid new positions within 30 min of release — let price react first"
    if impact == "MED":
        return "Expect moderate volatility"
    if "PMI"     in name: return "May shift intraday directional bias if significantly off consensus"
    if "RETAIL"  in name: return "Consumer-facing sectors may react"
    if "HOUSING" in name: return "Rate-sensitive sectors at risk"
    return "Minimal impact expected"


def _overnight_narrative(data_map: dict, regime: str, primary: str, secondary: str) -> str:
    """Generate structured overnight commentary from existing pipeline data."""
    futures_items = [("ES", "S&P futures"), ("NQ", "Nasdaq futures"), ("RTY", "Russell")]
    best_label, best_name, best_pct = None, None, 0.0
    for label, name in futures_items:
        d = data_map.get(label)
        if d and abs(d["pct"]) > abs(best_pct):
            best_pct  = d["pct"]
            best_label, best_name = label, name

    safe_primary = _safe_driver(primary)
    safe_secondary = _safe_driver(secondary)
    safe_regime = _safe_regime(regime)
    if not best_label or abs(best_pct) < 0.05:
        return "Overnight action mixed, no clear directional signal. No dominant driver is firmly in control. Stay reactive into the open."

    what = f"{best_name} {'led higher' if best_pct > 0 else 'led lower'} by {abs(best_pct):.1f}% overnight."
    if safe_secondary != safe_primary:
        why = f"Primary driver is {safe_primary.lower()}, with {safe_secondary.lower()} also influencing tone."
    else:
        why = f"Primary driver is {safe_primary.lower()}."

    impl_map = {
        "RISK ON": "Implication for the open: continuation is possible, but only if breadth confirms.",
        "RISK OFF": "Implication for the open: defensive positioning matters more than chasing longs.",
        "MIXED": "Implication for the open: treat the first 30 minutes as a direction test.",
        "NEUTRAL": "Implication for the open: stay reactive until price picks a side.",
    }
    vix_d = data_map.get("VIX")
    impl = "VIX spiking — hedge exposure and reduce size." if (vix_d and vix_d["pct"] > 5) \
           else impl_map.get(safe_regime, impl_map["NEUTRAL"])

    return f"{what} {why} {impl}"


def _daily_mission_html(regime: str, session: str, primary: str, secondary: str) -> str:
    """Render the at-a-glance daily context strip below the report header."""
    safe_regime = _safe_regime(regime)
    safe_session = _safe_session(session)
    safe_primary = _safe_driver(primary)
    safe_secondary = _safe_driver(secondary)
    regime_cls = _regime_cls(safe_regime)
    plan = _execution_plan(safe_regime)
    return f"""
    <div class="daily-mission">
        <div class="mission-row">
            <span class="mission-label">Regime</span>
            <span class="mission-value {regime_cls}">{safe_regime}</span>
            <span class="mission-sep">·</span>
            <span class="mission-label">Session</span>
            <span class="mission-value">{safe_session}</span>
            <span class="mission-sep">·</span>
            <span class="mission-label">Primary driver</span>
            <span class="mission-value">{safe_primary}</span>
            <span class="mission-sep">·</span>
            <span class="mission-label">Secondary driver</span>
            <span class="mission-value">{safe_secondary}</span>
        </div>
        <div class="mission-plan">{plan}</div>
    </div>"""


def _partition_setups(setups: list, regime: str) -> tuple[list, list[tuple], list[tuple], list[tuple]]:
    """
    Four-tier partition:
      validated — all structural guardrails pass; actionable
      partial   — exactly 1 guardrail fails; specific upgrade trigger exists
      watchlist — 2+ guardrail failures; broader monitoring
      rejected  — failed qualification; not actionable
    """
    validated = []
    partial   = []
    watchlist = []
    rejected  = []

    for s in setups:
        failures = _structural_guardrails(s, regime)
        if not failures:
            validated.append(s)
        elif s.grade in ("A", "B") and s.setup_type != "none":
            if len(failures) == 1:
                partial.append((s, failures))
            else:
                watchlist.append((s, failures))
        else:
            rejected.append((s, _rejected_reasons(s, failures)))

    return validated, partial, watchlist, rejected


def _expiry_band(s, opts) -> str:
    atr_pct = (s.atr / s.price) * 100 if getattr(s, "atr", None) and s.price else 0.0
    if opts and opts.dte <= 21:
        return "Short"
    if s.setup_type in ("breakout", "breakdown", "trend", "trend_rejection") and (s.rr >= 3.0 or atr_pct >= 2.0):
        return "Short"
    if atr_pct < 1.0 or s.setup_type in ("pullback", "reversal", "failed_breakout"):
        return "Longer"
    return "Medium"


def _strategy_suggestion(s, opts) -> tuple[str, str]:
    side = "Calls" if s.bias == "LONG" else "Puts"
    debit = "Debit Call Spread" if s.bias == "LONG" else "Debit Put Spread"
    credit = "Credit Put Spread" if s.bias == "LONG" else "Credit Call Spread"
    atr_pct = (s.atr / s.price) * 100 if getattr(s, "atr", None) and s.price else 0.0
    iv = getattr(opts, "iv", 0.0) if opts else 0.0
    liquidity = getattr(opts, "liquidity", "") if opts else ""

    if iv >= 0.45 and (atr_pct < 1.0 or s.rr < 2.5):
        return credit, "IV rich and expected move is tighter — defined-risk premium selling fits better"
    if iv >= 0.45 or liquidity == "Low":
        return debit, "IV elevated or fills may be thin — cap premium outlay with a spread"
    if atr_pct >= 2.0 or s.rr >= 3.0:
        return side, "Cleaner directional setup with enough room to justify outright exposure"
    return debit, "Moderate move profile — defined-risk directional spread is cleaner than naked premium"


def _premium_view(opts) -> str:
    if not opts:
        return "Premium view unavailable"
    if opts.iv >= 0.45:
        return f"Premium rich — IV {opts.iv_pct} favors defined-risk structures"
    if opts.iv <= 0.25:
        return f"Premium relatively cheap — IV {opts.iv_pct} is reasonable for directional buying"
    return f"Premium moderate — IV {opts.iv_pct} is not stretched"


def _suitability_view(s, expression: str) -> str:
    atr_pct = (s.atr / s.price) * 100 if getattr(s, "atr", None) and s.price else 0.0
    if "Credit" in expression:
        return "Range-to-grind profile — premium-selling structure suits slower follow-through"
    if atr_pct >= 2.0 or s.rr >= 3.0:
        return "Directional profile — enough range for a cleaner outright move"
    return "Directional but contained — spread keeps the expression compact"


def _options_context_html(s, opts) -> str:
    if not opts:
        return """
                <div class="setup-pane options-context">
                    <div class="pane-label">Options Context</div>
                    <div class="options-empty">Options data unavailable</div>
                </div>"""

    expression, why = _strategy_suggestion(s, opts)
    expiry_band = _expiry_band(s, opts)
    premium_view = _premium_view(opts)
    suitability = _suitability_view(s, expression)
    spread_proxy = f"{opts.spread_pct * 100:.1f}%"
    liq_cls = "liq-high" if opts.liquidity == "High" else ("liq-med" if opts.liquidity == "Medium" else "liq-low")

    return f"""
                <div class="setup-pane options-context">
                    <div class="pane-label">Options Context</div>
                    <div class="options-row">
                        <span class="options-badge bias-{s.bias.lower()}">{expression}</span>
                        <span class="options-badge expiry-{expiry_band.lower()}">{expiry_band} expiry</span>
                        <span class="liq-badge {liq_cls}">{opts.liquidity} liquidity</span>
                    </div>
                    <div class="options-metrics">
                        <span class="options-kv"><span class="options-k">IV</span><span class="options-v">{opts.iv_pct}</span></span>
                        <span class="options-kv"><span class="options-k">Vol</span><span class="options-v">{opts.volume:,}</span></span>
                        <span class="options-kv"><span class="options-k">OI</span><span class="options-v">{opts.open_interest:,}</span></span>
                        <span class="options-kv"><span class="options-k">Spread</span><span class="options-v">{spread_proxy}</span></span>
                    </div>
                    <div class="options-contract">{opts.contract_note} &nbsp;·&nbsp; Bid/Ask {opts.bid}/{opts.ask}</div>
                    <div class="options-note">{why}</div>
                    <div class="options-note">{premium_view}</div>
                    <div class="options-note">{suitability}</div>
                </div>"""


def _setup_cards(setups: list, regime: str, options_map: dict[str, object] | None = None) -> str:
    """
    Four-tier presentation:
      1. Validated Top Trades      — all structural guardrails pass; actionable
      2. Partially Qualified       — exactly 1 guardrail blocking; specific trigger to upgrade
      3. Watchlist Setups          — 2+ guardrail issues; broader monitoring
      4. Rejected                  — failed qualification; compact reason only

    No setup may appear in tier 1 unless it passes every structural guardrail.
    Each tier is in its own block; only tier 1 uses the card grid.
    """
    options_map = options_map or {}
    validated, partial, watchlist, rejected = _partition_setups(setups, regime)

    bias_cls_map  = {"LONG": "bias-long", "SHORT": "bias-short"}
    grade_cls_map = {"A": "grade-a", "B": "grade-b", "C": "grade-c"}
    html = ""

    # ── Tier 1: Validated Top Trades (card grid) ──────────────
    html += '<div class="setups-grid">'
    if not validated:
        html += '<div class="no-setups">No validated setups today</div>'
    else:
        for s in validated[:3]:
            bias_cls  = bias_cls_map.get(s.bias, "bias-neutral")
            grade_cls = grade_cls_map.get(s.grade, "")
            atr = getattr(s, "atr", None)
            atr_pane = ""
            if atr:
                atr_pct  = (atr / s.price) * 100
                interp   = _atr_interp(atr, s.price, s.support, s.resistance, s.bias)
                atr_pane = f"""
                <div class="setup-pane">
                    <div class="pane-label">Volatility</div>
                    <div class="pane-row">
                        <div class="pane-kv"><span class="pane-k">ATR</span><span class="pane-v">{fmt_price(atr)}</span></div>
                        <div class="pane-kv"><span class="pane-k">ATR %</span><span class="pane-v">{atr_pct:.1f}%</span></div>
                        <span class="pane-interp">{interp}</span>
                    </div>
                </div>"""
            html += f"""
            <div class="setup-card">
                <div class="setup-header">
                    <span class="setup-ticker">{s.ticker}</span>
                    <span class="setup-bias {bias_cls}">{s.bias}</span>
                    <span class="setup-grade {grade_cls}">{s.grade}</span>
                    <span class="setup-type-chip">{s.setup_type.replace("_", " ")}</span>
                    <span class="setup-conf">conf {s.confidence}/10</span>
                </div>

                <div class="setup-pane">
                    <div class="pane-label">Structure</div>
                    <div class="pane-row">
                        <div class="pane-kv"><span class="pane-k">Price</span><span class="pane-v">{s.price}</span></div>
                        <div class="pane-kv"><span class="pane-k">Support</span><span class="pane-v">{s.support}</span></div>
                        <div class="pane-kv"><span class="pane-k">Resistance</span><span class="pane-v">{s.resistance}</span></div>
                    </div>
                </div>

                <div class="setup-pane">
                    <div class="pane-label">Moving Averages</div>
                    <div class="pane-row">
                        <div class="pane-kv"><span class="pane-k">EMA 9</span><span class="pane-v">{s.e9}</span></div>
                        <div class="pane-kv"><span class="pane-k">EMA 21</span><span class="pane-v">{s.e21}</span></div>
                        <div class="pane-kv"><span class="pane-k">EMA 50</span><span class="pane-v">{s.e50}</span></div>
                    </div>
                    <div class="pane-note">{_alignment_label(s.alignment)}</div>
                </div>

                {atr_pane}

                <div class="setup-pane exec-pane">
                    <div class="pane-label">Execution</div>
                    <div class="exec-row"><span class="exec-k">Entry</span><span class="exec-v entry-note">{s.entry_note}</span></div>
                    <div class="exec-row"><span class="exec-k">Stop</span><span class="exec-v">{s.invalidation}</span></div>
                    <div class="exec-row"><span class="exec-k">R:R</span><span class="exec-v rr-val">{s.rr:.1f}:1</span></div>
                    <div class="exec-row"><span class="exec-k">RSI</span><span class="exec-v">{s.rsi_val}</span></div>
                    <div class="exec-row"><span class="exec-k">Confirms</span><span class="exec-v">{_confirms_note(s)}</span></div>
                    <div class="exec-row"><span class="exec-k">Avoid if</span><span class="exec-v avoid-note">{_avoid_if_top(s)}</span></div>
                </div>

                {_options_context_html(s, options_map.get(s.ticker))}
            </div>"""
    html += '</div>'  # close setups-grid

    # ── Tier 2: Partially Qualified — one trigger away ─────────
    if partial:
        html += """
        <div class="partial-section-label">Partially Qualified — One Trigger Away</div>
        <div class="partial-section-note">Structure is valid and one guardrail is blocking. Know the exact condition required to trade.</div>"""
        for s, failures in partial[:4]:
            bias_cls     = bias_cls_map.get(s.bias, "bias-neutral")
            disqualifier = _primary_disqualifier(failures)
            working      = _confirms_note(s)
            trigger      = _wl_upgrades(failures, s)
            atr          = getattr(s, "atr", None)
            atr_kv       = f'<span class="wl-kv"><span class="wl-k">ATR</span><span class="wl-v">{fmt_price(atr)}</span></span>' if atr else ""
            html += f"""
            <div class="partial-card {bias_cls}">
                <div class="partial-header">
                    <span class="watchlist-ticker">{s.ticker}</span>
                    <span class="setup-bias {bias_cls}" style="font-size:0.72rem;padding:1px 7px">{s.bias}</span>
                    <span class="watchlist-grade grade-{s.grade.lower()}">{s.grade}</span>
                    <span class="watchlist-setup-type">{s.setup_type.replace("_", " ")}</span>
                    <span class="partial-rr">R:R {s.rr:.1f}:1</span>
                </div>
                <div class="partial-kv-row">
                    <span class="wl-kv"><span class="wl-k">Price</span><span class="wl-v">{s.price}</span></span>
                    <span class="wl-kv"><span class="wl-k">Support</span><span class="wl-v">{s.support}</span></span>
                    <span class="wl-kv"><span class="wl-k">Resistance</span><span class="wl-v">{s.resistance}</span></span>
                    {atr_kv}
                </div>
                <div class="partial-working">{working}</div>
                <div class="partial-missing">{disqualifier}</div>
                <div class="partial-trigger">{trigger}</div>
            </div>"""

    # ── Tier 3: Watchlist — Broader Monitoring ─────────────────
    if watchlist:
        html += """
        <div class="watchlist-label">Watchlist Setups — Good Structure, Not Trade-Ready</div>
        <div class="watchlist-note">Multiple guardrails blocking. Monitor only — do not force entry.</div>"""
        for s, reasons in watchlist[:5]:
            bias_cls     = bias_cls_map.get(s.bias, "bias-neutral")
            disqualifier = _primary_disqualifier(reasons)
            atr          = getattr(s, "atr", None)
            atr_kv       = f'<span class="wl-kv"><span class="wl-k">ATR</span><span class="wl-v">{fmt_price(atr)}</span></span>' if atr else ""
            html += f"""
            <div class="watchlist-card {bias_cls}">
                <div class="watchlist-row">
                    <span class="watchlist-ticker">{s.ticker}</span>
                    <span class="setup-bias {bias_cls}" style="font-size:0.72rem;padding:1px 7px">{s.bias}</span>
                    <span class="watchlist-grade grade-{s.grade.lower()}">{s.grade}</span>
                    <span class="watchlist-setup-type">{s.setup_type.replace("_", " ")}</span>
                    <span class="watchlist-score">Score {_setup_score_pct(s)}</span>
                </div>
                <div class="watchlist-blocker">Why not trading: {disqualifier}</div>
                <div class="watchlist-context">
                    <div class="wl-kv-row">
                        <span class="wl-kv"><span class="wl-k">Price</span><span class="wl-v">{s.price}</span></span>
                        <span class="wl-kv"><span class="wl-k">Support</span><span class="wl-v">{s.support}</span></span>
                        <span class="wl-kv"><span class="wl-k">Resistance</span><span class="wl-v">{s.resistance}</span></span>
                        <span class="wl-kv"><span class="wl-k">R:R</span><span class="wl-v">{s.rr:.1f}:1</span></span>
                        {atr_kv}
                    </div>
                    <div class="wl-alignment">EMA {s.alignment.title()} · EMA9 {s.e9} · EMA21 {s.e21} · RSI {s.rsi_val}</div>
                    <div class="wl-look-for">{_wl_look_for(s)}</div>
                    <div class="wl-upgrades">{_wl_upgrades(reasons, s)}</div>
                    <div class="wl-avoid">{_wl_avoid(s)}</div>
                </div>
            </div>"""
    else:
        html += """
        <div class="watchlist-label">Watchlist Setups — Good Structure, Not Trade-Ready</div>
        <div class="watchlist-note">No watchlist candidates</div>"""

    # ── Tier 4: Rejected ──────────────────────────────────────
    if rejected:
        html += """
        <div class="rejected-label">Rejected — Failed Qualification</div>
        <div class="rejected-note">Not actionable today. Keep the reason short and explicit.</div>"""
        for s, reasons in rejected[:6]:
            brief = reasons[0] if reasons else "Failed qualification"
            html += f"""
            <div class="rejected-card">
                <div class="rejected-row">
                    <span class="watchlist-ticker">{s.ticker}</span>
                    <span class="watchlist-grade grade-{s.grade.lower()}">{s.grade}</span>
                    <span class="watchlist-setup-type">{s.setup_type.replace("_", " ")}</span>
                </div>
                <div class="rejected-reason">{brief}</div>
            </div>"""

    return html


def _upcoming_rows(events: list[dict]) -> str:
    if not events:
        return '<tr><td colspan="4" class="no-events">No major events remaining this month</td></tr>'
    rows = []
    current_date = None
    for e in events:
        d = e.get("date", "")
        if d != current_date:
            current_date = d
            try:
                from datetime import datetime as _dt
                label = _dt.strptime(d, "%Y-%m-%d").strftime("%a  %b %d")
            except Exception:
                label = d
            rows.append(f'<tr><td colspan="4" class="ev-date-header">{label}</td></tr>')
        url = e.get("url", "#")
        rows.append(f"""
        <tr>
            <td class="ev-time">{e['time']} UTC</td>
            <td><span class="impact-badge impact-high">HIGH</span></td>
            <td class="ev-name"><a href="{url}" target="_blank" rel="noopener">{e['event']}</a></td>
            <td class="ev-est">{e['consensus']}</td>
        </tr>""")
    return "".join(rows)


def _sector_rows(data_map: dict, extra: dict) -> str:
    combined = {**data_map, **extra}
    sections = [
        ("Metals",   ["XAU", "XAG", "GDX"]),
        ("Oil",      ["WTI", "BRT", "XLE"]),
        ("Equities", ["SPY", "QQQ", "IWM"]),
        ("Credit",   ["HYG", "BTC"]),
    ]
    rows = []
    for name, labels in sections:
        cells = []
        for label in labels:
            d = combined.get(label)
            if d:
                cls = _cls(d["pct"])
                cells.append(f'<span class="sector-item {cls}">{label} {arrow(d["pct"])} {fmt_pct(d["pct"])}</span>')
        if cells:
            rows.append(f"""
        <tr>
            <td class="sector-name">{name}</td>
            <td class="sector-cells">{"".join(cells)}</td>
        </tr>""")
    return "".join(rows)


# ── Stylesheet ───────────────────────────────────────────────

_STYLE = """
    /* Futures */
    .futures-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .fut-card {
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 12px; padding: 14px; text-align: center;
    }
    .fut-name  { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
    .fut-price { font-size: 1.3rem; font-weight: 700; margin-bottom: 4px; }
    .fut-change { font-size: 0.95rem; font-weight: 600; }

    /* Macro table */
    .macro-table { width: 100%; border-collapse: collapse; }
    .macro-table tr { border-bottom: 1px solid rgba(55,65,81,0.5); }
    .macro-table tr:last-child { border-bottom: none; }
    .row-label  { color: var(--muted); padding: 7px 0; width: 38%; }
    .row-price  { font-weight: 600; padding: 7px 8px; }
    .row-dollar { padding: 7px 6px; font-size: 0.85rem; }
    .row-change { font-weight: 600; padding: 7px 0; text-align: right; }

    /* Calendar */
    .cal-table { width: 100%; border-collapse: collapse; }
    .cal-table tr { border-bottom: 1px solid rgba(55,65,81,0.5); }
    .cal-table tr:last-child { border-bottom: none; }
    .ev-time  { color: var(--muted); padding: 7px 12px 7px 0; white-space: nowrap; width: 110px; }
    .ev-name  { padding: 7px 8px; }
    .ev-est   { color: var(--muted); padding: 7px 0; text-align: right; font-size: 0.85rem; }
    .impact-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; }
    .impact-high { background: rgba(224,108,117,0.2); color: #e89099; }
    .impact-med  { background: rgba(97,175,239,0.15); color: #93c5fd; }
    .impact-low  { background: rgba(139,147,166,0.12); color: #a3a8b4; }
    .no-events   { color: var(--muted); padding: 12px 0; text-align: center; }
    .ev-date-header { background: rgba(30,58,95,0.4); color: var(--muted);
                      font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                      letter-spacing: 0.07em; padding: 6px 4px; }
    .ev-name a  { color: var(--text); text-decoration: none; }
    .ev-name a:hover { color: var(--blue); text-decoration: underline; }

    /* Setups */
    .setups-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }
    .setup-card {
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 12px; padding: 14px;
    }
    .setup-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    .setup-ticker { font-size: 1.1rem; font-weight: 700; }
    .setup-bias, .setup-grade {
        padding: 2px 10px; border-radius: 999px;
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;
    }
    .bias-long    { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .bias-short   { background: rgba(224,108,117,0.15); color: #e89099; }
    .bias-neutral { background: rgba(229,192,123,0.15); color: #ecd09a; }
    .grade-a { background: rgba(152,195,121,0.15); color: #a8d69e; }
    .grade-b { background: rgba(229,192,123,0.15); color: #ecd09a; }
    .grade-c { background: rgba(139,147,166,0.15); color: #a3a8b4; }

    /* ── Watchlist — visually and semantically distinct from validated trades ── */
    .watchlist-label {
        margin-top: 20px; padding: 6px 0 2px;
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: #6b7280;
        border-top: 1px dashed rgba(75,85,99,0.4);
    }
    .watchlist-note {
        font-size: 0.75rem; color: #6b7280; margin-bottom: 8px; font-style: italic;
    }
    .watchlist-card {
        background: var(--surface); border: 1px solid var(--border);
        border-left-width: 3px; border-radius: 6px;
        padding: 8px 12px; margin-bottom: 5px;
    }
    .watchlist-card.bias-long  { border-left-color: var(--green); }
    .watchlist-card.bias-short { border-left-color: var(--red);   }
    .watchlist-card.bias-long  .watchlist-ticker { color: var(--green); }
    .watchlist-card.bias-short .watchlist-ticker { color: var(--red);   }
    .watchlist-row { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }
    .watchlist-ticker { font-weight: 700; font-size: 0.88rem; color: var(--muted); }
    .watchlist-grade  { font-size: 0.72rem; margin-left: auto; padding: 1px 7px;
                        border-radius: 4px; }
    .watchlist-score {
        font-size: 0.68rem; color: var(--muted);
        padding: 1px 6px; border-radius: 4px;
        border: 1px solid rgba(55,65,81,0.4);
    }
    .watchlist-blocker { font-size: 0.75rem; color: var(--muted); }
    .watchlist-blocker::before { content: "↳ "; color: var(--border); }
    .setup-row { display: flex; gap: 16px; margin-bottom: 6px; }
    .setup-stat { font-size: 0.85rem; color: var(--muted); }
    .setup-stat strong { color: var(--text); }
    .setup-levels { font-size: 0.82rem; color: var(--muted); margin-bottom: 8px; }
    .setup-entry { font-size: 0.88rem; color: var(--blue); border-top: 1px solid var(--border); padding-top: 8px; }
    .skip-list { color: var(--muted); font-size: 0.85rem; margin-top: 8px; }
    .no-setups { color: var(--muted); text-align: center; padding: 20px; }
    .regime-note {
        padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;
        font-size: 0.88rem; font-weight: 600;
        background: rgba(224,108,117,0.08); border: 1px solid rgba(224,108,117,0.2); color: #e89099;
    }
    .regime-note.on   { background: rgba(152,195,121,0.08); border-color: rgba(152,195,121,0.2); color: #a8d69e; }
    .regime-note.mixed{ background: rgba(229,192,123,0.08); border-color: rgba(229,192,123,0.2); color: #ecd09a; }

    /* Incidents */
    .incident-box {
        background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25);
        border-radius: 10px; padding: 10px 14px; margin-bottom: 12px;
    }
    .incident-item { color: #fca5a5; font-size: 0.88rem; margin: 2px 0; }

    /* Sector */
    .sector-table { width: 100%; border-collapse: collapse; }
    .sector-table tr { border-bottom: 1px solid rgba(30,58,95,0.5); }
    .sector-table tr:last-child { border-bottom: none; }
    .sector-name  { color: var(--muted); padding: 8px 12px 8px 0; width: 90px; font-weight: 600; }
    .sector-cells { padding: 8px 0; display: flex; flex-wrap: wrap; gap: 12px; }
    .sector-item  { font-size: 0.88rem; font-weight: 600; }

    /* Summary box */
    .summary-box {
        background: rgba(255,255,255,0.03); border: 1px solid var(--border);
        border-radius: 10px; padding: 12px 14px; margin-top: 12px;
        color: var(--muted); font-size: 0.9rem;
    }

    /* Colors */
    .up   { color: var(--green); }
    .dn   { color: var(--red); }
    .flat { color: var(--yellow); }

    /* ── Setup type chip / confidence ─────────────────────── */
    .setup-type-chip {
        font-size: 0.65rem; padding: 2px 7px; border-radius: 3px;
        background: rgba(97,175,239,0.1); color: var(--blue);
        text-transform: capitalize; letter-spacing: 0.03em;
    }
    .setup-conf { margin-left: auto; font-size: 0.7rem; color: var(--muted); }

    /* ── Expanded setup card panes ──────────────────────── */
    .setup-pane {
        border-top: 1px solid var(--border);
        padding-top: 8px; margin-top: 8px;
    }
    .pane-label {
        font-size: 0.63rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: var(--muted); margin-bottom: 6px;
    }
    .pane-row {
        display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: flex-end;
    }
    .pane-kv { display: flex; flex-direction: column; gap: 1px; }
    .pane-k  { font-size: 0.63rem; color: var(--muted); }
    .pane-v  { font-size: 0.85rem; font-weight: 600; color: var(--text); }
    .pane-note  { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
    .pane-interp { font-size: 0.75rem; color: var(--yellow); }

    /* ── Execution pane rows ────────────────────────────── */
    .exec-pane .exec-row {
        display: flex; gap: 8px; font-size: 0.8rem;
        margin-bottom: 3px; align-items: flex-start;
    }
    .exec-k    { color: var(--muted); min-width: 68px; flex-shrink: 0; font-size: 0.73rem; }
    .exec-v    { color: var(--text); }
    .entry-note { color: var(--blue); }
    .rr-val    { color: var(--green); font-weight: 700; }
    .avoid-note { color: var(--muted); }

    /* ── Options context pane ───────────────────────────── */
    .options-context { border-top: 1px dashed rgba(55,65,81,0.5); }
    .options-row {
        display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;
    }
    .options-badge {
        padding: 2px 8px; border-radius: 999px;
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.05em;
        border: 1px solid rgba(55,65,81,0.55);
        background: rgba(255,255,255,0.03);
    }
    .expiry-short  { color: var(--green); }
    .expiry-medium { color: var(--blue); }
    .expiry-longer { color: var(--yellow); }
    .options-metrics {
        display: flex; flex-wrap: wrap; gap: 6px 14px; margin-bottom: 6px;
    }
    .options-kv { display: flex; gap: 4px; align-items: center; font-size: 0.76rem; }
    .options-k  { color: var(--muted); }
    .options-v  { color: var(--text); font-weight: 700; }
    .options-contract {
        font-size: 0.76rem; color: var(--muted); margin-bottom: 5px;
    }
    .options-note {
        font-size: 0.76rem; color: var(--text); margin-bottom: 2px;
    }
    .options-empty {
        font-size: 0.74rem; color: #6b7280; font-style: italic;
    }

    /* ── Watchlist expanded context ─────────────────────── */
    .watchlist-setup-type {
        font-size: 0.63rem; padding: 1px 5px; border-radius: 3px;
        background: rgba(97,175,239,0.08); color: var(--muted);
        text-transform: capitalize;
    }
    .watchlist-context {
        margin-top: 6px; padding-top: 6px;
        border-top: 1px solid rgba(55,65,81,0.35);
    }
    .wl-kv-row { display: flex; flex-wrap: wrap; gap: 5px 14px; margin-bottom: 5px; }
    .wl-kv  { display: flex; gap: 4px; font-size: 0.75rem; align-items: center; }
    .wl-k   { color: var(--muted); }
    .wl-v   { font-weight: 600; }
    .wl-alignment { font-size: 0.72rem; color: #6b7280; margin-bottom: 5px; }
    .wl-look-for  { font-size: 0.78rem; color: var(--text); margin-bottom: 3px; }
    .wl-look-for::before  { content: "Look for: "; color: var(--muted); }
    .wl-upgrades  { font-size: 0.73rem; color: var(--green); margin-bottom: 2px; }
    .wl-upgrades::before  { content: "Upgrades if: "; color: var(--muted); font-style: italic; }
    .wl-avoid     { font-size: 0.73rem; color: var(--red); }
    .wl-avoid::before     { content: "Avoid if: "; color: var(--muted); font-style: italic; }

    /* Daily mission strip */
    .daily-mission {
        background: rgba(255,255,255,0.02); border: 1px solid var(--border);
        border-left: 3px solid var(--blue); border-radius: 8px;
        padding: 12px 16px; margin: 0 0 16px;
    }
    .mission-row {
        display: flex; align-items: center; flex-wrap: wrap; gap: 8px 12px;
        font-size: 0.8rem; margin-bottom: 6px;
    }
    .mission-label { color: var(--muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em; }
    .mission-value { font-weight: 700; font-size: 0.82rem; }
    .mission-sep   { color: var(--border); }
    .mission-plan  { font-size: 0.88rem; color: var(--text); line-height: 1.5; }

    /* Event vol/trade annotation */
    .ev-vol-note   { font-size: 0.72rem; color: var(--yellow); margin-top: 3px; }
    .ev-trade-note { font-size: 0.70rem; color: #6b7280; margin-top: 1px; }

    /* Overnight narrative */
    .overnight-narrative {
        margin-top: 12px; padding: 10px 14px;
        background: rgba(255,255,255,0.02); border: 1px solid var(--border);
        border-radius: 8px; font-size: 0.88rem; color: var(--muted); line-height: 1.6;
    }

    /* Section subtitle */
    .section-subtitle { font-size: 0.8rem; color: var(--muted); margin-bottom: 8px; }

    /* Partially Qualified tier */
    .partial-section-label {
        margin-top: 20px; padding: 6px 0 2px;
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: var(--yellow);
        border-top: 1px dashed rgba(229,192,123,0.3);
    }
    .partial-section-note { font-size: 0.75rem; color: #6b7280; margin-bottom: 8px; font-style: italic; }
    .partial-card {
        background: var(--surface); border: 1px solid var(--border);
        border-left: 3px solid rgba(229,192,123,0.4);
        border-radius: 6px; padding: 8px 12px; margin-bottom: 5px;
    }
    .partial-card.bias-long  { border-left-color: rgba(152,195,121,0.45); }
    .partial-card.bias-short { border-left-color: rgba(224,108,117,0.45); }
    .partial-header { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
    .partial-rr     { margin-left: auto; font-size: 0.72rem; color: var(--muted); }
    .partial-kv-row { display: flex; flex-wrap: wrap; gap: 5px 14px; margin-bottom: 5px; }
    .partial-working {
        font-size: 0.75rem; color: var(--green); margin-bottom: 2px;
    }
    .partial-working::before { content: "✓  Working: "; color: var(--muted); }
    .partial-missing {
        font-size: 0.75rem; color: var(--red); margin-bottom: 2px;
    }
    .partial-missing::before { content: "✗  Missing: "; color: var(--muted); }
    .partial-trigger {
        font-size: 0.78rem; color: var(--blue); font-weight: 600; margin-top: 4px;
    }
    .partial-trigger::before { content: "⟶  Trade when: "; color: var(--muted); font-weight: normal; }

    /* Rejected tier */
    .rejected-label {
        margin-top: 20px; padding: 6px 0 2px;
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: #8b93a6;
        border-top: 1px dashed rgba(107,114,128,0.35);
    }
    .rejected-note {
        font-size: 0.75rem; color: #6b7280; margin-bottom: 8px; font-style: italic;
    }
    .rejected-card {
        background: rgba(255,255,255,0.02); border: 1px solid rgba(55,65,81,0.45);
        border-radius: 6px; padding: 8px 12px; margin-bottom: 5px;
    }
    .rejected-row { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }
    .rejected-reason { font-size: 0.75rem; color: var(--muted); }
    .rejected-reason::before { content: "Rejected: "; color: #8b93a6; }

    @media (max-width: 640px) {
        .futures-grid { grid-template-columns: 1fr; }
        .two-col { grid-template-columns: 1fr; }
        .setups-grid { grid-template-columns: 1fr; }
        .sector-cells { flex-direction: column; gap: 4px; }
    }
"""


# ── Full HTML builder ────────────────────────────────────────

def build_premarket_html(data_map: dict, setups: list, extra: dict | None = None,
                         month_events: list | None = None,
                         events: list | None = None,
                         options_map: dict[str, object] | None = None) -> str:
    if extra is None:
        extra = {}
    if month_events is None:
        month_events = []
    if options_map is None:
        options_map = {}

    _local  = datetime.now().astimezone()
    _utc    = datetime.now(timezone.utc)
    now     = _local.strftime("%A, %B %d %Y  —  %I:%M %p %Z")
    utc_str = _utc.strftime("%H:%M UTC")
    session = _safe_session(current_session())
    _as_of_raw = next((d["as_of"] for d in data_map.values() if d and d.get("as_of")), None)
    data_as_of = f"Prices as of {_as_of_raw}" if _as_of_raw else "Prices as of —"
    regime = _safe_regime(classify(data_map))
    primary_raw, secondary_raw = drivers(data_map)
    primary = _safe_driver(primary_raw)
    secondary = _safe_driver(secondary_raw)
    incidents = detect(data_map)
    read = cross_asset_read(data_map)
    if events is None:
        events = get_events()

    regime_cls = _regime_cls(regime)

    incident_html = ""
    if incidents:
        items = "".join(f'<div class="incident-item">⚠ {i}</div>' for i in incidents)
        incident_html = f'<div class="incident-box">{items}</div>'

    regime_note_cls = "on" if regime == "RISK ON" else ("mixed" if regime == "MIXED" else "")
    regime_note_text = {
        "RISK OFF": "⚠ RISK OFF — reduce size, favor shorts or cash",
        "MIXED":    "~ Mixed environment — be selective",
        "RISK ON":  "✓ RISK ON — favorable for long setups",
    }.get(regime, "Mixed / indecisive — stay reactive")

    overnight_narrative = _overnight_narrative(data_map, regime, primary, secondary)

    body = f"""
    {nav_bar("premarket")}

    {report_header(
        title="Pre-Market Report",
        meta_line=f"Generated: {now} &nbsp;·&nbsp; Market ref: {utc_str} &nbsp;·&nbsp; {data_as_of} &nbsp;·&nbsp; {session} Session",
        regime=regime,
        driver_text=f"{primary} &nbsp;·&nbsp; {secondary}",
        note_text="Flagship execution plan: market context, validated top trades, watchlist setups, and embedded Options Context.",
    )}

    {_daily_mission_html(regime, session, primary, secondary)}

    {section_block(
        "Today's Events",
        card_block(
            f'{incident_html}'
            f'<table class="cal-table">{_calendar_rows(events)}</table>'
        ),
    )}

    {section_block(
        "Overnight Futures & Cross-Asset Read",
        f'<div class="futures-grid">{_futures_cards(data_map)}</div>'
        f'<div class="overnight-narrative">{overnight_narrative}</div>',
    )}

    {section_block(
        "Macro Snapshot",
        card_block(
            f'<table class="macro-table">{_macro_rows(data_map)}</table>'
            f'<div class="summary-box">{read}</div>'
            f'<div class="summary-box" style="margin-top:6px;font-size:0.82rem">'
            f'Primary: {primary} &nbsp;·&nbsp; Secondary: {secondary}</div>'
        ),
    )}

    {section_block(
        "Trade Funnel",
        f'<div class="section-subtitle">Validated → Partially Qualified → Watchlist → Rejected</div>'
        f'<div class="regime-note {regime_note_cls}">{regime_note_text}</div>'
        f'{_setup_cards(setups, regime, options_map)}',
    )}

    {section_block(
        "Upcoming This Month — High Impact Only",
        card_block(f'<table class="cal-table">{_upcoming_rows(month_events)}</table>'),
    )}

    {section_block(
        "Sector Snapshot",
        card_block(f'<table class="sector-table">{_sector_rows(data_map, extra)}</table>'),
    )}

    {footer("Pre-Market Report")}
    """

    return page_shell(
        title=f"Pre-Market Report — {datetime.now().strftime('%b %d')}",
        body_html=body,
        extra_css=_STYLE,
    )


def save(path: str = "premarket.html", data_map: dict | None = None,
         setups: list | None = None, extra: dict | None = None,
         month_events: list | None = None) -> None:
    from config.tickers import MACRO_SYMBOLS, SNIPER_SYMBOLS
    from core.fetcher import fetch_all
    from sniper.scanner import scan

    if data_map is None:
        data_map = fetch_all(MACRO_SYMBOLS)
    if setups is None:
        setups = scan(SNIPER_SYMBOLS)
    if extra is None:
        extra = fetch_all({"GDX": ["GDX"], "IWM": ["IWM"]})
    if month_events is None:
        month_events = get_month_events()

    regime = _safe_regime(classify(data_map))
    validated, _, _, _ = _partition_setups(setups, regime)
    options_map = {}
    try:
        from options.chain import analyze
        options_map = {
            s.ticker: analyze(s.ticker, s.bias, s.price)
            for s in validated[:3]
        }
    except Exception:
        options_map = {}

    html = build_premarket_html(data_map, setups, extra, month_events, None, options_map)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved → {path}")
