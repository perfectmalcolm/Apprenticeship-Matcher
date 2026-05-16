import os
import httpx
import asyncio
from database import search_apprentices_in_db, save_master
import africastalking
from google import genai
from google.genai import types

# Initialize Africa's Talking
AT_USERNAME = os.environ.get("AT_USERNAME", "sandbox")
AT_API_KEY = os.environ.get("AT_API_KEY", "dummy_key")
africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Define tools for the agent (standard Python functions)
def search_apprentices(trade: str, location: str) -> str:
    """Searches the database for youth apprentices matching the trade and location."""
    print(f"Agent tool call: search_apprentices({trade}, {location})")
    matches = search_apprentices_in_db(trade, location)
    if not matches:
        return "No matching apprentices found in this location."
    return f"Found matching apprentices: {', '.join(matches)}"

def notify_apprentice(youth_phone: str, master_phone: str, trade: str) -> str:
    """Sends an SMS to a matched apprentice."""
    message = f"Jua Kali Match! A Master in {trade} is looking for you. Call them: {master_phone}"
    try:
        sms.send(message, [youth_phone])
        return f"Successfully notified {youth_phone}"
    except Exception as e:
        return f"Failed to notify {youth_phone}: {str(e)}"

def notify_master(master_phone: str, summary: str) -> str:
    """Sends a final summary SMS to the master."""
    try:
        sms.send(summary, [master_phone])
        return "Master notified."
    except Exception as e:
        return f"Failed to notify master: {str(e)}"

async def process_master_request(master_phone: str, audio_url: str = None, text: str = None):
    """The core Agent loop using Gemini 1.5 Flash."""
    print(f"Agent starting for {master_phone}")
    
    contents = []
    if audio_url:
        # For audio, we'd normally download and send to Gemini
        # In this SDK we use client.files.upload
        local_filename = f"/tmp/{master_phone}_audio.wav"
        try:
            async with httpx.AsyncClient() as httpx_client:
                resp = await httpx_client.get(audio_url)
                with open(local_filename, "wb") as f:
                    f.write(resp.content)
            
            # Note: Uploading in this SDK is synchronous in the current version
            myfile = client.files.upload(path=local_filename)
            contents.append(myfile)
        except Exception as e:
            print(f"Audio error: {e}")
            return

    if text:
        contents.append(f"User Request: {text}")

    try:
        # Run the agent with tool use
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[search_apprentices, notify_apprentice, notify_master],
                system_instruction=(
                    "You are the Jua Kali Matcher Agent. "
                    "1. Extract 'trade' and 'location' from the user input. "
                    "2. ALWAYS call search_apprentices to find youth. "
                    "3. If matches found, call notify_apprentice for EACH match. "
                    "4. Finally, call notify_master to give them a brief result summary. "
                    f"The master's phone number is {master_phone}."
                ),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )
        
        print(f"Agent finished. Summary: {response.text}")
        save_master(master_phone, "AI Extracted", "AI Extracted", audio_url or "SMS", response.text)
        
    except Exception as e:
        print(f"Agent Error: {e}")
    finally:
        if audio_url and os.path.exists(local_filename):
            os.remove(local_filename)
