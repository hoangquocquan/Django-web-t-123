# Phase 14.1 Migration Result

## Selected Domain

```text
Newsletter subscribers
```

## Migration Files

Created:

- `django_backend/apps/newsletter/migrations/0001_initial.py`
- `django_backend/apps/newsletter/migrations/0002_import_legacy_subscribers.py`

## Applied Migrations

Command:

```text
python manage.py migrate
```

Working directory:

```text
django_backend
```

Applied:

```text
newsletter.0001_initial: OK
newsletter.0002_import_legacy_subscribers: OK
```

Django also applied built-in migrations for:

- `admin`
- `auth`
- `contenttypes`
- `sessions`

## Database Changes

Django default database now owns:

```text
newsletter_subscribers
```

Fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | AutoField primary key | Subscriber identity |
| `email` | EmailField unique | Subscriber email |
| `status` | CharField | Subscription status |
| `source` | CharField | Source of subscription/import |
| `subscribed_at` | DateTimeField | Subscribe timestamp |
| `unsubscribed_at` | DateTimeField nullable | Unsubscribe timestamp |

Index:

```text
newsletter_status_idx(status)
```

## Data Import

The data migration imports legacy rows from:

```text
backend/database/mecprecision.sqlite
```

Imported row observed locally:

```text
id=1
email=hoangquocquanepu@gmail.com
status=subscribed
source=legacy_import
```

## Legacy Database Impact

```text
No legacy database writes were performed.
```

Legacy SQLite size after validation:

```text
544768 bytes
```

## Result

```text
MIGRATION_APPLIED
```
