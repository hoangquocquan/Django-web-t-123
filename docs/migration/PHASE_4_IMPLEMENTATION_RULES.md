# Phase 4 Implementation Rules

## Objective

Phase 4 chỉ ánh xạ catalog legacy database sang Django ORM ở chế độ read-only.

## Hard Rules

- Không sửa `backend/app.py`.
- Không sửa repository hoặc service legacy.
- Không chạy `makemigrations`.
- Không chạy `migrate` cho legacy database.
- Không ghi dữ liệu vào database legacy.
- Không đổi schema SQLite hiện tại.
- Không tạo API mới trong Phase 4A hoặc 4.1.

## Database Rules

- Tất cả truy vấn catalog Django phải dùng database alias `legacy`.
- Test không được đọc trực tiếp database thật nếu có thể dùng bản copy fixture.
- Cấu hình legacy database phải dùng SQLite URI `mode=ro` để chặn ghi ở tầng database.
- Model legacy phải kế thừa `LegacyReadOnlyModel`.

## Model Rules

- Mọi model ánh xạ bảng legacy phải đặt `managed = False`.
- Tên bảng phải giữ đúng bằng `db_table`.
- Tên cột legacy phải giữ bằng `db_column` khi cần.
- Không thêm field không tồn tại trong database legacy.
- Composite relationship table phải được review riêng trước khi mở rộng.

## Repository Rules

- Repository là nơi duy nhất tạo query trực tiếp cho catalog.
- QuerySet phải dùng `.using("legacy")`.
- Service không được truy cập ORM trực tiếp nếu đã có repository tương ứng.

## Test Rules

- Phải có test xác nhận repository dùng alias `legacy`.
- Phải có test xác nhận read-only enforcement.
- Phải có test xác nhận relationship chính hoạt động.
- Phải có test xác nhận composite relationship truy cập được dữ liệu liên quan.

## Future Write Migration

Khi cần ghi dữ liệu bằng Django, phải tạo phase riêng để:

- Thiết kế schema Django write-enabled.
- Tạo migrations mới.
- Viết data migration.
- Chạy validation dữ liệu.
- Chuẩn bị rollback.
