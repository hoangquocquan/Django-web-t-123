# Database Inventory And Mapping

Phase: 3 - Database Mapping / Legacy Schema Analysis  
Rule: Documentation only. No Django models, no migrations, no database changes.

## 1. Located Legacy Database

- Location: `backend\database\mecprecision.sqlite`
- Database engine: SQLite
- SQLite library version: `3.49.1`
- Size: `544768` bytes
- Schema definition: `backend\database\schema.sql`
- Compatibility migrations: `backend\database\migrations.py`
- Tables analyzed: `39` user tables
- Views analyzed: `1`
- Explicit indexes analyzed: `19`

## 2. Source Files Inspected

| Type | Path | Purpose |
|---|---|---|
| SQLite database | `backend/database/mecprecision.sqlite` | Runtime legacy database inspected read-only |
| Schema SQL | `backend/database/schema.sql` | Main schema definition |
| Seed SQL | `backend/database/seed.sql` | Demo/default data source |
| Migration helper | `backend/database/migrations.py` | Compatibility table/index additions |
| Repository | `backend/repositories/__init__.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/activity_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/ai_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/auth_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/categories_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/cms_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/contacts_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/dashboard_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/enterprise_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/news_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/products_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/public_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/settings_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/translation_repository.py` | Raw SQL/query usage scan |
| Repository | `backend/repositories/users_repository.py` | Raw SQL/query usage scan |

## 3. Tables

### admin_2fa_challenges

- Purpose: Two-factor authentication challenge codes.
- Row count at inspection time: `0`
- Used by: auth_repository.py
- Related modules: `accounts`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `challenge_id` | `TEXT` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `admin_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `code` | `TEXT` | No | `` | Sensitive/auth token field; do not expose in API output. |
| `used_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `challenge_id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `admin_id` | `admin_users.id` | `NO ACTION` | `CASCADE` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_admin_2fa_challenges_1` | `1` | `pk` | `challenge_id` |

Constraints: unique index/constraint present, foreign key constraint present

### admin_activity_logs

- Purpose: Admin audit log for sensitive CMS actions.
- Row count at inspection time: `55`
- Used by: activity_repository.py
- Related modules: `accounts`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `admin_id` | `INTEGER` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `actor_name` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `action` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `target_type` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `target_id` | `TEXT` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `description` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `remote_addr` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `admin_id` | `admin_users.id` | `NO ACTION` | `SET NULL` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_admin_activity_logs_created` | `0` | `c` | `created_at` |

Constraints: foreign key constraint present

### admin_sessions

- Purpose: Admin login sessions and multi-device tracking.
- Row count at inspection time: `1`
- Used by: dashboard_repository.py, users_repository.py
- Related modules: `accounts`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `session_id` | `TEXT` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `admin_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `full_name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `email` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `role` | `TEXT` | No | `` | Workflow/classification value; preserve legacy vocabulary. |
| `expires_at` | `INTEGER` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `remote_addr` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `user_agent` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `last_seen_at` | `INTEGER` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |

Primary Key: `session_id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `admin_id` | `admin_users.id` | `NO ACTION` | `CASCADE` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_admin_sessions_expires_at` | `0` | `c` | `expires_at` |
| `sqlite_autoindex_admin_sessions_1` | `1` | `pk` | `session_id` |

Constraints: unique index/constraint present, foreign key constraint present

### admin_users

- Purpose: Admin user accounts for CMS login and role checks.
- Row count at inspection time: `5`
- Used by: auth_repository.py, cms_repository.py, users_repository.py
- Related modules: `accounts`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `full_name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `email` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `password_hash` | `TEXT` | No | `` | Sensitive/auth token field; do not expose in API output. |
| `role` | `TEXT` | No | `'editor'` | Workflow/classification value; preserve legacy vocabulary. |
| `is_active` | `INTEGER` | No | `1` | Boolean stored as INTEGER 0/1. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `avatar_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `two_factor_enabled` | `INTEGER` | No | `0` | Boolean stored as INTEGER 0/1. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_admin_users_1` | `1` | `u` | `email` |

Constraints: unique index/constraint present

