"""Serializers for Django-owned business core APIs."""

from rest_framework import serializers


class BusinessProductSerializer(serializers.Serializer):
    """Validate product create/update payloads."""

    legacy_category_id = serializers.IntegerField(required=False, allow_null=True)
    category_name = serializers.CharField(required=False, allow_blank=True, max_length=160)
    name = serializers.CharField(max_length=220)
    slug = serializers.SlugField(max_length=240)
    sku = serializers.CharField(required=False, allow_blank=True, max_length=120)
    price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)
    status = serializers.CharField(required=False, max_length=30)
    short_description = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    main_image = serializers.CharField(required=False, allow_blank=True)
    seo_title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    seo_description = serializers.CharField(required=False, allow_blank=True)
    seo_keywords = serializers.CharField(required=False, allow_blank=True)
    sort_order = serializers.IntegerField(required=False)
    published_at = serializers.CharField(required=False, allow_blank=True, max_length=80)


class BusinessProductUpdateSerializer(BusinessProductSerializer):
    """Validate partial product update payloads."""

    name = serializers.CharField(required=False, max_length=220)
    slug = serializers.SlugField(required=False, max_length=240)


class BusinessCustomerSerializer(serializers.Serializer):
    """Validate customer create/update payloads."""

    company_name = serializers.CharField(required=False, allow_blank=True, max_length=220)
    contact_name = serializers.CharField(max_length=160)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=80)
    country = serializers.CharField(required=False, allow_blank=True, max_length=120)
    status = serializers.CharField(required=False, max_length=40)
    notes = serializers.CharField(required=False, allow_blank=True)


class BusinessCustomerUpdateSerializer(BusinessCustomerSerializer):
    """Validate partial customer update payloads."""

    contact_name = serializers.CharField(required=False, max_length=160)


class InventoryWarehouseSerializer(serializers.Serializer):
    """Validate warehouse creation payloads."""

    code = serializers.CharField(max_length=40)
    name = serializers.CharField(max_length=160)
    location = serializers.CharField(required=False, allow_blank=True, max_length=220)
    is_active = serializers.BooleanField(required=False)


class InventoryItemSerializer(serializers.Serializer):
    """Validate stock item creation payloads."""

    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    quantity = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)
    reorder_point = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)


class InventoryAdjustmentSerializer(serializers.Serializer):
    """Validate stock movement payloads."""

    quantity_delta = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = serializers.CharField(required=False, max_length=40)
    reason = serializers.CharField(required=False, allow_blank=True)
    reference = serializers.CharField(required=False, allow_blank=True, max_length=120)


def business_product_to_dict(product):
    """Convert a Django-owned product to API JSON."""
    return {
        "id": product.id,
        "legacy_product_id": product.legacy_product_id,
        "legacy_category_id": product.legacy_category_id,
        "category_name": product.category_name,
        "name": product.name,
        "slug": product.slug,
        "sku": product.sku,
        "price": str(product.price),
        "status": product.status,
        "short_description": product.short_description,
        "description": product.description,
        "main_image": product.main_image,
        "seo": {
            "title": product.seo_title,
            "description": product.seo_description,
            "keywords": product.seo_keywords,
        },
        "sort_order": product.sort_order,
        "published_at": product.published_at,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def business_customer_to_dict(customer):
    """Convert a Django-owned customer to API JSON."""
    return {
        "id": customer.id,
        "legacy_customer_id": customer.legacy_customer_id,
        "company_name": customer.company_name,
        "contact_name": customer.contact_name,
        "email": customer.email,
        "phone": customer.phone,
        "country": customer.country,
        "status": customer.status,
        "notes": customer.notes,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
    }


def warehouse_to_dict(warehouse):
    """Convert a warehouse to API JSON."""
    return {
        "id": warehouse.id,
        "code": warehouse.code,
        "name": warehouse.name,
        "location": warehouse.location,
        "is_active": warehouse.is_active,
        "created_at": warehouse.created_at.isoformat() if warehouse.created_at else None,
    }


def inventory_item_to_dict(item):
    """Convert an inventory item to API JSON."""
    return {
        "id": item.id,
        "product": business_product_to_dict(item.product),
        "warehouse": warehouse_to_dict(item.warehouse),
        "quantity": str(item.quantity),
        "reserved_quantity": str(item.reserved_quantity),
        "reorder_point": str(item.reorder_point),
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }
