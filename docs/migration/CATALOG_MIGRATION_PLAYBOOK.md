# Catalog Migration Playbook

## Objective

Tài liệu này biến Catalog ORM thành mẫu chuẩn cho các phase sau như CRM, Sales và CMS.

## Model Pattern

Model legacy cần:

- Kế thừa `LegacyReadOnlyModel`.
- Đặt `managed = False`.
- Khai báo `db_table` đúng tên bảng legacy.
- Giữ đúng field hiện có trong SQLite.
- Dùng `db_column` nếu tên field Django khác tên cột database.
- Không thêm field chưa tồn tại trong legacy database.

## Repository Pattern

Repository cần:

- Kế thừa base repository của module.
- Khai báo `model`.
- Dùng `self.queryset()` làm điểm bắt đầu.
- Tối ưu relationship bằng `select_related` hoặc `prefetch_related`.

## Service Pattern

Service cần:

- Nhận repository qua constructor để dễ test.
- Không gọi ORM trực tiếp.
- Không biết database alias.
- Chỉ xử lý business flow nhẹ ở phase read-only.

## Test Pattern

Test cần:

- Dùng fixture `legacy_db`.
- Đọc database qua bản copy read-only.
- Có test mapping model.
- Có test repository dùng alias `legacy`.
- Có test read-only enforcement.
- Có test query count cho relationship quan trọng.
- Có test service bằng fake repository.

## Common Mistakes

- Gọi `Product.objects` trực tiếp trong service.
- Quên `.using("legacy")`.
- Dùng `select_related` cho quan hệ một-nhiều.
- Quên `prefetch_related` khi list view cần ảnh/spec/tag.
- Thêm field chưa có trong SQLite.
- Chạy `makemigrations` cho unmanaged legacy models.
- Viết test dùng database thật thay vì fixture copy.

## Migration Readiness Checklist

Trước khi migrate module tiếp theo:

- Có database mapping document.
- Có model unmanaged read-only.
- Có repository chuẩn hóa alias.
- Có service không phụ thuộc ORM.
- Có query count test.
- Có ADR nếu có quyết định kiến trúc mới.
- Có review summary và changeset patch.