### ai_conversations

- Purpose: AI chatbot/conversation history.
- Row count at inspection time: `30`
- Used by: ai_repository.py
- Related modules: `ai`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `channel` | `TEXT` | No | `'public'` | Workflow/classification value; preserve legacy vocabulary. |
| `user_message` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `assistant_message` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `model` | `TEXT` | Yes | `` | Workflow/classification value; preserve legacy vocabulary. |
| `provider` | `TEXT` | No | `'ollama'` | Workflow/classification value; preserve legacy vocabulary. |
| `status` | `TEXT` | No | `'ok'` | Workflow/classification value; preserve legacy vocabulary. |
| `error` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_ai_conversations_created` | `0` | `c` | `created_at` |

Constraints: None beyond column definitions

### ai_translation_cache

- Purpose: AI translation cache/history.
- Row count at inspection time: `235`
- Used by: translation_repository.py
- Related modules: `ai`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `source_hash` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `source_text` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `target_language` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `translated_text` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `provider` | `TEXT` | No | `'ollama'` | Workflow/classification value; preserve legacy vocabulary. |
| `model` | `TEXT` | Yes | `` | Workflow/classification value; preserve legacy vocabulary. |
| `status` | `TEXT` | No | `'ok'` | Workflow/classification value; preserve legacy vocabulary. |
| `error` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `updated_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_ai_translation_cache_lookup` | `0` | `c` | `source_hash, target_language, model` |
| `sqlite_autoindex_ai_translation_cache_1` | `1` | `u` | `source_hash, target_language, model` |

Constraints: unique index/constraint present

### auth_email_outbox

- Purpose: Authentication-related email outbox.
- Row count at inspection time: `3`
- Used by: auth_repository.py
- Related modules: `accounts`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `recipient` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `subject` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `body` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes: `None`

Constraints: None beyond column definitions

### capabilities

- Purpose: Manufacturing capability cards/content.
- Row count at inspection time: `4`
- Used by: public_repository.py
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `title` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `content` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `icon_label` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes: `None`

Constraints: None beyond column definitions

### capability_machines

- Purpose: Many-to-many link between capabilities and machines.
- Row count at inspection time: `5`
- Used by: No direct repository reference found; verify app routes/services.
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `capability_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `machine_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |

Primary Key: `capability_id, machine_id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `machine_id` | `machines.id` | `NO ACTION` | `CASCADE` |
| `capability_id` | `capabilities.id` | `NO ACTION` | `CASCADE` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_capability_machines_1` | `1` | `pk` | `capability_id, machine_id` |

Constraints: unique index/constraint present, foreign key constraint present, composite primary key

### cms_banners

- Purpose: Homepage/banner/advertisement placements.
- Row count at inspection time: `0`
- Used by: cms_repository.py
- Related modules: `cms`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `title` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `placement` | `TEXT` | No | `'home_slider'` | Workflow/classification value; preserve legacy vocabulary. |
| `image_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `link_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `content` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `status` | `TEXT` | No | `'draft'` | Workflow/classification value; preserve legacy vocabulary. |
| `starts_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |
| `ends_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_cms_banners_placement` | `0` | `c` | `placement` |

Constraints: None beyond column definitions

### cms_menu_items

- Purpose: Header/footer/sidebar menu items with nesting.
- Row count at inspection time: `18`
- Used by: cms_repository.py
- Related modules: `cms`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `location` | `TEXT` | No | `'header'` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `parent_id` | `INTEGER` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `label` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `url` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `status` | `TEXT` | No | `'published'` | Workflow/classification value; preserve legacy vocabulary. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `parent_id` | `cms_menu_items.id` | `NO ACTION` | `SET NULL` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_cms_menu_location` | `0` | `c` | `location` |

Constraints: foreign key constraint present

### cms_pages

- Purpose: Dynamic CMS pages.
- Row count at inspection time: `10`
- Used by: cms_repository.py
- Related modules: `cms`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `title` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `slug` | `TEXT` | No | `` | URL-friendly unique identifier. |
| `content` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `seo_title` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `seo_description` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `status` | `TEXT` | No | `'draft'` | Workflow/classification value; preserve legacy vocabulary. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `updated_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_cms_pages_slug` | `0` | `c` | `slug` |
| `sqlite_autoindex_cms_pages_1` | `1` | `u` | `slug` |

Constraints: unique index/constraint present

### contact_requests

- Purpose: Public contact form submissions and admin handling status.
- Row count at inspection time: `6`
- Used by: contacts_repository.py, dashboard_repository.py
- Related modules: `crm`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `contact` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `message` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `status` | `TEXT` | No | `'new'` | Workflow/classification value; preserve legacy vocabulary. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `is_read` | `INTEGER` | No | `0` | Boolean stored as INTEGER 0/1. |
| `note` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `company` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `phone` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `email` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `country` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `interested_product` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `attachment_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |

