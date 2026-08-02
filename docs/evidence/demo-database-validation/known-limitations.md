# Known Limitations

- Một báo giá demo có tổng tiền âm và chưa được tự động sửa.
- Hai customer không có tên công ty; model hiện cho phép trường này rỗng.
- Mật khẩu `admin123` chỉ dành cho local demo và không an toàn cho production.
- Mypy toàn repository cần `django-stubs`; targeted validation files đã PASS
  với `--follow-imports=skip` để không coi dynamic Django managers là lỗi của
  phần code mới.
- Kiểm thử trình duyệt trong phase dùng Django test client; đăng nhập thật tại
  `http://127.0.0.1:8001/admin/login/` cũng đã được xác minh HTTP 200/302/200.
