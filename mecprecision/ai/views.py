"""Views Django cho module AI.

Các endpoint ở đây nhận JSON, gọi service AI, rồi trả JSON lại cho frontend/Admin.
"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .services import (
    analyze_quote_request,
    ask_ai,
    ask_developer_ai,
    generate_dashboard_insights,
    generate_product_content,
    get_ai_status,
    get_recent_ai_messages,
    smart_search_content,
    summarize_recent_contacts,
    translate_text,
)


def read_json_body(request):
    """Đọc JSON body từ request, nếu rỗng thì trả dict rỗng."""
    return json.loads(request.body.decode("utf-8") or "{}")


def ai_home(request):
    """Trang demo đơn giản để xem trạng thái AI và lịch sử gần nhất."""
    return render(request, "ai/ai_home.html", {"status": get_ai_status(), "messages": get_recent_ai_messages(20)})


@csrf_exempt
def chat_api(request):
    """API chatbot AI."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = read_json_body(request)
        result = ask_ai(payload.get("message", ""), channel=payload.get("channel", "public"), model=payload.get("model"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(result)


@csrf_exempt
def translate_api(request):
    """API AI dịch nội dung."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = read_json_body(request)
        result = translate_text(
            payload.get("source_text", ""),
            payload.get("target_language", ""),
            payload.get("source_language", ""),
            payload.get("tone", ""),
            payload.get("model"),
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(result)


@csrf_exempt
def developer_api(request):
    """API Developer AI để giải thích code/log."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = read_json_body(request)
        result = ask_developer_ai(payload.get("question", ""), payload.get("code_context", ""), payload.get("language", ""), payload.get("model"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(result)


@csrf_exempt
def product_content_api(request):
    """API AI tạo nội dung sản phẩm và SEO."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = read_json_body(request)
        result = generate_product_content(payload, payload.get("model"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(result)


def contacts_summary_api(request):
    """API AI tóm tắt liên hệ mới."""
    result = summarize_recent_contacts(limit=request.GET.get("limit", 8), model=request.GET.get("model"))
    return JsonResponse(result)


def quote_analysis_api(request):
    """API AI phân tích yêu cầu báo giá."""
    try:
        result = analyze_quote_request(quote_id=request.GET.get("quote_id", 0), model=request.GET.get("model"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(result)


def smart_search_api(request):
    """API AI tìm kiếm thông minh trong sản phẩm/tin tức."""
    try:
        result = smart_search_content(query=request.GET.get("q", ""), scope=request.GET.get("scope", "all"), model=request.GET.get("model"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(result)


def dashboard_insights_api(request):
    """API AI dashboard: hôm nay website có gì cần chú ý."""
    result = generate_dashboard_insights(model=request.GET.get("model"))
    return JsonResponse(result)


def status_api(request):
    """API trạng thái cấu hình AI."""
    return JsonResponse(get_ai_status())
