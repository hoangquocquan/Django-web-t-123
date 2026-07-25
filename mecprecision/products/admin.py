"""Đăng ký Product model vào Django Admin.

Các model đang `managed = False`, nên admin dùng để xem/chỉnh bảng cũ khi đã kiểm tra kỹ.
"""

from django.contrib import admin

from .models import Product, ProductCategory, ProductImage, ProductSpec


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "sort_order")
    search_fields = ("name", "slug")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductSpecInline(admin.TabularInline):
    model = ProductSpec
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "sku", "price", "status", "sort_order")
    list_filter = ("status", "category")
    search_fields = ("name", "sku", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductSpecInline]
