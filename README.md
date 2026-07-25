# MecPrecision VIETNAM

Đây là website động MecPrecision VIETNAM, đã được tổ chức lại theo cấu trúc tách riêng `backend`, `frontend`, `database` và `scripts`.

## Cấu trúc thư mục

```text
mecprecision-vietnam/
├── backend/
│   ├── app.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── database/
│   │   ├── mecprecision.sqlite
│   │   ├── schema.sql
│   │   └── seed.sql
│   ├── utils/
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── cong-nghe.html
│   ├── san-pham.html
│   ├── lien-he.html
│   ├── tin-tuc.html
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js
│   │   └── data.js
│   ├── images/
│   ├── icons/
│   └── fonts/
├── scripts/
│   ├── init_database.py
│   ├── export_home_data.py
│   └── check_database.py
├── .gitignore
├── README.md
└── LICENSE
```

## Cách chạy web động

Mở Terminal tại thư mục:

```text
C:\Users\hoang\Documents\Codex\mecprecision-vietnam
```

Chạy backend:

```text
python backend\app.py
```

Mở trình duyệt:

```text
http://127.0.0.1:8000
```

## Luồng hoạt động

```text
backend/database/mecprecision.sqlite
→ backend/repositories đọc/ghi SQL
→ backend/services kiểm tra dữ liệu và xử lý nghiệp vụ
→ backend/controllers điều phối API
→ backend/app.py nhận request, gọi controller/service, render HTML hoặc trả JSON API
→ frontend/css/styles.css tạo giao diện
→ frontend/js/app.js xử lý menu mobile và form liên hệ
```

## Các trang động

- `/` hoặc `/index.html`: trang chủ
- `/san-pham.html`: sản phẩm
- `/cong-nghe.html`: công nghệ
- `/tin-tuc.html`: tin tức
- `/lien-he.html`: liên hệ
- `/{slug}`: trang động tạo từ CMS Pages, ví dụ `/about`, `/privacy`, `/career`

## Admin CMS

Đăng nhập CMS:

```text
http://127.0.0.1:8000/admin/login
```

Tài khoản demo local:

```text
admin@mecprecision.vn / admin123
```

Các module CMS chính:

- `/admin/products`: sản phẩm, danh mục, tag text, slug, SEO, thumbnail, gallery, related products, sort order, status.
- `/admin/news`: tin tức, category, tag text, SEO, thumbnail, author, publish date, schedule publish, featured, status.
- `/admin/pages`: tạo trang động như About, Contact, Privacy, Terms, Career, History.
- `/admin/menus`: Menu Builder cho Header, Footer, Sidebar, nested menu bằng parent menu và sort order.
- `/admin/banners`: Banner trang chủ, slider, popup và advertisement.
- `/admin/contacts`: danh sách liên hệ, đánh dấu đã đọc, ghi chú nội bộ, export CSV.
- `/admin/quotes`: quản lý yêu cầu báo giá, phân công nhân viên, trạng thái xử lý.
- `/admin/customers`: khách hàng, công ty, email, điện thoại, ghi chú/lịch sử.
- `/admin/newsletter`: đăng ký/hủy đăng ký newsletter và export CSV.

## API hiện có

- `GET /api/home`
- `GET /api/products`
- `GET /api/products/1`
- `POST /api/products`
- `PUT /api/products/1`
- `DELETE /api/products/1`
- `GET /api/product-categories`
- `GET /api/capabilities`
- `GET /api/news`
- `POST /api/contact`
- `GET /api/external/weather`
- `GET /api/openapi.json`
- `GET /api/docs`

## Test tự động

Dự án có test tự động trong thư mục:

```text
backend/tests/
```

Chạy toàn bộ test:

```powershell
python -m unittest discover -s backend\tests -p "test_*.py"
```

Test hiện có:

- Unit test cho service/repository sản phẩm.
- Test transaction rollback.
- Integration test cho `/api/openapi.json`, `/api/products`, `/api/contact` và API 404.

## OpenAPI / Swagger

Tài liệu API dạng OpenAPI JSON:

```text
http://127.0.0.1:8000/api/openapi.json
```

Trang xem nhanh API:

```text
http://127.0.0.1:8000/api/docs
```

OpenAPI giúp frontend hoặc đối tác biết backend có endpoint nào, gửi dữ liệu gì và nhận dữ liệu gì.

## Environment tách biệt

File mẫu:

```text
.env.example
```

Khi chạy local, có thể copy thành `.env` và sửa:

```text
MEC_ENV=development
MEC_DEBUG=true
MEC_HOST=127.0.0.1
MEC_PORT=8000
MEC_DATABASE_PATH=backend/database/mecprecision.sqlite
```

Lưu ý: `.env` đã nằm trong `.gitignore`, không nên commit file `.env` thật nếu có mật khẩu/secret.

