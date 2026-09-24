# Database Dry Run Report

## Phase

Phase 10.2 - Database Dry Run Migration Execution

## Result

```text
DRY RUN COMPLETED
```

## Objective

Run a controlled PostgreSQL migration simulation against the non-production
database `mecprecision_dryrun` without importing production data, changing
legacy SQLite or creating production Django migrations.

## Target Environment

| Item | Result |
|---|---|
| PostgreSQL container | `mecprecision_phase10_dryrun_postgres` |
| Container health | `running healthy` |
| PostgreSQL version | `16.14 (Debian 16.14-1.pgdg13+1)` |
| Target database | `mecprecision_dryrun` |
| Target schema | `phase10_dry_run` |
| Target URL in reports | password masked |

## Execution Summary

| Step | Status |
|---|---|
| PostgreSQL dry-run connection | PASS |
| Database name safety check | PASS |
| Legacy SQLite opened read-only | PASS |
| Transient PostgreSQL schema creation | PASS |
| Full copied dataset import | PASS |
| Relationship validation | PASS |
| Composite/link-table uniqueness validation | PASS |
| Row-count comparison | PASS |
| Rollback simulation | PASS |
| Production touched | NO |
| Legacy SQLite mutated | NO |
| Django production migrations generated | NO |

## Migration Time

```text
1.4023 seconds
```

## Row Count Validation

| Table | Source Rows | Target Rows | Result |
|---|---:|---:|---|
| `product_categories` | 8 | 8 | PASS |
| `materials` | 4 | 4 | PASS |
| `machines` | 4 | 4 | PASS |
| `manufacturing_processes` | 5 | 5 | PASS |
| `capabilities` | 4 | 4 | PASS |
| `products` | 11 | 11 | PASS |
| `product_images` | 3 | 3 | PASS |
| `product_specs` | 5 | 5 | PASS |
| `product_materials` | 6 | 6 | PASS |
| `product_processes` | 7 | 7 | PASS |
| `capability_machines` | 5 | 5 | PASS |
| `customers` | 3 | 3 | PASS |
| `customer_notes` | 0 | 0 | PASS |
| `contact_requests` | 6 | 6 | PASS |
| `quote_requests` | 1 | 1 | PASS |
| `quote_request_items` | 1 | 1 | PASS |
| `quote_files` | 1 | 1 | PASS |
| `cms_pages` | 10 | 10 | PASS |
| `cms_menu_items` | 18 | 18 | PASS |
| `cms_banners` | 0 | 0 | PASS |
| `newsletter_subscribers` | 1 | 1 | PASS |
| `admin_users` | 5 | 5 | PASS |
| `admin_sessions` | 1 | 1 | PASS |
| `login_attempts` | 30 | 30 | PASS |
| `password_reset_tokens` | 2 | 2 | PASS |
| `admin_2fa_challenges` | 0 | 0 | PASS |
| `admin_activity_logs` | 55 | 55 | PASS |

## Data Safety

The legacy SQLite database size before and after dry-run remained:

```text
544768 bytes
```

The migration script opened SQLite with read-only URI mode and confirmed row
counts after execution.

## Django Migration Note

This dry-run did not commit Django production migration files. Instead, it
generated transient PostgreSQL DDL inside the dry-run transaction from the
approved Phase 10.1 schema strategy and rolled the transaction back.

This keeps the phase reversible while still validating schema creation, data
copy, row counts, relationships and rollback behavior.

## Completion

The dry-run completed successfully and is ready for architecture review before
any reconciliation or production-oriented migration phase.
