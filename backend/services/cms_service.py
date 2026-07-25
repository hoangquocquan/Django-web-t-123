from datetime import datetime

from repositories import cms_repository
from utils.text import get_page_offset, make_slug


VALID_STATUS = {"draft", "published", "archived"}


def get_paginated_pages(q="", page=1, per_page=8):
    return cms_repository.list_paginated("cms_pages", ["title", "slug", "content", "status"], f"%{q.strip()}%", per_page, get_page_offset(page, per_page), "sort_order, id DESC")


def get_page_record(page_id):
    return cms_repository.get_record("cms_pages", page_id)


def get_public_page_by_slug(slug):
    """Lấy trang động public theo slug, ví dụ /about hoặc /privacy."""
    return cms_repository.get_public_page_by_slug(slug)


def get_active_banners(placement):
    """Lấy banner published để render ngoài trang chủ."""
    return cms_repository.list_active_banners(placement)


def save_page(payload, page_id=None):
    title = str(payload.get("title", "")).strip()
    status = str(payload.get("status", "draft")).strip() or "draft"
    if not title:
        raise ValueError("Tiêu đề trang là bắt buộc.")
    if status not in VALID_STATUS:
        raise ValueError("Status chỉ được là draft, published hoặc archived.")
    page = {
        "title": title,
        "slug": str(payload.get("slug", "")).strip() or make_slug(title),
        "content": str(payload.get("content", "")).strip(),
        "seo_title": str(payload.get("seo_title", title)).strip(),
        "seo_description": str(payload.get("seo_description", "")).strip(),
        "status": status,
        "sort_order": int(payload.get("sort_order", 0) or 0),
    }
    if page_id:
        cms_repository.update_page(page_id, page)
        return get_page_record(page_id)
    return get_page_record(cms_repository.insert_page(page))


def delete_page(page_id):
    item = get_page_record(page_id)
    if item:
        cms_repository.delete_record("cms_pages", page_id)
    return item


def get_menu_items():
    return cms_repository.list_menu_items()


def get_menu_record(item_id):
    return cms_repository.get_record("cms_menu_items", item_id)


def save_menu_item(payload, item_id=None):
    label = str(payload.get("label", "")).strip()
    url = str(payload.get("url", "")).strip()
    if not label or not url:
        raise ValueError("Label và URL menu là bắt buộc.")
    parent_id = int(payload.get("parent_id", 0) or 0) or None
    item = {
        "location": str(payload.get("location", "header")).strip() or "header",
        "parent_id": parent_id,
        "label": label,
        "url": url,
        "sort_order": int(payload.get("sort_order", 0) or 0),
        "status": str(payload.get("status", "published")).strip() or "published",
    }
    if item_id:
        cms_repository.update_menu_item(item_id, item)
        return get_menu_record(item_id)
    return get_menu_record(cms_repository.insert_menu_item(item))


def delete_menu_item(item_id):
    item = get_menu_record(item_id)
    if item:
        cms_repository.delete_record("cms_menu_items", item_id)
    return item


def get_paginated_banners(q="", page=1, per_page=8):
    return cms_repository.list_paginated("cms_banners", ["title", "placement", "status", "content"], f"%{q.strip()}%", per_page, get_page_offset(page, per_page), "sort_order, id DESC")


def get_banner_record(banner_id):
    return cms_repository.get_record("cms_banners", banner_id)


def save_banner(payload, banner_id=None):
    title = str(payload.get("title", "")).strip()
    if not title:
        raise ValueError("Tiêu đề banner là bắt buộc.")
    banner = {
        "title": title,
        "placement": str(payload.get("placement", "home_slider")).strip() or "home_slider",
        "image_url": str(payload.get("image_url", "")).strip(),
        "link_url": str(payload.get("link_url", "")).strip(),
        "content": str(payload.get("content", "")).strip(),
        "sort_order": int(payload.get("sort_order", 0) or 0),
        "status": str(payload.get("status", "draft")).strip() or "draft",
        "starts_at": str(payload.get("starts_at", "")).strip(),
        "ends_at": str(payload.get("ends_at", "")).strip(),
    }
    if banner_id:
        cms_repository.update_banner(banner_id, banner)
        return get_banner_record(banner_id)
    return get_banner_record(cms_repository.insert_banner(banner))


def delete_banner(banner_id):
    item = get_banner_record(banner_id)
    if item:
        cms_repository.delete_record("cms_banners", banner_id)
    return item


def get_paginated_quotes(q="", page=1, per_page=8):
    return cms_repository.list_quotes(f"%{q.strip()}%", per_page, get_page_offset(page, per_page))


def get_quote_record(quote_id):
    return cms_repository.get_record("quote_requests", quote_id)


