# Technical Audit Report - mecprecision-vietnam

Phase: 0 - Technical Audit Only  
Date: 2026-07-25  
Scope: Legacy Python backend, database, frontend integration, infrastructure, migration risks.

## 1. Executive Summary

The current `mecprecision-vietnam` system is a custom Python backend built around `backend/app.py`, SQLite, manually written repositories/services, a CMS admin interface, public HTML pages, JSON APIs, file uploads, optional Redis cache, AI/Ollama integration, and Docker/Nginx deployment scaffolding.

The system is already modularized to a useful degree:

- `app.py` owns HTTP routing, page rendering, admin route handling, request parsing, response output.
- `controllers/` contains public API controller functions.
- `services/` contains business logic.
- `repositories/` contains SQL access.
- `database/` contains SQLite schema, seed, migrations, and connection helpers.
- `auth/` contains password/session/permission helpers.
- `middleware/` contains exception handling and security headers.
- `cache/` contains optional Redis cache helpers.
- `tests/` contains unit/integration tests for important behavior.

Migration to Django should be gradual and read-only first. The safest next step is to map the existing SQLite schema to Django unmanaged ORM models before moving any business logic.

Important note: the repository currently also contains `django_backend/` and `mecprecision/` Django-related folders from prior work. This audit focuses on the legacy system and treats those folders as migration artifacts, not as the production legacy runtime.

## 2. Current Project Structure

Root-level folders:

| Path | Purpose |
|---|---|
| `backend/` | Main legacy Python backend. |
| `frontend/` | Static HTML/CSS/JS frontend assets. |
| `scripts/` | Database and utility scripts. |
| `nginx/` | Nginx reverse proxy sample config. |
| `.github/` | CI/CD workflow folder. |
| `backups/` | Database backup output folder. |
| `django_backend/` | Parallel Django migration artifact. |
| `mecprecision/` | Earlier Django migration artifact. |

Legacy backend folders:

| Path | Purpose |
|---|---|
| `backend/app.py` | Custom HTTP server, routing, page rendering, admin CMS route handling. |
| `backend/api/` | OpenAPI schema generation. |
| `backend/auth/` | Password hashing, session handling, role permission checks. |
| `backend/cache/` | Optional Redis cache integration. |
| `backend/config/` | Environment/settings loader. |
| `backend/controllers/` | API controller layer between HTTP routes and services. |
| `backend/database/` | SQLite schema, seed, migrations, connection helpers. |
| `backend/middleware/` | Exception handler and security headers. |
| `backend/repositories/` | SQL query/write layer. |
| `backend/services/` | Business logic layer. |
| `backend/tests/` | Automated tests. |
| `backend/uploads/` | Uploaded images/files. |
| `backend/utils/` | Routing, text, uploads, logging helpers. |
| `backend/validators/` | Validation placeholder/docs. |

## 3. Backend Architecture

### 3.1 Runtime

The production legacy entrypoint is:

```powershell
python backend\app.py
```

It runs a custom Python HTTP server, not Flask/FastAPI/Django.

The server is responsible for:

- Serving public pages.
- Serving static assets and uploads.
- Rendering admin CMS pages.
- Handling admin form POST routes.
- Handling JSON APIs.
- Parsing request body/form data.
- Reading/writing cookies.
- Applying custom exception handling.
- Sending JSON/HTML/CSV/file responses.

### 3.2 Layering

Current architecture is approximately:

```text
HTTP request
  -> backend/app.py route matching
  -> controller or direct render/admin handler
  -> service
  -> repository
  -> database.connection
  -> SQLite
```

For public JSON APIs, the flow is cleaner:

```text
app.py
  -> controllers/api_controller.py
  -> services/*
  -> repositories/*
  -> database/connection.py
```

For admin CMS routes, much logic is still handled directly in `app.py`, including:

- Route dispatch.
- Permission checks.
- Form rendering.
- Form POST handling.
- Redirects.
- Delete/edit route parsing.

### 3.3 Controllers

`backend/controllers/api_controller.py` handles important public APIs:

- home data
- products
- product categories
- capabilities
- news
- contact submission
- product CRUD API
- OpenAPI response

It already centralizes controller return format as `(data, status)`.

### 3.4 Services

