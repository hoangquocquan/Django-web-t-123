# Demo Database Validation Review

## Quyết định

`DEMO_DATABASE_VALIDATION_FAILED`

Trạng thái: `WAITING_FOR_HUMAN_APPROVAL`.

## Database

- Path: `django_backend/db.sqlite3`.
- Engine: SQLite qua Django ORM.
- Header SQLite: hợp lệ.
- SHA-256 trước: `a9f0a9ad2e43a8f8023ca6f99345cd5a1ae6cc5bdd7578a44006f7966f51114d`.
- SHA-256 sau: `a9f0a9ad2e43a8f8023ca6f99345cd5a1ae6cc5bdd7578a44006f7966f51114d`.
- Database gốc bị sửa bởi validation: không.

Trước validation, migration bảo mật `foundation.0006` đã được áp dụng để sửa lỗi
login 500. Database được sao lưu vào thư mục Temp trước migration.

## Kết quả chính

- ORM và raw SQLite có số lượng giống nhau ở cả sáu nhóm dữ liệu.
- Tất cả số lượng khớp đúng dữ liệu dự kiến.
- Focused tests: 8 passed.
- Full regression: 554 passed.
- Django check và migration drift check: PASS.
- Ruff, targeted mypy và Bandit High findings: PASS.
- UI, API, AI Sales và RAG grounding: PASS.
- Không phát hiện N+1 trong năm truy vấn đại diện.

## Finding chặn

Một báo giá demo có tổng tiền âm:

`SQ-DEMO-000208`: `subtotal=56`, `discount=94`, `total=-38`.

Theo điều kiện PASS, High finding phải bằng 0. Validation không tự sửa bản ghi gốc
và không hạ mức độ finding để ép kết quả PASS.

## Ollama

Local Ollama `llama3` đã phản hồi thật, schema hợp lệ và không dùng fallback.
Lần review cuối trả `BLOCKED` với một High finding về artifact evidence. Finding
này diễn đạt chưa rõ nhưng không được bỏ qua theo fail-closed policy. Đồng thời,
deterministic data gate đã độc lập chặn phase vì báo giá âm.

## Hành động cần người duyệt

Xác nhận business rule cho discount lớn hơn subtotal. Sau khi sửa dữ liệu bằng
thao tác được phê duyệt và bổ sung validation ở luồng tạo báo giá, chạy lại phase
để đạt High findings = 0.
