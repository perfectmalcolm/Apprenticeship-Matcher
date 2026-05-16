import os
import httpx
from database import search_apprentices_in_db, save_master
import africastalking
from pydantic import BaseModel, Field

# Initialize Africa's Talking
# Default to sandbox for hackathon
AT_USERNAME = os.environ.get("AT_USERNAME", "sandbox")
AT_API_KEY = os.environ.get("AT_API_KEY", "dummy_key")
africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

# Initialize Gemini
import google.generativeai as genai
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Define tools for the agent
def search_apprentices(trade: str, location: str) -> list:
    """Searches the database for youth apprentices matching the trade and location."""
    print(f"Agent searching for: {trade} in {location}")
    matches = search_apprentices_in_db(trade, location)
    return matches

def notify_apprentice(youth_phone: str, master_phone: str, message: str) -> str:
    """Sends an SMS to a matched apprentice with the master's details."""
    try:
        response = sms.send(message, [youth_phone])
        print(f"Sent SMS to {youth_phone}: {response}")
        return "Success"
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return f"Failed: {e}"

def notify_master(master_phone: str, message: str) -> str:
    """Sends a summary SMS to the master after processing their request."""
    try:
        response = sms.send(message, [master_phone])
        print(f"Sent SMS to master {master_phone}: {response}")
        return "Success"
    except Exception as e:
        print(f"Failed to send SMS to master: {e}")
        return f"Failed: {e}"

async def process_master_audio(master_phone: str, audio_url: str):
    """Downloads the audio, sends it to Gemini, and executes the agent loop."""
    print(f"Processing audio for {master_phone} from {audio_url}")
    
    # 1. Download audio file temporarily
    local_filename = f"/tmp/{master_phone}_audio.wav"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(audio_url)
            with open(local_filename, "wb") as f:
                f.write(resp.content)
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return

    # 2. Upload to Gemini
    try:
        audio_file = genai.upload_file(path=local_filename)
        
        # 3. Initialize Agent with tools
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[search_apprentices, notify_apprentice, notify_master],
            system_instruction=(
                "You are the Jua Kali Matcher Agent. A master has left a voice message looking for an apprentice. "
                f"The master's phone number is {master_phone}. "
                "Step 1: Listen to the audio to extract the 'trade' (e.g. Carpentry, Welding, Plumbing) and the 'location'. "
                "Step 2: Use the search_apprentices tool to find matching youth. "
                "Step 3: If you find matches, use the notify_apprentice tool to send EACH of them an SMS telling them about the master. Keep it brief. "
                "Step 4: Use the notify_master tool to send an SMS to the master summarizing the results (e.g. 'We found 2 youth for you...')."
            )
        )
        
        # Start a chat session to handle multi-turn tool calling
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        # Send the audio to kick off the process
        response = chat.send_message([audio_file, "Please process this master's request."])
        print(f"Agent finished. Final response: {response.text}")
        
        # Cleanup
        genai.delete_file(audio_file.name)
        
        # Optional: Save master to DB
        # Note: Since the agent doesn't return structured data directly here, we'll just save a placeholder or use another call to extract.
        # For simplicity, we just save the fact that they called.
        save_master(master_phone, "Unknown (Handled by Agent)", "Unknown", audio_url, response.text)
        
    except Exception as e:
        print(f"Error in Gemini processing: {e}")
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)
