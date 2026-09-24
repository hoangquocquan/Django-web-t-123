# Legacy To Django ORM Mapping Strategy

Phase: 3 - Database Mapping / Legacy Schema Analysis  
Rule: Strategy only. No Django models or migrations are created.

## 1. Global Mapping Rules

- First Django ORM mapping must be read-only and unmanaged: `managed = False`.
- Use explicit `db_table` for every legacy table.
- Preserve legacy primary key values.
- Preserve legacy field names initially unless an adapter layer explicitly maps names.
- Composite link tables should become explicit through models.
- Keep SQLite TEXT timestamps as carefully validated datetime/text mappings in the first pass.
- Keep INTEGER booleans compatible with `0/1`.
- Do not point Django migrations at the legacy database until architecture review approves it.

## 2. Table Mapping Matrix

### admin_2fa_challenges

Legacy Table: `admin_2fa_challenges`

->

Django App: `accounts`

->

Django Model Name: `AdminTwoFactorChallenge`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `challenge_id`.
- Map foreign keys after referenced table model is approved.
- Do not migrate auth behavior in ORM mapping phase; security review required.
- Purpose: Two-factor authentication challenge codes.

### admin_activity_logs

Legacy Table: `admin_activity_logs`

->

Django App: `accounts`

->

Django Model Name: `AdminActivityLog`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Do not migrate auth behavior in ORM mapping phase; security review required.
- Purpose: Admin audit log for sensitive CMS actions.

### admin_sessions

Legacy Table: `admin_sessions`

->

Django App: `accounts`

->

Django Model Name: `AdminSession`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `session_id`.
- Map foreign keys after referenced table model is approved.
- Do not migrate auth behavior in ORM mapping phase; security review required.
- Purpose: Admin login sessions and multi-device tracking.

### admin_users

Legacy Table: `admin_users`

->

Django App: `accounts`

->

Django Model Name: `AdminUser`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Keep media/path fields as text until media storage migration.
- Do not migrate auth behavior in ORM mapping phase; security review required.
- Purpose: Admin user accounts for CMS login and role checks.

### ai_conversations

Legacy Table: `ai_conversations`

->

Django App: `ai`

->

Django Model Name: `AiConversation`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: AI chatbot/conversation history.

### ai_translation_cache

Legacy Table: `ai_translation_cache`

->

Django App: `ai`

->

Django Model Name: `AiTranslationCache`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: AI translation cache/history.

### auth_email_outbox

Legacy Table: `auth_email_outbox`

->

Django App: `accounts`

->

Django Model Name: `AuthEmailOutbox`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Do not migrate auth behavior in ORM mapping phase; security review required.
- Purpose: Authentication-related email outbox.

### capabilities

Legacy Table: `capabilities`

->

Django App: `catalog`

->

Django Model Name: `Capability`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Manufacturing capability cards/content.

### capability_machines

Legacy Table: `capability_machines`

->

Django App: `catalog`

->

Django Model Name: `CapabilityMachine`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Composite primary key/link table; model as explicit through table and review Django limitation around composite PKs.
- Map foreign keys after referenced table model is approved.
- Purpose: Many-to-many link between capabilities and machines.

### cms_banners

Legacy Table: `cms_banners`

->

Django App: `cms`

->

Django Model Name: `CmsBanner`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Keep media/path fields as text until media storage migration.
- Purpose: Homepage/banner/advertisement placements.

### cms_menu_items

Legacy Table: `cms_menu_items`

->

Django App: `cms`

->

Django Model Name: `CmsMenuItem`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Purpose: Header/footer/sidebar menu items with nesting.

### cms_pages

Legacy Table: `cms_pages`

->

Django App: `cms`

->

Django Model Name: `CmsPage`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Dynamic CMS pages.

### contact_requests

Legacy Table: `contact_requests`

->

Django App: `crm`

->

Django Model Name: `ContactRequest`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Keep media/path fields as text until media storage migration.
- Purpose: Public contact form submissions and admin handling status.

### customer_notes

Legacy Table: `customer_notes`

->

Django App: `crm`

->

Django Model Name: `CustomerNote`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Purpose: Internal notes for customer history.

### customers

Legacy Table: `customers`

->

Django App: `crm`

->

Django Model Name: `Customer`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Customer/company master data.

### enterprise_events

Legacy Table: `enterprise_events`