## Docker

Dự án đã có:

```text
Dockerfile
docker-compose.yml
.dockerignore
```

Build Docker image:

```powershell
docker build -t mecprecision-vietnam .
```

Chạy web kèm Redis bằng Docker Compose:

```powershell
docker-compose up --build
```

Sau khi chạy, mở:

```text
http://127.0.0.1:8000
```

## Redis cache/session-ready

Redis hiện được chuẩn bị ở mức cache tùy chọn. Local không bật Redis vẫn chạy bình thường.

Khi muốn bật Redis trong `.env`:

```text
MEC_REDIS_CACHE_ENABLED=true
MEC_REDIS_URL=redis://127.0.0.1:6379/0
```

Trong `docker-compose.yml`, service `redis` đã được khai báo sẵn. Hiện controller `/api/home` có thể dùng Redis cache nếu Redis được bật.

## Demo API liên kết ngoại

Endpoint này cho thấy backend local gọi một API bên ngoài rồi trả kết quả về frontend:

```text
Frontend -> backend local /api/external/weather -> Open-Meteo API -> backend local -> frontend
```

Gọi thử bằng PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/external/weather
```

API bên ngoài đang dùng:

```text
Open-Meteo Forecast API
```

Lý do chọn Open-Meteo: không cần API key, dễ demo trên máy local. Nếu sau này dùng API có key như AWS, Stripe, Zalo, Google Maps, thì backend sẽ giữ API key, frontend không gọi trực tiếp ra ngoài.

## Demo API sản phẩm local

API sản phẩm đọc/ghi trực tiếp vào bảng `products` trong SQLite.

Lấy danh mục sản phẩm để biết `category_id`:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/product-categories
```

Tạo sản phẩm mới:

```powershell
$payload = @{
  category_id = 1
  name = 'Sản phẩm API Local'
  short_description = 'Mô tả ngắn của sản phẩm.'
  description = 'Mô tả chi tiết của sản phẩm.'
  main_image = 'https://images.unsplash.com/photo-1565043589221-1a6fd9ae45c7?auto=format&fit=crop&w=900&q=80'
  is_featured = $false
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/products' -ContentType 'application/json; charset=utf-8' -Body $payload
```

Cập nhật sản phẩm có id là `4`:

```powershell
$payload = @{
  name = 'Tên sản phẩm đã sửa'
  short_description = 'Mô tả ngắn đã sửa.'
  description = 'Mô tả chi tiết đã sửa.'
  main_image = 'https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=900&q=80'
} | ConvertTo-Json

Invoke-RestMethod -Method Put -Uri 'http://127.0.0.1:8000/api/products/4' -ContentType 'application/json; charset=utf-8' -Body $payload
```

Xóa sản phẩm có id là `4`:

```powershell
Invoke-RestMethod -Method Delete -Uri 'http://127.0.0.1:8000/api/products/4'
```

## Đăng nhập quản trị

Trang đăng nhập:

```text
http://127.0.0.1:8000/admin/login
```

Quên mật khẩu:

```text
http://127.0.0.1:8000/admin/forgot-password
```

Trang tài khoản sau khi đăng nhập:

```text
http://127.0.0.1:8000/admin/account
```

Tài khoản demo:

```text
Email: admin@mecprecision.vn
Mật khẩu: admin123
```

Sau khi đăng nhập, dashboard nằm ở:

```text
http://127.0.0.1:8000/admin
```

Admin CMS hiện có các module:

- Dashboard: `/admin`
- Quản lý sản phẩm: `/admin/products`
- Quản lý danh mục: `/admin/categories`
- Quản lý tin tức: `/admin/news`
- Media Manager: `/admin/media`
- Quản lý liên hệ: `/admin/contacts`
- Quản lý người dùng: `/admin/users`
- Cài đặt hệ thống: `/admin/settings`
- Tài khoản của tôi: `/admin/account`

Các module quản trị hỗ trợ form thêm/sửa, danh sách, tìm kiếm, phân trang, xóa có xác nhận. Riêng sản phẩm và tin tức có thêm upload ảnh local và xem trước ảnh trước khi lưu.

## Dashboard

Dashboard nằm tại:

```text
http://127.0.0.1:8000/admin
```

Dashboard hiện có:

- Tổng sản phẩm.
- Tổng tin tức.
- Tổng khách hàng.
- Yêu cầu báo giá.
- Liên hệ mới.
- Người online.
- Lượt truy cập.
- Biểu đồ lượt truy cập 7 ngày.
- Biểu đồ lượt truy cập 30 ngày.
- Biểu đồ lượt truy cập 12 tháng.

Lượt truy cập được ghi vào bảng:

```text
page_visits
```

## Media Manager

