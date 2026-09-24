# Database Migration Strategy - mecprecision-vietnam

Phase: 1 - Migration Planning  
Rule: Planning only. No code, no Django models, no database migration.

## 1. Purpose

This document defines how the current SQLite database should be analyzed, mapped, validated, backed up, and eventually migrated into Django ORM safely.

Important:

- Do not run Django migrations against the legacy database yet.
- Do not create Django models in this phase.
- Do not modify `backend/database/mecprecision.sqlite`.
- Do not rename tables or fields.
- Do not change business data.

## 2. Current SQLite Analysis

### 2.1 Current Database Engine

Current engine:

```text
SQLite
```

Current database file:

```text
backend/database/mecprecision.sqlite
```

Schema source:

```text
backend/database/schema.sql
```

Seed data:

```text
backend/database/seed.sql
```

Compatibility migrations:

```text
backend/database/migrations.py
```

Connection helper:

```text
backend/database/connection.py
```

### 2.2 Current Connection Behavior

The legacy database layer:

- Opens SQLite connections per operation.
- Enables foreign keys with `PRAGMA foreign_keys = ON`.
- Uses `sqlite3.Row` to access columns by name.
- Provides helper functions:
  - `query_all`
  - `query_one`
  - `execute_write`
  - `transaction`

Transaction support exists for multi-step writes, for example quote creation.

### 2.3 Current Table Groups

| Group | Tables |
|---|---|
| Authentication | `admin_users`, `admin_sessions`, `login_attempts`, `password_reset_tokens`, `admin_2fa_challenges`, `auth_email_outbox` |
| Audit | `admin_activity_logs` |
| Catalog | `product_categories`, `products`, `product_images`, `product_specs`, `materials`, `machines`, `manufacturing_processes`, `product_materials`, `product_processes`, `capabilities`, `capability_machines` |
| CRM | `customers`, `customer_notes`, `contact_requests` |
| Sales | `quote_requests`, `quote_request_items`, `quote_files` |
| Content | `news_categories`, `news`, `tags`, `news_tags` |
| CMS | `cms_pages`, `cms_menu_items`, `cms_banners`, `newsletter_subscribers` |
| Analytics | `page_visits` |
| Enterprise/System | `enterprise_events`, `job_queue`, `notifications`, `system_settings` |
| AI | `ai_conversations`, `ai_translation_cache` |

### 2.4 Current Indexes

Existing indexes cover common lookup paths:

- product category/slug
- news category
- quote/customer relations
- quote item parent
- admin sessions expiry
- login attempt lookup
- password reset lookup
- activity logs by created time
- page visits by visit time
- event/job/notification lookup
- AI conversation/cache lookup

These indexes must be preserved during any future migration.

### 2.5 Current View

Existing view:

```text
product_overview
```

Django ORM should not rely on this view initially unless a read-only unmanaged model is explicitly approved.

## 3. SQLite-Specific Risks

| Risk | Severity | Explanation | Mitigation |
|---|---:|---|---|
| Write locking | Medium | SQLite allows limited concurrent writes. | Keep writes on legacy until migration is stable; consider PostgreSQL later. |
| TEXT timestamps | Medium | Several timestamp columns are stored as `TEXT`. | Document exact format and map carefully to `DateTimeField` only after testing. |
| Integer booleans | Low/Medium | Booleans are stored as `0/1`. | Map carefully to `BooleanField` in Django unmanaged models. |
| Composite keys | Medium | Tables like `news_tags` use composite keys. | Use explicit through models or unmanaged models; avoid assumptions. |
| Manual migrations | Medium | `migrations.py` can alter existing DB state. | Freeze actual current schema before Django mapping. |
| File paths in DB | Medium | Products/news/banners/users may reference local upload paths. | Keep as text fields initially; migrate storage later. |
| Raw SQL behavior | Medium | Existing queries may not map 1:1 to Django ORM. | Compare legacy SQL output with Django ORM output. |

## 4. Django ORM Migration Approach

### 4.1 Stage 1 - Schema Inventory

Before creating models, produce:

```text
DATABASE_MAPPING.md
```

