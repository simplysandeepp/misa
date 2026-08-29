import os
import requests
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Store conversation history in memory for simplicity
messages = [
    {"role": "system", "content": "You are a highly capable AI assistant. Adapt your response length to the user's query: for simple greetings or casual chat (like 'hi' or 'hello'), be brief, friendly, and concise. For complex questions or when asked for explanations, provide detailed, well-structured, and comprehensive answers."}
]

def home(request):
    return render(request, "index.html")

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_input = data.get("message")
            if not user_input:
                return JsonResponse({"error": "No message provided"}, status=400)
                
            messages.append({"role": "user", "content": user_input})
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Django Local Chatbot"
                },
                data=json.dumps({
                    "model": "nvidia/nemotron-3.5-lightning:free",
                    "messages": messages,
                    "reasoning": {"enabled": True},
                    "max_tokens": 4096
                })
            )
            
            response_data = response.json()
            
            if response.status_code == 401:
                return JsonResponse({"error": f"Authentication Error: OpenRouter rejected your API key. (Error: {response_data.get('error', {}).get('message')})"}), 401
                
            if 'error' in response_data:
                return JsonResponse({"error": str(response_data['error'])}, status=500)
                
            assistant_message = response_data['choices'][0]['message']
            bot_reply = assistant_message.get('content')
            reasoning_details = assistant_message.get('reasoning_details')
            
            new_message = {
                "role": "assistant",
                "content": bot_reply
            }
            if reasoning_details:
                new_message["reasoning_details"] = reasoning_details
                
            messages.append(new_message)
            
            return JsonResponse({
                "reply": bot_reply,
                "reasoning": reasoning_details
            })
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Invalid method"}, status=405)
