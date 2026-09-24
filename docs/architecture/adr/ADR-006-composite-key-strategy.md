# Architecture Decision Record

## ID

ADR-006

## Decision

Các bảng quan hệ legacy không có cột `id` sẽ dùng `models.CompositePrimaryKey` trong Django unmanaged models.

## Context

Một số bảng catalog như `product_materials`, `product_processes` và `capability_machines` dùng cặp khóa ngoại làm khóa chính. Phase 4 không được thay đổi schema legacy.

## Options Considered

- Thêm cột `id` vào database legacy.
- Bỏ ánh xạ khóa chính composite.
- Dùng `CompositePrimaryKey` cho unmanaged model.

## Decision Reason

`CompositePrimaryKey` giữ nguyên cấu trúc legacy và không yêu cầu migration. Vì model chỉ đọc, rủi ro thấp hơn so với việc sửa schema.

## Consequences

- Mapping phản ánh đúng database hiện tại.
- Relationship nhiều-nhiều có thể được test qua model explicit.
- Một số tính năng write hoặc package bên ngoài cần review lại ở phase sau.

## Status

Accepted
