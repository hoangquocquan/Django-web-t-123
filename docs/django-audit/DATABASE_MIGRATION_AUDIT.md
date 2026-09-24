# Database Migration Audit

## Scope

This audit inspected database configuration, ORM mapping, migrations, and runtime migration status. It did not migrate data or modify schema.

## Database Configuration

Django defines two database connections:

| Alias | Purpose | Configuration |
| --- | --- | --- |
| `default` | Django-owned future database fallback | SQLite `django_backend/db.sqlite3` unless `DATABASE_URL` is configured |
| `legacy` | Read-only legacy source | SQLite URI pointing to `backend/database/mecprecision.sqlite` with `mode=ro` |

## Legacy SQLite Inventory

Read-only inspection found:

```text
Database: backend/database/mecprecision.sqlite
Size: 544768 bytes
Tables: 39
```

Important row counts:

| Table | Rows |
| --- | ---: |
| products | 11 |
| product_categories | 8 |
| contact_requests | 6 |
| customers | 3 |
| quote_requests | 1 |
| cms_pages | 10 |
| cms_menu_items | 18 |
| admin_users | 5 |
| admin_activity_logs | 55 |
| page_visits | 134 |
| ai_translation_cache | 235 |

## Django ORM Coverage

Django maps 27 legacy tables through unmanaged models.

Mapped tables:

- `admin_2fa_challenges`
- `admin_activity_logs`
- `admin_sessions`
- `admin_users`
- `capabilities`
- `capability_machines`
- `cms_banners`
- `cms_menu_items`
- `cms_pages`
- `contact_requests`
- `customer_notes`
- `customers`
- `login_attempts`
- `machines`
- `manufacturing_processes`
- `materials`
- `newsletter_subscribers`
- `password_reset_tokens`
- `product_categories`
- `product_images`
- `product_materials`
- `product_processes`
- `product_specs`
- `products`
- `quote_files`
- `quote_request_items`
- `quote_requests`

Legacy tables not currently mapped by Django unmanaged models include:

- `ai_conversations`
- `ai_translation_cache`
- `auth_email_outbox`
- `enterprise_events`
- `job_queue`
- `news`
- `news_categories`
- `news_tags`
- `notifications`
- `page_visits`
- `system_settings`
- `tags`

## Migration Files

No project app migration folders were found under:

```text
django_backend/apps/
```

`python manage.py showmigrations` reports only built-in Django app migrations:

- `admin`
- `auth`
- `contenttypes`
- `sessions`

All are currently unapplied in the inspected local environment.

## Runtime Migration Status

Command:

```text
python manage.py showmigrations
```

Result:

```text
Built-in Django migrations listed, all unchecked.
No business app migrations listed.
```

## Conclusion

The database is not fully migrated to Django ownership. Django uses unmanaged read-only models against legacy SQLite and has not applied a business schema migration.

Status:

```text
DATABASE_PARTIALLY_MIGRATED_READ_ONLY
```
