# Wave 5 Admin Foundation Report

## Purpose

This report describes the Django-owned foundation layer used by the new admin interface.

## Django Admin Authentication

New endpoint:

`POST /api/v1/admin/login/`

The endpoint uses:

- `FoundationLoginSerializer`
- `FoundationAuthService.login()`
- `FoundationUser`
- `FoundationRole`
- token response compatible with DRF-style API clients

The endpoint returns:

- token
- expiry time
- user profile
- admin navigation metadata

## Django Admin Permission Enforcement

Every protected admin endpoint calls the shared foundation permission helper before running business logic.

Pattern:

1. Read Bearer token from request.
2. Resolve Django-owned foundation user.
3. Check role permissions using `FoundationPermissionService`.
4. Continue only when the requested module/action is allowed.

Permission modules used in Wave 5:

- `dashboard`
- `permissions`
- `products`
- `customers`
- `inventory`
- `orders`
- `workflows`
- `transactions`

## Admin Navigation

The function `admin_navigation_to_dict()` returns a backend-owned navigation contract for admin clients.

This gives frontend/admin UI code a stable list of modules and paths without hardcoding the menu in multiple places.

## Ownership Boundary

Wave 5 admin foundation is Django-owned for API usage. Legacy HTML admin login/session pages remain available until a later frontend cutover phase.

## Result

Django now owns the admin authentication and permission entry point for migrated API domains.
