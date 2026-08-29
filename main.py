import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the client pointing to OpenRouter
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.environ.get("OPENROUTER_API_KEY"),
)

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
            # Using a free model available on OpenRouter
            response = client.chat.completions.create(
                model="meta-llama/llama-3.1-8b-instruct:free",
                messages=messages,
            )
            
            bot_reply = response.choices[0].message.content
            print(f"\nBot: {bot_reply}")
            
            messages.append({"role": "assistant", "content": bot_reply})
            
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    chat()
