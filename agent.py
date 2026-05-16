import os
import httpx
import json
from database import search_apprentices_in_db, save_master
import africastalking

# Initialize Africa's Talking
AT_USERNAME = os.environ.get("AT_USERNAME", "sandbox")
AT_API_KEY = os.environ.get("AT_API_KEY", "dummy_key")
africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

async def process_master_request(master_phone: str, audio_url: str = None, text: str = None):
    """Processes a master's request using a direct Gemini API call for maximum reliability."""
    print(f"Agent starting for {master_phone}...")
    
    prompt = f"Extract 'trade' and 'location' from this request: '{text if text else 'A voice recording'}' and provide a JSON response like {{\"trade\": \"...\", \"location\": \"...\", \"summary\": \"...\"}}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=30.0)
            result = resp.json()
            
            if 'candidates' not in result:
                print(f"Gemini Error: {result}")
                return

            content_text = result['candidates'][0]['content']['parts'][0]['text']
            data = json.loads(content_text)
            
            trade = data.get("trade", "Unknown")
            location = data.get("location", "Unknown")
            summary = data.get("summary", "No summary")
            
            print(f"Extracted: {trade} in {location}")
            
            # Match and Notify
            matches = search_apprentices_in_db(trade, location)
            if matches:
                sms.send(f"Success! Found {len(matches)} matches for {trade}. They have been notified.", [master_phone])
                for app_phone in matches:
                    sms.send(f"Jua Kali Match! Master in {trade} is looking for you. Call: {master_phone}", [app_phone])
            else:
                sms.send(f"Received request for {trade} in {location}. Searching for matches...", [master_phone])
            
            save_master(master_phone, trade, location, audio_url or "SMS", summary)
            print("Successfully saved to DB.")
            
    except Exception as e:
        print(f"Agent Loop Error: {e}")
