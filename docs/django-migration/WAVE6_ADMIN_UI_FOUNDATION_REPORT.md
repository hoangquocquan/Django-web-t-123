# Wave 6 Admin UI Foundation Report

## Django UI App

Created app:

`django_backend/apps/admin_ui/`

Main files:

- `forms.py`
- `views.py`
- `urls.py`
- `templates/admin_ui/`
- `static/admin_ui/admin.css`

## Routing

Browser-facing MEC admin UI now uses:

`/admin/`

Django technical admin remains available at:

`/django-admin/`

## Authentication Integration

The login page posts to `/admin/login/`.

Flow:

```text
Browser form
-> Django CSRF middleware
-> AdminLoginForm
-> FoundationAuthService.login()
-> Store Foundation token in Django session
-> Redirect to dashboard
```

## Permission-Based Menu

The sidebar is generated from the current Foundation user role.

Only modules with read permission are shown.

Write actions call `FoundationPermissionService.require_permission()` before service-layer writes.

## Security

- CSRF middleware remains enabled.
- Login and all browser forms include CSRF tokens.
- Admin secrets are not embedded in templates.
- Production approval remains human-controlled.

## Result

Django now owns the browser admin UI foundation for migrated modules.