Module media nằm tại:

```text
http://127.0.0.1:8000/admin/media
```

Chức năng hiện có:

- Upload file.
- Quản lý theo folder.
- Tạo folder mới.
- Rename file.
- Delete file.
- Preview ảnh/file.
- Copy URL.
- Search theo tên file hoặc URL.

Media được lưu trong:

```text
backend/uploads/
```

## User Management

Module người dùng nằm tại:

```text
http://127.0.0.1:8000/admin/users
```

Chức năng hiện có:

- Danh sách người dùng.
- Thêm người dùng.
- Sửa người dùng.
- Xóa người dùng.
- Tìm kiếm theo tên, email, role.
- Phân quyền bằng role: `admin`, `editor`, `viewer`.
- Avatar: nhập URL ảnh hoặc upload file ảnh.
- Khóa tài khoản.
- Mở khóa tài khoản.
- Nhật ký hoạt động gần đây trong CMS.

Nhật ký hoạt động lưu trong bảng:

```text
admin_activity_logs
```

## Authentication

Các chức năng authentication hiện có:

- Login: `/admin/login`
- Logout: `/admin/logout`
- Quên mật khẩu: `/admin/forgot-password`
- Reset password bằng email demo: `/admin/reset-password?token=...`
- Đổi mật khẩu: `/admin/account`
- Đổi email: `/admin/account`
- Khóa tài khoản: trong `/admin/users`
- Mở khóa tài khoản: trong `/admin/users`
- Session nhiều thiết bị: xem tại `/admin/account`
- Thu hồi session thiết bị khác: trong `/admin/account`
- Tự động hết hạn session: theo `MEC_SESSION_TTL_SECONDS`

Lưu ý: bản local chưa gửi email thật. Khi quên mật khẩu, email reset được lưu vào bảng `auth_email_outbox` và cũng hiển thị link demo để bạn test nhanh.

## Nâng cấp gần chuẩn production

Dự án hiện đã có thêm các phần nền tảng để gần chuẩn dự án thực tế hơn:

- Có tách lớp hạ tầng ra khỏi `backend/app.py`:
  - `backend/config/settings.py`: cấu hình đường dẫn, port, session.
  - `backend/database/connection.py`: kết nối SQLite và helper query.
  - `backend/database/migrations.py`: tạo bảng bổ sung cho CMS/session.
  - `backend/auth/`: password hash, session, phân quyền.
  - `backend/middleware/security_headers.py`: HTTP security headers.
  - `backend/utils/`: xử lý text, route id, upload, logging.
- Có tách các module chính theo hướng service/repository:
  - `backend/controllers/`: nhận yêu cầu API và gọi service.
  - `backend/services/`: business logic, validate dữ liệu, quyết định luồng xử lý.
  - `backend/repositories/`: câu lệnh SQL đọc/ghi SQLite.
  - Các module đã tách: sản phẩm, danh mục, tin tức, liên hệ, người dùng, cài đặt, dashboard, dữ liệu public.
