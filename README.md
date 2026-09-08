# MecPrecision Vietnam

Repository này có backend chính là Django và frontend chính là React/Vite. Các
thư mục `backend/`, `frontend/` và `mecprecision/` được giữ lại để tương thích,
đối chiếu lịch sử hoặc rollback; chúng không phải đường chạy mặc định và không
nên được dùng để bắt đầu phát triển mới.

## Cấu trúc chính

```text
.
├── django_backend/          # Backend Django chính; manage.py nằm tại đây
├── figma_make_frontend/     # Frontend React 19 + Vite chính
├── backend/                 # Backend Python/SQLite legacy
├── frontend/                # Giao diện HTML/JS legacy
├── mecprecision/            # Django prototype cũ
├── .github/workflows/       # CI
├── Dockerfile               # Image production của django_backend
└── docker-compose.yml       # Django + PostgreSQL + Redis + n8n
```

Entrypoint backend là `django_backend/manage.py` và `config.wsgi:application`.
Entrypoint frontend là `figma_make_frontend/src/main.tsx`.

## Yêu cầu

- Python 3.12 (khớp Dockerfile và CI).
- Node.js 22 và pnpm 10.34.3 (khớp `figma_make_frontend/.mise.toml`).
- Docker Desktop/Compose chỉ cần khi chạy stack container.

Không tự ý nâng phiên bản dependency. Backend dùng
`django_backend/requirements.txt`; frontend dùng `pnpm-lock.yaml`.

## Chạy backend Django ở local

Từ thư mục gốc repository, tạo và kích hoạt virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r django_backend\requirements.txt
```

Trên macOS/Linux, lệnh kích hoạt tương ứng là `source .venv/bin/activate`.

Tạo cấu hình local:

```powershell
Copy-Item .env.example django_backend\.env
```

Mặc định Django có thể dùng SQLite riêng tại `django_backend/db.sqlite3`. Có thể
để `DATABASE_URL` trống, hoặc đặt URI SQLite tuyệt đối trong
`django_backend/.env`. PostgreSQL dùng URI dạng:

```text
DATABASE_URL=postgresql://mecprecision:password@localhost:5432/mecprecision
```

Khởi tạo schema và chạy server:

```powershell
Set-Location django_backend
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Các route quản trị được tách rõ:

- `/admin/`: giao diện quản trị tùy biến của dự án.
- `/django-admin/`: Django admin kỹ thuật tích hợp sẵn.

## Database legacy (tùy chọn)

Fresh clone không cần file SQLite của backend cũ. Alias `legacy` bị tắt theo mặc
định để Django không phụ thuộc hoặc vô tình tạo database bị `.gitignore`.

Chỉ bật khi cần kiểm tra tương thích với một file đã tồn tại và phải dùng URI
đọc-only:

```text
LEGACY_DATABASE_ENABLED=true
LEGACY_DATABASE_URL=file:C:/absolute/path/to/mecprecision.sqlite?mode=ro
```

Các màn hình/API chưa di chuyển hoàn toàn khỏi dữ liệu legacy sẽ không có dữ
liệu tương thích khi alias này tắt. Không chạy script seed trong quy trình cài
đặt mặc định.

## Chạy frontend React/Vite

```powershell
Set-Location figma_make_frontend
pnpm install --frozen-lockfile
pnpm dev
```

Vite mặc định lắng nghe cổng `8443`. Có thể cấu hình URL API cho frontend bằng
`VITE_API_BASE_URL=http://127.0.0.1:8000` nếu mã frontend sử dụng biến này.

Build production:

```powershell
pnpm build
```

`package.json` hiện không định nghĩa script test hoặc lint; script chất lượng có
sẵn là `pnpm format`. CI chỉ chạy build thay vì tuyên bố có test frontend.

## Kiểm tra backend

Lane mặc định chạy toàn bộ suite và an toàn cho fresh clone. Những test thực sự
cần SQLite legacy vẫn được collect nhưng skip có điều kiện với marker
`legacy_artifact` khi artifact chưa được cấu hình:

```powershell
Set-Location django_backend
$env:DJANGO_SETTINGS_MODULE = "config.settings.test"
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest -q
```

Lane legacy tùy chọn chỉ chạy khi Owner cung cấp artifact thật. Không có database
nào được tự tạo hoặc seed:

```powershell
$env:LEGACY_DATABASE_ENABLED = "true"
$env:LEGACY_DATABASE_URL = "file:C:/path/to/existing/mecprecision.sqlite?mode=ro"
python -m pytest -m legacy_artifact -q
```

Fixture tương thích sao chép artifact đã cấu hình sang thư mục tạm và mở bản sao
ở chế độ read-only; database legacy không phải dependency khởi động của ứng
dụng. Nếu biến bật, URI read-only hoặc file bị thiếu, lane mặc định ghi rõ lý do
skip thay vì tạo database giả.

## Docker Compose

`docker-compose.yml` hỗ trợ stack production-like gồm Django/Gunicorn,
PostgreSQL 16, Redis 7 và n8n. WhiteNoise phục vụ static files trong image.

Sao chép `.env.example` thành `.env`, thay toàn bộ placeholder password/key bằng
giá trị local không commit, sau đó chạy:

```powershell
Copy-Item .env.example .env
docker compose config
docker compose up --build
```

Compose áp dụng settings production và yêu cầu tối thiểu `SECRET_KEY`,
`POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `METRICS_BEARER_TOKEN`,
`N8N_ENCRYPTION_KEY` và `N8N_WEBHOOK_SECRET` có giá trị. Stack không dùng
database SQLite legacy.

## CI

Workflow chính `.github/workflows/ci.yml` cài dependency từ manifest hiện hành,
chạy Django system check, kiểm tra migration, full pytest của backend và build
frontend từ lockfile. Các workflow chuyên biệt hiện hữu cũng dùng requirements
của Django; không workflow nào cài dependency từ backend legacy.

Không có deployment tự động trong các workflow này.
