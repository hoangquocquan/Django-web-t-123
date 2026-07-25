# Architecture Decision Record

## ID

ADR-008

## Decision

Catalog ORM dùng repository làm điểm duy nhất tạo truy vấn, với `select_related` cho quan hệ nhiều-sang-một và `prefetch_related` cho quan hệ một-sang-nhiều.

## Context

Phase 4A đã ánh xạ catalog legacy database bằng unmanaged read-only models. Phase 4.1 đã củng cố routing, fixture và read-only protection. Trước khi dùng catalog làm mẫu cho CRM, Sales và CMS, cần khóa chiến lược truy vấn để tránh N+1 queries.

## Options Considered

- Cho service/controller tự tối ưu query khi cần.
- Đưa toàn bộ query vào repository và test bằng query count.
- Chờ tới khi có API mới tối ưu sau.

## Decision Reason

Repository là nơi phù hợp nhất để giữ logic truy vấn vì nó biết model, relationship và database alias. Query count test giúp phát hiện lỗi hiệu năng sớm khi module mở rộng.

## Consequences

- Service dễ test bằng fake repository.
- Controller/API tương lai không cần biết chi tiết ORM.
- Mỗi repository mới ở phase sau phải có test routing và query count.
- Khi response cần thêm relationship, repository phải cập nhật prefetch/select strategy trước.

## Status

Accepted
