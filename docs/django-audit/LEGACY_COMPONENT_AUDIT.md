# Legacy Component Audit

## Scope

This audit inspected legacy components without modifying, deleting, refactoring, or migrating them.

## Legacy Backend Still Present

The legacy backend is still present under:

```text
backend/
```

Key legacy files and folders:

- `backend/app.py`
- `backend/controllers/`
- `backend/services/`
- `backend/repositories/`
- `backend/auth/`
- `backend/cache/`
- `backend/middleware/`
- `backend/api/`
- `backend/database/`
- `backend/uploads/`
- `backend/tests/`

## Legacy Database Still Present

Legacy SQLite database:

```text
backend/database/mecprecision.sqlite
```

Schema and seed files still exist:

- `backend/database/schema.sql`
- `backend/database/seed.sql`
- `backend/database/migrations.py`

## Duplicate Business Logic

Business logic exists in both stacks:

| Domain | Legacy Location | Django Location | Status |
| --- | --- | --- | --- |
| Products/Catalog | `backend/services/products_service.py`, repositories | `django_backend/apps/catalog/`, `apps/api/views/catalog.py` | Duplicated during migration |
| CRM/Contacts | `backend/services/contacts_service.py` | `django_backend/apps/crm/`, `apps/api/views/crm.py` | Duplicated during migration |
| Quotes/Sales | `backend/services/*quote*` style logic via enterprise/sales areas | `django_backend/apps/sales/` | Partially duplicated |
| CMS | `backend/services/cms_service.py` | `django_backend/apps/cms/` | Duplicated during migration |
| Auth/Admin | `backend/auth/`, `backend/services/auth_service.py` | `django_backend/apps/accounts/`, `apps/api/views/auth.py` | Compatibility layer only |
| AI | `backend/services/ai_service.py` | Django exposes `api/v1/ai/chat/` replacement view | Still mixed |

## Deprecated Or Old Framework Indicators

The legacy backend still has:

- Custom `backend/app.py`
- Custom controller routing
- Custom middleware
- Custom repositories
- Legacy upload folders
- SQLite schema ownership

This indicates Django has not replaced the legacy runtime completely.

## Unused Files

No files were deleted or marked for deletion in this audit. Because legacy shutdown requires production traffic evidence and human approval, no legacy file should be treated as safely removable yet.

## Conclusion

Legacy components are still active project components and remain necessary for rollback, database ownership, upload behavior, and historical business logic reference.

Status:

```text
LEGACY_STILL_PRESENT
```
