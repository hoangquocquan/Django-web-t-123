# Architecture Decision Record

## ID

ADR-005

## Decision

Django catalog ORM sẽ đọc legacy SQLite database ở chế độ read-only trong Phase 4.

## Context

Dự án đang migrate từng bước từ Python legacy backend sang Django. Catalog là module đầu tiên được ánh xạ bằng Django ORM, nhưng legacy backend vẫn đang phục vụ website hiện tại.

## Options Considered

- Cho Django đọc trực tiếp database legacy và chặn ghi.
- Copy toàn bộ dữ liệu sang database Django mới.
- Rewrite catalog business logic ngay trong Django.

## Decision Reason

Read-only ORM là lựa chọn an toàn nhất vì cho phép kiểm tra mapping, relationship và repository mà không làm thay đổi dữ liệu đang chạy.

## Consequences

- Django có thể đọc dữ liệu catalog thật.
- Legacy backend vẫn giữ quyền vận hành hiện tại.
- Chưa thể tạo, sửa, xóa catalog bằng Django ở phase này.
- Phase write-enabled phải được thiết kế riêng.

## Status

Accepted