For every table:

- table name
- column name
- SQLite type
- nullable or not
- default value
- primary key
- unique constraints
- foreign keys
- indexes
- proposed Django model name
- proposed Django field type
- relationship mapping
- risk level

### 4.2 Stage 2 - Unmanaged Read-Only Models

Initial Django ORM models should use:

```text
managed = False
```

Reason:

- Django can read existing tables.
- Django will not create, alter, or drop legacy tables.
- Rollback is easy: remove/disable Django code only.

Rules:

- No `makemigrations` for legacy tables.
- No `migrate` against legacy data.
- No schema changes.
- No field renaming.
- Use `db_table` explicitly.
- Use `db_column` explicitly when helpful.
- Avoid model-level assumptions that differ from SQLite schema.

### 4.3 Stage 3 - Read Parity Tests

For each unmanaged model:

1. Read sample rows using legacy repository.
2. Read same rows using Django ORM.
3. Compare IDs, key fields, status, relationships.
4. Verify count parity.
5. Verify ordering parity where API depends on ordering.

Examples:

| Legacy read | Django read |
|---|---|
| `products_repository.list_products()` | `Product.objects...` |
| `public_repository.list_news()` | `NewsArticle.objects...` |
| `contacts_repository.list_recent_contacts()` | `ContactRequest.objects...` |

### 4.4 Stage 4 - Read APIs

After read models are validated:

- Add DRF serializers.
- Add read-only API views.
- Keep endpoints under parallel namespace first.
- Compare responses with legacy APIs.

No write APIs in this stage.

### 4.5 Stage 5 - Controlled Write APIs

Only after read parity:

- Move low-risk write APIs.
- Use `transaction.atomic()`.
- Match legacy validation.
- Match legacy error response.
- Match legacy side effects:
  - cache clear
  - event publish
  - queue jobs
  - notifications
  - audit logs

### 4.6 Stage 6 - Managed Django Migrations

Do not enable managed migrations for legacy tables until:

- all models are mapped,
- all data is validated,
- Django read/write parity is proven,
- backup/restore is tested,
- stakeholder approves database ownership transfer.

Possible future options:

Option A: Keep existing SQLite schema and unmanaged models long-term.

Pros:

- Lowest risk.
- Fastest rollback.
- Legacy can coexist.

Cons:

- Less benefit from Django migrations.
- Schema evolution remains manual.

Option B: Convert SQLite schema to Django-managed migrations.

Pros:

- Django owns schema.
- Easier future evolution.

Cons:

- High risk.
- Requires careful fake initial migrations.

Option C: Move from SQLite to PostgreSQL.

Pros:

- Better concurrency and production readiness.
- Stronger type handling.

Cons:

- Highest migration complexity.
- Requires data export/import validation.
- Requires deployment changes.

Recommendation:

Start with Option A. Revisit Option B or C only after full ORM/API parity.

## 5. Data Migration Plan

### 5.1 Current Phase

No data migration.

Allowed:

- Read schema.
- Read data counts.
- Create documentation.

Not allowed:

- `migrate`
- `makemigrations` for legacy models
- schema changes
- data rewrites

### 5.2 Future Read-Only Mapping Phase

Steps:

1. Back up database.
2. Inspect actual database with SQLite introspection.
3. Generate `DATABASE_MAPPING.md`.
4. Create unmanaged models after review.
5. Run Django read-only tests.
6. Compare legacy vs Django output.

### 5.3 Future Write Migration Phase

For each write module:

1. Back up database.
2. Identify write tables.
3. Identify side effects.
4. Add transaction tests.
5. Add validation tests.
6. Add API contract tests.
7. Enable write route in staging only.
8. Compare output and side effects.
9. Enable production route gradually.

### 5.4 Future Database Engine Migration Phase

If moving from SQLite to PostgreSQL later:

1. Freeze writes.
2. Back up SQLite.
3. Export tables in dependency order.
4. Import into PostgreSQL.
5. Validate row counts.
6. Validate foreign key integrity.
7. Validate critical API outputs.
8. Run full test suite.
9. Run staging cutover.
10. Keep SQLite backup for rollback.

