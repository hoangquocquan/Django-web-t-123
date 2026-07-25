from repositories import news_repository
from datetime import datetime
from utils.text import get_page_offset, make_slug, parse_bool


def get_news_categories():
    return news_repository.list_news_categories()


def get_paginated_news(q="", page=1, per_page=8, category_id=0, status="", sort="newest"):
    filters = {
        "keyword": f"%{q.strip()}%",
        "category_id": int(category_id or 0),
        "status": str(status or "").strip(),
        "sort": str(sort or "newest").strip(),
    }
    return news_repository.list_paginated_news(filters, per_page, get_page_offset(page, per_page))


def get_news_record(news_id):
    return news_repository.get_news_record(news_id)


def normalize_news_payload(payload):
    category_id = int(payload.get("category_id", 0) or 0)
    title = str(payload.get("title", "")).strip()
    slug = str(payload.get("slug", "")).strip() or make_slug(title)
    image = str(payload.get("image", "")).strip()
    description = str(payload.get("description", "")).strip()
    content = str(payload.get("content", "")).strip()
    tags_text = str(payload.get("tags_text", "")).strip()
    seo_title = str(payload.get("seo_title", title)).strip()
    seo_description = str(payload.get("seo_description", description)).strip()
    thumbnail_url = str(payload.get("thumbnail_url", image)).strip() or image
    author = str(payload.get("author", "MecPrecision Editorial")).strip()
    published_at = str(payload.get("published_at", "")).strip()
    scheduled_at = str(payload.get("scheduled_at", "")).strip()
    is_featured = parse_bool(payload.get("is_featured", 0))
    status = str(payload.get("status", "published")).strip() or "published"

    if not category_id or not title or not image or not description:
        raise ValueError("Cần nhập danh mục, tiêu đề, ảnh và mô tả tin tức.")
    if status not in {"draft", "published", "archived"}:
        raise ValueError("Status tin tức chỉ được là draft, published hoặc archived.")

    return {
        "category_id": category_id,
        "title": title,
        "slug": slug,
        "image": image,
        "description": description,
        "content": content,
        "tags_text": tags_text,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "thumbnail_url": thumbnail_url,
        "author": author,
        "published_at": published_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_at": scheduled_at,
        "is_featured": is_featured,
        "status": status,
    }


def save_news(payload, news_id=None):
    news = normalize_news_payload(payload)
    if news_id:
        news_repository.update_news_record(news_id, news)
        return get_news_record(news_id)
    new_id = news_repository.insert_news(news)
    return get_news_record(new_id)


def delete_news(news_id):
    item = get_news_record(news_id)
    if not item:
        return None
    news_repository.delete_news_record(news_id)
    return item