def get_admin_options():
    return cms_repository.list_admin_options()


def save_quote(payload, quote_id):
    quote = {
        "status": str(payload.get("status", "new")).strip() or "new",
        "assigned_to": int(payload.get("assigned_to", 0) or 0) or None,
        "internal_note": str(payload.get("internal_note", "")).strip(),
        "quoted_at": str(payload.get("quoted_at", "")).strip(),
        "completed_at": str(payload.get("completed_at", "")).strip(),
    }
    cms_repository.update_quote(quote_id, quote)
    return get_quote_record(quote_id)


def create_public_quote_request(payload):
    """Tạo yêu cầu báo giá từ form public."""
    contact_name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    product_name = str(payload.get("product", "")).strip()
    if not contact_name or not (email or phone) or not product_name:
        raise ValueError("Cần nhập tên, email/điện thoại và sản phẩm cần báo giá.")

    customer = {
        "company_name": str(payload.get("company", "")).strip(),
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "country": str(payload.get("country", "Vietnam")).strip() or "Vietnam",
    }
    quote = {
        "project_name": f"Báo giá {product_name}",
        "message": str(payload.get("note", "")).strip(),
    }
    item = {
        "drawing_code": product_name,
        "quantity": int(payload.get("quantity", 1) or 1),
        "tolerance": str(payload.get("tolerance", "")).strip(),
        "note": f"Deadline: {payload.get('deadline', '')}. {payload.get('note', '')}".strip(),
    }
    files = [
        {"file_name": "drawing_pdf", "file_url": str(payload.get("drawing_pdf", "")).strip(), "file_type": "pdf"},
        {"file_name": "step_file", "file_url": str(payload.get("step_file", "")).strip(), "file_type": "step"},
        {"file_name": "dwg_file", "file_url": str(payload.get("dwg_file", "")).strip(), "file_type": "dwg"},
    ]
    quote_id = cms_repository.insert_quote_request_with_item(customer, quote, item, files)
    return get_quote_record(quote_id)


def get_paginated_customers(q="", page=1, per_page=8):
    return cms_repository.list_paginated("customers", ["company_name", "contact_name", "email", "phone", "country"], f"%{q.strip()}%", per_page, get_page_offset(page, per_page))


def get_customer_record(customer_id):
    return cms_repository.get_record("customers", customer_id)


def save_customer(payload, customer_id=None):
    contact_name = str(payload.get("contact_name", "")).strip()
    if not contact_name:
        raise ValueError("Tên liên hệ là bắt buộc.")
    customer = {
        "company_name": str(payload.get("company_name", "")).strip(),
        "contact_name": contact_name,
        "email": str(payload.get("email", "")).strip(),
        "phone": str(payload.get("phone", "")).strip(),
        "country": str(payload.get("country", "Vietnam")).strip() or "Vietnam",
    }
    if customer_id:
        cms_repository.update_customer(customer_id, customer)
        return get_customer_record(customer_id)
    return get_customer_record(cms_repository.insert_customer(customer))


def delete_customer(customer_id):
    item = get_customer_record(customer_id)
    if item:
        cms_repository.delete_record("customers", customer_id)
    return item


def add_customer_note(customer_id, note, created_by):
    note = str(note or "").strip()
    if not note:
        raise ValueError("Nội dung ghi chú là bắt buộc.")
    return cms_repository.insert_customer_note(customer_id, note, created_by)


def get_customer_notes(customer_id):
    return cms_repository.list_customer_notes(customer_id)


def get_paginated_newsletter(q="", page=1, per_page=8):
    return cms_repository.list_paginated("newsletter_subscribers", ["email", "status"], f"%{q.strip()}%", per_page, get_page_offset(page, per_page))


def get_newsletter_record(subscriber_id):
    return cms_repository.get_record("newsletter_subscribers", subscriber_id)


def save_newsletter(payload, subscriber_id=None):
    email = str(payload.get("email", "")).strip().lower()
    status = str(payload.get("status", "subscribed")).strip() or "subscribed"
    if "@" not in email:
        raise ValueError("Email newsletter không hợp lệ.")
    if status not in {"subscribed", "unsubscribed"}:
        raise ValueError("Status newsletter không hợp lệ.")
    subscriber = {
        "email": email,
        "status": status,
        "unsubscribed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == "unsubscribed" else "",
    }
    return get_newsletter_record(cms_repository.upsert_newsletter(subscriber))


def delete_newsletter(subscriber_id):
    item = get_newsletter_record(subscriber_id)
    if item:
        cms_repository.delete_record("newsletter_subscribers", subscriber_id)
    return item


def get_newsletter_csv_rows():
    return cms_repository.list_all_newsletter_subscribers()
