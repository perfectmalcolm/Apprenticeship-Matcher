# The Jua Kali Apprenticeship Matcher

## The Problem
Kenya’s jua kali sector employs over 15 million people, with skills primarily passed down orally. A major bottleneck in this sector is connection: Masters can’t find willing apprentices, and interested youth can’t find masters to train them. Traditional tech solutions fail here because many masters and youth rely on feature phones and will never open a smartphone app.

## Our Solution
A feature-phone-first platform using Voice and USSD, powered by a Gemini AI Agent. 
- **Youth** register their trade interests and locations via a simple USSD menu.
- **Masters** call a phone number and leave a natural, 60-second voice message explaining who they are and what they need.

## Agent Architecture
Our solution uses a true AI Agent architecture, moving beyond simple API wrappers:

- **The Jua Kali Matcher Agent:** Built using the Gemini 1.5 Flash model with native audio understanding.
- **Tools:** The agent is equipped with three tools:
  1. `search_apprentices(trade, location)`: Queries our SQLite database for matches.
  2. `notify_apprentice(youth_phone, master_phone, message)`: Sends an Africa's Talking SMS to the matched youth.
  3. `notify_master(master_phone, message)`: Sends a summary SMS back to the master.
- **Workflow:** When a master calls, Africa's Talking records the audio. Our webhook downloads this audio and sends it to the Gemini Agent. The Agent *listens* to the audio, extracts the trade and location, *autonomously* searches the database for matching youth, and *decides* to send SMS notifications to all parties involved, summarizing the matches.

## How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/perfectmalcolm/Apprenticeship-Matcher.git
   cd Apprenticeship-Matcher
   ```
2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   AT_USERNAME=sandbox
   AT_API_KEY=your_africas_talking_api_key
   GEMINI_API_KEY=your_gemini_api_key
   BASE_URL=https://your-ngrok-url.ngrok-free.app
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
5. Use a tool like `ngrok` to expose your local port 8000 to the internet, and configure the webhook URLs in your Africa's Talking sandbox (USSD: `/ussd`, Voice: `/voice`).

## How to Interact with the Deployed Version

- **Youth Registration:** Dial the Africa's Talking USSD code (e.g., `*384*XXXX#`) from the simulator or a registered phone. Follow the prompts to register for a trade (e.g., "Welding") in a location (e.g., "Nairobi").
- **Master Request:** Call the Africa's Talking Voice number associated with the app. You will hear a greeting. Leave a voice message like: *"Hello, I am a welder in Nairobi looking for a hardworking apprentice to help me."*
- **Wait for SMS:** Within seconds, the Gemini Agent will process the audio and send an SMS to the registered youth and a confirmation SMS to the master.

## Demo Video / Screenshots
*(Add a link to the demo video or embed screenshots from the Africa's Talking Simulator here)*

## Team Members
- [Your Name / Alias] - Full Stack & AI Agent Engineer
- [Other Members]
