# Architecture Decision Record

## ID

ADR-007

## Decision

Django dùng database alias `legacy` cho ORM đọc dữ liệu từ SQLite legacy.

## Context

Project Django mới sẽ tồn tại song song với backend cũ. Django cần có database mặc định cho hệ thống mới, đồng thời cần đọc database legacy để kiểm tra mapping catalog.

## Options Considered

- Dùng một database alias duy nhất.
- Dùng alias `default` để trỏ thẳng vào legacy SQLite.
- Tách `default` và `legacy`.

## Decision Reason

Tách `default` và `legacy` giúp giảm rủi ro ghi nhầm vào database cũ. Repository phải gọi `.using("legacy")` rõ ràng để người đọc code biết dữ liệu đến từ đâu.

## Consequences

- Code rõ nguồn dữ liệu hơn.
- Test có thể kiểm tra routing qua alias.
- Sau này có thể thêm database Django production mà không phá mapping legacy.

## Status

Accepted
