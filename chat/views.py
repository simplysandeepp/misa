import os
import requests
import json
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("OPENROUTER_API_KEY")

def get_session_messages(request):
    if 'messages' not in request.session:
        request.session['messages'] = [
            {"role": "system", "content": "You are a highly capable AI assistant. Adapt your response length to the user's query: for simple greetings or casual chat (like 'hi' or 'hello'), be brief, friendly, and concise. For complex questions, provide detailed answers. Use clean formatting: prefer simple numbered lists (1. 2. 3.) and bullet points, and avoid excessive markdown symbols."}
        ]
    return request.session['messages']

def home(request):
    # Ensure session is created if it doesn't exist
    if not request.session.session_key:
        request.session.create()
    return render(request, "index.html")

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_input = data.get("message")
            if not user_input:
                return JsonResponse({"error": "No message provided"}, status=400)
                
            messages = get_session_messages(request)
            messages.append({"role": "user", "content": user_input})
            request.session['messages'] = messages
            request.session.save()
            
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
                        "reasoning": {"enabled": False},
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
                
                # Update session manually since StreamingHttpResponse bypasses middleware saving
                messages.append({"role": "assistant", "content": full_reply})
                request.session['messages'] = messages
                request.session.save()
                
            return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Invalid method"}, status=405)

@csrf_exempt
def clear_chat(request):
    if request.method == "POST":
        request.session['messages'] = [
            {"role": "system", "content": "You are a highly capable AI assistant. Adapt your response length to the user's query: for simple greetings or casual chat (like 'hi' or 'hello'), be brief, friendly, and concise. For complex questions, provide detailed answers. Use clean formatting: prefer simple numbered lists (1. 2. 3.) and bullet points, and avoid excessive markdown symbols."}
        ]
        request.session.save()
        return JsonResponse({"status": "cleared"})
    return JsonResponse({"error": "Invalid method"}, status=405)

def chat_history(request):
    if request.method == "GET":
        messages = get_session_messages(request)
        history = [msg for msg in messages if msg.get('role') != 'system']
        return JsonResponse({"history": history})
    return JsonResponse({"error": "Invalid method"}, status=405)