->

Django App: `system`

->

Django Model Name: `EnterpriseEvent`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Domain event log for workflow side effects.

### job_queue

Legacy Table: `job_queue`

->

Django App: `system`

->

Django Model Name: `JobQueueItem`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: SQLite-backed background job queue.

### login_attempts

Legacy Table: `login_attempts`

->

Django App: `accounts`

->

Django Model Name: `LoginAttempt`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Do not migrate auth behavior in ORM mapping phase; security review required.
- Purpose: Login attempt audit and lockout support.

### machines

Legacy Table: `machines`

->

Django App: `catalog`

->

Django Model Name: `Machine`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Machine/capability reference data.

### manufacturing_processes

Legacy Table: `manufacturing_processes`

->

Django App: `catalog`

->

Django Model Name: `ManufacturingProcess`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Manufacturing process reference data.

### materials

Legacy Table: `materials`

->

Django App: `catalog`

->

Django Model Name: `Material`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Manufacturing material reference data.

### news

Legacy Table: `news`

->

Django App: `content`

->

Django Model Name: `NewsArticle`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Keep media/path fields as text until media storage migration.
- Purpose: News/article content with SEO and publishing metadata.

### news_categories

Legacy Table: `news_categories`

->

Django App: `content`

->

Django Model Name: `NewsCategory`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: News category taxonomy.

### news_tags

Legacy Table: `news_tags`

->

Django App: `content`

->

Django Model Name: `NewsTag`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Composite primary key/link table; model as explicit through table and review Django limitation around composite PKs.
- Map foreign keys after referenced table model is approved.
- Purpose: Many-to-many link between news and tags.

### newsletter_subscribers

Legacy Table: `newsletter_subscribers`

->

Django App: `cms`

->

Django Model Name: `NewsletterSubscriber`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Newsletter subscription list.

### notifications

Legacy Table: `notifications`

->

Django App: `system`

->

Django Model Name: `Notification`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Admin/system notification records.

### page_visits

Legacy Table: `page_visits`

->

Django App: `dashboard`

->

Django Model Name: `PageVisit`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Page visit analytics events.

### password_reset_tokens

Legacy Table: `password_reset_tokens`

->

Django App: `accounts`

->

Django Model Name: `PasswordResetToken`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `token`.
- Map foreign keys after referenced table model is approved.
- Do not migrate auth behavior in ORM mapping phase; security review required.
- Purpose: Password reset token lifecycle.

### product_categories

Legacy Table: `product_categories`

->

Django App: `catalog`

->

Django Model Name: `ProductCategory`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Product category taxonomy.

### product_images

Legacy Table: `product_images`

->

Django App: `catalog`

->

Django Model Name: `ProductImage`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Keep media/path fields as text until media storage migration.
- Purpose: Product gallery images.

### product_materials

Legacy Table: `product_materials`

->

Django App: `catalog`

->

Django Model Name: `ProductMaterial`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Composite primary key/link table; model as explicit through table and review Django limitation around composite PKs.
- Map foreign keys after referenced table model is approved.
- Purpose: Many-to-many link between products and materials.

### product_processes

Legacy Table: `product_processes`

->

Django App: `catalog`

->

Django Model Name: `ProductProcess`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Composite primary key/link table; model as explicit through table and review Django limitation around composite PKs.
- Map foreign keys after referenced table model is approved.
- Purpose: Many-to-many/process-step link between products and manufacturing processes.

### product_specs

Legacy Table: `product_specs`

->

Django App: `catalog`

->

Django Model Name: `ProductSpec`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Purpose: Product technical specifications.

### products

Legacy Table: `products`

->

Django App: `catalog`

->

Django Model Name: `Product`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Keep media/path fields as text until media storage migration.
- Purpose: Main product catalog and SEO/media metadata.

### quote_files

Legacy Table: `quote_files`

->

Django App: `sales`

->

Django Model Name: `QuoteFile`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Keep media/path fields as text until media storage migration.
- Write behavior requires transaction rollback tests before cutover.
- Purpose: Files attached to quotation requests.

### quote_request_items

Legacy Table: `quote_request_items`

->

Django App: `sales`

->

Django Model Name: `QuoteRequestItem`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Write behavior requires transaction rollback tests before cutover.
- Purpose: Quotation request line items.

### quote_requests

Legacy Table: `quote_requests`

