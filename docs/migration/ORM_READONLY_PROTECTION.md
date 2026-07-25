# ORM Read-Only Protection

Phase: 3.2 - ORM Implementation Readiness & Legacy Database Integration Design  
Rule: Documentation only. No model/base class/router implementation in this phase.

## 1. Purpose

Phase 4 will introduce unmanaged Django ORM models. The main safety risk is accidental writes to the legacy SQLite database.

This document defines how to prevent accidental writes.

## 2. Option A - Base Abstract Model Override

Concept:

```text
LegacyReadOnlyModel
  -> disables save()
  -> disables delete()
```

Advantages:

- Protection is close to the model.
- Easy to understand.
- Blocks common accidental `.save()` and `.delete()`.

Disadvantages:

- Does not automatically block every QuerySet bulk operation.
- Needs consistent inheritance.
- Does not replace database-level protection.

Risks:

- A developer may forget to inherit from the base.
- Raw SQL can still write if allowed.

## 3. Option B - Service Layer Protection

Concept:

```text
Only repository adapters can read legacy ORM.
Services expose read-only use cases.
No write use case exists in Phase 4.
```

Advantages:

- Fits existing service/repository architecture.
- Keeps API away from ORM.
- Easy to test at use-case level.

Disadvantages:

- Requires discipline.
- Does not protect accidental writes from direct model imports.

Risks:

- Future code bypasses the service layer.

## 4. Option C - Database Permission Protection

Concept:

```text
Database user/file permission prevents writes.
```

Advantages:

- Strongest protection when available.
- Protects against raw SQL and ORM writes.

Disadvantages:

- SQLite file permissions can be awkward on local Windows/dev environments.
- The same SQLite file may need writes by legacy backend.
- Harder to configure cross-platform.

Risks:

- Misconfigured permission can break legacy backend.
- Tests may behave differently from local development.

## 5. Recommended Solution

Recommended Phase 4 protection:

```text
Layered protection:
1. Unmanaged models.
2. LegacyReadOnlyModel concept for save/delete blocking.
3. Repository/service-only access.
4. Tests proving write operations are blocked.
5. No migrations against legacy alias.
```

Do not rely on only one protection layer.

## 6. Required Rules

Future Phase 4 rules:

- `save()` disabled for legacy models.
- `delete()` disabled for legacy models.
- bulk update disabled by policy/tests.
- bulk delete disabled by policy/tests.
- raw SQL write operations forbidden.
- API serializers must not save unmanaged legacy models.
- Django admin must not register legacy models for write usage.

## 7. Validation Tests

Tests should attempt and expect failure for:

- instance `.save()`,
- instance `.delete()`,
- queryset `.update()`,
- queryset `.delete()`,
- serializer `.save()` if serializer exists later,
- migration attempt against legacy alias should not exist.

## 8. Rollback

If read-only protection is uncertain:

- do not implement the model,
- do not expose the repository adapter,
- keep legacy backend as data access owner,
- request architecture review.