Primary Key: `id`

Foreign Keys: `None`

Indexes: `None`

Constraints: None beyond column definitions

### customer_notes

- Purpose: Internal notes for customer history.
- Row count at inspection time: `0`
- Used by: cms_repository.py
- Related modules: `crm`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `customer_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `note` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_by` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `customer_id` | `customers.id` | `NO ACTION` | `CASCADE` |

Indexes: `None`

Constraints: foreign key constraint present

### customers

- Purpose: Customer/company master data.
- Row count at inspection time: `3`
- Used by: cms_repository.py, dashboard_repository.py
- Related modules: `crm`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `company_name` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `contact_name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `email` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `phone` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `country` | `TEXT` | Yes | `'Vietnam'` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes: `None`

Constraints: None beyond column definitions

### enterprise_events

- Purpose: Domain event log for workflow side effects.
- Row count at inspection time: `3`
- Used by: enterprise_repository.py
- Related modules: `system`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `event_name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `entity_type` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `entity_id` | `TEXT` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `payload` | `TEXT` | Yes | `` | Serialized JSON/text payload; validate format before typed mapping. |
| `status` | `TEXT` | No | `'published'` | Workflow/classification value; preserve legacy vocabulary. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_enterprise_events_created` | `0` | `c` | `created_at` |

Constraints: None beyond column definitions

### job_queue

- Purpose: SQLite-backed background job queue.
- Row count at inspection time: `5`
- Used by: enterprise_repository.py
- Related modules: `system`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `job_type` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `payload` | `TEXT` | Yes | `` | Serialized JSON/text payload; validate format before typed mapping. |
| `status` | `TEXT` | No | `'pending'` | Workflow/classification value; preserve legacy vocabulary. |
| `attempts` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `available_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `started_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |
| `finished_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |
| `last_error` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_job_queue_status` | `0` | `c` | `status, available_at` |

Constraints: None beyond column definitions

### login_attempts

- Purpose: Login attempt audit and lockout support.
- Row count at inspection time: `30`
- Used by: No direct repository reference found; verify app routes/services.
- Related modules: `accounts`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `email` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `remote_addr` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `success` | `INTEGER` | No | `0` | Boolean stored as INTEGER 0/1. |
| `created_at` | `INTEGER` | No | `` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_login_attempts_email_time` | `0` | `c` | `email, created_at` |

Constraints: None beyond column definitions

### machines

- Purpose: Machine/capability reference data.
- Row count at inspection time: `4`
- Used by: No direct repository reference found; verify app routes/services.
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `machine_type` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `brand` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `max_size` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `tolerance` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `status` | `TEXT` | No | `'active'` | Workflow/classification value; preserve legacy vocabulary. |

Primary Key: `id`

Foreign Keys: `None`

Indexes: `None`

Constraints: None beyond column definitions

### manufacturing_processes

- Purpose: Manufacturing process reference data.
- Row count at inspection time: `5`
- Used by: No direct repository reference found; verify app routes/services.
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `description` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_manufacturing_processes_1` | `1` | `u` | `name` |

Constraints: unique index/constraint present

### materials

- Purpose: Manufacturing material reference data.
- Row count at inspection time: `4`
- Used by: products_repository.py
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `standard` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `description` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_materials_1` | `1` | `u` | `name` |

