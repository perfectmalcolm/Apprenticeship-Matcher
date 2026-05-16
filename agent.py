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
    print(f"Direct Agent processing for {master_phone}...")
    
    # 1. Prepare the prompt
    prompt = f"""
    You are the Jua Kali Matcher Agent.
    User Request: {text if text else 'A voice recording was provided.'}
    
    Task:
    1. Identify the 'trade' (e.g., Welding, Carpentry) and 'location' (e.g., Nairobi).
    2. Respond ONLY with a JSON object in this format:
    {{"trade": "extracted_trade", "location": "extracted_location", "summary": "A brief 1-sentence summary of what the master wants"}}
    """

    # 2. Call Gemini API directly (no SDK dependencies)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {{
        "contents": [{{"parts": [{{"text": prompt}}]}}],
        "generationConfig": {{"response_mime_type": "application/json"}}
    }}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=30.0)
            result = resp.json()
            content = result['candidates'][0]['content']['parts'][0]['text']
            data = json.loads(content)
            
            trade = data.get("trade", "Unknown")
            location = data.get("location", "Unknown")
            summary = data.get("summary", "No summary available")
            
            print(f"Extracted: {trade} in {location}")
            
            # 3. Match and Notify
            matches = search_apprentices_in_db(trade, location)
            
            if matches:
                match_count = len(matches)
                # Notify master
                sms.send(f"Success! We found {match_count} apprentices for {trade} in {location}. They have been notified.", [master_phone])
                
                # Notify each apprentice
                for app_phone in matches:
                    sms.send(f"Jua Kali Match! A Master in {trade} is looking for you. Call them: {master_phone}", [app_phone])
            else:
                sms.send(f"We received your request for {trade} in {location}, but no matches were found yet. We will notify you when someone registers!", [master_phone])
            
            # 4. Save to DB
            save_master(master_phone, trade, location, audio_url or "SMS", summary)
            
    except Exception as e:
        print(f"Direct Agent Error: {e}")
        save_master(master_phone, "Error", "Error", "Error", f"Failed to process: {str(e)}")
