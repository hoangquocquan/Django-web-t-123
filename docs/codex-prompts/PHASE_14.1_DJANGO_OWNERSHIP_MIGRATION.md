# Phase 14.1 - Django Ownership Migration

## Objective

Transfer ownership of one selected low-risk business domain from the legacy system to Django.

## Selected Domain

Newsletter subscribers.

## Scope

- Create Django-owned managed newsletter model
- Create Django migrations
- Add Django service layer
- Add DRF serializer and API endpoint
- Preserve legacy read-only compatibility
- Add ownership tests

## DO NOT

- Delete legacy backend
- Migrate all modules
- Modify unrelated modules
- Remove old services
- Break existing API compatibility

## Expected Status

```text
DJANGO_OWNERSHIP_MIGRATION_COMPLETE
```
