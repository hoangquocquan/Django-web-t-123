# Demo Database Data Quality Report

## Phạm vi

Database được kiểm tra là `django_backend/db.sqlite3`. Command kiểm tra chỉ đọc,
đối chiếu Django ORM với kết nối SQLite ở chế độ `mode=ro`.

## Số lượng

| Nhóm dữ liệu | Dự kiến | ORM | SQLite | Kết quả |
| --- | ---: | ---: | ---: | --- |
| Sản phẩm | 214 | 214 | 214 | PASS |
| Hồ sơ khách hàng | 501 | 501 | 501 | PASS |
| Lead | 1.003 | 1.003 | 1.003 | PASS |
| Báo giá | 503 | 503 | 503 | PASS |
| Tài liệu kiến thức | 105 | 105 | 105 | PASS |
| Người dùng nền tảng | 17 | 17 | 17 | PASS |

## Phát hiện

- Critical: 0.
- High: 1 loại lỗi, ảnh hưởng 1 bản ghi.
- Low: 1 loại vấn đề, ảnh hưởng 2 bản ghi.
- Informational: tài khoản admin local vẫn dùng mật khẩu demo.

### High

`SQ-DEMO-000208` có `subtotal=56`, `discount_total=94`, `total=-38`. Đây là dữ
liệu không hợp lệ về nghiệp vụ. Validation không tự sửa vì prompt cấm thay đổi
dữ liệu gốc chỉ để đạt PASS.

### Low

Hai `BusinessCustomer` không có tên công ty. Trường này được model cho phép để
hỗ trợ khách hàng cá nhân nên chưa được coi là lỗi chặn.

## Quan hệ

- Không có user thiếu role hoặc role thiếu permission.
- Không có lead thiếu owner, công ty hoặc trạng thái hợp lệ.
- Không có opportunity có xác suất lớn hơn 100 hoặc trạng thái không hợp lệ.
- Không có tài liệu thiếu chunk; không có chunk thiếu embedding.
- Không có báo giá thiếu đồng thời customer và opportunity.

## Kết luận

`DEMO_DATABASE_VALIDATION_FAILED` vì còn một phát hiện High. Database không bị
thay đổi trong quá trình kiểm tra.
