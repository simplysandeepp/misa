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
    {"role": "system", "content": "You are a highly capable AI assistant. Adapt your response length to the user's query: for simple greetings or casual chat (like 'hi' or 'hello'), be brief, friendly, and concise. For complex questions, provide detailed answers. Use clean formatting: prefer simple numbered lists (1. 2. 3.) and bullet points, and avoid excessive markdown symbols."}
]

def home(request):
    return render(request, "index.html")

from django.http import JsonResponse, StreamingHttpResponse

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_input = data.get("message")
            if not user_input:
                return JsonResponse({"error": "No message provided"}, status=400)
                
            messages.append({"role": "user", "content": user_input})
            
            def event_stream():
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "Django Local Chatbot"
                    },
                    json={
                        "model": "nvidia/nemotron-3.5-lightning:free",
                        "messages": messages,
                        "reasoning": {"enabled": True},
                        "max_tokens": 4096,
                        "stream": True
                    },
                    stream=True
                )
                
                full_reply = ""
                
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': 'API Error ' + str(response.status_code)})}\n\n"
                    return
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            payload = line[6:]
                            if payload == '[DONE]':
                                break
                            try:
                                chunk = json.loads(payload)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content_chunk = delta.get('content', '')
                                    if content_chunk:
                                        full_reply += content_chunk
                                        yield f"data: {json.dumps({'content': content_chunk})}\n\n"
                            except json.JSONDecodeError:
                                pass
                
                messages.append({"role": "assistant", "content": full_reply})
                
            return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Invalid method"}, status=405)

@csrf_exempt
def clear_chat(request):
    if request.method == "POST":
        global messages
        messages = [
            {"role": "system", "content": "You are a highly capable AI assistant. Adapt your response length to the user's query: for simple greetings or casual chat (like 'hi' or 'hello'), be brief, friendly, and concise. For complex questions or when asked for explanations, provide detailed, well-structured, and comprehensive answers."}
        ]
        return JsonResponse({"status": "cleared"})
    return JsonResponse({"error": "Invalid method"}, status=405)

def chat_history(request):
    if request.method == "GET":
        history = [msg for msg in messages if msg.get('role') != 'system']
        return JsonResponse({"history": history})
    return JsonResponse({"error": "Invalid method"}, status=405)
