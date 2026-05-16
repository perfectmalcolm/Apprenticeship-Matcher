import asyncio
import os
from agent import process_master_audio
from database import register_youth, init_db

async def test_flow():
    # 1. Initialize DB and register a test apprentice
    init_db()
    register_youth("+254712345678", "Welding", "Nairobi")
    print("Registered test apprentice: +254712345678 for Welding in Nairobi")

    # 2. Simulate a master's audio recording callback
    # You will need a valid GEMINI_API_KEY in your environment for this to work.
    # Also need a sample audio URL or a way to mock the download.
    # For this test, we assume you have a link to a WAV file.
    test_audio_url = "https://www.soundjay.com/buttons/button-1.wav" # Just a placeholder
    master_phone = "+254700000000"
    
    print(f"Starting agent process for master {master_phone}...")
    if not os.environ.get("GEMINI_API_KEY"):
        print("SKIP: GEMINI_API_KEY not set. Cannot run agent test.")
        return

    await process_master_audio(master_phone, test_audio_url)
    print("Test finished. Check console for agent tool calls and matching results.")

if __name__ == "__main__":
    asyncio.run(test_flow())
