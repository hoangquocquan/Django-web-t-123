# Composite Key Implementation Review

## Scope

Review này kiểm tra cách Phase 4A ánh xạ các bảng quan hệ nhiều-nhiều trong legacy SQLite bằng Django ORM read-only.

Các bảng được xem xét:

- `product_materials`
- `product_processes`
- `capability_machines`

## Current Implementation

Các bảng trên không có cột `id` riêng. Khóa chính của mỗi dòng được tạo từ hai khóa ngoại.

Trong Django 5.2, dự án dùng:

```python
pk = models.CompositePrimaryKey("product", "material")
```

Cách này giữ đúng cấu trúc legacy database và không cần thêm cột giả.

## Why CompositePrimaryKey Is Acceptable

- Database legacy đã tồn tại và không được sửa schema ở Phase 4.
- Các model catalog đang là `managed = False`, nên Django không tạo migration cho các bảng này.
- Chức năng hiện tại chỉ đọc dữ liệu, chưa cần admin form hoặc API write.
- Quan hệ vẫn truy cập được bằng `select_related()` trong test.

## Limitations

- Composite primary key là tính năng mới hơn so với kiểu model Django truyền thống.
- Một số thư viện bên ngoài có thể giả định model luôn có khóa chính đơn `id`.
- Khi chuyển sang API write hoặc Django Admin write, cần review lại serializer, form và validation.
- Không nên dùng các model composite này làm điểm ghi dữ liệu cho tới khi có phase migration riêng.

## Test Coverage

Đã bổ sung test kiểm tra:

- ORM đọc được bảng quan hệ composite.
- Composite relationship truy cập được model liên quan.
- Repository vẫn đi qua database alias `legacy`.
- Model legacy chặn `save()`, `delete()`, `update()` và bulk `delete()`.

## Recommendation

Giữ nguyên chiến lược hiện tại cho giai đoạn read-only.

Khi chuyển sang write-enabled Django models, cần quyết định một trong hai hướng:

1. Giữ composite key nếu toàn bộ stack hỗ trợ tốt.
2. Tạo bảng Django mới có khóa chính đơn và migrate dữ liệu sang schema mới.

Hiện tại khuyến nghị không đổi schema legacy.