Constraints: unique index/constraint present

### news

- Purpose: News/article content with SEO and publishing metadata.
- Row count at inspection time: `8`
- Used by: cms_repository.py, dashboard_repository.py, news_repository.py, public_repository.py
- Related modules: `content`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `category_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `title` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `slug` | `TEXT` | No | `` | URL-friendly unique identifier. |
| `image` | `TEXT` | No | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `description` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `content` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `published_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `tags_text` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `seo_title` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `seo_description` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `thumbnail_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `author` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `scheduled_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |
| `is_featured` | `INTEGER` | No | `0` | Boolean stored as INTEGER 0/1. |
| `status` | `TEXT` | No | `'published'` | Workflow/classification value; preserve legacy vocabulary. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `category_id` | `news_categories.id` | `NO ACTION` | `NO ACTION` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_news_category_id` | `0` | `c` | `category_id` |
| `sqlite_autoindex_news_1` | `1` | `u` | `slug` |

Constraints: unique index/constraint present, foreign key constraint present

### news_categories

- Purpose: News category taxonomy.
- Row count at inspection time: `5`
- Used by: news_repository.py, public_repository.py
- Related modules: `content`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `slug` | `TEXT` | No | `` | URL-friendly unique identifier. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_news_categories_2` | `1` | `u` | `slug` |
| `sqlite_autoindex_news_categories_1` | `1` | `u` | `name` |

Constraints: unique index/constraint present

### news_tags

- Purpose: Many-to-many link between news and tags.
- Row count at inspection time: `3`
- Used by: No direct repository reference found; verify app routes/services.
- Related modules: `content`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `news_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `tag_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |

Primary Key: `news_id, tag_id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `tag_id` | `tags.id` | `NO ACTION` | `CASCADE` |
| `news_id` | `news.id` | `NO ACTION` | `CASCADE` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_news_tags_1` | `1` | `pk` | `news_id, tag_id` |

Constraints: unique index/constraint present, foreign key constraint present, composite primary key

### newsletter_subscribers

- Purpose: Newsletter subscription list.
- Row count at inspection time: `1`
- Used by: cms_repository.py
- Related modules: `cms`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `email` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `status` | `TEXT` | No | `'subscribed'` | Workflow/classification value; preserve legacy vocabulary. |
| `subscribed_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `unsubscribed_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_newsletter_status` | `0` | `c` | `status` |
| `sqlite_autoindex_newsletter_subscribers_1` | `1` | `u` | `email` |

Constraints: unique index/constraint present

### notifications

- Purpose: Admin/system notification records.
- Row count at inspection time: `3`
- Used by: enterprise_repository.py
- Related modules: `system`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `recipient_type` | `TEXT` | No | `'admin'` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `recipient_id` | `INTEGER` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `title` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `message` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `level` | `TEXT` | No | `'info'` | Workflow/classification value; preserve legacy vocabulary. |
| `is_read` | `INTEGER` | No | `0` | Boolean stored as INTEGER 0/1. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `read_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_notifications_read` | `0` | `c` | `is_read, created_at` |

Constraints: None beyond column definitions

### page_visits

- Purpose: Page visit analytics events.
- Row count at inspection time: `134`
- Used by: dashboard_repository.py
- Related modules: `dashboard`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `path` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `remote_addr` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `user_agent` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `visited_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_page_visits_visited_at` | `0` | `c` | `visited_at` |

Constraints: None beyond column definitions

### password_reset_tokens

- Purpose: Password reset token lifecycle.
- Row count at inspection time: `2`
- Used by: auth_repository.py
- Related modules: `accounts`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `token` | `TEXT` | Yes | `` | Sensitive/auth token field; do not expose in API output. |
| `admin_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `email` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `expires_at` | `INTEGER` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `used_at` | `INTEGER` | Yes | `` | Timestamp stored in legacy SQLite format. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `token`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `admin_id` | `admin_users.id` | `NO ACTION` | `CASCADE` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_password_reset_tokens_admin` | `0` | `c` | `admin_id` |
| `sqlite_autoindex_password_reset_tokens_1` | `1` | `pk` | `token` |

Constraints: unique index/constraint present, foreign key constraint present

### product_categories

- Purpose: Product category taxonomy.
- Row count at inspection time: `8`
- Used by: categories_repository.py, products_repository.py
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `slug` | `TEXT` | No | `` | URL-friendly unique identifier. |
| `description` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_product_categories_2` | `1` | `u` | `slug` |
| `sqlite_autoindex_product_categories_1` | `1` | `u` | `name` |

