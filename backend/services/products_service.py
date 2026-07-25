from repositories import products_repository
from utils.text import get_page_offset, make_slug, parse_bool


def get_products():
    """Service lấy danh sách sản phẩm cho public/API."""
    return products_repository.list_products()


def get_product_categories():
    """Service lấy danh mục sản phẩm."""
    return products_repository.list_product_categories()


def get_paginated_products(q="", page=1, per_page=8, category_id=0, status="", sort="newest"):
    """Service lấy sản phẩm cho trang CMS có tìm kiếm/phân trang."""
    filters = {
        "keyword": f"%{q.strip()}%",
        "category_id": int(category_id or 0),
        "status": str(status or "").strip(),
        "sort": str(sort or "newest").strip(),
    }
    return products_repository.list_paginated_products(filters, per_page, get_page_offset(page, per_page))


def get_product_by_id(product_id):
    """Service lấy sản phẩm theo id."""
    return products_repository.get_product_by_id(product_id)


def get_product_record(product_id):
    """Service lấy bản ghi gốc để điền form CMS."""
    return products_repository.get_product_record(product_id)


def normalize_product_payload(payload, existing_product=None):
    """Chuẩn hóa và kiểm tra dữ liệu sản phẩm trước khi ghi database."""
    source = existing_product or {}
    category_id = int(payload.get("category_id", source.get("category_id", 0)) or 0)
    name = str(payload.get("name", source.get("name", ""))).strip()
    short_description = str(payload.get("short_description", source.get("short_description", ""))).strip()
    description = str(payload.get("description", source.get("description", ""))).strip()
    main_image = str(payload.get("main_image", source.get("main_image", ""))).strip()
    is_featured = parse_bool(payload.get("is_featured", source.get("is_featured", 0)))
    sku = str(payload.get("sku", source.get("sku", ""))).strip()
    price = float(payload.get("price", source.get("price", 0)) or 0)
    thumbnail_url = str(payload.get("thumbnail_url", source.get("thumbnail_url", main_image))).strip() or main_image
    gallery_urls = str(payload.get("gallery_urls", source.get("gallery_urls", ""))).strip()
    pdf_url = str(payload.get("pdf_url", source.get("pdf_url", ""))).strip()
    video_url = str(payload.get("video_url", source.get("video_url", ""))).strip()
    tags_text = str(payload.get("tags_text", source.get("tags_text", ""))).strip()
    seo_title = str(payload.get("seo_title", source.get("seo_title", name))).strip()
    seo_description = str(payload.get("seo_description", source.get("seo_description", short_description))).strip()
    seo_keywords = str(payload.get("seo_keywords", source.get("seo_keywords", ""))).strip()
    canonical_url = str(payload.get("canonical_url", source.get("canonical_url", ""))).strip()
    og_image = str(payload.get("og_image", source.get("og_image", thumbnail_url))).strip() or thumbnail_url
    robots = str(payload.get("robots", source.get("robots", "index,follow"))).strip() or "index,follow"
    schema_json = str(payload.get("schema_json", source.get("schema_json", ""))).strip()
    related_product_ids = str(payload.get("related_product_ids", source.get("related_product_ids", ""))).strip()
    sort_order = int(payload.get("sort_order", source.get("sort_order", 0)) or 0)
    status = str(payload.get("status", source.get("status", "published"))).strip() or "published"
    published_at = str(payload.get("published_at", source.get("published_at", ""))).strip()

    if "slug" in payload:
        slug = str(payload.get("slug", "")).strip() or make_slug(name)
    elif existing_product:
        slug = str(existing_product["slug"])
    else:
        slug = make_slug(name)

    if not category_id or not name or not short_description or not description or not main_image:
        raise ValueError("Thiếu dữ liệu. Cần category_id, name, short_description, description và main_image.")

    if not products_repository.product_category_exists(category_id):
        raise ValueError("category_id không tồn tại trong bảng product_categories.")
    if status not in {"draft", "published", "archived"}:
        raise ValueError("Status sản phẩm chỉ được là draft, published hoặc archived.")

    return {
        "category_id": category_id,
        "name": name,
        "slug": slug,
        "short_description": short_description,
        "description": description,
        "main_image": main_image,
        "is_featured": is_featured,
        "sku": sku,
        "price": price,
        "thumbnail_url": thumbnail_url,
        "gallery_urls": gallery_urls,
        "pdf_url": pdf_url,
        "video_url": video_url,
        "tags_text": tags_text,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "seo_keywords": seo_keywords,
        "canonical_url": canonical_url,
        "og_image": og_image,
        "robots": robots,
        "schema_json": schema_json,
        "related_product_ids": related_product_ids,
        "sort_order": sort_order,
        "status": status,
        "published_at": published_at,
    }


def create_product(payload):
    """Tạo sản phẩm mới từ JSON/form CMS."""
    product = normalize_product_payload(payload)
    product_id = products_repository.insert_product(product)
    return get_product_by_id(product_id)


def update_product(product_id, payload):
    """Cập nhật sản phẩm theo id."""
    existing_product = get_product_record(product_id)
    if not existing_product:
        return None

    product = normalize_product_payload(payload, existing_product)
    products_repository.update_product_record(product_id, product)
    return get_product_by_id(product_id)


def delete_product(product_id):
    """Xóa sản phẩm theo id."""
    # CMS cần xóa được cả draft/archived nên đọc bảng gốc, không đọc public query.
    product = get_product_record(product_id)
    if not product:
        return None
    products_repository.delete_product_record(product_id)
    return product
