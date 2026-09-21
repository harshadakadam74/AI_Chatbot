# AI Chatbot

A Streamlit chatbot powered by Gemini or the OpenAI Responses API with conversational memory, assistant modes, and local SQLite chat history.

## Setup

1. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set `GEMINI_API_KEY`.

4. Start the app:

   ```powershell
   streamlit run app.py
   ```

Gemini is the default provider. Set `AI_PROVIDER=openai` to use OpenAI instead. The selected provider's model setting must be available to your API account.

## Project layout

- `app.py`: Streamlit UI and session state.
- `chatbot.py`: Gemini and OpenAI API integrations.
- `utils/database.py`: SQLite persistence helpers.
- `database/chat_history.db`: Created automatically at runtime.

The sidebar supports separate conversations for General Assistant, Python Tutor, Coding Assistant, Resume Assistant, English Tutor, and Study Assistant. Each mode adds a focused system prompt while preserving the conversation history for that chat.
