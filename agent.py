import os
import httpx
from database import search_apprentices_in_db, save_master
import africastalking

# Initialize Africa's Talking
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

async def process_master_request(master_phone: str, audio_url: str = None, text: str = None):
    """Processes a master's request (either from audio or text) using the Gemini Agent."""
    print(f"Processing request for {master_phone}. Audio: {audio_url}, Text: {text}")
    
    inputs = []
    if audio_url:
        # Download audio file
        local_filename = f"/tmp/{master_phone}_audio.wav"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(audio_url)
                with open(local_filename, "wb") as f:
                    f.write(resp.content)
            audio_file = genai.upload_file(path=local_filename)
            inputs.append(audio_file)
        except Exception as e:
            print(f"Error handling audio: {e}")
            return
    
    if text:
        inputs.append(f"Master sent this text message: {text}")

    try:
        # Initialize Agent with tools
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[search_apprentices, notify_apprentice, notify_master],
            system_instruction=(
                "You are the Jua Kali Matcher Agent. A master is looking for an apprentice. "
                f"The master's phone number is {master_phone}. "
                "Step 1: Extract the 'trade' and the 'location' from the provided audio or text. "
                "Step 2: Use search_apprentices tool to find matching youth. "
                "Step 3: If found, use notify_apprentice tool to text them. "
                "Step 4: Use notify_master tool to text the master with a summary. "
                "Always call the tools to perform these actions."
            )
        )
        
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(inputs)
        print(f"Agent finished: {response.text}")
        
        # Extract trade/location for DB (simplified extraction)
        # In a real app we'd use a structured output call, but here we'll just save the summary
        save_master(master_phone, "Extracted by Agent", "Extracted by Agent", audio_url or "SMS", response.text)
        
        # Cleanup audio if used
        if audio_url:
            genai.delete_file(audio_file.name)
            if os.path.exists(local_filename):
                os.remove(local_filename)
                
    except Exception as e:
        print(f"Error in Gemini processing: {e}")
