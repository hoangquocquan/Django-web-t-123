# Wave 4 Database Ownership Report

## Classification

| Table / Domain | Classification | Owner / Notes |
|---|---|---|
| `foundation_users`, `foundation_user_profiles`, `foundation_roles`, `foundation_permissions`, `foundation_auth_tokens` | DJANGO_OWNED | Wave 1 foundation ownership |
| `newsletter_subscribers` Django model | DJANGO_OWNED | Django has managed newsletter table; legacy table name overlap remains compatibility-sensitive |
| `business_products`, `business_customers` | DJANGO_OWNED | Wave 2 business core ownership |
| `inventory_warehouses`, `inventory_items`, `inventory_transactions` | DJANGO_OWNED | Wave 2 inventory ownership |
| `transaction_orders`, `transaction_order_items`, `order_status_history`, `workflow_approvals`, `transaction_history` | DJANGO_OWNED | Wave 3 transaction ownership |
| `admin_users`, `admin_sessions`, auth legacy tables | SHARED | Django owns new auth; legacy read-only compatibility remains |
| `products`, `product_categories`, product related tables | SHARED | Legacy read-only catalog remains while business product ownership is Django-owned |
| `customers`, `customer_notes`, `contact_requests` | SHARED | Django owns business customers; legacy CRM/contact remains for compatibility |
| `quote_requests`, `quote_request_items`, `quote_files` | SHARED | Django owns orders; legacy quote read APIs remain |
| `cms_pages`, `cms_menu_items`, `cms_banners` | SHARED | Django maps read-only; legacy admin CMS still owns writes |
| `news`, `news_categories`, `news_tags`, `tags` | LEGACY_ONLY | Not fully migrated to managed Django ownership |
| `media/uploads` files | LEGACY_ONLY | Filesystem upload ownership remains legacy |
| `ai_conversations`, `ai_translation_cache` | LEGACY_ONLY | Runtime AI data remains legacy |
| `system_settings` | LEGACY_ONLY | Admin configurable settings remain legacy |
| `job_queue`, `notifications` | LEGACY_ONLY | Operational async/notification state remains legacy |
| `enterprise_events` | SHARED | Legacy event table copied into Django transaction history, legacy still exists |
| `page_visits` | LEGACY_ONLY | Analytics tracking remains legacy |

## Managed Model Status

Django managed apps:

- `apps.newsletter`
- `apps.foundation`
- `apps.business_core`
- `apps.transaction_domain`

Django unmanaged compatibility apps:

- `apps.accounts`
- `apps.catalog`
- `apps.crm`
- `apps.sales`
- `apps.cms`

## Final Database Ownership Status

```text
PARTIALLY_FINALIZED
```

Core operational ownership is Django-owned, but legacy remains necessary for compatibility, CMS/admin, media, AI runtime, settings, and payment future work.

## Safety Review

No destructive migration is approved. Legacy tables must remain until a separate shutdown phase verifies traffic, parity, backups, rollback, and human approval.
