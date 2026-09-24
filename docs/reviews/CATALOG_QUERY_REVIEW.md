# Catalog Query Review

## Scope

Review này kiểm tra truy vấn ORM của module catalog trong Django migration.

Các file được xem:

- `django_backend/apps/catalog/repositories/product_repository.py`
- `django_backend/apps/catalog/repositories/category_repository.py`
- `django_backend/apps/catalog/services/catalog_service.py`
- `django_backend/apps/catalog/tests/`
- `django_backend/tests/`

## Findings

### Direct ORM Usage

Application code chỉ dùng ORM trong repository.

Service `CatalogService` không gọi trực tiếp `Product.objects`, `Category.objects` hoặc `.using("legacy")`.

Direct ORM còn xuất hiện trong test để kiểm chứng mapping, relationship và read-only behavior. Đây là chấp nhận được vì test cần đối chiếu trực tiếp với legacy database.

## Query Strategy

### Product List

Repository dùng:

```python
self.queryset().select_related("category").all()
```

Lý do:

- `Product.category` là quan hệ nhiều-sang-một.
- `select_related("category")` join category trong cùng một query.
- Khi template hoặc service đọc `product.category.name`, Django không tạo thêm query theo từng sản phẩm.

### Product Detail

Hiện tại detail dùng:

- 1 query lấy product kèm category.
- 1 query lấy danh sách ảnh.

Cách này ổn cho detail page vì chỉ xử lý một sản phẩm.

### Product List With Images

Đã bổ sung:

```python
list_products_with_images()
```

Hàm này dùng `prefetch_related("images")` với image queryset trên alias `legacy`.

Lý do:

- `Product.images` là quan hệ một-sang-nhiều.
- Nếu không prefetch, list view có thể tạo lỗi N+1.
- `prefetch_related` giảm pattern đó về 2 query ổn định.

## Query Count Tests

Đã bổ sung test:

- Product list + category: 1 query.
- Product list + images: 2 query.
- Product detail: 2 query.
- Service có thể dùng repository double mà không cần ORM.

## Risks

- Query count có thể thay đổi khi thêm relationship mới như specs, materials, processes.
- Khi mở API read-only, serializer có thể vô tình gọi relationship chưa prefetch.
- Composite key relationship cần tiếp tục được kiểm tra nếu expose qua API.

## Recommendation

- Mọi list view có relationship nhiều-sang-một nên dùng `select_related`.
- Mọi list view có relationship một-sang-nhiều hoặc nhiều-nhiều nên dùng `prefetch_related`.
- Serializer hoặc controller tương lai không được tự gọi ORM; phải dùng repository/service.
- Khi thêm field relationship mới vào response, phải thêm query count test tương ứng.