Constraints: unique index/constraint present

### product_images

- Purpose: Product gallery images.
- Row count at inspection time: `3`
- Used by: products_repository.py
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `product_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `image_url` | `TEXT` | No | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `alt_text` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `product_id` | `products.id` | `NO ACTION` | `CASCADE` |

Indexes: `None`

Constraints: foreign key constraint present

### product_materials

- Purpose: Many-to-many link between products and materials.
- Row count at inspection time: `6`
- Used by: products_repository.py
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `product_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `material_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |

Primary Key: `product_id, material_id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `material_id` | `materials.id` | `NO ACTION` | `CASCADE` |
| `product_id` | `products.id` | `NO ACTION` | `CASCADE` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_product_materials_1` | `1` | `pk` | `product_id, material_id` |

Constraints: unique index/constraint present, foreign key constraint present, composite primary key

### product_processes

- Purpose: Many-to-many/process-step link between products and manufacturing processes.
- Row count at inspection time: `7`
- Used by: products_repository.py
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `product_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `process_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `step_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `note` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |

Primary Key: `product_id, process_id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `process_id` | `manufacturing_processes.id` | `NO ACTION` | `CASCADE` |
| `product_id` | `products.id` | `NO ACTION` | `CASCADE` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_product_processes_1` | `1` | `pk` | `product_id, process_id` |

Constraints: unique index/constraint present, foreign key constraint present, composite primary key

### product_specs

- Purpose: Product technical specifications.
- Row count at inspection time: `5`
- Used by: products_repository.py
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `product_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `spec_name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `spec_value` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `unit` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `product_id` | `products.id` | `NO ACTION` | `CASCADE` |

Indexes: `None`

Constraints: foreign key constraint present

### products

- Purpose: Main product catalog and SEO/media metadata.
- Row count at inspection time: `11`
- Used by: dashboard_repository.py, products_repository.py
- Related modules: `catalog`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `category_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `slug` | `TEXT` | No | `` | URL-friendly unique identifier. |
| `short_description` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `description` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `main_image` | `TEXT` | No | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `is_featured` | `INTEGER` | No | `0` | Boolean stored as INTEGER 0/1. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `updated_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `thumbnail_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `gallery_urls` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `tags_text` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `seo_title` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `seo_description` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `related_product_ids` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `sort_order` | `INTEGER` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `status` | `TEXT` | No | `'published'` | Workflow/classification value; preserve legacy vocabulary. |
| `sku` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `price` | `REAL` | No | `0` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `pdf_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `video_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `seo_keywords` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `canonical_url` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `og_image` | `TEXT` | Yes | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `robots` | `TEXT` | No | `'index,follow'` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `schema_json` | `TEXT` | Yes | `` | Serialized JSON/text payload; validate format before typed mapping. |
| `published_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `category_id` | `product_categories.id` | `NO ACTION` | `NO ACTION` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_products_slug` | `0` | `c` | `slug` |
| `idx_products_category_id` | `0` | `c` | `category_id` |
| `sqlite_autoindex_products_1` | `1` | `u` | `slug` |

Constraints: unique index/constraint present, foreign key constraint present

### quote_files

- Purpose: Files attached to quotation requests.
- Row count at inspection time: `1`
- Used by: cms_repository.py
- Related modules: `sales`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `quote_request_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `file_name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `file_url` | `TEXT` | No | `` | Media/path/URL value; keep text mapping before media storage migration. |
| `file_type` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `uploaded_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `quote_request_id` | `quote_requests.id` | `NO ACTION` | `CASCADE` |

Indexes: `None`

Constraints: foreign key constraint present

### quote_request_items

