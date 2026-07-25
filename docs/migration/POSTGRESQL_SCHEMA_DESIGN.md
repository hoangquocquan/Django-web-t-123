# PostgreSQL Schema Design

## Phase

Phase 10.1 - PostgreSQL Schema Design

## Objective

Design the target PostgreSQL schema before any data migration or production
database cutover. This document is design-only and does not create Django
migrations.

## Naming Convention

| Item | Convention | Example |
|---|---|---|
| App labels | keep current Django app names | `catalog`, `crm`, `sales`, `cms`, `accounts` |
| Tables | keep legacy table names unless a future ADR approves rename | `products`, `quote_requests` |
| Primary keys | preserve existing IDs during import | `id` |
| Foreign keys | use explicit FK fields matching domain ownership | `product.category_id` |
| Index names | `idx_<table>_<columns>` | `idx_products_slug` |
| Unique constraints | `uq_<table>_<columns>` | `uq_products_slug` |

## Global Field Type Rules

| Legacy pattern | PostgreSQL/Django target |
|---|---|
| `TextField` identifiers such as slug/email/session/token | `CharField` with explicit max length where business length is known |
| long content/body fields | `TextField` |
| timestamps stored as text | keep as `DateTimeField` target after data parsing plan |
| integer timestamp fields | convert to `DateTimeField` only after auth/session migration review |
| booleans | `BooleanField` |
| money/price floats | use `DecimalField` in target schema |
| JSON-like text | `JSONField` after validation, otherwise `TextField` |

## Module Migration Order

1. Catalog reference data
2. CRM customer/contact data
3. Sales quotation data
4. CMS content/menu data
5. Accounts/auth data after security approval

## Catalog Target Schema

| Model | Table | Target PK | Foreign keys | Indexes | Constraints | Notes |
|---|---|---|---|---|---|---|
| `Category` | `product_categories` | `id` BigAutoField/preserved integer | none | `sort_order`, `slug` | unique `slug` | migrate before products |
| `Material` | `materials` | `id` | none | `name` | unique `name` | referenced by products and quotes |
| `Machine` | `machines` | `id` | none | `machine_type`, `status` | none initially | reference data |
| `ManufacturingProcess` | `manufacturing_processes` | `id` | none | `sort_order`, `name` | unique `name` | referenced by product process |
| `Capability` | `capabilities` | `id` | none | `sort_order` | none initially | content/reference hybrid |
| `Product` | `products` | `id` | `category_id` -> `Category` | `slug`, `sku`, `status`, `category_id`, `sort_order` | unique `slug`; optional unique `sku` after validation | price should become decimal |
| `ProductImage` | `product_images` | `id` | `product_id` -> `Product` | `product_id`, `sort_order` | none initially | preserve media URL text |
| `ProductSpec` | `product_specs` | `id` | `product_id` -> `Product` | `product_id`, `sort_order` | optional unique `(product_id, spec_name)` after validation | technical metadata |
| `ProductMaterial` | `product_materials` | surrogate `id` recommended | `product_id`, `material_id` | `product_id`, `material_id` | unique `(product_id, material_id)` | see composite key strategy |
| `ProductProcess` | `product_processes` | surrogate `id` recommended | `product_id`, `process_id` | `product_id`, `process_id`, `step_order` | unique `(product_id, process_id)` | preserve `step_order` |
| `CapabilityMachine` | `capability_machines` | surrogate `id` recommended | `capability_id`, `machine_id` | `capability_id`, `machine_id` | unique `(capability_id, machine_id)` | see composite key strategy |

## CRM Target Schema

| Model | Table | Target PK | Foreign keys | Indexes | Constraints | Notes |
|---|---|---|---|---|---|---|
| `Customer` | `customers` | `id` | none | `email`, `phone`, `created_at` | no unique email until duplicate review | owns customer identity |
| `CustomerNote` | `customer_notes` | `id` | `customer_id` -> `Customer` | `customer_id`, `created_at` | none initially | notes are operational history |
| `ContactRequest` | `contact_requests` | `id` | none in Phase 10.1 | `status`, `is_read`, `created_at`, `email`, `phone` | none initially | do not auto-link to customers yet |

