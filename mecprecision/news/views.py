"""Views Django cho module News."""

from django.http import JsonResponse
from django.shortcuts import render

from .services import (
    filter_news,
    get_news_categories,
    get_news_detail,
    news_detail_to_dict,
    news_to_dict,
    paginate_news,
)


def news_list(request):
    """Trang danh sách tin tức public."""
    queryset = filter_news(
        keyword=request.GET.get("q", ""),
        category_id=int(request.GET.get("category_id") or 0),
        sort=request.GET.get("sort", "newest"),
        public_only=True,
    )
    page_obj = paginate_news(queryset, page=request.GET.get("page", 1), per_page=9)
    return render(
        request,
        "news/news_list.html",
        {"page_obj": page_obj, "categories": get_news_categories(), "q": request.GET.get("q", "")},
    )


def news_detail(request, news_id):
    """Trang chi tiết tin tức public."""
    article = get_news_detail(news_id, public_only=True)
    return render(request, "news/news_detail.html", {"article": article})


def news_list_api(request):
    """API JSON danh sách tin tức."""
    queryset = filter_news(
        keyword=request.GET.get("q", ""),
        category_id=int(request.GET.get("category_id") or 0),
        status=request.GET.get("status", "published"),
        sort=request.GET.get("sort", "newest"),
        public_only=request.GET.get("public_only", "1") != "0",
    )
    page_obj = paginate_news(queryset, page=request.GET.get("page", 1), per_page=20)
    return JsonResponse(
        {
            "count": page_obj.paginator.count,
            "page": page_obj.number,
            "num_pages": page_obj.paginator.num_pages,
            "results": [news_to_dict(article) for article in page_obj.object_list],
        }
    )


def news_detail_api(request, news_id):
    """API JSON chi tiết tin tức."""
    article = get_news_detail(news_id, public_only=request.GET.get("public_only", "1") != "0")
    return JsonResponse(news_detail_to_dict(article))
