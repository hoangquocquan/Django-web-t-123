# Phase 10 Row Count Baseline

## Source

Read-only snapshot of:

```text
backend/database/mecprecision.sqlite
```

Database size:

```text
544768 bytes
```

## Baseline Counts

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

## Usage In Phase 10

Use these counts as the first reconciliation target for dry-run migration. Any
target PostgreSQL import must match these counts unless a documented data
cleanup decision is approved.
