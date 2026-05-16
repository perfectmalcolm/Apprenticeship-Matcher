# The Jua Kali Apprenticeship Matcher 🚀

**Build AI Agents. Solve Kenya’s Real Problems.**

## 1. The Problem (Plain Language)
Kenya’s jua kali sector employs over 15 million people, yet it remains almost entirely informal. Skills and opportunities are shared orally, which creates a massive "connection gap": masters with decades of experience can't find apprentices, and eager youth can't find mentors. Because these users primarily use feature phones and often work in noisy, hands-on environments, traditional smartphone apps are useless to them.

## 2. Our Solution
A "No-App" platform that brings the power of **Gemini AI Agents** to every feature phone in Kenya.
- **Youth** register their interest and location via a fast **USSD menu**.
- **Masters** describe their needs naturally via **Voice** (or SMS).
- **The Agent** listens, reasons, and matches them instantly.

## 3. Agent Architecture
Our solution is a genuine AI Agent, not a simple wrapper. It demonstrates **autonomous tool use** and **natural language reasoning**:

- **Brain:** Gemini 1.5 Flash (with native audio and text understanding).
- **Tools:**
  - `search_apprentices`: The agent decides when to query the database for matches.
  - `notify_apprentice`: The agent autonomously sends SMS matches to the youth.
  - `notify_master`: The agent summarizes the outcome for the master.
- **Workflow:** When a Master's voice or text request comes in, the Agent extracts the intent (Trade & Location), decides to search the database, and executes the notifications without any human intervention.

## 4. How to Run Locally

1. **Clone & Setup:**
   ```bash
   git clone https://github.com/perfectmalcolm/Apprenticeship-Matcher.git
   cd Apprenticeship-Matcher
   python -m venv venv
   source venv/bin/activate  # venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. **Environment:** Create a `.env` file:
   ```env
   GEMINI_API_KEY=your_key
   AT_USERNAME=sandbox
   AT_API_KEY=your_at_key
   ```
3. **Run:**
   ```bash
   uvicorn main:app --reload
   ```

## 5. How to Interact (Pitch Demo)

**Deployed Version:** [https://jua-kali-matcher-775881152318.us-central1.run.app/dashboard](https://jua-kali-matcher-775881152318.us-central1.run.app/dashboard)

1. **Apprentice Side (USSD):**
   - Open the [Africa's Talking Simulator](https://simulator.africastalking.com/).
   - Dial `*384*54593#`.
   - Register a youth (e.g., "Welding" in "Nairobi").
2. **Master Side (SMS Fallback):**
   - Send an SMS to the shortcode starting with the word **`MASTER`**.
   - *Example:* `MASTER: I am a welder in Nairobi looking for a hardworking apprentice.`
3. **The Result:**
   - Watch the **Live Dashboard**! The Master's request will appear, and the matching youth will receive an SMS automatically.

## 6. Team Members
- **Malcolm Kioko** - Lead AI Agent & Backend Engineer
- **Macklee Gitonga**
- **Abigail Wairi**
- **Lucy Karimi**

## 7. Project Submission
- **GitHub:** [https://github.com/perfectmalcolm/Apprenticeship-Matcher](https://github.com/perfectmalcolm/Apprenticeship-Matcher)
- **Live Demo:** [https://jua-kali-matcher-775881152318.us-central1.run.app/dashboard](https://jua-kali-matcher-775881152318.us-central1.run.app/dashboard)
