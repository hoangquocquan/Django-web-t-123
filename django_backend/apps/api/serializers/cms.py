"""Serializer helpers for read-only CMS API responses."""


def page_to_dict(page):
    """Convert a CMS page ORM object into JSON."""
    return {
        "id": page.id,
        "title": page.title,
        "slug": page.slug,
        "content": page.content,
        "seo_title": page.seo_title,
        "seo_description": page.seo_description,
        "status": page.status,
        "sort_order": page.sort_order,
        "created_at": page.created_at,
        "updated_at": page.updated_at,
    }


def banner_to_dict(banner):
    """Convert a CMS banner ORM object into JSON."""
    return {
        "id": banner.id,
        "title": banner.title,
        "placement": banner.placement,
        "image_url": banner.image_url,
        "link_url": banner.link_url,
        "content": banner.content,
        "sort_order": banner.sort_order,
        "status": banner.status,
        "starts_at": banner.starts_at,
        "ends_at": banner.ends_at,
        "created_at": banner.created_at,
    }


def menu_item_to_dict(item):
    """Convert a menu item and its already-prefetched children into JSON."""
    return {
        "id": item.id,
        "location": item.location,
        "label": item.label,
        "url": item.url,
        "sort_order": item.sort_order,
        "status": item.status,
        "children": [
            {
                "id": child.id,
                "location": child.location,
                "label": child.label,
                "url": child.url,
                "sort_order": child.sort_order,
                "status": child.status,
            }
            for child in item.children.all()
        ],
    }
