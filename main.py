import os
import requests
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")

app = Flask(__name__)

# Store conversation history in memory for simplicity
# Updated the system prompt to explicitly ask for detailed and comprehensive answers.
messages = [
    {"role": "system", "content": "You are a highly capable AI assistant. Please provide very detailed, well-structured, and comprehensive answers to all user questions. Expand on topics to ensure the user gets a full understanding."}
]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
        
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Using the NVIDIA model with reasoning enabled
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Local Chatbot"
            },
            data=json.dumps({
                "model": "nvidia/nemotron-3.5-lightning:free",
                "messages": messages,
                "reasoning": {"enabled": True},
                "max_tokens": 4096 # Allow for long, detailed answers
            })
        )
        
        response_data = response.json()
        
        if response.status_code == 401:
            return jsonify({"error": f"Authentication Error: OpenRouter rejected your API key. (Error: {response_data.get('error', {}).get('message')})"}), 401
            
        if 'error' in response_data:
            return jsonify({"error": str(response_data['error'])}), 500
            
        assistant_message = response_data['choices'][0]['message']
        bot_reply = assistant_message.get('content')
        reasoning_details = assistant_message.get('reasoning_details')
        
        # Preserve the assistant message with reasoning_details for context
        new_message = {
            "role": "assistant",
            "content": bot_reply
        }
        if reasoning_details:
            new_message["reasoning_details"] = reasoning_details
            
        messages.append(new_message)
        
        return jsonify({
            "reply": bot_reply,
            "reasoning": reasoning_details
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not API_KEY or API_KEY == "your_openrouter_api_key_here":
        print("WARNING: Please set your OPENROUTER_API_KEY in the .env file.")
    print("Starting server... Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True, port=5000)