Important service modules:

| Service | Responsibility |
|---|---|
| `products_service.py` | Product list/detail/create/update/delete and payload normalization. |
| `categories_service.py` | Product category CRUD. |
| `contacts_service.py` | Contact request CRUD, validation, CSV rows. |
| `cms_service.py` | Pages, menus, banners, quotes, customers, newsletter. |
| `news_service.py` | News CRUD and payload normalization. |
| `users_service.py` | Admin user CRUD and avatar/password payload handling. |
| `auth_service.py` | Password reset, change password/email, lock/unlock account. |
| `security_service.py` | CSRF, captcha, password policy, 2FA helper. |
| `dashboard_service.py` | Dashboard counts, visits, chart data. |
| `ai_service.py` | Ollama chatbot, translation, developer AI, quote/contact analysis, product SEO. |
| `media_service.py` | Upload, folder, rename, delete, preview/media list. |
| `developer_service.py` | Health/system info, migrations, backups, logs. |
| `queue_service.py` | SQLite job queue processing. |
| `event_service.py` | Event publishing and job creation. |
| `notification_service.py` | CMS notification creation/read state. |
| `settings_service.py` | System settings. |
| `localization_service.py` | Language/page translation helpers. |

### 3.5 Repositories

Repositories contain raw SQL and direct SQLite reads/writes:

| Repository | Responsibility |
|---|---|
| `products_repository.py` | Product SQL. |
| `categories_repository.py` | Category SQL. |
| `contacts_repository.py` | Contact SQL. |
| `cms_repository.py` | CMS pages, menus, banners, quotes, customers, newsletter SQL. |
| `news_repository.py` | News SQL. |
| `users_repository.py` | Admin user SQL. |
| `auth_repository.py` | Auth/account/reset token SQL. |
| `dashboard_repository.py` | Counts, visits, charts SQL. |
| `enterprise_repository.py` | Event, queue, notification SQL. |
| `ai_repository.py` | AI conversation/cache SQL. |
| `settings_repository.py` | Settings SQL. |
| `translation_repository.py` | Translation SQL. |
| `public_repository.py` | Public page data SQL. |
| `activity_repository.py` | Admin activity log SQL. |

### 3.6 Middleware / Error Handling

`backend/middleware/exception_handler.py` centralizes request exception handling:

- `AppError` -> structured response with status/code.
- `ValueError` -> `400 VALIDATION_ERROR`.
- `sqlite3.IntegrityError` -> `409 DATABASE_CONSTRAINT_ERROR`.
- unknown exception -> `500 INTERNAL_SERVER_ERROR`.

