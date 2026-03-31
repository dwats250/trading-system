from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from outputs.premarket_html import build_premarket_html


@dataclass
class FixtureSetup:
    ticker: str
    price: float
    e9: float
    e21: float
    e50: float
    rsi_val: float
    alignment: str
    support: float
    resistance: float
    score: int
    grade: str
    confidence: int
    setup_type: str
    bias: str
    entry_note: str
    invalidation: float
    rr: float
    atr: float


def _setup(ticker: str, **overrides) -> FixtureSetup:
    base = dict(
        ticker=ticker,
        price=100.0,
        e9=99.5,
        e21=98.8,
        e50=96.0,
        rsi_val=58.0,
        alignment="bullish",
        support=97.5,
        resistance=103.0,
        score=5,
        grade="A",
        confidence=8,
        setup_type="breakout",
        bias="LONG",
        entry_note="Break and close above 103.00",
        invalidation=98.4,
        rr=2.6,
        atr=1.8,
    )
    base.update(overrides)
    return FixtureSetup(**base)


def _render(name: str, data_map: dict, setups: list[FixtureSetup], events: list[dict]) -> str:
    html = build_premarket_html(
        data_map=data_map,
        setups=setups,
        extra={},
        month_events=[],
        events=events,
        options_map={},
    )
    assert "<html" in html.lower(), f"{name}: missing html shell"
    return html


def main() -> None:
    bullish_calm = _render(
        "bullish_calm",
        {
            "ES": {"price": 5230, "pct": 0.8},
            "NQ": {"price": 18310, "pct": 1.1},
            "RTY": {"price": 2098, "pct": 0.4},
            "VIX": {"price": 13.2, "pct": -2.1},
            "DXY": {"price": 103.4, "pct": -0.2},
            "10Y": {"price": 4.11, "pct": -0.3},
            "WTI": {"price": 78.2, "pct": 0.5},
            "XAU": {"price": 2332.0, "pct": 0.2},
        },
        [_setup("NVDA"), _setup("AAPL", rr=2.2, setup_type="pullback", entry_note="Dip to EMA21 and hold")],
        [{"time": "12:30", "event": "Retail Sales", "impact": "MED", "consensus": "0.2%"}],
    )
    assert "Options Context" in bullish_calm

    risk_off_spike = _render(
        "risk_off_spike",
        {
            "ES": {"price": 5070, "pct": -1.8},
            "NQ": {"price": 17600, "pct": -2.3},
            "RTY": {"price": 2010, "pct": -1.4},
            "VIX": {"price": 20.1, "pct": 6.4},
            "DXY": {"price": 104.9, "pct": 0.6},
            "10Y": {"price": 4.32, "pct": 0.5},
        },
        [_setup("TSLA", bias="SHORT", alignment="bearish", grade="A", setup_type="breakdown", rr=2.7, e9=171.0, e21=173.5, e50=178.0, support=168.0, resistance=176.0, price=169.2, invalidation=172.5, rsi_val=39.0)],
        [],
    )
    assert "VIX spiking" in risk_off_spike

    major_event_day = _render(
        "major_event_day",
        {
            "ES": {"price": 5150, "pct": 0.1},
            "NQ": {"price": 18010, "pct": 0.0},
            "VIX": {"price": 15.9, "pct": 0.9},
        },
        [],
        [{"time": "12:30", "event": "CPI", "impact": "HIGH", "consensus": "3.1%"}],
    )
    assert "Avoid new positions within 30 min" in major_event_day

    no_validated = _render(
        "no_validated",
        {
            "ES": {"price": 5140, "pct": 0.2},
            "NQ": {"price": 18000, "pct": 0.3},
            "VIX": {"price": 14.6, "pct": 0.4},
        },
        [
            _setup("AMD", grade="B", rr=1.7),
            _setup("MSFT", grade="B", rr=1.8, setup_type="pullback"),
        ],
        [],
    )
    assert "No validated setups today" in no_validated
    assert "Partially Qualified" in no_validated

    thin_data = _render(
        "thin_data",
        {
            "VIX": {"price": 14.2, "pct": 0.0},
        },
        [_setup("QQQ", grade="C", setup_type="none", bias="NEUTRAL", alignment="mixed", rr=1.3, score=1)],
        [],
    )
    assert "No major events today" in thin_data
    assert "Overnight action mixed, no clear directional signal" in thin_data
    assert "Rejected — Failed Qualification" in thin_data

    print("Pre-Market fixture scenarios passed")


if __name__ == "__main__":
    main()