## 6. Backup Strategy

### 6.1 Before Any Database Operation

Always back up:

```text
backend/database/mecprecision.sqlite
```

Recommended backup path:

```text
backups/mecprecision_YYYYMMDD_HHMMSS.sqlite
```

### 6.2 Backup Validation

Backup is not valid until:

1. File exists.
2. File size is greater than zero.
3. SQLite can open it.
4. `PRAGMA integrity_check` returns `ok`.
5. Critical table counts match source.

Critical table counts:

- `admin_users`
- `products`
- `product_categories`
- `customers`
- `contact_requests`
- `quote_requests`
- `news`
- `cms_pages`
- `ai_conversations`

### 6.3 Backup Frequency During Migration

Recommended:

- Before each migration phase.
- Before each module write migration.
- Before any schema change.
- Before production route switch.
- After successful production cutover.

### 6.4 Rollback From Backup

Rollback steps:

1. Stop Django write route.
2. Stop legacy backend if database file replacement is required.
3. Copy backup over active SQLite file.
4. Start legacy backend.
5. Run health check.
6. Run critical read APIs.
7. Verify admin login.

## 7. Validation Strategy

### 7.1 Schema Validation

Validate:

- all expected tables exist,
- columns match `schema.sql`,
- foreign keys exist,
- indexes exist,
- view exists,
- default values match,
- nullable settings match.

### 7.2 Data Validation

For each table:

- row count,
- primary key min/max,
- null count for required fields,
- duplicate check for unique fields,
- orphan foreign key check,
- invalid status value check.

Example status fields:

- `products.status`
- `news.status`
- `quote_requests.status`
- `contact_requests.status`
- `cms_pages.status`
- `cms_banners.status`
- `job_queue.status`
- `notifications.is_read`

### 7.3 Relationship Validation

Validate relationships:

- products have valid categories,
- product images/specs reference valid products,
- quote requests reference valid customers,
- quote items reference valid quote requests,
- quote item products/materials are valid when present,
- news reference valid categories,
- news tags reference valid news and tags,
- admin sessions reference valid admin users,
- customer notes reference valid customers.

### 7.4 API Parity Validation

For each migrated read API:

1. Call legacy API.
2. Call Django API.
3. Normalize response ordering if needed.
4. Compare required fields.
5. Compare status code.
6. Compare error cases.

Critical APIs:

- `/api/home`
- `/api/products`
- `/api/products/{id}`
- `/api/product-categories`
- `/api/capabilities`
- `/api/news`

### 7.5 Write Validation

For each migrated write:

- success path,
- validation error,
- duplicate/constraint error,
- transaction rollback,
- side effect creation,
- audit log,
- cache invalidation.

Critical write APIs:

- `/api/contact`
- `/api/quote-request`
- `/api/products`
- admin CMS writes.

### 7.6 Security Validation

Validate:

- auth required for admin writes,
- CSRF on admin forms,
- permission matrix,
- file upload path safety,
- sensitive data not leaked in API,
- debug disabled in production,
- AI cannot execute privileged actions.

## 8. Django Database Configuration Strategy

### 8.1 Initial Django Foundation

Use placeholder database config:

```text
DATABASE_URL if provided
fallback: BASE_DIR / "db.sqlite3"
```

Do not point Django migrations to legacy SQLite until mapping is approved.

### 8.2 Read-Only Mapping Stage

Options:

Option A: Django reads legacy SQLite directly.

Pros:

- Real data parity.
- No export/import required.

Cons:

- Must avoid migrations.
- Must handle SQLite timestamp/boolean quirks.

Option B: Copy legacy SQLite to a test/staging file.

Pros:

- Safer for model development.

Cons:

- Data may drift from production.

Recommendation:

- Develop against a copied SQLite file first.
- Only read production SQLite after validation.

### 8.3 Migration Ownership Decision

Do not let Django own legacy schema until a formal decision is made.

Decision checklist:

- Are all modules migrated?
- Are all write paths in Django?
- Is legacy backend retired?
- Are backups tested?
- Is PostgreSQL needed?
- Is downtime acceptable?

