"""Service layer cho Product trong Django.

Service gom query và chuẩn hóa output để view không phải biết quá nhiều chi tiết model.
"""

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Product, ProductCategory


def get_published_products():
    """Lấy sản phẩm đã published cho trang public/API."""
    return Product.objects.select_related("category").filter(status=Product.STATUS_PUBLISHED)


def filter_products(keyword="", category_id=0, status="", sort="newest"):
    """Lọc sản phẩm theo keyword, danh mục, trạng thái và kiểu sắp xếp."""
    queryset = Product.objects.select_related("category")
    keyword = str(keyword or "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword)
            | Q(short_description__icontains=keyword)
            | Q(sku__icontains=keyword)
            | Q(category__name__icontains=keyword)
        )
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if status:
        queryset = queryset.filter(status=status)

    sort_map = {
        "oldest": "id",
        "name": "name",
        "price_desc": "-price",
        "price_asc": "price",
        "sort_order": "sort_order",
    }
    return queryset.order_by(sort_map.get(sort, "-id"), "-id")


def paginate_products(queryset, page=1, per_page=8):
    """Phân trang sản phẩm bằng Paginator có sẵn của Django."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page)


def get_product_detail(product_id):
    """Lấy chi tiết sản phẩm published hoặc trả 404."""
    return get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images", "specs"),
        id=product_id,
        status=Product.STATUS_PUBLISHED,
    )


def get_product_categories():
    """Lấy toàn bộ danh mục sản phẩm."""
    return ProductCategory.objects.all()


def product_to_dict(product):
    """Đổi Product model thành dict để trả JSON API."""
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "category": product.category.name,
        "description": product.short_description,
        "image": product.main_image,
        "thumbnail_url": product.thumbnail_url,
        "sku": product.sku,
        "price": product.price,
        "status": product.status,
        "sort_order": product.sort_order,
    }


def product_detail_to_dict(product):
    """Đổi chi tiết Product thành dict đầy đủ hơn."""
    data = product_to_dict(product)
    data.update(
        {
            "long_description": product.description,
            "pdf_url": product.pdf_url,
            "video_url": product.video_url,
            "tags_text": product.tags_text,
            "seo_title": product.seo_title,
            "seo_description": product.seo_description,
            "seo_keywords": product.seo_keywords,
            "images": [
                {"url": image.image_url, "alt": image.alt_text, "sort_order": image.sort_order}
                for image in product.images.all()
            ],
            "specs": [
                {
                    "name": spec.spec_name,
                    "value": spec.spec_value,
                    "unit": spec.unit,
                    "sort_order": spec.sort_order,
                }
                for spec in product.specs.all()
            ],
        }
    )
    return data
