# Demo Database CRUD Report

## Cách kiểm tra

CRUD được chạy bằng `pytest` trên Django test database. Mỗi test được rollback;
không thao tác Create/Update/Delete trên `django_backend/db.sqlite3`.

## Kết quả

- Product: create, read, update và delete PASS.
- Customer: create, read, update và delete PASS.
- Validation: giá âm được command data-quality phát hiện PASS.
- Permission: admin đăng nhập và tạo session PASS.
- Rollback/isolation: SHA-256 database gốc trước và sau giống nhau PASS.

Focused suite: `8 passed`.

Full regression: `554 passed`.

## Lỗi đăng nhập đã xử lý

Database local thiếu migration `foundation.0006`, vì vậy login ghi audit vào
bảng chưa tồn tại và gây lỗi 500. Database đã được sao lưu trước khi áp dụng
migration; sau đó login trả `302 /admin/` và dashboard trả HTTP 200.
