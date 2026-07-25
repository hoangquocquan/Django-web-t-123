# Cache

Thư mục này chứa lớp cache.

Hiện tại dự án có `redis_cache.py`, dùng Redis khi bật cấu hình:

```text
MEC_REDIS_CACHE_ENABLED=true
MEC_REDIS_URL=redis://127.0.0.1:6379/0
```

Nếu chưa bật Redis, app vẫn chạy bình thường. Đây là cách làm an toàn khi phát triển local.

Luồng cache ví dụ:

```text
Controller kiểm tra Redis
→ nếu có dữ liệu: trả nhanh từ Redis
→ nếu chưa có: đọc database qua service/repository
→ lưu lại Redis trong vài giây/phút
```
