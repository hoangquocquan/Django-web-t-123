from repositories import categories_repository
from utils.text import get_page_offset, make_slug


def get_paginated_categories(q="", page=1, per_page=8):
    keyword = f"%{q.strip()}%"
    return categories_repository.list_paginated_categories(keyword, per_page, get_page_offset(page, per_page))


def get_category_record(category_id):
    return categories_repository.get_category_record(category_id)


def save_category(payload, category_id=None):
    name = str(payload.get("name", "")).strip()
    slug = str(payload.get("slug", "")).strip() or make_slug(name)
    description = str(payload.get("description", "")).strip()
    sort_order = int(payload.get("sort_order", 0) or 0)

    if not name:
        raise ValueError("Tên danh mục là bắt buộc.")

    category = {
        "name": name,
        "slug": slug,
        "description": description,
        "sort_order": sort_order,
    }

    if category_id:
        categories_repository.update_category(category_id, category)
        return get_category_record(category_id)

    new_id = categories_repository.insert_category(category)
    return get_category_record(new_id)


def delete_category(category_id):
    category = get_category_record(category_id)
    if not category:
        return None
    categories_repository.delete_category_record(category_id)
    return category

