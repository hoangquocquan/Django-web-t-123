# Media Migration Strategy

Phase: 3.1 - Database Mapping Hardening & ORM Preparation Rules  
Rule: Documentation only. No Django models, migrations, or file moves.

## 1. Purpose

This document defines the media boundary for Phase 4 read-only ORM models.

The legacy project stores media references as paths or URLs in SQLite and on disk. Phase 4 must not move files or change storage behavior.

## 2. Current Media References

Media/path fields exist in multiple tables:

| Table | Fields |
|---|---|
| `admin_users` | `avatar_url` |
| `products` | `main_image`, `thumbnail_url`, `gallery_urls`, `pdf_url`, `video_url`, `og_image` |
| `product_images` | `image_url` |
| `quote_files` | `file_url` |
| `news` | `image`, `thumbnail_url` |
| `contact_requests` | `attachment_url` |
| `cms_banners` | `image_url` |

Current upload/file areas observed in the project include:

```text
backend/uploads/
media/
```

## 3. Phase 4 Rule

Keep media references as plain text fields:

```text
CharField or TextField
```

Do not convert these fields to Django media/storage fields in Phase 4.

Do not use:

- `ImageField`
- `FileField`
- custom storage backend
- automatic file movement
- thumbnail regeneration

## 4. Do Not Change

Phase 4 must not:

- move files,
- rename files,
- change upload paths,
- rewrite URLs,
- migrate storage to Django MEDIA_ROOT,
- migrate storage to S3/CDN,
- delete unused files,
- create thumbnails,
- change database file path values.

## 5. Future Media Storage Phase

A dedicated future media migration phase should decide:

- canonical storage location,
- public URL convention,
- upload validation,
- image optimization,
- thumbnail strategy,
- folder organization,
- permission model,
- backup/restore plan,
- S3/CDN readiness,
- cleanup of orphan files.

## 6. Validation Requirements For Phase 4

For read-only ORM mapping:

- Confirm media/path values are read exactly as stored.
- Confirm public pages still render the same URLs.
- Confirm empty/null media values behave the same.
- Confirm `gallery_urls` and similar text lists are not parsed destructively.
- Confirm no file system writes happen during tests.

## 7. Risk

Risk level:

```text
Medium for read-only, high for upload/write/delete.
```

Media writes must wait until auth, permission, validation, audit log, and rollback strategy are reviewed.