`backend/middleware/security_headers.py` adds:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`

Risk: middleware behavior is custom and not framework-standard. When migrating to Django, map this to Django middleware and DRF exception handler.

## 4. Database Map

### 4.1 Engine

Current database engine:

```text
SQLite
backend/database/mecprecision.sqlite
```

Connection helper:

```text
backend/database/connection.py
```

Important behavior:

- Enables foreign keys with `PRAGMA foreign_keys = ON`.
- Uses `sqlite3.Row` row factory.
- Provides `query_all`, `query_one`, `execute_write`, and `transaction`.
- Multi-step write rollback is manually handled by `transaction()`.

### 4.2 Schema Files

| File | Purpose |
|---|---|
| `backend/database/schema.sql` | Main schema, FK, indexes, view. |
| `backend/database/seed.sql` | Demo seed data. |
| `backend/database/migrations.py` | Incremental compatibility migrations for older SQLite files. |

### 4.3 Tables

| Table | Group | Notes |
|---|---|---|
| `admin_users` | Auth/CMS | Admin users, role, active status, avatar, 2FA flag. |
| `admin_sessions` | Auth | DB-backed admin sessions. |
| `login_attempts` | Auth/Security | Rate-limit/audit login attempts. |
| `password_reset_tokens` | Auth | One-time password reset tokens. |
| `admin_2fa_challenges` | Auth | One-time 2FA challenge codes. |
| `auth_email_outbox` | Auth/Email | Demo email outbox. |
| `admin_activity_logs` | Audit | CMS activity logs. |
| `product_categories` | Product | Category master. |
| `materials` | Product/Manufacturing | Material master. |
| `machines` | Manufacturing | Machine master. |
| `manufacturing_processes` | Manufacturing | Process master. |
| `products` | Product | Product content, SEO, media, status. |
| `product_materials` | Product M2M | Product-material relationship. |
| `product_processes` | Product M2M | Product-process workflow. |
| `product_images` | Product media | Product gallery. |
| `product_specs` | Product specs | Key/value specs. |
| `capabilities` | Public content | Manufacturing capabilities. |
| `capability_machines` | Capability M2M | Capability-machine relationship. |
| `customers` | CRM | Customer/company data. |
| `customer_notes` | CRM | Customer care notes. |
| `contact_requests` | CRM | Public contact form submissions. |
| `quote_requests` | Sales | Quote workflow. |
| `quote_request_items` | Sales | Quote line items. |
| `quote_files` | Sales | Quote attachments. |
| `newsletter_subscribers` | Marketing | Newsletter subscribers. |
| `news_categories` | Content | News category master. |
| `news` | Content | News articles, SEO, publish scheduling. |
| `tags` | Content | Tags. |
| `news_tags` | Content M2M | News-tag relationship. |
| `page_visits` | Analytics | Public visit tracking. |
| `cms_pages` | CMS | Dynamic pages. |
| `cms_menu_items` | CMS | Header/footer/sidebar nested menu. |
| `cms_banners` | CMS | Slider/popup/ads banners. |
| `enterprise_events` | System/Event | Business event log. |
| `job_queue` | System/Queue | Background job queue. |
| `notifications` | CMS/System | Internal notifications. |
| `ai_conversations` | AI | AI conversation/history. |
| `ai_translation_cache` | AI | AI translation cache. |
| `system_settings` | System | Key/value settings. |

### 4.4 Important Relationships

| Relationship | Type |
|---|---|
| `products.category_id -> product_categories.id` | many products to one category |
| `product_materials.product_id -> products.id` | product M2M material |
| `product_materials.material_id -> materials.id` | product M2M material |
| `product_processes.product_id -> products.id` | product M2M process |
| `product_processes.process_id -> manufacturing_processes.id` | product M2M process |
| `product_images.product_id -> products.id` | product has many images |
| `product_specs.product_id -> products.id` | product has many specs |
| `capability_machines.capability_id -> capabilities.id` | capability M2M machine |
| `capability_machines.machine_id -> machines.id` | capability M2M machine |
| `quote_requests.customer_id -> customers.id` | quote belongs to customer |
| `quote_request_items.quote_request_id -> quote_requests.id` | quote has many items |
| `quote_request_items.product_id -> products.id` | quote item may reference product |
| `quote_request_items.material_id -> materials.id` | quote item may reference material |
| `quote_files.quote_request_id -> quote_requests.id` | quote has many files |
| `news.category_id -> news_categories.id` | news belongs to category |
| `news_tags.news_id -> news.id` | news M2M tags |
| `news_tags.tag_id -> tags.id` | news M2M tags |
| `admin_sessions.admin_id -> admin_users.id` | admin has many sessions |
| `password_reset_tokens.admin_id -> admin_users.id` | admin has reset tokens |
| `customer_notes.customer_id -> customers.id` | customer has notes |
| `cms_menu_items.parent_id -> cms_menu_items.id` | nested menu |

### 4.5 Indexes

Existing indexes:

- `idx_products_category_id`
- `idx_products_slug`
- `idx_news_category_id`
- `idx_quote_requests_customer_id`
- `idx_quote_items_quote_request_id`
- `idx_admin_sessions_expires_at`
- `idx_login_attempts_email_time`
- `idx_password_reset_tokens_admin`
- `idx_admin_activity_logs_created`
- `idx_page_visits_visited_at`
- `idx_enterprise_events_created`
- `idx_job_queue_status`
- `idx_notifications_read`
- `idx_ai_conversations_created`
- `idx_ai_translation_cache_lookup`

Existing view:

- `product_overview`

### 4.6 Database Risks

| Risk | Severity | Notes |
|---|---:|---|
| SQLite as production database | Medium/High | Acceptable for local/demo, but concurrency/write-locking can become a limitation. |
| Raw SQL spread across repositories | Medium | Good for explicit control, but migration requires careful model mapping. |
| Schema evolved through custom `migrations.py` | Medium | Need exact state detection before Django ORM/migrations. |
| TEXT fields used for timestamps | Medium | Django `DateTimeField` mapping needs careful parsing/timezone policy. |
| Boolean stored as integer | Low/Medium | Map to Django `BooleanField` carefully. |
| M2M bridge tables with composite primary keys | Medium | Django model mapping may require through models/unmanaged models. |
| Existing file paths in uploads | Medium | Need media storage migration strategy. |

## 5. API Map

### 5.1 Public Page Routes

Dynamic/public routes are handled by `backend/app.py`.

Known page routes include:

| Route | Purpose |
|---|---|
| `/` | Homepage. |
| `/index.html` | Homepage alias. |
| `/san-pham.html`, `/san-pham` | Product page. |
| `/cong-nghe.html`, `/cong-nghe` | Technology/capability page. |
| `/tin-tuc.html`, `/tin-tuc` | News page. |
| `/lien-he.html`, `/lien-he` | Contact page. |
| `/api-aws.html` | API/AWS demo page. |
| Dynamic CMS pages | Slug-based published pages are supported through CMS page logic. |

### 5.2 Public JSON APIs

| Method | Route | Purpose | Main handler |
|---|---|---|---|
| GET | `/api/home` | Home page data | `get_home_response()` |
| GET | `/api/products` | Product list | `list_products_response()` |
| POST | `/api/products` | Create product | `create_product_response()` |
| GET | `/api/products/{id}` | Product detail | `get_product_response()` |
| PUT | `/api/products/{id}` | Update product | `update_product_response()` |
| DELETE | `/api/products/{id}` | Delete product | `delete_product_response()` |
| GET | `/api/product-categories` | Product categories | `list_product_categories_response()` |
| GET | `/api/capabilities` | Capability list | `list_capabilities_response()` |
| GET | `/api/news` | News list | `list_news_response()` |
| POST | `/api/contact` | Submit contact request | `create_contact_response()` |
| POST | `/api/quote-request` | Submit quote request | `create_public_quote_request()` via route |
| POST | `/api/ai/chat` | Public AI chatbot | `ask_ai()` |
| GET | `/api/external/weather` | External API demo | app route |
| GET | `/api/aws-demo` | AWS/API demo | app route |
| GET | `/api/openapi.json` | OpenAPI schema | `openapi_response()` |
| GET | `/api/health` | Health check | app route |
| GET | `/api/version` | API version | app route |
| GET | `/api/docs` | API docs page | app route |

### 5.3 Admin CMS Routes

Admin routes are mostly implemented directly in `backend/app.py`.

Authentication routes:

| Method | Route | Purpose |
|---|---|---|
| GET/POST | `/admin/login` | Login. |
| GET | `/admin/logout` | Logout. |
| GET/POST | `/admin/forgot-password` | Request password reset. |
| GET/POST | `/admin/reset-password` | Reset password by token. |
| GET/POST | `/admin/2fa` | 2FA challenge. |
| GET | `/admin/account` | My account/session page. |
| POST | `/admin/account/change-password` | Change password. |
| POST | `/admin/account/change-email` | Change email. |
| POST | `/admin/account/sessions/revoke` | Revoke session. |
| POST | `/admin/account/2fa` | Toggle 2FA. |

CMS module routes:

| Route group | Features |
|---|---|
| `/admin` | Dashboard. |
| `/admin/products` | Product list/filter/form. |
| `/admin/products/{id}/edit` | Product edit. |
| `/admin/products/save` | Product create/update. |
| `/admin/products/{id}/delete` | Product delete. |
| `/admin/products/ai-generate` | AI product content/SEO generation. |
| `/admin/categories` | Category CRUD. |
| `/admin/news` | News CRUD/filter/status/schedule/SEO. |
| `/admin/media` | Media manager: upload, folder, search, rename, delete. |
| `/admin/pages` | CMS dynamic page CRUD. |
| `/admin/menus` | Menu builder CRUD. |
| `/admin/banners` | Banner CRUD. |
| `/admin/contacts` | Contact CRUD/export. |
| `/admin/quotes` | Quote workflow management. |
| `/admin/customers` | Customer CRUD and notes. |
| `/admin/newsletter` | Newsletter CRUD/export. |
| `/admin/users` | Admin user CRUD, lock/unlock, avatar. |
| `/admin/settings` | System settings and password policy. |
| `/admin/ai` | AI admin tools. |
| `/admin/developer` | Developer/system tools. |

Developer/admin operation routes:

| Route | Purpose |
|---|---|
| `/admin/developer/cache-clear` | Clear cache. |
| `/admin/developer/migrate` | Run legacy migrations. |
| `/admin/developer/backup` | Create database backup. |
| `/admin/developer/demo-event` | Create demo event. |
| `/admin/developer/run-worker` | Process queue jobs. |
| `/admin/developer/demo-backup-job` | Enqueue backup job. |
| `/admin/developer/ai-code` | Developer AI code assistant. |
| `/admin/ai/ask` | Admin AI chat. |
| `/admin/ai/translate` | AI translation. |
| `/admin/ai/contacts-summary` | AI contact summary. |
| `/admin/ai/quote-analysis` | AI quote analysis. |
| `/admin/ai/smart-search` | AI smart search. |
| `/admin/ai/dashboard-insights` | AI dashboard insights. |
| `/admin/ai/document-read` | AI document reader. |

### 5.4 API Risks

| Risk | Severity | Notes |
|---|---:|---|
| Route dispatch is centralized in a large `app.py` | High | Hard to reason about, test, extend, and secure. |
| Mixed HTML rendering and API logic | Medium/High | Django should split views/templates/API ViewSets gradually. |
| Admin APIs are form POST routes, not REST APIs | Medium | Migration should preserve behavior first. |
| OpenAPI covers only key public APIs | Medium | Admin and AI operation routes are not fully documented. |
| CSRF protection is custom | Medium | Should map to Django CSRF before switching admin forms. |

## 6. Authentication & Authorization

### 6.1 Login Flow

Current flow:

1. User opens `/admin/login`.
2. Form submits email/password to `/admin/login`.
3. `app.py` checks IP whitelist/captcha/rate limit as configured.
4. Password is verified using `auth/passwords.py`.
5. If user has 2FA enabled, a 2FA challenge is created.
6. If successful, `auth/sessions.py` creates `admin_sessions` row.
7. Session id is stored in cookie `mecprecision_session`.
8. Admin routes call `get_current_admin()`, load session, and merge user record.

### 6.2 Passwords

Current password support:

- PBKDF2-HMAC-SHA256 custom format: `pbkdf2_sha256$iterations$salt$hash`.
- Legacy SHA-256 salted hash still supported for old demo accounts.
- Password policy configurable through `system_settings`.

Migration recommendation:

- Move to Django password hashers.
- Keep legacy hash compatibility during transition with a custom Django password hasher or migration command.

### 6.3 Sessions

Current session support:

- Database-backed sessions in `admin_sessions`.
- Multiple device sessions.
- Expiration timestamp.
- `last_seen_at` tracking.
- Session revocation.
- Remember login with longer TTL.

Migration recommendation:

- Use Django sessions for new Django admin/auth.
- Keep legacy session read support only during transition if both systems must share admin login.

### 6.4 Authorization

Current authorization:

- Role-based: `admin`, `editor`, `viewer`.
- `admin`: all permissions.
- `editor`: read/write on operational modules.
- `viewer`: read only.

Migration recommendation:

- Map roles to Django Groups and Permissions.
- Preserve role semantics exactly before changing permission model.

### 6.5 Security Features

Implemented:

- Password reset token.
- Login attempt logging and rate limiting.
- Session expiration.
- Account lock/unlock.
- 2FA challenge.
- CSRF helper for admin forms.
- Captcha helper.
- Security headers.
- Admin activity logs.
- Password policy settings.

Security gaps/risks:

| Risk | Severity | Notes |
|---|---:|---|
| Custom auth/session implementation | High | More maintenance/security responsibility than Django Auth. |
| 2FA implementation appears demo/local | Medium | Needs expiry, replay, delivery, backup codes review. |
| Admin route authorization is manual | Medium/High | Easy to miss permission checks in large `app.py`. |
| File upload validation must be reviewed | Medium | Ensure extension/MIME/path traversal handling. |
| External AI/Ollama prompt injection risk | Medium | AI should not have write/admin capability without explicit review. |
| Error output in debug mode | Medium | Ensure production never exposes raw exceptions. |

## 7. Infrastructure

### 7.1 Environment

Settings are loaded from `.env` via custom parser in `backend/config/settings.py`.

Important variables:

- `MEC_ENV`
- `MEC_DEBUG`
- `MEC_HOST`
- `MEC_PORT`
- `MEC_DATABASE_PATH`
- `MEC_SESSION_TTL_SECONDS`
- `MEC_PASSWORD_SALT`
- `MEC_REDIS_URL`
- `MEC_REDIS_CACHE_ENABLED`
- `MEC_OLLAMA_URL`
- `MEC_OLLAMA_MODEL`
- `MEC_OLLAMA_TIMEOUT_SECONDS`

### 7.2 Cache

Redis is optional:

- Implemented manually using socket and RESP protocol in `backend/cache/redis_cache.py`.
- If Redis is disabled/down, helper returns `None` and app continues with SQLite.
- Public home API can be cached.

Migration recommendation:

- Use Django cache framework with Redis backend.
- Keep cache optional for local development.

### 7.3 Queue / Background Jobs

Current queue:

- SQLite table `job_queue`.
- `queue_service.py` processes pending jobs synchronously when called.
- Supported job types include:
  - `email.send`
  - `notification.create`
  - `database.backup`

Migration recommendation:

- Short term: keep SQLite queue and wrap with Django management command.
- Long term: Celery/RQ/Huey with Redis if background workload grows.

### 7.4 Events / Notifications

Current event system:

- `enterprise_events` table stores business events.
- Events may enqueue jobs.
- Notifications are stored in `notifications`.

Migration recommendation:

- Keep event naming and payload schema stable.
- Convert to Django service + transaction hooks later.

### 7.5 AI / Ollama

Current AI features:

- Public chatbot.
- Admin AI chat.
- Translation.
- Developer AI.
- Contact summary.
- Quote analysis.
- Document reader.
- Smart search.
- Dashboard insights.
- Product content and SEO generation.

AI data tables:

- `ai_conversations`
- `ai_translation_cache`

Migration recommendation:

- Treat AI services as isolated app.
- Do not allow AI to mutate production data without explicit human confirmation.
- Maintain fallback behavior when Ollama is unavailable.

### 7.6 Deployment

Current deployment scaffolding:

- `Dockerfile` runs `python backend/app.py`.
- `docker-compose.yml` defines:
  - `web`
  - `redis`
  - `nginx`
- `nginx/nginx.conf` proxies to web and adds cache headers for static/upload paths.

Migration recommendation:

- Add Django as a separate service first.
- Avoid replacing legacy `web` service until parity is validated.
- Use distinct ports/domains for parallel run.

## 8. Current Test Coverage

Current test command:

```powershell
python -m unittest discover -s backend\tests -p "test_*.py"
```

Existing test categories:

- Service/repository tests.
- Controller tests.
- Cache optional behavior.
- Transaction rollback.
- Dashboard counts/charts.
- Media manager.
- CMS pages/banner/newsletter.
- AI fallback/content/translation/developer/search/document tests.
- Security helpers.
- Developer tools.
- Event/queue/notification/email flow.
- Authentication reset/lock/session/avatar/activity log tests.
- Endpoint integration tests.

Strengths:

- Tests use temporary SQLite and do not touch real `mecprecision.sqlite`.
- Integration tests exist for important API behavior.
- AI fallback behavior is tested.
- Transaction rollback is tested.

Gaps:

- Admin HTML route coverage appears limited.
- Permission matrix coverage should be expanded.
- File upload security cases should be expanded.
- OpenAPI coverage is partial.
- No Django test framework yet for future migration path.

## 9. Technical Debt

### 9.1 Large `app.py`

`backend/app.py` handles too many responsibilities:

- HTTP server.
- Routing.
- HTML rendering.
- Admin CMS forms.
- Auth redirects.
- API dispatch.
- File serving.
- Response formatting.

Risk: high change risk and difficult review.

Migration recommendation: extract route groups gradually into Django apps or preserve behavior behind adapter endpoints.

### 9.2 Raw SQL Everywhere

Repositories are explicit and readable, but every query is manually maintained.

Risk:

- Schema changes require manual updates in multiple places.
- Hard to enforce consistency.
- Hard to compose complex queries safely.

Migration recommendation: create unmanaged Django models first, then replace repositories module by module.

### 9.3 Custom Auth Instead of Django Auth

Current auth is functional but custom.

Risk:

- Security maintenance burden.
- Role/permission checks are manual.
- Password hash migration needs care.

Migration recommendation: design compatibility bridge to Django Auth.

### 9.4 Encoding/Comment Artifacts

Some files show mojibake comments in terminal output. This may be terminal/codepage display, but needs review before generating documentation/user-facing text.

Risk: low/medium.

Migration recommendation: standardize UTF-8 and verify editor/terminal encoding.

### 9.5 Mixed Public/Admin/API Concerns

Public pages, CMS, API, AI, Developer tools all share the same server file.

Risk: medium/high.

Migration recommendation: split apps according to target architecture:

- `core`
- `accounts`
- `catalog.products`
- `catalog.categories`
- `crm.customers`
- `crm.contacts`
- `sales.quotation`
- `content.news`
- `ai`
- `dashboard`
- `common`

## 10. Risk Assessment

| Area | Risk | Severity | Recommendation |
|---|---|---:|---|
| Database migration | Incorrect model mapping can corrupt data | High | Start with unmanaged read-only Django models. |
| Authentication | Session/password incompatibility | High | Design auth compatibility before switching admin login. |
| Admin CMS | Large route surface | High | Migrate one admin module at a time. |
| File uploads | Storage/path behavior mismatch | Medium/High | Audit upload paths and media URLs before Django storage. |
| AI | Prompt injection/fallback behavior | Medium | Keep AI isolated and non-mutating. |
| Redis/cache | Manual Redis client | Medium | Move to Django cache framework later. |
| SQLite concurrency | Write locking under traffic | Medium | Consider PostgreSQL only after Django model parity. |
| OpenAPI | Partial documentation | Medium | Generate DRF schema after API migration. |
| Tests | Legacy tests only | Medium | Add pytest/pytest-django in Django foundation. |

## 11. Migration Recommendation

### Recommended Migration Path

1. Keep legacy backend running unchanged.
2. Keep new Django backend as a parallel service.
3. Do not migrate database yet.
4. Create `DATABASE_MAPPING.md` before any Django models.
5. Create unmanaged Django models mapped to existing SQLite tables.
6. Add read-only APIs first.
7. Compare Django read output with legacy API output.
8. Move write endpoints only after parity tests exist.
9. Move authentication last or behind a compatibility bridge.
10. Only after full parity, decide whether to:
    - keep SQLite,
    - move to PostgreSQL,
    - or run dual-write/backup migration.

### Suggested Module Order

1. Core health/config/logging.
2. Product/category read models.
3. Customer/contact read models.
4. Quotation read models.
5. News/content read models.
6. AI read/history APIs.
7. Dashboard read APIs.
8. Authentication compatibility.
9. Admin write workflows.
10. Developer/system tools.

## 12. Rollback Strategy

For each migration step:

- Do not remove legacy route.
- Do not modify legacy schema directly.
- Keep Django on separate port/service.
- Add read-only comparison tests first.
- If failure occurs, stop Django service and continue using legacy backend.
- Back up `backend/database/mecprecision.sqlite` before any schema operation.
- Use feature flags or separate URLs for Django endpoints until parity is proven.

## 13. Phase 0 Conclusion

The current legacy system is more mature than a simple prototype: it includes CMS, authentication, AI, queue, event, notifications, Redis optional cache, OpenAPI, Docker/Nginx scaffolding, and automated tests.

The highest migration risks are:

1. Custom auth/session compatibility.
2. Large `backend/app.py` route surface.
3. Raw SQL and SQLite schema mapping.
4. Admin CMS form behavior.
5. Upload/media handling.

The next phase should not write models yet. It should create a formal migration plan.

Recommended next step:

```text
PHASE 1 - MIGRATION PLAN
Create MIGRATION_PLAN.md
No code changes.
```

Stop here and wait for confirmation.
