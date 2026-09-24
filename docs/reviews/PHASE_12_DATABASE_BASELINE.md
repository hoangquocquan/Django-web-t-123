# Phase 12 Database Baseline

## Database Engine

Current legacy database:

| Item | Value |
| --- | --- |
| Engine | SQLite |
| File | `backend/database/mecprecision.sqlite` |
| Size | 544768 bytes |
| Django legacy access | read-only URI mode |
| Archive status | `DATABASE_ARCHIVE_COMPLETE` |

## Tables

Current inventory contains 39 application tables:

| Group | Tables |
| --- | --- |
| Auth/Admin | `admin_users`, `admin_sessions`, `admin_activity_logs`, `login_attempts`, `password_reset_tokens`, `admin_2fa_challenges`, `auth_email_outbox` |
| Catalog | `product_categories`, `products`, `product_images`, `product_specs`, `materials`, `machines`, `manufacturing_processes`, `product_materials`, `product_processes`, `capabilities`, `capability_machines` |
| CRM | `customers`, `customer_notes`, `contact_requests`, `newsletter_subscribers`, `page_visits` |
| Sales | `quote_requests`, `quote_request_items`, `quote_files` |
| CMS | `cms_pages`, `cms_menu_items`, `cms_banners`, `news_categories`, `news`, `tags`, `news_tags`, `system_settings` |
| AI/System | `ai_conversations`, `ai_translation_cache`, `enterprise_events`, `job_queue`, `notifications` |

## Indexes

Current inventory contains 19 named indexes, including:

- `idx_products_category_id`
- `idx_products_slug`
- `idx_news_category_id`
- `idx_quote_requests_customer_id`
- `idx_quote_items_quote_request_id`
- `idx_admin_sessions_expires_at`
- `idx_password_reset_tokens_admin`
- `idx_ai_translation_cache_lookup`
- `idx_job_queue_status`

## Relationships

Important relationships documented in earlier mapping phases:

- category -> products
- customer -> quote requests
- quote request -> quote items
- quote request -> quote files
- news category -> news
- news -> tags through `news_tags`
- products -> materials through `product_materials`
- products -> manufacturing processes through `product_processes`

## Migration Status

The Django ORM currently uses unmanaged/read-only model patterns for migrated
domains. Database ownership migration has been planned and tested through prior
phases, but this Phase 12 audit does not create migrations or change schema.

## Backup Status

Earlier backup scripts exist under `scripts/`. Phase 11.2 created a new archive
workflow with checksum and integrity verification.

## Archive Status

| Check | Result |
| --- | --- |
| Backup exists | `True` |
| Metadata exists | `True` |
| Checksum valid | `True` |
| Archive readable | `True` |
| SQLite integrity | `ok` |
| Verification status | `ARCHIVE_VERIFIED` |
| Final status | `DATABASE_ARCHIVE_COMPLETE` |

## Database Baseline Decision

The legacy SQLite database remains intact. Archive metadata and verification
records are complete. No database schema or production data was modified in
Phase 12.
