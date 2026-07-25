"""Views Django cho module Customers.

File này có hai nhóm view:
- HTML view: render template để người dùng xem trên trình duyệt.
- API view: trả JSON để frontend hoặc hệ thống khác có thể tích hợp.
"""

from django.http import JsonResponse
from django.shortcuts import render

from .services import (
    contact_request_to_dict,
    customer_detail_to_dict,
    customer_to_dict,
    filter_contact_requests,
    filter_customers,
    get_contact_request_detail,
    get_customer_detail,
    paginate_queryset,
)


def customer_list(request):
    """Trang danh sách khách hàng."""
    queryset = filter_customers(keyword=request.GET.get("q", ""), sort=request.GET.get("sort", "newest"))
    page_obj = paginate_queryset(queryset, page=request.GET.get("page", 1), per_page=10)
    return render(request, "customers/customer_list.html", {"page_obj": page_obj, "q": request.GET.get("q", "")})


def customer_detail(request, customer_id):
    """Trang chi tiết khách hàng."""
    customer = get_customer_detail(customer_id)
    return render(request, "customers/customer_detail.html", {"customer": customer})


def contact_request_list(request):
    """Trang danh sách liên hệ khách gửi từ website."""
    queryset = filter_contact_requests(
        keyword=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        sort=request.GET.get("sort", "newest"),
    )
    page_obj = paginate_queryset(queryset, page=request.GET.get("page", 1), per_page=10)
    return render(
        request,
        "customers/contact_request_list.html",
        {
            "page_obj": page_obj,
            "q": request.GET.get("q", ""),
            "status": request.GET.get("status", ""),
        },
    )


def contact_request_detail(request, contact_id):
    """Trang chi tiết một liên hệ."""
    contact = get_contact_request_detail(contact_id)
    return render(request, "customers/contact_request_detail.html", {"contact": contact})


def customer_list_api(request):
    """API JSON danh sách khách hàng."""
    queryset = filter_customers(keyword=request.GET.get("q", ""), sort=request.GET.get("sort", "newest"))
    page_obj = paginate_queryset(queryset, page=request.GET.get("page", 1), per_page=20)
    return JsonResponse(
        {
            "count": page_obj.paginator.count,
            "page": page_obj.number,
            "num_pages": page_obj.paginator.num_pages,
            "results": [customer_to_dict(customer) for customer in page_obj.object_list],
        }
    )


def customer_detail_api(request, customer_id):
    """API JSON chi tiết khách hàng."""
    customer = get_customer_detail(customer_id)
    return JsonResponse(customer_detail_to_dict(customer))


def contact_request_list_api(request):
    """API JSON danh sách liên hệ."""
    queryset = filter_contact_requests(
        keyword=request.GET.get("q", ""),
        status=request.GET.get("status", ""),
        sort=request.GET.get("sort", "newest"),
    )
    page_obj = paginate_queryset(queryset, page=request.GET.get("page", 1), per_page=20)
    return JsonResponse(
        {
            "count": page_obj.paginator.count,
            "page": page_obj.number,
            "num_pages": page_obj.paginator.num_pages,
            "results": [contact_request_to_dict(contact) for contact in page_obj.object_list],
        }
    )


def contact_request_detail_api(request, contact_id):
    """API JSON chi tiết liên hệ."""
    contact = get_contact_request_detail(contact_id)
    return JsonResponse(contact_request_to_dict(contact))