## 9. Rollback Strategy

### 9.1 Read-Only ORM Rollback

If a read-only model is wrong:

- Disable Django route.
- Fix mapping.
- No database restore needed because data was not changed.

### 9.2 Write API Rollback

If Django write API is wrong:

- Disable Django write route.
- Restore legacy route.
- Compare database state.
- Restore from backup only if incorrect data was written.

### 9.3 Schema Migration Rollback

Schema changes should not occur until late phase.

If schema migration fails:

- Stop app.
- Restore database backup.
- Re-run validation.
- Keep legacy backend as source of truth.

## 10. Exit Criteria Before Creating Django Models

Before Phase 4 models:

- `DATABASE_MAPPING.md` is complete.
- Model names and app locations are reviewed.
- All FK relationships are confirmed.
- Composite/M2M strategy is reviewed.
- Timestamp/boolean mapping strategy is reviewed.
- Backups are tested.
- Legacy tests pass.

## 11. Conclusion

The safest database path is:

1. Analyze and document schema.
2. Create formal database mapping.
3. Use unmanaged read-only Django models.
4. Validate output against legacy repositories.
5. Add read-only APIs.
6. Move writes only after parity tests.
7. Decide later whether Django should own migrations or whether PostgreSQL is required.

No database migration should be performed in Phase 1.

## 12. Phase 1 Review Update - Current Database Summary

Current database:

```text
SQLite
```

Current database file:

```text
backend/database/mecprecision.sqlite
```

Current schema source:

```text
backend/database/schema.sql
```

Current relationship style:

- Primary keys are mostly integer IDs.
- Foreign keys connect products, catalog metadata, CRM, quotation, news, CMS, users, sessions, and system data.
- Some many-to-many relationships are represented by join tables such as `product_materials`, `product_processes`, `capability_machines`, and `news_tags`.
- File/media references are mostly stored as text paths or URLs, not formal media foreign keys.

Current table groups that must be mapped before Django ownership:

| Group | Tables |
|---|---|
| Auth/Security | `admin_users`, `admin_sessions`, `login_attempts`, `password_reset_tokens`, `admin_2fa_challenges`, `auth_email_outbox`, `admin_activity_logs` |
| Catalog | `product_categories`, `products`, `product_images`, `product_specs`, `materials`, `machines`, `manufacturing_processes`, `product_materials`, `product_processes`, `capabilities`, `capability_machines` |
| CRM | `customers`, `customer_notes`, `contact_requests` |
| Sales | `quote_requests`, `quote_request_items`, `quote_files` |
| Content/CMS | `news_categories`, `news`, `tags`, `news_tags`, `cms_pages`, `cms_menu_items`, `cms_banners`, `newsletter_subscribers` |
| Analytics/System | `page_visits`, `enterprise_events`, `job_queue`, `notifications`, `system_settings` |
| AI | `ai_conversations`, `ai_translation_cache` |

## 13. Phase 1 Review Update - Migration Approach

Recommended migration flow:

```text
Legacy database
  -> Django ORM models
  -> Data validation
  -> Cutover
```

Detailed meaning:

1. Legacy database remains the source of truth first.
2. Django ORM models are created later as unmanaged, read-only mappings.
3. Data validation compares legacy SQL/repository output with Django ORM output.
4. Cutover happens only after parity is proven and rollback is tested.

No production database migration should happen directly.

## 14. Phase 1 Review Update - Database Migration Rules

Mandatory rules:

- No production migration directly.
- Backup before migration.
- Migration scripts must be reversible.
- Data validation is required before and after migration.
- Do not run Django migrations against the legacy SQLite file until approved.
- Do not rename legacy tables or fields during the first ORM mapping.
- Use read-only/unmanaged models first.
- Use write APIs only after transaction and rollback behavior is tested.

## 15. Phase 1 Review Update - Table Mapping Strategy

Each legacy table must be documented in a future `DATABASE_MAPPING.md`.

Required mapping columns:

