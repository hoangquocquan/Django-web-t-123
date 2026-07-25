# Legacy Access Layer Strategy

Phase: 3.2 - ORM Implementation Readiness & Legacy Database Integration Design  
Rule: Documentation only. No services, repositories, models, or API endpoints are implemented in this phase.

## 1. Purpose

This document defines how future Django code should access legacy data safely.

The goal is to avoid API code directly depending on ORM models and to keep business behavior isolated.

## 2. Recommended Architecture

```text
API
  -> Service Layer
  -> Repository Adapter
  -> Unmanaged Django ORM
  -> Legacy Database
```

## 3. Layer Responsibilities

### API

Responsibilities:

- HTTP request/response handling.
- Serializer input/output.
- Authentication/permission checks when appropriate.

Rules:

- API must not directly call unmanaged ORM models.
- API must not contain business rules.
- API must not decide database alias behavior.

### Service Layer

Responsibilities:

- Business workflow orchestration.
- Validation coordination.
- Read-only use case behavior.
- Future transaction boundary decisions.

Rules:

- Service should call repository adapter.
- Service should return data structures safe for serializers.
- Service should not hide accidental writes.

### Repository Adapter

Responsibilities:

- Encapsulate legacy ORM queries.
- Select `legacy` database alias.
- Preserve query behavior compatible with legacy repositories.
- Provide a testable interface for parity checks.

Rules:

- Repository adapter may use unmanaged ORM.
- Repository adapter should remain read-only in Phase 4.
- Repository adapter should not call API or UI code.

### Unmanaged Django ORM

Responsibilities:

- Map legacy tables.
- Provide safe query interface.

Rules:

- `managed = False`.
- `db_table` set explicitly.
- write methods blocked or forbidden by service/repository policy.

## 4. Why Keep Repository/Service Pattern

Reasons:

- Legacy project already has service/repository separation.
- It reduces API coupling to database details.
- It makes contract testing easier.
- It allows future switch from legacy ORM to managed Django models without rewriting API.
- It keeps business logic out of models.
- It creates a clear place for read-only/write protection.

## 5. Do Not Do

Do not:

- let API views directly call `.objects`,
- put business workflows in Django models,
- put SQL compatibility logic in serializers,
- write to legacy database in Phase 4,
- bypass repository adapter for convenience.

## 6. Future Naming Direction

Future implementation can use:

```text
apps/catalog/repositories/
apps/catalog/services/
```

or equivalent module structure approved in `DJANGO_APP_STRUCTURE_DECISION.md`.

## 7. Validation

Each repository adapter should have parity tests:

- legacy repository output vs unmanaged ORM output,
- row counts,
- important field values,
- relationship counts,
- ordering and filtering behavior.
