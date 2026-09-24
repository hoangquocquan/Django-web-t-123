# Repository Pattern Standard

## Purpose

Repository là lớp duy nhất được phép tạo query ORM trực tiếp cho module đang migrate.

Nói dễ hiểu: service hỏi repository để lấy dữ liệu, còn repository mới biết dữ liệu nằm ở bảng nào, database nào và cần join/prefetch ra sao.

## Current Catalog Pattern

```text
Controller hoặc API tương lai
        |
        v
Service
        |
        v
Repository
        |
        v
Django ORM using("legacy")
        |
        v
Legacy SQLite
```

## Base Repository

Catalog dùng `LegacyCatalogRepository`.

Nhiệm vụ:

- Khai báo `database_alias = "legacy"`.
- Ép QuerySet gốc dùng `.using("legacy")`.
- Buộc repository con khai báo `model`.

## Rules

- Không gọi `.objects` trong service.
- Không gọi `.using("legacy")` trong service.
- Không gọi ORM trong controller/API tương lai.
- Repository phải trả QuerySet hoặc object Django ORM đúng mục đích.
- Query cần relationship phải khai báo rõ `select_related` hoặc `prefetch_related`.

## Example

Đúng:

```python
repository.list_products()
```

Sai:

```python
Product.objects.using("legacy").all()
```

nếu dòng này nằm trong service, controller hoặc serializer.

## Testing Rule

Mỗi repository mới trong Phase 5, 6, 7 cần có test:

- QuerySet dùng đúng database alias.
- Query count không tăng bất thường.
- Service có thể dùng repository giả để test độc lập.
