"""Views Django cho module Chatbot."""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .services import send_chatbot_message


def chatbot_home(request):
    """Trang demo chatbot public."""
    return render(request, "chatbot/chatbot_home.html")


@csrf_exempt
def chatbot_message_api(request):
    """API nhận câu hỏi chatbot và trả câu trả lời AI."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        result = send_chatbot_message(payload.get("message", ""), payload.get("model"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(result)
