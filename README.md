# Misa - Hinglish AI Chatbot

A highly capable, unfiltered AI chatbot powered by the **NVIDIA Nemotron-3.5-Lightning** model via OpenRouter. Misa acts as a close, humorous "bro" who speaks fluently in Hinglish (Hindi + English) and pure English. 

Built with Django on the backend and plain HTML/JS on the frontend, this app features:
- **Real-time Streaming**: Watch the AI type out its responses in real-time, just like ChatGPT.
- **Multiple Chat Sessions**: Sidebar UI to create, switch between, and delete independent chat threads.
- **Persistent Memory**: Uses Django sessions to remember conversation context per chat tab.
- **Custom Persona**: Tuned for 18+ adult, dark-humored, brotherhood-style banter.

## Setup Instructions

1. Clone the repository.
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file in the root directory and add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```
6. Run database migrations to enable session storage: `python manage.py migrate`
7. Start the development server: `python manage.py runserver`
8. Open your browser and navigate to `http://127.0.0.1:8000/`.
