import os
import httpx
import json
import re
from database import search_apprentices_in_db, save_master
import africastalking

# Initialize Africa's Talking
AT_USERNAME = os.environ.get("AT_USERNAME", "sandbox")
AT_API_KEY = os.environ.get("AT_API_KEY", "dummy_key")
africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

async def process_master_request(master_phone: str, audio_url: str = None, text: str = None):
    """Processes a master's request with multi-model fallback and Regex engine."""
    print(f"Agent starting for {master_phone}...")
    
    trade, location, summary = "Unknown", "Unknown", "No summary"
    success = False

    # --- PHASE 1: Try Multiple Gemini Models ---
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-8b", "gemini-pro"]
    prompt = f"Extract 'trade' and 'location' from this request: '{text if text else 'A voice recording'}' and respond with JSON: {{\"trade\": \"...\", \"location\": \"...\", \"summary\": \"...\"}}"

    for model in models:
        if success: break
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            print(f"Trying {model}...")
            payload = {{"contents": [{{"parts": [{{"text": prompt}}]}}]}}
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
                result = resp.json()
                if 'candidates' in result:
                    content_text = result['candidates'][0]['content']['parts'][0]['text']
                    clean_content = content_text.strip().strip('`').replace('json\n', '', 1)
                    data = json.loads(clean_content)
                    trade = data.get("trade", "Unknown")
                    location = data.get("location", "Unknown")
                    summary = data.get("summary", "AI Processed")
                    success = True
                    print(f"Success with {model}!")
        except:
            continue

    # --- PHASE 2: Fallback to Regex Match Engine (Unbreakable) ---
    if not success and text:
        print("AI failed. Falling back to Regex Match Engine...")
        text_upper = text.upper()
        # Common Jua Kali trades
        trades = ["CARPENTER", "CARPENTRY", "WELD", "WELDING", "PLUMB", "PLUMBING", "TAILOR", "MECHANIC"]
        for t in trades:
            if t in text_upper:
                trade = t.capitalize()
                break
        
        # Common locations
        locations = ["NAIROBI", "MOMBASA", "KISUMU", "NAKURU"]
        for l in locations:
            if l in text_upper:
                location = l.capitalize()
                break
        
        summary = f"Processed via Match Engine: {text[:50]}..."
        success = True

    # --- PHASE 3: Match, Notify, and Save ---
    if success:
        print(f"Extracted: {trade} in {location}")
        matches = search_apprentices_in_db(trade, location)
        if matches:
            sms.send(f"Success! Found {len(matches)} matches for {trade}. They have been notified.", [master_phone])
            for app_phone in matches:
                sms.send(f"Jua Kali Match! Master in {trade} is looking for you. Call: {master_phone}", [app_phone])
        else:
            sms.send(f"Received request for {trade} in {location}. Searching...", [master_phone])
        
        save_master(master_phone, trade, location, audio_url or "SMS", summary)
        print("Data saved successfully.")
    else:
        print("All processing methods failed.")
