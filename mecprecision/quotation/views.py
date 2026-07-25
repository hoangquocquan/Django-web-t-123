"""Views Django cho module Quotation."""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .services import (
    create_public_quote_request,
    filter_quotes,
    get_quote_detail,
    paginate_quotes,
    quote_detail_to_dict,
    quote_to_dict,
)


def quote_list(request):
    """Trang danh sách yêu cầu báo giá."""
    queryset = filter_quotes(
        keyword=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        sort=request.GET.get("sort", "newest"),
    )
    page_obj = paginate_quotes(queryset, page=request.GET.get("page", 1), per_page=10)
    return render(
        request,
        "quotation/quote_list.html",
        {"page_obj": page_obj, "q": request.GET.get("q", ""), "status": request.GET.get("status", "")},
    )


def quote_detail(request, quote_id):
    """Trang chi tiết một yêu cầu báo giá."""
    quote = get_quote_detail(quote_id)
    return render(request, "quotation/quote_detail.html", {"quote": quote})


def quote_list_api(request):
    """API JSON danh sách báo giá."""
    queryset = filter_quotes(
        keyword=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        sort=request.GET.get("sort", "newest"),
    )
    page_obj = paginate_quotes(queryset, page=request.GET.get("page", 1), per_page=20)
    return JsonResponse(
        {
            "count": page_obj.paginator.count,
            "page": page_obj.number,
            "num_pages": page_obj.paginator.num_pages,
            "results": [quote_to_dict(quote) for quote in page_obj.object_list],
        }
    )


def quote_detail_api(request, quote_id):
    """API JSON chi tiết báo giá."""
    quote = get_quote_detail(quote_id)
    return JsonResponse(quote_detail_to_dict(quote))


@csrf_exempt
def public_quote_create_api(request):
    """API demo tạo báo giá từ form public.

    Trong dự án thật nên dùng CSRF/token đầy đủ. Ở giai đoạn demo, endpoint này
    mở để dễ thử bằng JavaScript hoặc Postman trên local.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        quote = create_public_quote_request(payload)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"id": quote.id, "message": "Đã tạo yêu cầu báo giá.", "quote": quote_detail_to_dict(quote)}, status=201)