- Purpose: Quotation request line items.
- Row count at inspection time: `1`
- Used by: cms_repository.py
- Related modules: `sales`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `quote_request_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `product_id` | `INTEGER` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `drawing_code` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `material_id` | `INTEGER` | Yes | `` | Foreign key/reference column; preserve relationship. |
| `quantity` | `INTEGER` | No | `1` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `tolerance` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `note` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `material_id` | `materials.id` | `NO ACTION` | `NO ACTION` |
| `product_id` | `products.id` | `NO ACTION` | `NO ACTION` |
| `quote_request_id` | `quote_requests.id` | `NO ACTION` | `CASCADE` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_quote_items_quote_request_id` | `0` | `c` | `quote_request_id` |

Constraints: foreign key constraint present

### quote_requests

- Purpose: Quotation request header/workflow.
- Row count at inspection time: `1`
- Used by: cms_repository.py, dashboard_repository.py
- Related modules: `sales`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `customer_id` | `INTEGER` | No | `` | Foreign key/reference column; preserve relationship. |
| `project_name` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `message` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `status` | `TEXT` | No | `'new'` | Workflow/classification value; preserve legacy vocabulary. |
| `created_at` | `TEXT` | No | `CURRENT_TIMESTAMP` | Timestamp stored in legacy SQLite format. |
| `assigned_to` | `INTEGER` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `internal_note` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `quoted_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |
| `completed_at` | `TEXT` | Yes | `` | Timestamp stored in legacy SQLite format. |

Primary Key: `id`

Foreign Keys:

| Column | References | On Update | On Delete |
|---|---|---|---|
| `customer_id` | `customers.id` | `NO ACTION` | `NO ACTION` |

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `idx_quote_requests_customer_id` | `0` | `c` | `customer_id` |

Constraints: foreign key constraint present

### system_settings

- Purpose: Key/value system settings.
- Row count at inspection time: `4`
- Used by: settings_repository.py
- Related modules: `system`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `setting_key` | `TEXT` | Yes | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `setting_value` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |

Primary Key: `setting_key`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_system_settings_1` | `1` | `pk` | `setting_key` |

Constraints: unique index/constraint present

### tags

- Purpose: Shared content tag taxonomy.
- Row count at inspection time: `3`
- Used by: news_repository.py, products_repository.py
- Related modules: `content`

Columns:

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | Yes | `` | Integer primary key; preserve existing value. |
| `name` | `TEXT` | No | `` | Legacy field; preserve name/type during unmanaged ORM mapping. |
| `slug` | `TEXT` | No | `` | URL-friendly unique identifier. |

Primary Key: `id`

Foreign Keys: `None`

Indexes:

| Index | Unique | Origin | Columns |
|---|---|---|---|
| `sqlite_autoindex_tags_2` | `1` | `u` | `slug` |
| `sqlite_autoindex_tags_1` | `1` | `u` | `name` |

Constraints: unique index/constraint present

## 4. Views

### product_overview

Purpose: read-only convenience view. Do not map as a primary Django model until reviewed.

```sql
CREATE VIEW product_overview AS
            SELECT
              products.id,
              products.category_id,
              products.name,
              products.slug,
              product_categories.name AS category_name,
              products.short_description,
              products.main_image,
              products.is_featured,
              products.sku,
              products.price,
              products.thumbnail_url,
              products.gallery_urls,
              products.pdf_url,
              products.video_url,
              products.tags_text,
              products.seo_title,
              products.seo_description,
              products.seo_keywords,
              products.canonical_url,
              products.og_image,
              products.robots,
              products.schema_json,
              products.related_product_ids,
              products.sort_order,
              products.status,
              products.published_at
            FROM products
            JOIN product_categories ON product_categories.id = products.category_id
```

## 5. Phase 3 Rules

- Preserve existing primary keys during first ORM mapping.
- Use unmanaged Django models first: `managed = False`.
- Do not run `makemigrations` or `migrate` in this phase.
- Keep media/file path fields as text until media storage migration is approved.
- Auth/session/password tables require separate security review before cutover.
- Quote/contact write flows require transaction parity tests before any Django write endpoint.