| Mapping Field | Meaning |
|---|---|
| Legacy table | Exact SQLite table name |
| Django app | Proposed Django app/module |
| Django model | Proposed model class name |
| Managed mode | `managed = False` first, unless explicitly approved |
| Primary key | Existing PK column and Django equivalent |
| Foreign keys | Existing FK relationships |
| Indexes | Existing indexes that must be preserved |
| Status values | Draft/published/archived/workflow values |
| Timestamp format | TEXT/date/datetime mapping rule |
| Boolean format | Integer 0/1 mapping rule |
| Risk | Low, medium, high |

Example mapping intent:

| Legacy table | Proposed Django area | First strategy |
|---|---|---|
| `product_categories` | Catalog | Unmanaged read-only model |
| `products` | Catalog | Unmanaged read-only model |
| `contact_requests` | CRM | Unmanaged read-only model, write later |
| `quote_requests` | Sales | Unmanaged read-only model, write much later |
| `admin_users` | Security | Read-only mapping before auth cutover |
| `cms_pages` | Content/CMS | Unmanaged read-only model |
| `ai_conversations` | AI | Read-only or append-only after AI strategy review |

## 16. Phase 1 Review Update - Primary Key Strategy

Initial rule:

- Preserve existing primary key values.
- Do not regenerate IDs.
- Do not change integer IDs to UUIDs during early migration.
- Do not merge or split rows during first mapping.

Reason:

- Existing foreign keys depend on current IDs.
- Existing uploaded file paths or admin screens may reference IDs.
- Keeping IDs stable makes legacy-vs-Django validation easier.

If PostgreSQL migration happens later:

- Import records with original IDs.
- Reset database sequences after import.
- Validate max ID and next generated ID.

## 17. Phase 1 Review Update - Foreign Key Strategy

Initial rule:

- Document every FK relationship before creating models.
- Keep nullable/optional relationship behavior identical to SQLite.
- Use explicit `db_column` when needed.
- Use explicit through models for many-to-many join tables.

High-priority FK checks:

| Relationship | Risk |
|---|---|
| `products.category_id -> product_categories.id` | Product listing/detail can break |
| `product_images.product_id -> products.id` | Gallery can break |
| `quote_request_items.quote_request_id -> quote_requests.id` | Quote detail can break |
| `quote_request_items.product_id -> products.id` | Quote/product relationship can break |
| `customer_notes.customer_id -> customers.id` | CRM history can break |
| `admin_sessions.user_id -> admin_users.id` | Admin login/session can break |
| `news.category_id -> news_categories.id` | News filtering can break |
| `cms_menu_items.parent_id -> cms_menu_items.id` | Nested menu can break |

## 18. Phase 1 Review Update - Index Strategy

Initial rule:

- Preserve current indexes.
- Document index purpose before recreating it in Django.
- Do not remove or rename indexes during early migration.

Index categories to validate:

- Slug lookups.
- Category filters.
- Status filters.
- Created/published date ordering.
- Session token lookups.
- Password reset token lookups.
- Contact/quote dashboard filters.
- AI cache lookup.

Future Django models should include matching index definitions only after schema mapping is reviewed.

## 19. Phase 1 Review Update - Migration Testing Strategy

Migration testing must include:

1. Schema validation.
2. Row count validation.
3. Primary key validation.
4. Foreign key validation.
5. Index presence validation.
6. API response parity.
7. Transaction rollback validation for write flows.
8. Backup restore validation.

Required validation examples:

| Validation | Example |
|---|---|
| Row count | Legacy `products` count equals Django ORM product count |
| Relationship | Every `product_images.product_id` resolves to a product |
| API parity | Legacy `/api/products` response matches Django `/api/v1/products` required fields |
| Transaction | Failed quote creation rolls back quote, items, and files |
| Backup | Restored SQLite backup opens and passes count checks |

## 20. Phase 1 Review Update - Cutover Readiness

Database cutover cannot start until:

- `DATABASE_MAPPING.md` is reviewed.
- Unmanaged read-only models pass parity tests.
- Backup and restore procedure is tested.
- Write transaction strategy is tested.
- API compatibility strategy is approved.
- Security review is complete for admin/auth-related tables.
