# Tests

Thư mục này chứa test tự động.

Chạy test:

```powershell
python -m unittest discover -s backend\tests -p "test_*.py"
```

Các nhóm test hiện có:

- Unit test: kiểm tra service/repository có xử lý đúng không.
- Controller test: kiểm tra controller trả đúng dữ liệu/status hoặc ném AppError đúng.
- Cache test: kiểm tra Redis là tùy chọn, không làm hỏng local/test khi chưa bật.
- Transaction test: kiểm tra lỗi giữa chừng có rollback không.
- Integration test: bật server test bằng port tạm và gọi API thật.

Test dùng database SQLite tạm, không đụng vào file `backend/database/mecprecision.sqlite` thật.
Thư mục này dành cho test backend/API. Bước tiếp theo nên thêm test cho login, product API và CMS permission.
