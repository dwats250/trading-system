def change_class(direction: str) -> str:
    if direction == "up":
        return "move-up"
    if direction == "down":
        return "move-down"
    return "move-flat"


def format_html(data: dict) -> str:
    macro_cards = []
    for item in data["macro"]:
        macro_cards.append(f"""
        <div class="card macro-card">
            <div class="card-label">{item['name']}</div>
            <div class="card-value">{item['value']}</div>
            <div class="card-change {change_class(item['direction'])}">{item['change']}</div>
        </div>
        """)

    watchlist_cards = []
    for item in data["watchlist"]:
        watchlist_cards.append(f"""
        <div class="card watch-card">
            <div class="watch-ticker">{item['ticker']}</div>
            <div class="watch-note">{item['note']}</div>
        </div>
        """)

    incident_html = ""
    if data.get("incident", {}).get("active"):
        incident_html = f"""
        <div class="incident-banner">
            <div class="incident-title">Incident detected</div>
            <div class="incident-text">{data['incident']['message']}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Macro Pulse</title>
    <style>
        :root {{
            --bg: #081225;
            --panel: #0f1b33;
            --panel-2: #14213d;
            --border: #213455;
            --text: #e8eefc;
            --muted: #9fb2d4;
            --green: #22c55e;
            --red: #ef4444;
            --yellow: #f59e0b;
            --blue: #60a5fa;
            --incident-bg: rgba(127, 29, 29, 0.95);
            --incident-border: #b91c1c;
            --shadow: 0 10px 30px rgba(0, 0, 0, 0.28);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 18px;
            font-family: Arial, Helvetica, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 32%),
                linear-gradient(180deg, #081225 0%, #07101f 100%);
            color: var(--text);
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        .hero {{
            background: linear-gradient(180deg, rgba(19, 34, 63, 0.98), rgba(12, 22, 42, 0.98));
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: var(--shadow);
            margin-bottom: 16px;
        }}

        .hero-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 14px;
        }}

        .title-block h1 {{
            margin: 0 0 6px 0;
            font-size: 1.7rem;
            line-height: 1.15;
        }}

        .subtitle {{
            color: var(--muted);
            font-size: 0.95rem;
        }}

        .timestamp {{
            color: var(--muted);
            font-size: 0.92rem;
            white-space: nowrap;
        }}

        .pill-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 14px;
        }}

        .pill {{
            background: rgba(96, 165, 250, 0.1);
            border: 1px solid rgba(96, 165, 250, 0.25);
            color: #dbeafe;
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 0.88rem;
        }}

        .pill strong {{
            color: white;
        }}

        .summary-box {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px;
        }}

        .summary-title {{
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }}

        .summary-text {{
            font-size: 1rem;
            line-height: 1.45;
        }}

        .incident-banner {{
            background: var(--incident-bg);
            border: 1px solid var(--incident-border);
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 16px;
            box-shadow: var(--shadow);
        }}

        .incident-title {{
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            opacity: 0.9;
            margin-bottom: 6px;
        }}

        .incident-text {{
            font-size: 1rem;
            font-weight: bold;
        }}

        .section {{
            margin-bottom: 18px;
        }}

        .section-title {{
            font-size: 1.05rem;
            font-weight: bold;
            margin: 0 0 10px 0;
            color: #f8fbff;
        }}

        .grid {{
            display: grid;
            gap: 10px;
        }}

        .macro-grid {{
            grid-template-columns: repeat(auto-fit, minmax(125px, 1fr));
        }}

        .watch-grid {{
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        }}

        .card {{
            background: linear-gradient(180deg, rgba(20, 33, 61, 0.98), rgba(14, 24, 44, 0.98));
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 14px;
            box-shadow: var(--shadow);
        }}

        .macro-card {{
            min-height: 108px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .card-label {{
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 8px;
        }}

        .card-value {{
            font-size: 1.25rem;
            font-weight: bold;
            line-height: 1.15;
        }}

        .card-change {{
            font-size: 0.96rem;
            font-weight: bold;
            margin-top: 8px;
        }}

        .move-up {{
            color: var(--green);
        }}

        .move-down {{
            color: var(--red);
        }}

        .move-flat {{
            color: var(--yellow);
        }}

        .watch-ticker {{
            font-size: 1rem;
            font-weight: bold;
            margin-bottom: 8px;
        }}

        .watch-note {{
            color: var(--muted);
            line-height: 1.45;
            font-size: 0.95rem;
        }}

        .footer {{
            color: var(--muted);
            text-align: center;
            font-size: 0.86rem;
            padding: 10px 0 2px;
        }}

        @media (max-width: 600px) {{
            body {{
                padding: 12px;
            }}

            .hero {{
                padding: 14px;
                border-radius: 16px;
            }}

            .title-block h1 {{
                font-size: 1.45rem;
            }}

            .card-value {{
                font-size: 1.1rem;
            }}

            .watch-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <section class="hero">
            <div class="hero-top">
                <div class="title-block">
                    <h1>Macro Pulse</h1>
                    <div class="subtitle">Macro regime dashboard</div>
                </div>
                <div class="timestamp">{data['timestamp']}</div>
            </div>

            <div class="pill-row">
                <div class="pill"><strong>Session:</strong> {data['session']}</div>
                <div class="pill"><strong>Regime:</strong> {data['regime']}</div>
                <div class="pill"><strong>Primary driver:</strong> {data['primary_driver']}</div>
                <div class="pill"><strong>Secondary:</strong> {data['secondary_driver']}</div>
            </div>

            <div class="summary-box">
                <div class="summary-title">Market summary</div>
                <div class="summary-text">{data['summary']}</div>
            </div>
        </section>

        {incident_html}

        <section class="section">
            <h2 class="section-title">Macro</h2>
            <div class="grid macro-grid">
                {''.join(macro_cards)}
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">Watchlist</h2>
            <div class="grid watch-grid">
                {''.join(watchlist_cards)}
            </div>
        </section>

        <div class="footer">
            Prototype HTML output for Macro Pulse
        </div>
    </div>
</body>
</html>
"""
    return html