->

Django App: `sales`

->

Django Model Name: `QuoteRequest`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Map foreign keys after referenced table model is approved.
- Write behavior requires transaction rollback tests before cutover.
- Purpose: Quotation request header/workflow.

### system_settings

Legacy Table: `system_settings`

->

Django App: `system`

->

Django Model Name: `SystemSetting`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `setting_key`.
- Purpose: Key/value system settings.

### tags

Legacy Table: `tags`

->

Django App: `content`

->

Django Model Name: `Tag`

->

Migration Notes:

- Use `managed = False` initially.
- Set `db_table` to legacy table name.
- Preserve primary key `id`.
- Purpose: Shared content tag taxonomy.

## 3. Module Notes

- `accounts`: Security/auth migration must remain late; map read-only first.
- `catalog`: Catalog should migrate before sales and AI. Use unmanaged models first.
- `crm`: CRM reads can migrate before sales writes. Public contact write needs validation/anti-spam.
- `sales`: High-risk transactional module. Requires transaction parity and rollback tests.
- `content`: Public content module. Preserve slug/status/publish behavior.
- `cms`: CMS content must stay separate from common utilities.
- `dashboard`: Analytics/dashboard should migrate after source modules are mapped.
- `system`: System/event/job tables are cross-cutting and should migrate after core data reads.
- `ai`: AI tables can be mapped after catalog/content/CRM context is available.

## 4. Do Not Implement Yet

- Do not create Django model files from this strategy until architecture review approves Phase 3.
- Do not create migrations.
- Do not run migrations.
- Do not change legacy repositories or APIs.

## 5. Phase 3.1 Hardening - Read-Only ORM Flow

Approved preparation flow for Phase 4:

```text
Legacy Database
  -> Unmanaged Django Models
  -> Validation
  -> Service Layer
  -> API Migration
```

Meaning:

1. Legacy SQLite remains the source of truth.
2. Django models read existing tables only.
3. Validation compares Django ORM output with legacy SQLite/repository output.
4. Service layer comes after model validation.
5. API migration comes after service/read parity.

No database ownership transfer happens in Phase 4.

## 6. Phase 3.1 Hardening - Ownership Rules

Phase 4 must use:

```python
class Meta:
    managed = False
    db_table = "legacy_table_name"
```

Phase 4 must not:

- run `makemigrations`,
- run `migrate`,
- create managed models for legacy tables,
- add columns,
- rename columns,
- add surrogate IDs,
- migrate files/media,
- migrate auth/session behavior.

## 7. Phase 3.1 Hardening - Supporting Rule Documents

Before implementing any Phase 4 model, check:

| Document | Purpose |
|---|---|
| `ORM_MODEL_CONVENTION.md` | Model naming, table mapping, field mapping, PK/FK rules |
| `COMPOSITE_KEY_STRATEGY.md` | Junction table and composite PK handling |
| `DATABASE_VIEW_STRATEGY.md` | Read-only view mapping rules |
| `MEDIA_MIGRATION_STRATEGY.md` | Media/path fields remain text |
| `AUTH_MIGRATION_BOUNDARY.md` | Auth tables remain read-only boundary |

## 8. Phase 3.1 Hardening - Recommended Phase 4 Slices

| Slice | Scope | Reason |
|---|---|---|
| 4A Catalog ORM | categories, materials, machines, processes, products, images, specs, capability links | Highest read-only value and needed by future APIs. |
| 4B CRM/Sales Read ORM | customers, contacts, quotes, quote items, quote files | Needed for business workflows, but writes remain later. |
| 4C Content ORM | news categories, news, tags, news_tags | Supports public content and SEO. |
| 4D CMS Read ORM | pages, menus, banners, newsletter | Admin read visibility only. |
| 4E System/Analytics Read ORM | visits, events, jobs, notifications, settings | Dashboard/supporting infrastructure. |
| 4F AI Read ORM | conversations, translation cache | AI history/cache read support only. |
| 4G Auth Read Boundary | users, sessions, reset, 2FA, audit | Conditional; security review required before behavior migration. |

## 9. Phase 3.1 Hardening - Validation Before API Migration

Every Phase 4 model must pass:

- row count parity,
- primary key parity,
- foreign key resolution,
- null/default behavior review,
- representative field comparison,
- no API response changes,
- no database writes.
