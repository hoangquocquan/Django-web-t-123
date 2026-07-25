# Database Migration Impact Assessment

## Objective

Assess the impact of moving from legacy SQLite ownership to Django database
ownership in a future Phase 10. This document does not perform the migration.

## Schema Risks

- SQLite text-heavy columns may need stricter PostgreSQL field decisions.
- Boolean values currently represented by SQLite must be validated during import.
- Composite key relationship tables require explicit migration handling.
- Existing slug/email uniqueness must be verified before adding strict
  production constraints.

## Data Volume Risks

Current data volume is small, but migration design must still support growth.

Highest observed row counts:

- `admin_activity_logs`: 55
- `login_attempts`: 30
- `cms_menu_items`: 18
- `products`: 11
- `cms_pages`: 10

Risk is low for current volume, but future production data needs batching and
validation scripts.

## Relationship Risks

- Sales depends on CRM and Catalog.
- Quote items reference live product/material master data; historical snapshot
  behavior is not fully solved yet.
- `contact_requests` has no durable relationship to `customers`.
- CMS menu has self-referential parent/child hierarchy.
- Auth tables include session/token/challenge relationships that require
  security approval before ownership migration.

## Constraint Risks

- Unique constraints: category slug, material name, product slug, admin email,
  newsletter email and CMS page slug need duplicate validation.
- Nullable foreign keys and `DO_NOTHING` relationships must be reviewed before
  PostgreSQL enforcement.
- Composite primary keys should either remain composite or receive an approved
  surrogate-key design.

## Indexing Risks

Recommended future indexes:

- `products.slug`
- `products.category_id`
- `contact_requests.status`
- `contact_requests.created_at`
- `quote_requests.customer_id`
- `quote_requests.status`
- `cms_pages.slug`
- `cms_menu_items.location`
- `admin_users.email`
- `admin_sessions.admin_id`
- `admin_activity_logs.created_at`

## Downtime Risks

Current database size suggests low migration time, but downtime risk depends on
production traffic and write freeze strategy.

Phase 10 should define:

- backup point
- legacy write freeze window
- migration dry run
- validation window
- rollback deadline

## Overall Assessment

Application layer readiness is strong for read-only APIs. Database ownership
migration should proceed only after Phase 10 planning confirms backups,
validation scripts, rollback plan and auth boundary decisions.