- `backend/app.py` hiện tập trung vào route HTTP: nhận request, gọi controller/service, trả HTML/JSON.
- Có exception handler tập trung tại `backend/middleware/exception_handler.py`.
- Password hash dùng `PBKDF2-HMAC-SHA256`.
- Hash SHA-256 cũ vẫn đăng nhập được và tự nâng cấp sang PBKDF2 sau khi login đúng.
- Session admin lưu trong SQLite qua bảng `admin_sessions`, không còn phụ thuộc RAM.
- Session lưu IP, trình duyệt, thời gian hoạt động cuối để mô phỏng nhiều thiết bị.
- Login attempt được ghi vào bảng `login_attempts`.
- Reset password dùng bảng `password_reset_tokens`.
- Email demo lưu trong bảng `auth_email_outbox`.
- Có rate limit đăng nhập sai theo email + IP.
- Có phân quyền role cơ bản: `admin`, `editor`, `viewer`.
- Có HTTP security headers cơ bản.
- Có thư mục log `backend/logs/` và file `app.log`.
- Có exception handler chung để API lỗi trả về format thống nhất:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Nội dung lỗi"
  }
}
```

- Có transaction helper trong `backend/database/connection.py` để rollback khi thao tác nhiều bước bị lỗi.
- Có CI cơ bản tại `.github/workflows/ci.yml` để tự động compile backend, kiểm tra JS và chạy test.
- CI cũng build Docker image để phát hiện sớm lỗi Dockerfile.

Các bảng bổ sung:

```text
admin_sessions
login_attempts
system_settings
```

## Database

Database nằm trong:

```text
backend/database/mecprecision.sqlite
```

Các file SQL:

- `backend/database/schema.sql`: cấu trúc bảng.
- `backend/database/seed.sql`: dữ liệu mẫu.

Tạo lại database:

```text
python scripts\init_database.py
```

Kiểm tra database:

```text
python scripts\check_database.py
```

Thêm dữ liệu demo cho Admin CMS:

```text
python scripts\seed_cms_demo_data.py
```

Script này thêm nhiều sản phẩm, danh mục, tin tức, liên hệ và người dùng mẫu để bạn có dữ liệu sửa trực tiếp trong CMS. Script có kiểm tra trùng, nên có thể chạy lại mà không nhân đôi các bản ghi đã có.

## Giai đoạn 5-10 đã bổ sung

System Settings:

- Company, Logo, Favicon, SMTP, Google Analytics, Social Links, Language, Timezone nằm ở `/admin/settings`.
- Header/footer public đọc dữ liệu từ Settings, nên đổi tên công ty/email/hotline/logo không cần sửa code.

Security:

- CSRF tự động chèn vào form Admin.
- 2FA bật/tắt trong `/admin/account`, mã demo lưu ở Email outbox.
- Remember Login 30 ngày ở form login.
- Audit Log đã có trong CMS người dùng và Developer actions.
- IP Whitelist, Password Policy, Captcha nằm ở `/admin/settings`.
- Backup Database nằm ở `/admin/developer` và script `scripts/backup_database.py`.

Developer:

- Health Check: `/api/health`
- API Version: `/api/version`
- OpenAPI: `/api/openapi.json`
- Developer panel: `/admin/developer`
- Developer panel có System Info, Environment, Cache Clear, Log Viewer, Migration, Backup.

Hiệu năng:

- Redis cache đã có ở `backend/cache/redis_cache.py`.
- Pagination đã có ở các module CMS.
- Lazy load ảnh đã thêm cho card sản phẩm/tin tức/banner.
- CDN ready ở mức cấu hình: static/upload có thể đi qua Nginx hoặc CDN.
- Background job backup mẫu: `python scripts\backup_database.py`.

Testing:

- Unit/Integration test hiện nằm trong `backend/tests/test_app_behavior.py`.
- Test hiện phủ service/repository/controller/cache/security/developer/API cơ bản.

Triển khai:

- Docker: `Dockerfile`
- Docker Compose: `docker-compose.yml`
- Nginx mẫu: `nginx/nginx.conf`
- GitHub Actions: `.github/workflows/ci.yml`
- Backup: `python scripts\backup_database.py`
- Restore: `python scripts\restore_database.py backups\tên-file.sqlite`

## Ghi chú cho người mới học code

- Muốn sửa giao diện: xem `frontend/css/styles.css`.
- Muốn sửa HTML mẫu tĩnh: xem các file trong `frontend/`.
- Muốn sửa web động/API: xem `backend/app.py`.
- Muốn sửa dữ liệu mẫu: xem `backend/database/seed.sql`.
- Muốn sửa cấu trúc database: xem `backend/database/schema.sql`.
## Demo Enterprise Backend trên trình duyệt

Mở trang:

```text
http://127.0.0.1:8000/admin/developer
```

Các nút demo chính:

- `Create demo event`: tạo event `contact.created`. Đây là ví dụ khi khách hàng gửi form liên hệ.
- `Run worker now`: xử lý các job đang chờ trong queue.
- `Queue backup job`: đưa tác vụ backup database vào queue để worker xử lý sau.

Các bảng trên trang Developer giúp bạn nhìn rõ luồng backend:

- `Events`: ghi nhận sự kiện nghiệp vụ đã xảy ra.
- `Queue Jobs`: danh sách tác vụ nền, ví dụ gửi email, tạo notification, backup database.
- `Notifications`: thông báo nội bộ trong CMS.
- `Email Outbox`: email demo được lưu lại trong database thay vì gửi SMTP thật.

Chạy worker bằng terminal:

```text
python scripts\run_worker.py
```

Chạy worker liên tục khi demo:

```text
python scripts\run_worker.py --loop
```

## Demo AI với Ollama local

Trang Admin AI:

```text
http://127.0.0.1:8000/admin/ai
```

API chatbot:

```text
POST http://127.0.0.1:8000/api/ai/chat
Content-Type: application/json

{
  "message": "MecPrecision có gia công CNC không?",
  "model": "llama3:latest"
}
```

Mặc định backend gọi Ollama tại:

```text
http://127.0.0.1:11434
```

Chạy Ollama thật:

```text
ollama run llama3:latest
```

Nếu Ollama chưa bật, backend vẫn trả lời fallback demo để website không bị lỗi.

Biến môi trường có thể đổi trong `.env`:

```text
MEC_OLLAMA_URL=http://127.0.0.1:11434
MEC_OLLAMA_MODEL=llama3:latest
MEC_OLLAMA_TIMEOUT_SECONDS=20
```
