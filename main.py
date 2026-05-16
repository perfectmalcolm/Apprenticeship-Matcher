import os
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import PlainTextResponse, Response, HTMLResponse
from database import register_youth, get_all_youth, get_all_masters
from agent import process_master_audio
from agent import process_master_audio

app = FastAPI(title="Jua Kali Apprenticeship Matcher")

@app.get("/")
def read_root():
    return {"message": "Jua Kali Matcher API is running. Visit /dashboard for the UI."}

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    youths = get_all_youth()
    masters = get_all_masters()
    
    youth_cards = ""
    for y in youths:
        youth_cards += f"""
        <div class="card">
            <h3>Trade: {y['trade_interest']}</h3>
            <p><strong>Phone:</strong> {y['phone_number']}</p>
            <p><strong>Location:</strong> {y['location']}</p>
            <p class="time">Registered: {y['registered_at']}</p>
        </div>
        """
        
    master_cards = ""
    for m in masters:
        master_cards += f"""
        <div class="card master-card">
            <h3>Trade: {m['trade']}</h3>
            <p><strong>Phone:</strong> {m['phone_number']}</p>
            <p><strong>Location:</strong> {m['location']}</p>
            <p><strong>Agent Summary:</strong> {m['summary']}</p>
            <p class="time">Processed: {m['created_at']}</p>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jua Kali Matcher - Live Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: #0f172a;
                --card-bg: rgba(30, 41, 59, 0.7);
                --accent: #3b82f6;
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --master-border: #10b981;
            }}
            body {{
                margin: 0;
                font-family: 'Outfit', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                background-image: radial-gradient(circle at top right, #1e1b4b, transparent 40%),
                                  radial-gradient(circle at bottom left, #064e3b, transparent 40%);
                min-height: 100vh;
            }}
            header {{
                text-align: center;
                padding: 3rem 2rem;
                background: rgba(15, 23, 42, 0.5);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
            h1 {{
                margin: 0;
                font-size: 3rem;
                background: linear-gradient(to right, #60a5fa, #34d399);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            p.subtitle {{
                color: var(--text-muted);
                font-size: 1.2rem;
            }}
            .container {{
                display: flex;
                flex-wrap: wrap;
                gap: 2rem;
                padding: 2rem;
                max-width: 1400px;
                margin: 0 auto;
            }}
            .column {{
                flex: 1;
                min-width: 300px;
            }}
            h2 {{
                border-bottom: 2px solid var(--accent);
                padding-bottom: 0.5rem;
                margin-bottom: 1.5rem;
            }}
            .card {{
                background: var(--card-bg);
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                border: 1px solid rgba(255,255,255,0.05);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
                backdrop-filter: blur(5px);
            }}
            .card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 15px rgba(0,0,0,0.2);
            }}
            .master-card {{
                border-left: 4px solid var(--master-border);
            }}
            .card h3 {{ margin-top: 0; color: #fff; }}
            .card p {{ margin: 0.5rem 0; color: #cbd5e1; }}
            .time {{ font-size: 0.8rem; color: var(--text-muted) !important; margin-top: 1rem !important; }}
        </style>
    </head>
    <body>
        <header>
            <h1>Jua Kali Matcher</h1>
            <p class="subtitle">Live Agent Arbitration Dashboard</p>
        </header>
        <div class="container">
            <div class="column">
                <h2>Registered Youth (Apprentices)</h2>
                {youth_cards if youth_cards else "<p>No youth registered yet. Dial the USSD code to register!</p>"}
            </div>
            <div class="column">
                <h2>Master Requests (Processed by Agent)</h2>
                {master_cards if master_cards else "<p>No masters have called yet.</p>"}
            </div>
        </div>
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
    Africa's Talking sends the `text` parameter containing the user's input.
    """
    # Empty string means initial menu
    if text == "":
        response = "CON Welcome to Jua Kali Matcher\n"
        response += "Enter the trade you want to learn (e.g. Carpentry, Welding):"
    else:
        # Split the text by '*' to get the sequence of inputs
        parts = text.split('*')
        
        if len(parts) == 1:
            # User just entered the trade, now ask for location
            response = f"CON You selected {parts[0]}.\n"
            response += "Enter your location (e.g. Nairobi, Kisumu):"
        elif len(parts) == 2:
            # User entered both trade and location
            trade = parts[0]
            location = parts[1]
            
            # Save to database
            register_youth(phoneNumber, trade, location)
            
            response = f"END Thank you. You are registered for {trade} in {location}. We will SMS you when a Master is looking for an apprentice."
        else:
            response = "END Invalid input. Please try again."

    return response

@app.post("/voice", response_class=PlainTextResponse)
async def voice_webhook(
    sessionId: str = Form(...),
    isActive: str = Form(...),
    callerNumber: str = Form(...)
):
    """
    Voice Webhook for Masters.
    When a master calls, play a prompt and record their audio.
    """
    if isActive == "1":
        # The call is active. Prompt the user to speak and start recording.
        # Ensure your callbackUrl points to a publicly accessible URL (e.g., via ngrok)
        # Note: For production, this should be an environment variable
        base_url = os.environ.get("BASE_URL", "http://localhost:8000")
        callback_url = f"{base_url}/voice/recording"
        
        # Use Africa's Talking XML
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
    Callback webhook that Africa's Talking hits when the recording is done.
    """
    print(f"Received recording for {callerNumber}: {recordingUrl}")
    
    # Process the audio in the background so we can immediately return 200 OK to AT
    background_tasks.add_task(process_master_audio, callerNumber, recordingUrl)
    
    return {"status": "Processing"}
