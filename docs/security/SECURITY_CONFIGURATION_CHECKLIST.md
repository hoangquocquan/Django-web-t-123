# Security Configuration Checklist

## CORS

| Check | Status |
| --- | --- |
| `django-cors-headers` installed | Present |
| `CORS_ALLOWED_ORIGINS` configurable | Present |
| Wildcard production CORS | Not configured in baseline |

Recommendation:

- keep `CORS_ALLOWED_ORIGINS` explicit in production
- do not use `*` for admin or authenticated APIs

## CSRF

| Check | Status |
| --- | --- |
| Django `CsrfViewMiddleware` enabled | Present |
| Legacy admin CSRF helper | Present |
| Future write API CSRF/token policy | Pending |

## HTTPS Settings

Django production settings include:

- `SECURE_SSL_REDIRECT`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`

## Headers

Django production settings include:

- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `X_FRAME_OPTIONS = "DENY"`

Recommended future additions:

- Content Security Policy
- Referrer-Policy
- Permissions-Policy

## Debug Mode

| Environment | Debug status |
| --- | --- |
| Django production | `False` |
| Django test | `False` |
| Django development | `True` |
| Legacy local default | development-friendly |

Production must run with debug disabled.

## Cookie Security

Django production secure cookie settings are present. Legacy cookie hardening
should be reviewed before public deployment, especially `Secure` behavior behind
Nginx/load balancer.

## Checklist Result

`SECURITY_CONFIGURATION_REVIEW_COMPLETE`
