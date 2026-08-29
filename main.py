import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")

def chat():
    print("Welcome to the Chatbot! (Type 'exit' to quit)")
    
    # Store conversation history
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Using the NVIDIA model with reasoning enabled
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000", # Recommended by OpenRouter
                    "X-Title": "Local Chatbot"              # Recommended by OpenRouter
                },
                data=json.dumps({
                    "model": "nvidia/nemotron-3.5-lightning:free",
                    "messages": messages,
                    "reasoning": {"enabled": True}
                })
            )
            
            response_data = response.json()
            
            if response.status_code == 401:
                print(f"\nAuthentication Error: OpenRouter rejected your API key. (Error: {response_data.get('error', {}).get('message')})")
                print("Please double-check that your OPENROUTER_API_KEY in the .env file is correct and your account is active.")
                continue
                
            if 'error' in response_data:
                print(f"\nAPI Error: {response_data['error']}")
                continue
                
            assistant_message = response_data['choices'][0]['message']
            bot_reply = assistant_message.get('content')
            reasoning_details = assistant_message.get('reasoning_details')
            
            print(f"\nBot: {bot_reply}")
            
            # Preserve the assistant message with reasoning_details for context
            new_message = {
                "role": "assistant",
                "content": bot_reply
            }
            if reasoning_details:
                new_message["reasoning_details"] = reasoning_details
                
            messages.append(new_message)
            
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    if not API_KEY or API_KEY == "your_openrouter_api_key_here":
        print("Please set your OPENROUTER_API_KEY in the .env file.")
    else:
        chat()
