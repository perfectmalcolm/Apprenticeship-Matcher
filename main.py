import os
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import PlainTextResponse, Response, HTMLResponse
from database import register_youth, get_all_youth, get_all_masters
from agent import process_master_request

app = FastAPI(title="Jua Kali Apprenticeship Matcher")

@app.get("/")
def read_root():
    return {"message": "Jua Kali Matcher API is running. Visit /dashboard for the UI."}

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    youths = get_all_youth()
    masters = get_all_masters()
    
    youth_count = len(youths)
    master_count = len(masters)

    youth_cards = ""
    for i, y in enumerate(youths):
        youth_cards += f"""
        <div class="sms-bubble youth-bubble" style="animation-delay: {i * 0.1}s">
            <div class="bubble-icon">&#128296;</div>
            <div class="bubble-content">
                <div class="bubble-trade">{y['trade_interest']}</div>
                <div class="bubble-detail"><span class="label">&#128222;</span> {y['phone_number']}</div>
                <div class="bubble-detail"><span class="label">&#128205;</span> {y['location']}</div>
                <div class="bubble-time">{y['registered_at']}</div>
            </div>
        </div>
        """
        
    master_cards = ""
    for i, m in enumerate(masters):
        master_cards += f"""
        <div class="sms-bubble master-bubble" style="animation-delay: {i * 0.1}s">
            <div class="bubble-icon">&#128119;</div>
            <div class="bubble-content">
                <div class="bubble-trade">{m['trade']}</div>
                <div class="bubble-detail"><span class="label">&#128222;</span> {m['phone_number']}</div>
                <div class="bubble-detail"><span class="label">&#128205;</span> {m['location']}</div>
                <div class="bubble-agent">&#129302; {m['summary']}</div>
                <div class="bubble-time">{m['created_at']}</div>
            </div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jua Kali Matcher — Live Dashboard</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=VT323&family=Space+Mono:wght@400;700&family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            /* ===== DESIGN TOKENS ===== */
            :root {{
                --nokia-green: #33ff33;
                --nokia-dark: #003300;
                --kenya-black: #111111;
                --kenya-red: #bb2222;
                --kenya-green: #006600;
                --spark-orange: #ff6600;
                --spark-yellow: #ffcc00;
                --metal-dark: #1a1a1a;
                --metal-mid: #2a2a2a;
                --metal-light: #3a3a3a;
                --text-dim: #667766;
                --screen-glow: rgba(51, 255, 51, 0.08);
            }}

            /* ===== RESET & BASE ===== */
            *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
            
            body {{
                font-family: 'Space Mono', monospace;
                background: var(--kenya-black);
                color: var(--nokia-green);
                min-height: 100vh;
                overflow-x: hidden;
            }}

            /* ===== CORRUGATED METAL BACKGROUND ===== */
            body::before {{
                content: '';
                position: fixed;
                inset: 0;
                background:
                    repeating-linear-gradient(
                        90deg,
                        rgba(255,255,255,0.02) 0px,
                        rgba(255,255,255,0.02) 2px,
                        transparent 2px,
                        transparent 12px
                    ),
                    repeating-linear-gradient(
                        0deg,
                        rgba(255,255,255,0.01) 0px,
                        transparent 1px,
                        transparent 4px
                    );
                pointer-events: none;
                z-index: 0;
            }}

            /* ===== PROGRESS BAR (NOKIA GREEN) ===== */
            .refresh-bar {{
                height: 3px;
                background: linear-gradient(90deg, var(--nokia-green), var(--spark-yellow), var(--spark-orange));
                width: 0%;
                position: fixed;
                top: 0; left: 0;
                transition: width 15s linear;
                z-index: 1000;
                box-shadow: 0 0 8px var(--nokia-green);
            }}

            /* ===== HEADER — FEATURE PHONE SCREEN ===== */
            header {{
                position: relative;
                text-align: center;
                padding: 2rem 1rem 1.5rem;
                background: var(--metal-dark);
                border-bottom: 3px solid var(--kenya-red);
                box-shadow: 0 2px 20px rgba(0,0,0,0.5);
                z-index: 1;
            }}
            header::after {{
                content: '';
                position: absolute;
                bottom: -3px; left: 0; right: 0;
                height: 3px;
                background: var(--kenya-green);
            }}

            .phone-screen {{
                display: inline-block;
                background: var(--nokia-dark);
                border: 2px solid #224422;
                border-radius: 8px;
                padding: 1rem 2rem;
                box-shadow: inset 0 0 30px rgba(51,255,51,0.05), 0 0 15px rgba(51,255,51,0.1);
                max-width: 500px;
                width: 100%;
            }}

            .phone-status-bar {{
                display: flex;
                justify-content: space-between;
                font-family: 'VT323', monospace;
                font-size: 0.85rem;
                color: var(--text-dim);
                margin-bottom: 0.5rem;
                padding-bottom: 0.4rem;
                border-bottom: 1px solid #224422;
            }}

            h1 {{
                font-family: 'VT323', monospace;
                font-size: 2.2rem;
                color: var(--nokia-green);
                text-shadow: 0 0 10px rgba(51,255,51,0.5);
                letter-spacing: 2px;
                margin: 0.25rem 0;
            }}

            .tagline {{
                font-family: 'VT323', monospace;
                color: var(--text-dim);
                font-size: 1.1rem;
                letter-spacing: 1px;
            }}

            /* ===== KENYA FLAG STRIPE ===== */
            .flag-stripe {{
                display: flex;
                height: 6px;
                z-index: 1;
                position: relative;
            }}
            .flag-stripe span {{
                flex: 1;
            }}
            .flag-stripe .fk {{ background: var(--kenya-black); }}
            .flag-stripe .fr {{ background: var(--kenya-red); }}
            .flag-stripe .fg {{ background: var(--kenya-green); }}

            /* ===== STATS BAR ===== */
            .stats-bar {{
                display: flex;
                justify-content: center;
                gap: 2rem;
                padding: 1rem;
                background: var(--metal-dark);
                border-bottom: 1px solid #333;
                z-index: 1;
                position: relative;
            }}
            .stat {{
                text-align: center;
            }}
            .stat-number {{
                font-family: 'VT323', monospace;
                font-size: 2rem;
                color: var(--nokia-green);
                text-shadow: 0 0 8px rgba(51,255,51,0.4);
            }}
            .stat-label {{
                font-size: 0.7rem;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            .stat-divider {{
                width: 1px;
                background: #333;
                align-self: stretch;
            }}

            /* ===== LIVE BADGE ===== */
            .live-badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 14px;
                background: rgba(51,255,51,0.08);
                border: 1px solid #224422;
                border-radius: 4px;
                font-family: 'VT323', monospace;
                font-size: 1rem;
                color: var(--nokia-green);
                margin-top: 0.75rem;
            }}
            .live-dot {{
                width: 8px; height: 8px;
                background: var(--nokia-green);
                border-radius: 50%;
                animation: pulse 1.5s ease-in-out infinite;
                box-shadow: 0 0 6px var(--nokia-green);
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.4; transform: scale(0.8); }}
            }}

            /* ===== MAIN CONTAINER ===== */
            .container {{
                display: flex;
                flex-wrap: wrap;
                gap: 1.5rem;
                padding: 1.5rem;
                max-width: 1300px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }}

            .column {{
                flex: 1;
                min-width: 320px;
            }}

            /* ===== SECTION HEADERS ===== */
            .section-header {{
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 1px dashed #333;
            }}
            .section-header h2 {{
                font-family: 'VT323', monospace;
                font-size: 1.4rem;
                color: var(--nokia-green);
                letter-spacing: 1px;
                border: none;
                margin: 0;
                padding: 0;
            }}
            .section-icon {{
                font-size: 1.3rem;
            }}
            .section-count {{
                margin-left: auto;
                font-family: 'VT323', monospace;
                font-size: 1.1rem;
                color: var(--text-dim);
                background: #1a1a1a;
                padding: 2px 10px;
                border-radius: 3px;
                border: 1px solid #333;
            }}

            /* ===== SMS BUBBLE CARDS ===== */
            .sms-bubble {{
                display: flex;
                gap: 0.75rem;
                background: var(--metal-mid);
                border: 1px solid #333;
                border-radius: 2px 12px 12px 12px;
                padding: 1rem;
                margin-bottom: 0.75rem;
                transition: all 0.25s ease;
                animation: slideIn 0.4s ease-out both;
                position: relative;
                overflow: hidden;
            }}
            .sms-bubble::before {{
                content: '';
                position: absolute;
                top: 0; left: 0;
                width: 3px; height: 100%;
            }}
            .youth-bubble::before {{
                background: linear-gradient(to bottom, var(--kenya-green), transparent);
            }}
            .master-bubble::before {{
                background: linear-gradient(to bottom, var(--spark-orange), var(--spark-yellow));
            }}
            .sms-bubble:hover {{
                border-color: var(--nokia-green);
                box-shadow: 0 0 12px rgba(51,255,51,0.08);
                transform: translateX(4px);
            }}
            @keyframes slideIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            .bubble-icon {{
                font-size: 1.5rem;
                flex-shrink: 0;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(51,255,51,0.06);
                border-radius: 50%;
                border: 1px solid #333;
            }}
            .bubble-content {{
                flex: 1;
                min-width: 0;
            }}
            .bubble-trade {{
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
                font-size: 1.05rem;
                color: #fff;
                margin-bottom: 0.3rem;
            }}
            .bubble-detail {{
                font-size: 0.8rem;
                color: #999;
                margin: 0.15rem 0;
            }}
            .bubble-detail .label {{
                font-size: 0.85rem;
                margin-right: 4px;
            }}
            .bubble-agent {{
                font-size: 0.8rem;
                color: var(--nokia-green);
                background: rgba(51,255,51,0.06);
                padding: 6px 8px;
                border-radius: 4px;
                margin-top: 0.4rem;
                border-left: 2px solid var(--nokia-green);
            }}
            .bubble-time {{
                font-family: 'VT323', monospace;
                font-size: 0.8rem;
                color: #555;
                margin-top: 0.4rem;
                text-align: right;
            }}

            /* ===== EMPTY STATE ===== */
            .empty-state {{
                text-align: center;
                padding: 2rem;
                color: #555;
                font-family: 'VT323', monospace;
                font-size: 1.1rem;
                border: 1px dashed #333;
                border-radius: 8px;
            }}
            .empty-state .blink {{
                animation: blink 1s step-end infinite;
            }}
            @keyframes blink {{
                50% {{ opacity: 0; }}
            }}

            /* ===== SPARK PARTICLES ===== */
            .spark {{
                position: fixed;
                width: 3px; height: 3px;
                background: var(--spark-orange);
                border-radius: 50%;
                pointer-events: none;
                z-index: 0;
                animation: sparkFly 3s ease-out infinite;
            }}
            @keyframes sparkFly {{
                0% {{ opacity: 1; transform: translateY(0) scale(1); }}
                100% {{ opacity: 0; transform: translateY(-120px) translateX(var(--drift)) scale(0); }}
            }}

            /* ===== FOOTER ===== */
            footer {{
                text-align: center;
                padding: 1.5rem;
                color: #444;
                font-family: 'VT323', monospace;
                font-size: 0.9rem;
                border-top: 1px solid #222;
                position: relative;
                z-index: 1;
            }}
            footer a {{
                color: var(--nokia-green);
                text-decoration: none;
            }}

            /* ===== RESPONSIVE ===== */
            @media (max-width: 700px) {{
                .container {{ padding: 1rem; }}
                h1 {{ font-size: 1.6rem; }}
                .phone-screen {{ padding: 0.75rem 1rem; }}
                .stats-bar {{ gap: 1rem; }}
            }}
        </style>
    </head>
    <body>
        <div class="refresh-bar" id="progressBar"></div>

        <header>
            <div class="phone-screen">
                <div class="phone-status-bar">
                    <span>Safaricom KE</span>
                    <span>&#9608;&#9608;&#9608;&#9608;&#9601;</span>
                </div>
                <h1>JUA KALI MATCHER</h1>
                <div class="tagline">Connecting Masters &amp; Apprentices</div>
                <div class="live-badge">
                    <span class="live-dot"></span>
                    LIVE &mdash; Next sync in <span id="timer">15</span>s
                </div>
            </div>
        </header>

        <div class="flag-stripe">
            <span class="fk"></span>
            <span class="fr"></span>
            <span class="fg"></span>
        </div>

        <div class="stats-bar">
            <div class="stat">
                <div class="stat-number">{youth_count}</div>
                <div class="stat-label">Apprentices</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat">
                <div class="stat-number">{master_count}</div>
                <div class="stat-label">Masters</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat">
                <div class="stat-number">{min(youth_count, master_count)}</div>
                <div class="stat-label">Matches</div>
            </div>
        </div>

        <div class="container">
            <div class="column">
                <div class="section-header">
                    <span class="section-icon">&#128296;</span>
                    <h2>APPRENTICES</h2>
                    <span class="section-count">{youth_count}</span>
                </div>
                {youth_cards if youth_cards else '<div class="empty-state">Dial *384*54593# to register<span class="blink">_</span></div>'}
            </div>
            <div class="column">
                <div class="section-header">
                    <span class="section-icon">&#128119;</span>
                    <h2>MASTER REQUESTS</h2>
                    <span class="section-count">{master_count}</span>
                </div>
                {master_cards if master_cards else '<div class="empty-state">SMS MASTER: to 24881<span class="blink">_</span></div>'}
            </div>
        </div>

        <footer>
            Powered by Gemini AI &bull; Africa&#39;s Talking &bull; Google Cloud Run<br>
            <a href="https://github.com/perfectmalcolm/Apprenticeship-Matcher">GitHub</a> &bull; GDG Nairobi Agentathon 2026
        </footer>

        <!-- Spark Particles (welding effect) -->
        <div id="sparks"></div>

        <script>
            // Auto-refresh with countdown
            (function() {{
                const bar = document.getElementById('progressBar');
                const timerText = document.getElementById('timer');
                let timeLeft = 15;
                setTimeout(() => bar.style.width = '100%', 100);
                const countdown = setInterval(() => {{
                    timeLeft--;
                    timerText.innerText = timeLeft;
                    if (timeLeft <= 0) {{
                        clearInterval(countdown);
                        window.location.reload();
                    }}
                }}, 1000);
            }})();

            // Welding Spark Particles
            (function() {{
                const container = document.getElementById('sparks');
                function createSpark() {{
                    const spark = document.createElement('div');
                    spark.className = 'spark';
                    spark.style.left = (Math.random() * 100) + 'vw';
                    spark.style.top = (60 + Math.random() * 40) + 'vh';
                    spark.style.setProperty('--drift', (Math.random() * 60 - 30) + 'px');
                    spark.style.animationDuration = (2 + Math.random() * 2) + 's';
                    spark.style.background = Math.random() > 0.5 ? '#ff6600' : '#ffcc00';
                    container.appendChild(spark);
                    setTimeout(() => spark.remove(), 4000);
                }}
                setInterval(createSpark, 400);
            }})();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/ussd", response_class=PlainTextResponse)
async def ussd_webhook(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form("")
):
    """
    USSD Webhook for Youth to register.
    """
    if text == "":
        response = "CON Welcome to Jua Kali Matcher\n"
        response += "Enter the trade you want to learn (e.g. Carpentry, Welding):"
    else:
        parts = text.split('*')
        if len(parts) == 1:
            response = f"CON You selected {parts[0]}.\n"
            response += "Enter your location (e.g. Nairobi, Kisumu):"
        elif len(parts) == 2:
            trade = parts[0]
            location = parts[1]
            register_youth(phoneNumber, trade, location)
            response = f"END Thank you. You are registered for {trade} in {location}. We will SMS you when a Master is looking for an apprentice."
        else:
            response = "END Invalid input. Please try again."
    return response

@app.post("/voice", response_class=PlainTextResponse)
async def voice_webhook(
    request: Request,
    sessionId: str = Form(...),
    isActive: str = Form(...),
    callerNumber: str = Form(...)
):
    """
    Voice Webhook for Masters.
    """
    if isActive == "1":
        # Automatically detect the base URL from the request
        base_url = str(request.base_url).rstrip("/")
        callback_url = f"{base_url}/voice/recording"
        xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Record finishOnKey="#" maxLength="60" playBeep="true" callbackUrl="{callback_url}">
        <Say>Welcome Master. Please tell us your trade, location, and the kind of apprentice you are looking for after the beep. Press hash when done.</Say>
    </Record>
</Response>"""
        return Response(content=xml_response, media_type="application/xml")
    return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")

@app.post("/voice/recording")
async def voice_recording_webhook(
    background_tasks: BackgroundTasks,
    callerNumber: str = Form(...),
    recordingUrl: str = Form(...)
):
    """
    Callback webhook for voice recordings.
    """
    print(f"Received recording for {callerNumber}: {recordingUrl}")
    await process_master_request(callerNumber, audio_url=recordingUrl)
    return {"status": "Processing"}

@app.post("/sms")
async def sms_webhook(
    background_tasks: BackgroundTasks,
    from_: str = Form(..., alias="from"),
    to: str = Form(...),
    text: str = Form(...),
    date: str = Form(...)
):
    """
    SMS Webhook for Masters (Fallback).
    """
    print(f"Received SMS from {from_}: {text}")
    clean_text = text.strip()
    if clean_text.upper().startswith("MASTER"):
        await process_master_request(from_, text=clean_text)
        return {"status": "Processing Master Request"}
    return {"status": "Ignored"}