## Sales Target Schema

| Model | Table | Target PK | Foreign keys | Indexes | Constraints | Notes |
|---|---|---|---|---|---|---|
| `QuoteRequest` | `quote_requests` | `id` | `customer_id` -> `Customer` | `customer_id`, `status`, `created_at`, `assigned_to` | none initially | migrate after CRM |
| `QuoteRequestItem` | `quote_request_items` | `id` | `quote_request_id`, nullable `product_id`, nullable `material_id` | `quote_request_id`, `product_id`, `material_id` | none initially | snapshot fields require later ADR |
| `QuoteFile` | `quote_files` | `id` | `quote_request_id` -> `QuoteRequest` | `quote_request_id`, `uploaded_at` | none initially | preserve file URL/path |

## CMS Target Schema

| Model | Table | Target PK | Foreign keys | Indexes | Constraints | Notes |
|---|---|---|---|---|---|---|
| `CmsPage` | `cms_pages` | `id` | none | `slug`, `status`, `sort_order` | unique `slug` | dynamic pages |
| `CmsMenuItem` | `cms_menu_items` | `id` | nullable self `parent_id` | `location`, `parent_id`, `sort_order` | none initially | preserve nested tree |
| `CmsBanner` | `cms_banners` | `id` | none | `placement`, `status`, `sort_order`, `starts_at`, `ends_at` | none initially | media/schedule fields |
| `NewsletterSubscriber` | `newsletter_subscribers` | `id` | none | `email`, `status` | unique `email` | compliance review before writes |

## Accounts Target Schema

Accounts is high-risk. The schema may be designed in Phase 10.1, but production
auth ownership must wait for separate security approval.

| Model | Table | Target PK | Foreign keys | Indexes | Constraints | Notes |
|---|---|---|---|---|---|---|
| `AdminUser` | `admin_users` | `id` | none | `email`, `role`, `is_active` | unique `email` | password hash remains protected |
| `AdminSession` | `admin_sessions` | `session_id` | `admin_id` -> `AdminUser` | `admin_id`, `expires_at`, `last_seen_at` | unique `session_id` | review session cutover separately |
| `LoginAttempt` | `login_attempts` | `id` | none | `email`, `remote_addr`, `success`, `created_at` | none initially | audit/security data |
| `PasswordResetToken` | `password_reset_tokens` | `token` | `admin_id` -> `AdminUser` | `admin_id`, `email`, `expires_at`, `used_at` | unique `token` | do not expose token values in logs/docs |
| `AdminTwoFactorChallenge` | `admin_2fa_challenges` | `challenge_id` | `admin_id` -> `AdminUser` | `admin_id`, `created_at`, `used_at` | unique `challenge_id` | code values are sensitive |
| `AdminActivityLog` | `admin_activity_logs` | `id` | nullable `admin_id` -> `AdminUser` | `admin_id`, `action`, `created_at` | none initially | retain for audit |

## Foreign Key Delete Policy

| Relationship type | Target policy |
|---|---|
| master data referenced by history | `PROTECT` or `DO_NOTHING` until archival policy exists |
| child rows owned by parent | `CASCADE` after data validation |
| optional audit/user links | `SET_NULL` |
| sales quote references | prefer `PROTECT` until snapshot design is approved |

## Required Pre-Migration Validations

- Duplicate check for all unique target fields.
- Orphan check for every foreign key.
- Composite/link table duplicate-pair check.
- Timestamp parseability check.
- Boolean normalization check.
- API response comparison before and after dry run.

## Output Decision

The schema is ready for architecture review, not execution. Phase 10.2 should
perform a dry-run migration only after this design is approved.
