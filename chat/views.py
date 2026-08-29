import os
import requests
import json
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("OPENROUTER_API_KEY")

SYSTEM_PROMPT = {"role": "system", "content": "You are 'Misa', a highly knowledgeable and encouraging AI study partner and companion. Your primary goal is to help the user learn various subjects, explain complex topics clearly, and support their educational journey. Be concise when needed, but provide detailed, well-structured explanations for academic or technical questions. Use clean formatting (1. 2. 3. or bullet points) without excessive markdown symbols."}

def get_chats(request):
    if 'chats' not in request.session:
        request.session['chats'] = {'Chat 1': [SYSTEM_PROMPT]}
    return request.session['chats']

def landing(request):
    return render(request, "landing.html")

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
            chat_id = data.get("chat_id", "Chat 1")
            
            if not user_input:
                return JsonResponse({"error": "No message provided"}, status=400)
                
            chats = get_chats(request)
            if chat_id not in chats:
                chats[chat_id] = [SYSTEM_PROMPT]
                
            messages = chats[chat_id]
            messages.append({"role": "user", "content": user_input})
            chats[chat_id] = messages
            request.session['chats'] = chats
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
                        "model": "meta-llama/llama-3.1-8b-instruct:free",
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
                chats[chat_id] = messages
                request.session['chats'] = chats
                request.session.save()
                
            return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Invalid method"}, status=405)

@csrf_exempt
def clear_chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chat_id = data.get("chat_id", "Chat 1")
        chats = get_chats(request)
        chats[chat_id] = [SYSTEM_PROMPT]
        request.session['chats'] = chats
        request.session.save()
        return JsonResponse({"status": "cleared"})
    return JsonResponse({"error": "Invalid method"}, status=405)

def chat_history(request):
    if request.method == "GET":
        chat_id = request.GET.get('chat_id', 'Chat 1')
        chats = get_chats(request)
        if chat_id not in chats:
            chats[chat_id] = [SYSTEM_PROMPT]
            request.session['chats'] = chats
            request.session.save()
            
        history = [msg for msg in chats[chat_id] if msg.get('role') != 'system']
        return JsonResponse({"history": history, "chat_ids": list(chats.keys())})
    return JsonResponse({"error": "Invalid method"}, status=405)

@csrf_exempt
def delete_chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chat_id = data.get("chat_id")
        chats = get_chats(request)
        if chat_id in chats and len(chats) > 1:
            del chats[chat_id]
            request.session['chats'] = chats
            request.session.save()
            return JsonResponse({"status": "deleted", "chat_ids": list(chats.keys())})
        elif len(chats) == 1:
            return JsonResponse({"error": "Cannot delete the last chat"}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)
