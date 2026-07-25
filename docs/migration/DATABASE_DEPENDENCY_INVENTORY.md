# Database Dependency Inventory

## Scope

Phase 9.3 validates database dependencies before Phase 10 Database Ownership
Migration. This is an audit-only document. No schema, data or ownership is
changed.

Legacy database:

```text
backend/database/mecprecision.sqlite
```

Observed size:

```text
544768 bytes
```

## Row Count Snapshot

| Table | Rows |
|---|---:|
| `product_categories` | 8 |
| `materials` | 4 |
| `machines` | 4 |
| `manufacturing_processes` | 5 |
| `capabilities` | 4 |
| `products` | 11 |
| `product_images` | 3 |
| `product_specs` | 5 |
| `product_materials` | 6 |
| `product_processes` | 7 |
| `capability_machines` | 5 |
| `customers` | 3 |
| `customer_notes` | 0 |
| `contact_requests` | 6 |
| `quote_requests` | 1 |
| `quote_request_items` | 1 |
| `quote_files` | 1 |
| `cms_pages` | 10 |
| `cms_menu_items` | 18 |
| `cms_banners` | 0 |
| `newsletter_subscribers` | 1 |
| `admin_users` | 5 |
| `admin_sessions` | 1 |
| `login_attempts` | 30 |
| `password_reset_tokens` | 2 |
| `admin_2fa_challenges` | 0 |
| `admin_activity_logs` | 55 |

## Application Dependencies

| Django app | Models used | Database tables | Legacy dependency | Read/write status | Migration priority |
|---|---|---|---|---|---|
| `apps.catalog` | `Category`, `Material`, `Machine`, `ManufacturingProcess`, `Capability`, `Product`, `ProductImage`, `ProductSpec`, `ProductMaterial`, `ProductProcess`, `CapabilityMachine` | catalog/product/capability tables | required for product APIs and sales quote item references | read-only | 1 |
| `apps.crm` | `Customer`, `CustomerNote`, `ContactRequest` | `customers`, `customer_notes`, `contact_requests` | required by customer/contact APIs and sales quote owner records | read-only | 2 |
| `apps.sales` | `QuoteRequest`, `QuoteRequestItem`, `QuoteFile` | quotation tables | depends on CRM customers and Catalog products/materials | read-only | 3 |
| `apps.cms` | `CmsPage`, `CmsMenuItem`, `CmsBanner`, `NewsletterSubscriber` | CMS content/menu/newsletter tables | required by CMS API and future frontend content cutover | read-only | 4 |
| `apps.accounts` | `AdminUser`, `AdminSession`, `LoginAttempt`, `PasswordResetToken`, `AdminTwoFactorChallenge`, `AdminActivityLog` | auth/admin tables | required for auth preparation and future admin ownership | read-only | 5 |
| `apps.api` | no database models | none directly | calls service layer only | read-only | cross-cutting |
| `apps.core` | no business models | legacy database file health check | required for health cutover | read-only | cross-cutting |

## Readiness Notes

- Catalog should migrate before Sales because quote items reference products and
  materials.
- CRM should migrate before Sales because quotes reference customers.
- Accounts should not migrate until authentication/security cutover is approved.
- API app has no model ownership and should remain a routing/serialization layer.
