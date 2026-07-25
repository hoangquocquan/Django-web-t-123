"""Views Django cho module Products.

Giai đoạn này tạo public HTML tối giản và JSON API cho Product.
"""

from django.http import JsonResponse
from django.shortcuts import render

from .services import (
    filter_products,
    get_product_categories,
    get_product_detail,
    paginate_products,
    product_detail_to_dict,
    product_to_dict,
)


def product_list(request):
    """Trang danh sách sản phẩm theo Django template."""
    queryset = filter_products(
        keyword=request.GET.get("q", ""),
        category_id=int(request.GET.get("category_id") or 0),
        status=request.GET.get("status", "published"),
        sort=request.GET.get("sort", "newest"),
    )
    page_obj = paginate_products(queryset, page=request.GET.get("page", 1), per_page=8)
    return render(
        request,
        "products/product_list.html",
        {
            "page_obj": page_obj,
            "categories": get_product_categories(),
            "q": request.GET.get("q", ""),
        },
    )


def product_detail(request, product_id):
    """Trang chi tiết sản phẩm."""
    product = get_product_detail(product_id)
    return render(request, "products/product_detail.html", {"product": product})


def product_list_api(request):
    """API JSON danh sách sản phẩm published."""
    queryset = filter_products(
        keyword=request.GET.get("q", ""),
        category_id=int(request.GET.get("category_id") or 0),
        status=request.GET.get("status", "published"),
        sort=request.GET.get("sort", "newest"),
    )
    page_obj = paginate_products(queryset, page=request.GET.get("page", 1), per_page=20)
    return JsonResponse(
        {
            "count": page_obj.paginator.count,
            "page": page_obj.number,
            "num_pages": page_obj.paginator.num_pages,
            "results": [product_to_dict(product) for product in page_obj.object_list],
        }
    )


def product_detail_api(request, product_id):
    """API JSON chi tiết sản phẩm."""
    product = get_product_detail(product_id)
    return JsonResponse(product_detail_to_dict(product))
