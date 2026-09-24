"""Serializer helpers for read-only catalog API responses."""


def category_to_dict(category):
    """Convert a category ORM object into safe JSON fields."""
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "sort_order": category.sort_order,
    }


def material_to_dict(material):
    """Convert a material ORM object into safe JSON fields."""
    return {
        "id": material.id,
        "name": material.name,
        "standard": material.standard,
        "description": material.description,
    }


def product_image_to_dict(image):
    """Convert a product image ORM object into JSON."""
    return {
        "id": image.id,
        "image_url": image.image_url,
        "alt_text": image.alt_text,
        "sort_order": image.sort_order,
    }


def product_to_dict(product):
    """Convert a product ORM object into a compact API representation."""
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "sku": product.sku,
        "price": product.price,
        "status": product.status,
        "short_description": product.short_description,
        "description": product.description,
        "main_image": product.main_image,
        "thumbnail_url": product.thumbnail_url,
        "category": category_to_dict(product.category),
        "seo": {
            "title": product.seo_title,
            "description": product.seo_description,
            "keywords": product.seo_keywords,
            "canonical_url": product.canonical_url,
            "robots": product.robots,
        },
        "published_at": product.published_at,
    }


def product_detail_to_dict(detail):
    """Convert product detail service result into JSON."""
    product = product_to_dict(detail["product"])
    product["images"] = [product_image_to_dict(image) for image in detail["images"]]
    return product
