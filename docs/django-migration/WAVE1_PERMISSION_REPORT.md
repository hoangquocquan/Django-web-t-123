# Wave 1 Permission Report

## Ownership Result

Django now owns the foundation permission matrix through:

- `FoundationRole`
- `FoundationPermission`
- `FoundationRolePermission`
- `FoundationPermissionService`

## Role Mapping

Legacy roles are mapped as:

- `admin`: full wildcard permission
- `editor`: read/write for operational modules except user and permission administration
- `viewer`: wildcard read permission

## API Protection

Foundation APIs enforce permissions using bearer token authentication and `FoundationPermissionService.require_permission`.

Protected endpoints:

- `/api/v1/foundation/users/`
- `/api/v1/foundation/users/<id>/profile/`
- `/api/v1/foundation/permissions/roles/`
- `/api/v1/foundation/permissions/check/`

## Compatibility

The old read-only permission compatibility service remains available for legacy audit and comparison.

## Remaining Work

Future phases can replace module-specific permission checks with reusable DRF permission classes after more APIs move to Django ownership.
