import os
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import PlainTextResponse, Response
from database import register_youth
from agent import process_master_audio

app = FastAPI(title="Jua Kali Apprenticeship Matcher")

@app.get("/")
def read_root():
    return {"message": "Jua Kali Matcher API is running"}

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
