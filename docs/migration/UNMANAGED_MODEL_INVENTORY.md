# Unmanaged Model Inventory

## Scope

All listed models inherit `LegacyReadOnlyModel` and use `managed = False`.
Phase 9.3 does not convert any model to managed mode.

## Catalog

| App | Model | Table | Managed | Primary key | Foreign keys | Dependencies | Complexity |
|---|---|---|---|---|---|---|---|
| catalog | `Category` | `product_categories` | False | `id` | none | Product | Low |
| catalog | `Material` | `materials` | False | `id` | none | ProductMaterial, QuoteRequestItem | Low |
| catalog | `Machine` | `machines` | False | `id` | none | CapabilityMachine | Low |
| catalog | `ManufacturingProcess` | `manufacturing_processes` | False | `id` | none | ProductProcess | Low |
| catalog | `Capability` | `capabilities` | False | `id` | none | CapabilityMachine | Low |
| catalog | `Product` | `products` | False | `id` | `category_id` -> `Category` | ProductImage, ProductSpec, ProductMaterial, ProductProcess, QuoteRequestItem | Medium |
| catalog | `ProductImage` | `product_images` | False | `id` | `product_id` -> `Product` | Product | Low |
| catalog | `ProductSpec` | `product_specs` | False | `id` | `product_id` -> `Product` | Product | Low |
| catalog | `ProductMaterial` | `product_materials` | False | composite `product`, `material` | `product_id`, `material_id` | Product, Material | High |
| catalog | `ProductProcess` | `product_processes` | False | composite `product`, `process` | `product_id`, `process_id` | Product, ManufacturingProcess | High |
| catalog | `CapabilityMachine` | `capability_machines` | False | composite `capability`, `machine` | `capability_id`, `machine_id` | Capability, Machine | High |

## CRM

| App | Model | Table | Managed | Primary key | Foreign keys | Dependencies | Complexity |
|---|---|---|---|---|---|---|---|
| crm | `Customer` | `customers` | False | `id` | none | CustomerNote, QuoteRequest | Medium |
| crm | `CustomerNote` | `customer_notes` | False | `id` | `customer_id` -> `Customer` | Customer | Low |
| crm | `ContactRequest` | `contact_requests` | False | `id` | none | future customer matching | Medium |

## Sales

| App | Model | Table | Managed | Primary key | Foreign keys | Dependencies | Complexity |
|---|---|---|---|---|---|---|---|
| sales | `QuoteRequest` | `quote_requests` | False | `id` | `customer_id` -> `Customer` | Customer, QuoteRequestItem, QuoteFile | High |
| sales | `QuoteRequestItem` | `quote_request_items` | False | `id` | `quote_request_id`, `product_id`, `material_id` | QuoteRequest, Product, Material | High |
| sales | `QuoteFile` | `quote_files` | False | `id` | `quote_request_id` -> `QuoteRequest` | file storage path | Medium |

## CMS

| App | Model | Table | Managed | Primary key | Foreign keys | Dependencies | Complexity |
|---|---|---|---|---|---|---|---|
| cms | `CmsPage` | `cms_pages` | False | `id` | none | API/frontend content | Low |
| cms | `CmsMenuItem` | `cms_menu_items` | False | `id` | self `parent_id` | nested menu tree | Medium |
| cms | `CmsBanner` | `cms_banners` | False | `id` | none | media paths/scheduling | Medium |
| cms | `NewsletterSubscriber` | `newsletter_subscribers` | False | `id` | none | email export/compliance | Low |

## Accounts

| App | Model | Table | Managed | Primary key | Foreign keys | Dependencies | Complexity |
|---|---|---|---|---|---|---|---|
| accounts | `AdminUser` | `admin_users` | False | `id` | none | sessions, tokens, logs | High |
| accounts | `AdminSession` | `admin_sessions` | False | `session_id` | `admin_id` -> `AdminUser` | active admin sessions | High |
| accounts | `LoginAttempt` | `login_attempts` | False | `id` | none | security audit | Medium |
| accounts | `PasswordResetToken` | `password_reset_tokens` | False | `token` | `admin_id` -> `AdminUser` | password reset workflow | High |
| accounts | `AdminTwoFactorChallenge` | `admin_2fa_challenges` | False | `challenge_id` | `admin_id` -> `AdminUser` | 2FA workflow | High |
| accounts | `AdminActivityLog` | `admin_activity_logs` | False | `id` | nullable `admin_id` -> `AdminUser` | audit log | Medium |

## Highest Complexity Areas

- Composite primary keys in catalog relationship tables.
- Sales quote ownership and snapshot semantics.
- Auth/session/token migration.
- CMS nested menu self-references.
- File path preservation for quote files and media-backed content.
